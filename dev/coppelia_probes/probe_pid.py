import sys
from dataclasses import replace
import numpy as np
from sortarm.config import Config
from sortarm.cs_world import CsWorld
from sortarm.simcs import JointPlantCS

wn = float(sys.argv[1]) if len(sys.argv) > 1 else 35.0
ff = int(sys.argv[2]) if len(sys.argv) > 2 else 1
cfg = replace(Config(), dt=Config().dt_cs, B_nom=(0.0, 0.0), wn=wn)
w = CsWorld(cfg)
J = w.nominal_inertia()
cfg = replace(cfg, J_nom=(float(J[0]), float(J[1])))
w.set_initial_pose(cfg.q_home)
p = JointPlantCS(cfg, w)
p.ff = bool(ff)
print("J", J, "kp", p.kp, "kd", p.kd, "ki", p.ki)
q0 = list(cfg.q_home)
for k in range(5):
    p.step(q0, [0, 0], [0, 0], cfg.dt)
print("settled q", [round(x, 3) for x in p.q])
ref = [q0[0] + 0.4, q0[1] - 0.3]
for k in range(160):
    p.step(ref, [0, 0], [0, 0], cfg.dt)
    if k % 10 == 0:
        print(k, [round(x, 3) for x in p.q], [round(x, 2) for x in p.qd])
w.close()
