from dataclasses import replace
from sortarm.config import Config
from sortarm.cs_world import CsWorld
from sortarm.simcs import JointPlantCS

cfg = replace(Config(), dt=Config().dt_cs, B_nom=(0.0, 0.0))
w = CsWorld(cfg)
sim = w.sim
J = w.nominal_inertia()
cfg = replace(cfg, J_nom=(float(J[0]), float(J[1])))
w.set_initial_pose(cfg.q_home)
p = JointPlantCS(cfg, w)
q0 = list(cfg.q_home)
tipxy = None
for k in range(40):
    p.step(q0, [0, 0], [0, 0], cfg.dt)
tp = sim.getObjectPosition(w.tip, sim.handle_world)
print("tip", [round(v, 3) for v in tp])
w.spawn_part(0, "blue", "square", tp[0], tp[1], 0.0)
w.step()
w.attach(0)
for target in ([q0[0] + 0.6, q0[1]], [q0[0] + 0.6, q0[1] - 0.5]):
    for k in range(120):
        p.step(target, [0, 0], [0, 0], cfg.dt)
    tp = sim.getObjectPosition(w.tip, sim.handle_world)
    pp = sim.getObjectPosition(w.parts[0], sim.handle_world)
    print("tip", [round(v, 3) for v in tp], "part", [round(v, 3) for v in pp], "parent is tip:", sim.getObjectParent(w.parts[0]) == w.tip)
w.close()
