from dataclasses import replace
from sortarm.arm import Scara
from sortarm.config import Config
from sortarm.cs_world import CsWorld, CUBE_H
from sortarm.simcs import JointPlantCS

cfg = replace(Config(), dt=Config().dt_cs, B_nom=(0.0, 0.0))
w = CsWorld(cfg)
sim = w.sim
J = w.nominal_inertia()
cfg = replace(cfg, J_nom=(float(J[0]), float(J[1])))
arm = Scara(cfg)
p = JointPlantCS(cfg, w)
for k in range(60):
    p.step(cfg.q_home, [0, 0], [0, 0], cfg.dt)
q = arm.ik(0.0, -0.35, cfg.q_home)
w.spawn_part(0, "green", "square", 0.2, 0.3, 0.3)
w.step()
p.z_cmd = w.z_to_rel(0.0)
# go to the belt part, attach
qa = arm.ik(0.2, 0.3, cfg.q_home)
for k in range(260):
    p.step(qa, [0, 0], [0, 0], cfg.dt)
w.attach(0)
p.z_cmd = w.z_to_rel(cfg.z_hover)
for k in range(300):
    p.step(q, [0, 0], [0, 0], cfg.dt)
tp = sim.getObjectPosition(w.tip, sim.handle_world)
print("tip at bin", [round(v, 3) for v in tp], "part", [round(v, 3) for v in sim.getObjectPosition(w.parts[0], sim.handle_world)])
w.detach(0)
h = w.parts[0]
for nm in ('shapeintparam_static','shapeintparam_respondable','shapeintparam_kinematic','shapeintparam_init_velocity_a'):
    try: print(nm, sim.getObjectInt32Param(h, getattr(sim, nm)))
    except Exception as e: print(nm, 'ERR', str(e)[:60])
print('parent', sim.getObjectParent(h))
print('dynamics enabled', sim.getBoolParam(sim.boolparam_dynamics_handling_enabled))
for k in range(120):
    p.step(q, [0, 0], [0, 0], cfg.dt)
    if k < 12 or k % 20 == 0:
        pos = sim.getObjectPosition(w.parts[0], sim.handle_world)
        vel = sim.getObjectVelocity(w.parts[0])
        print(k, [round(v, 3) for v in pos], "v", [round(v, 2) for v in vel[0]])
w.close()
