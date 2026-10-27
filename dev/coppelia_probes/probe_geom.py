from dataclasses import replace
from sortarm.config import Config
from sortarm.cs_world import CsWorld
from sortarm.simcs import JointPlantCS

cfg = replace(Config(), dt=Config().dt_cs, B_nom=(0.0, 0.0))
w = CsWorld(cfg)
sim = w.sim
J = w.nominal_inertia()
cfg = replace(cfg, J_nom=(float(J[0]), float(J[1])))
p = JointPlantCS(cfg, w)
l1 = sim.getObjectParent(w.j2)
l2 = sim.getObjectParent(w.j3)
ref = [0.8, 1.0]
for k in range(150):
    p.step(ref, [0, 0], [0, 0], cfg.dt)
print("joint q", [round(v, 3) for v in p.q])
for name, h in (("j2", w.j2), ("l1", l1), ("j3", w.j3), ("l2", l2), ("tip", w.tip)):
    print(name, [round(v, 3) for v in sim.getObjectPosition(h, sim.handle_world)])
import math
print("tip parent is j3:", sim.getObjectParent(w.tip)==w.j3, "tip type", sim.getObjectType(w.tip))
kids = sim.getObjectsInTree(w.j3, sim.handle_all, 1)
for h in kids: print(" child", h, sim.getObjectAlias(h), [round(v,3) for v in sim.getObjectPosition(h, sim.handle_world)])
print("expected tip", round(0.35 * math.cos(0.8) + 0.3 * math.cos(1.8), 3), round(0.35 * math.sin(0.8) + 0.3 * math.sin(1.8), 3))
print("static l1", sim.getObjectInt32Param(l1, sim.shapeintparam_static), "base static", sim.getObjectInt32Param(sim.getObjectParent(w.j1), sim.shapeintparam_static))
w.close()
