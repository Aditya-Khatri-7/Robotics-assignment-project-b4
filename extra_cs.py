"""Joint-controller tests in CoppeliaSim: 0.5 rad step response and 1.2 rad minimum-jerk tracking for P, PD, PID and PID + feedforward.

    python extra_cs.py            # writes results/cs_control.pkl
"""
import os
import pickle
from dataclasses import replace

import numpy as np

from sortarm.arm import mj
from sortarm.config import Config
from sortarm.cs_launch import launch, stop
from sortarm.cs_world import CsWorld
from sortarm.simcs import JointPlantCS

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
PORT = 23300


def make(client, kind):
    cfg = replace(Config(), dt=Config().dt_cs, B_nom=(0.0, 0.0), wn=Config().wn_cs)
    w = CsWorld(cfg, client=client, port=PORT)
    J = w.nominal_inertia()
    cfg = replace(cfg, J_nom=(float(J[0]), float(J[1])))
    w.set_initial_pose(cfg.q_home)
    p = JointPlantCS(cfg, w)
    kp, kd, ki = list(p.kp), list(p.kd), list(p.ki)
    if kind == "P":
        kd, ki = [0.0, 0.0], [0.0, 0.0]
    elif kind == "PD":
        ki = [0.0, 0.0]
    w.configure_controller(kp, kd, ki, cfg.J_nom, cfg.B_nom, cfg.tau_max)
    p.ff = kind == "PID+FF"
    q0 = list(cfg.q_home)
    for _ in range(80):
        p.step(q0, [0, 0], [0, 0], cfg.dt)
    return w, p, cfg, q0


def step_response(client, kind, T=0.6, amp=0.5):
    w, p, cfg, q0 = make(client, kind)
    base = p.q[0]
    y, t = [], []
    for k in range(int(T / cfg.dt)):
        p.step([q0[0] + amp, q0[1]], [0, 0], [0, 0], cfg.dt)
        y.append(p.q[0] - base)
        t.append(k * cfg.dt)
    w.close()
    return np.array(t), np.array(y)


def tracking(client, kind, T=0.8, amp=1.2):
    w, p, cfg, q0 = make(client, kind)
    base = p.q[0]
    err, t = [], []
    for k in range(int(T / cfg.dt)):
        s, ds, dds = mj(k * cfg.dt / T)
        p.step([q0[0] + amp * s, q0[1]], [amp * ds / T, 0], [amp * dds / T ** 2, 0], cfg.dt)
        err.append(amp * s - (p.q[0] - base))
        t.append(k * cfg.dt)
    w.close()
    return np.array(t), np.array(err)


def main():
    proc, client = launch(PORT)
    res = {"step": {}, "track": {}}
    try:
        for kind in ("P", "PD", "PID"):
            res["step"][kind] = step_response(client, kind)
        for kind in ("PD", "PID", "PID+FF"):
            res["track"][kind] = tracking(client, kind)
    finally:
        stop(proc, client)
    with open(os.path.join(OUT, "cs_control.pkl"), "wb") as f:
        pickle.dump(res, f)
    for k, (t, y) in res["step"].items():
        idx = np.where(abs(y - 0.5) > 0.01)[0]
        print("step", k, "overshoot %.1f %%" % (100 * (y.max() - 0.5) / 0.5), "settle %.2f s" % (t[idx[-1]] if len(idx) else 0.0), "final %.3f" % y[-1])
    for k, (t, e) in res["track"].items():
        print("track", k, "max err %.1f mrad" % (1000 * abs(e).max()))


if __name__ == "__main__":
    main()
