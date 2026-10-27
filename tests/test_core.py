"""Unit tests: python -m pytest tests -q   (or python tests/test_core.py)"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sortarm.arm import Scara, mj, mj_time, dh_chain
from sortarm.config import Config
from sortarm.tracker import Track
from sortarm.vision import Camera

cfg = Config()
arm = Scara(cfg)


def test_ik_fk_roundtrip():
    rng = np.random.default_rng(0)
    n = 0
    for _ in range(500):
        x, y = rng.uniform(-0.3, 0.3), rng.uniform(0.25, 0.42)
        q = arm.ik(x, y)
        if q is None:
            continue
        n += 1
        fx, fy = arm.fk(q)
        assert abs(fx - x) < 1e-9 and abs(fy - y) < 1e-9
    assert n > 450


def test_dh_chain_matches_fk():
    rng = np.random.default_rng(3)
    for _ in range(100):
        q = (rng.uniform(-2.5, 2.5), rng.uniform(-2.0, 2.0))
        z = rng.uniform(0, 0.2)
        T = dh_chain(cfg, q, z)
        fx, fy = arm.fk(q)
        assert abs(T[0, 3] - fx) < 1e-12 and abs(T[1, 3] - fy) < 1e-12 and abs(T[2, 3] + z) < 1e-12
        assert abs(T[0, 0] - math.cos(q[0] + q[1])) < 1e-12      # tool orientation = q1 + q2 about z


def test_ik_unreachable():
    assert arm.ik(1.0, 1.0) is None


def test_jacobian_finite_difference():
    q = (0.4, 1.3)
    J = np.array(arm.jac(q))
    h = 1e-6
    num = np.zeros((2, 2))
    for j in (0, 1):
        dq = list(q); dq[j] += h
        a, b = arm.fk(q), arm.fk(dq)
        num[:, j] = [(b[0] - a[0]) / h, (b[1] - a[1]) / h]
    assert np.allclose(J, num, atol=1e-5)


def test_resolved_rate_inverse():
    q = (0.2, 1.4)
    v = (0.1, -0.05)
    dq = arm.jinv_mul(q, v)
    J = np.array(arm.jac(q))
    assert np.allclose(J @ np.array(dq), v)


def test_min_jerk_boundaries():
    assert mj(0.0) == (0.0, 0.0, 0.0) and mj(1.0) == (1.0, 0.0, 0.0)
    s, ds, dds = mj(0.5)
    assert abs(s - 0.5) < 1e-12 and abs(dds) < 1e-12
    assert abs(ds - 1.875) < 1e-12          # peak speed factor


def test_mj_time_respects_limits():
    q0, q1 = (0.0, 0.0), (1.5, -1.0)
    T = mj_time(q0, q1, cfg)
    assert 1.875 * 1.5 / T <= cfg.w_max + 1e-9
    assert 5.7735 * 1.5 / T ** 2 <= cfg.a_max + 1e-6


def test_kalman_tracks_constant_velocity():
    rng = np.random.default_rng(1)
    tr = Track(0, 0.0, -0.8, 0.3, "red", 0.2, True)
    for k in range(1, 40):
        t = 0.05 * k
        tr.update(t, -0.8 + 0.2 * t + rng.normal(0, 0.003), 0.3 + rng.normal(0, 0.003), "red", 0.2 + rng.normal(0, 0.003))
    x, y, vx, vy = tr.estimate(2.5)
    assert abs(x - (-0.8 + 0.2 * 2.5)) < 0.004 and abs(vx - 0.2) < 0.01 and abs(vy) < 0.01


def test_homography_accuracy():
    cam = Camera(cfg, np.random.default_rng(0))
    u, v = 240.0, 52.0
    p = cam.Hm @ np.array([u, v, 1.0])
    x, y = p[0] / p[2], p[1] / p[2]
    xe, ye = cam._pix2w_exact(u, v)
    assert math.hypot(x - xe, y - ye) < 0.003


def test_mujoco_arm_matches_analytic_fk():
    import mujoco
    from sortarm.mj_world import World
    w = World(cfg, 1, ["red"])
    rng = np.random.default_rng(2)
    worst = 0.0
    for _ in range(50):
        q = (rng.uniform(-2.5, 2.5), rng.uniform(-2.0, 2.0))
        w.data.qpos[w.q_adr[0]], w.data.qpos[w.q_adr[1]] = q
        mujoco.mj_forward(w.model, w.data)
        p = w.data.xpos[w.tool_site_body]
        fx, fy = arm.fk(q)
        worst = max(worst, math.hypot(p[0] - fx, p[1] - fy))
    assert worst < 1e-9


def test_shape_and_colour_detection():
    import mujoco
    from sortarm.mj_world import World
    rng = np.random.default_rng(5)
    cam = Camera(cfg, rng)
    w = World(cfg, 4, ["red"] * 4)
    spec = [("red", "square"), ("green", "circle"), ("blue", "square"), ("red", "circle")]
    for k, (c, sh) in enumerate(spec):
        w.set_part(k, c, sh)
        w.place_cube(k, -0.7 + 0.25 * k, 0.31 + 0.02 * k, 0.4 * k)
    mujoco.mj_forward(w.model, w.data)
    img = np.clip(w.top_image().astype(np.float32) + cam._bg_tex[..., None] + rng.normal(0, cfg.img_noise, (cam.H, cam.W, 3)), 0, 255).astype(np.uint8)
    dets = sorted(cam.detect(img), key=lambda d: d[0])
    assert [(d[2], d[4]) for d in dets] == spec


def test_all_bins_reachable():
    for i, b in enumerate(cfg.bins):
        assert arm.ik(*b) is not None, "bin %d unreachable" % i
        from sortarm.sim import Sim
        for dx, dy in Sim.SLOTS:
            assert arm.ik(b[0] + dx, b[1] + dy) is not None


def test_end_to_end_m3_sorts_everything():
    from sortarm.sim import M3, Sim
    s = Sim(M3, 0.15, 0, n_obj=5).run()
    assert s["placed"] == 5 and s["correct"] == 5 and s["lost"] == 0
    assert s["false_accept"] == 0 and s["grasp_err_mm"] < 10


def test_runs_are_deterministic():
    from sortarm.sim import M3, Sim
    a = Sim(M3, 0.2, 7, n_obj=3).run()
    b = Sim(M3, 0.2, 7, n_obj=3).run()
    assert a == b


def test_stop_and_go_halts_belt():
    from sortarm.sim import M1, Sim
    s = Sim(M1, 0.2, 0, n_obj=3).run()
    assert s["correct"] == 3 and s["time"] > Sim(M1, 0.2, 0, n_obj=3).c.dt


def test_tracker_two_parts_keep_identity():
    from sortarm.tracker import Tracker
    tk = Tracker(True)
    for k in range(20):
        t = 0.05 * k
        tk.process(t, [(-0.8 + 0.2 * t, 0.28, "red", 0.0, "square"), (-0.8 + 0.2 * t - 0.1, 0.38, "blue", 0.0, "circle")], 0.2, t)
    assert len(tk.tracks) == 2
    assert sorted((tr.color, tr.shape, tr.hits) for tr in tk.tracks) == [("blue", "circle", 20), ("red", "square", 20)]


def test_tracker_survives_dropout_and_drops_stale():
    from sortarm.tracker import Tracker
    tk = Tracker(True)
    for k in range(10):
        t = 0.05 * k
        tk.process(t, [(-0.8 + 0.2 * t, 0.3, "red", 0.0, "square")], 0.2, t)
    for k in range(10, 14):                      # 4 missed frames: track must persist and keep predicting
        tk.process(0.05 * k, [], 0.2, 0.05 * k)
    assert len(tk.tracks) == 1
    x = tk.tracks[0].estimate(0.7)[0]
    assert abs(x - (-0.8 + 0.2 * 0.7)) < 0.01
    tk.process(2.0, [], 0.2, 2.0)
    assert tk.tracks == []


def test_tracker_history_bounded():
    tr = Track(0, 0.0, 0.0, 0.3, "red", 0.2, False)
    for k in range(1, 1000):
        tr.update(0.05 * k, 0.01 * k, 0.3, "red", 0.2)
    assert len(tr.hist) <= 200


def test_latency_zero_and_high_still_sort():
    from dataclasses import replace
    from sortarm.sim import M3, Sim
    for lat in (0.0, 0.16):
        s = Sim(M3, 0.15, 2, n_obj=4, cfg=replace(Config(), latency=lat)).run()
        assert s["placed"] == 4 and s["lost"] == 0


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
