"""Controller step responses, vision study and recorded trials, all on the MuJoCo 3-D model.

    python extra_experiments.py
"""
import math
import os
import pickle
from dataclasses import replace

import mujoco
import numpy as np

from sortarm.arm import mj
from sortarm.config import Config
from sortarm.mj_world import World
from sortarm.sim import M2, M3
from sortarm.sim3d import JointPlantMJ, Sim3D
from sortarm.vision import Camera, COLORS

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(OUT, exist_ok=True)
CFG = Config()


def make_plant(kind=None):
    w = World(CFG, 2, ["red", "red"])
    J = w.nominal_inertia((0.3, 1.5))
    cfg = replace(CFG, J_nom=(float(J[0]), float(J[1])))
    p = JointPlantMJ(cfg, w)
    if kind == "P":
        p.kd = [0.0, 0.0]; p.ki = [0.0, 0.0]; p.ff = False
    elif kind == "PD":
        p.ki = [0.0, 0.0]; p.ff = False
    elif kind == "PID":
        p.ff = False
    elif kind == "PID+FF":
        p.ff = True
    return p, w


def step_response(kind, T=0.6, amp=0.5):
    p, w = make_plant(kind)
    dt = CFG.dt
    q0 = list(p.q)
    t = np.arange(0, T, dt)
    y = []
    for _ in t:
        p.step([q0[0] + amp, q0[1]], [0, 0], [0, 0], dt)
        y.append(p.q[0] - q0[0])
    return t, np.array(y)


def traj_tracking(kind, T=0.8, amp=1.2):
    p, w = make_plant(kind)
    dt = CFG.dt
    q0 = list(p.q)
    t = np.arange(0, T, dt)
    err = []
    for ti in t:
        s, ds, dds = mj(ti / T)
        p.step([q0[0] + amp * s, q0[1]], [amp * ds / T, 0], [amp * dds / T ** 2, 0], dt)
        err.append(amp * s - (p.q[0] - q0[0]))
    return t, np.array(err)


def vision_study(seeds=6, n_frames=90):
    rows = []
    cfg = CFG
    for noise in (4, 8, 15, 25, 40, 60, 80):
        for light in (1.0, 0.7, 1.25):
            tot = det = col = shp_ok = 0
            errs = []
            for s in range(seeds):
                rng = np.random.default_rng(100 + s)
                cam = Camera(replace(cfg, img_noise=float(noise)), rng)
                w = World(cfg, 3, ["red"] * 3)
                for f in range(n_frames // seeds):
                    xs = sorted(rng.uniform(-0.75, 0.25, 3))
                    objs = []
                    for k in range(3):
                        col_name = COLORS[int(rng.integers(3))]
                        shp = "circle" if rng.random() < 0.4 else "square"
                        w.set_part(k, col_name, shp)
                        o = dict(x=float(xs[k]), y=float(rng.uniform(0.29, 0.37)), th=float(rng.uniform(0, 1.5)), color=col_name, shape=shp)
                        if k > 0 and o["x"] - objs[-1]["x"] < 0.08:
                            o["x"] = objs[-1]["x"] + 0.08
                        w.place_cube(k, o["x"], o["y"], o["th"])
                        objs.append(o)
                    mujoco.mj_forward(w.model, w.data)
                    img = w.top_image().astype(np.float32) * light + cam._bg_tex[..., None]
                    img += rng.normal(0, noise, img.shape).astype(np.float32)
                    dets = cam.detect(np.clip(img, 0, 255).astype(np.uint8))
                    for o in objs:
                        tot += 1
                        best = min(dets, key=lambda d: math.hypot(d[0] - o["x"], d[1] - o["y"]), default=None)
                        if best and math.hypot(best[0] - o["x"], best[1] - o["y"]) < 0.02:
                            det += 1
                            errs.append(math.hypot(best[0] - o["x"], best[1] - o["y"]))
                            col += best[2] == o["color"]
                            shp_ok += best[4] == o["shape"]
            rows.append((noise, light, tot, det, col, shp_ok, 1000 * float(np.sqrt(np.mean(np.square(errs)))) if errs else float("nan")))
    return rows


def main():
    res = {}
    res["step"] = {k: step_response(k) for k in ("P", "PD", "PID")}
    res["track"] = {k: traj_tracking(k) for k in ("PD", "PID", "PID+FF")}
    rows = vision_study()
    res["vision"] = rows
    with open(os.path.join(OUT, "vision_study.csv"), "w") as f:
        f.write("noise,light,objects,detected,color_correct,shape_correct,rmse_mm\n")
        for r in rows:
            f.write(",".join(str(x) for x in r) + "\n")
    for m, tag in ((M3, "m3"), (M2, "m2")):
        s = Sim3D(m, 0.25, 7, n_obj=8, record=True)
        s.run()
        res["trial_" + tag] = dict(frames=s.frames, grasps=s.grasps, bins=s.bin_log, summary=s.summary(),
                                  log=(s.ts, s.err_log, s.q_log))
    with open(os.path.join(OUT, "extra.pkl"), "wb") as f:
        pickle.dump(res, f)
    print("saved")


if __name__ == "__main__":
    main()
