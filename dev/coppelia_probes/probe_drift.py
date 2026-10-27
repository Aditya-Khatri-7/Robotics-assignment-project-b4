import sys
from dataclasses import replace
from sortarm.config import Config
from sortarm.cs_world import CsWorld

mode = sys.argv[1] if len(sys.argv) > 1 else "full"
cfg = replace(Config(), dt=Config().dt_cs)
w = CsWorld(cfg)
sim = w.sim
sim.stopSimulation()
while sim.getSimulationState() != sim.simulation_stopped:
    pass
if mode == "notool":
    kids = sim.getObjectsInTree(w.j3, sim.handle_all, 0)
    sim.removeObjects(kids)
if mode == "nogravity":
    sim.setArrayParam(sim.arrayparam_gravity, [0, 0, 0])
sim.setJointPosition(w.j1, cfg.q_home[0]); sim.setJointPosition(w.j2, cfg.q_home[1])
sim.startSimulation()
w.client.step()
z = w.z_to_rel(cfg.z_hover)
for k in range(30):
    if mode != "notool":
        w.apply(0, 0, z)
    else:
        sim.setJointTargetForce(w.j1, 0, True); sim.setJointTargetForce(w.j2, 0, True)
    w.step()
    if k in (0, 4, 9, 19, 29):
        r = w.read_joints()
        print(mode, "step", k + 1, "q", round(r[0], 3), round(r[1], 3), "qd", round(r[2], 3), round(r[3], 3))
w.close()
