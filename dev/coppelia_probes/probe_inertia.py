from dataclasses import replace
from sortarm.config import Config
from sortarm.cs_world import CsWorld

cfg = replace(Config(), dt=Config().dt_cs)
w = CsWorld(cfg)
w.set_initial_pose(cfg.q_home)
z = w.z_to_rel(cfg.z_hover)
for k in range(10):
    w.apply(0, 0, z); w.step()
print("free", [round(x, 4) for x in w.read_joints()])
for name, t1, t2 in (("tau2=+1", 0.0, 1.0), ("tau1=+5", 5.0, 0.0)):
    q = w.read_joints()
    print(name, "start", [round(x, 3) for x in q])
    for k in range(20):
        w.apply(t1, t2, z); w.step()
        if k in (4, 9, 19):
            r = w.read_joints()
            print("  step", k + 1, "qd", round(r[2], 3), round(r[3], 3), "q", round(r[0], 3), round(r[1], 3))
    for k in range(20):
        w.apply(0, 0, z); w.step()
    r = w.read_joints(); print("  after coast qd", round(r[2], 3), round(r[3], 3))
w.close()
