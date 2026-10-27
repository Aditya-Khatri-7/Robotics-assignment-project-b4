import sys
from dataclasses import replace
import numpy as np
from sortarm.arm import mj
from sortarm.config import Config
from sortarm.cs_world import CsWorld
from sortarm.simcs import JointPlantCS

wn = float(sys.argv[1]); ff = int(sys.argv[2]); jscale = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
cfg = replace(Config(), dt=Config().dt_cs, B_nom=(0.0, 0.0), wn=wn)
w = CsWorld(cfg)
J = w.nominal_inertia()
cfg = replace(cfg, J_nom=(float(J[0]) * jscale, float(J[1]) * jscale))
w.set_initial_pose(cfg.q_home)
p = JointPlantCS(cfg, w); p.ff = bool(ff)
q0 = list(cfg.q_home)
for k in range(60):
    p.step(q0, [0, 0], [0, 0], cfg.dt)
print("hold err", [round(1000 * (p.q[i] - q0[i]), 2) for i in (0, 1)], "mrad")
T, amp = 0.8, 0.8
errs = []
for k in range(int(T / cfg.dt)):
    t = k * cfg.dt
    s, ds, dds = mj(t / T)
    p.step([q0[0] + amp * s, q0[1]], [amp * ds / T, 0], [amp * dds / T ** 2, 0], cfg.dt)
    errs.append(amp * s - (p.q[0] - q0[0]))
for k in range(100):
    p.step([q0[0] + amp, q0[1]], [0, 0], [0, 0], cfg.dt)
print("wn", wn, "ff", ff, "Jscale", jscale, "max err mrad", round(1000 * max(abs(e) for e in errs), 1), "final err mrad", round(1000 * (amp - (p.q[0] - q0[0])), 1))
w.close()
