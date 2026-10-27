from dataclasses import replace
from sortarm.config import Config
from sortarm.cs_world import CsWorld

cfg = replace(Config(), dt=Config().dt_cs)
w = CsWorld(cfg)
sim = w.sim
P = sim.primitiveshape_cuboid
# A: dynamic from the start
a = w._shape(P, [0.03, 0.03, 0.03], [0.3, -0.35, 0.3], [1, 0, 0], mass=0.05, static=False, resp=True)
# B: static, toggled to dynamic after 10 steps
b = w._shape(P, [0.03, 0.03, 0.03], [0.4, -0.35, 0.3], [0, 1, 0], mass=0.05, static=True, resp=True)
for k in range(10):
    w.step()
sim.setObjectInt32Param(b, sim.shapeintparam_static, 0)
sim.resetDynamicObject(b)
for k in range(60):
    w.step()
    if k in (0, 20, 59):
        print(k, "A z", round(sim.getObjectPosition(a, sim.handle_world)[2], 3), "B z", round(sim.getObjectPosition(b, sim.handle_world)[2], 3))
w.close()
