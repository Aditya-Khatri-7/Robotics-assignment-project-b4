"""Live demonstration in CoppeliaSim (the platform assigned to this project).

    python demo_cs.py                     # proposed method M3, belt 0.25 m/s: opens the CoppeliaSim window
    python demo_cs.py --method m2 --speed 0.3
    python demo_cs.py --method m1         # stop-and-go baseline
    python demo_cs.py --attach            # use a CoppeliaSim you already started (remote API on port 23000)

The script starts CoppeliaSim (path from COPPELIASIM_PATH, see docs/COPPELIASIM_SETUP.md), builds the cell with the
remote API and runs the closed loop: vision sensor -> OpenCV colour + shape detection -> Kalman tracker -> intercept
planner -> joint controller -> suction pick -> bin.  Rotate the view with the mouse in the CoppeliaSim window.
"""
import argparse
import time

import numpy as np

from sortarm.cs_launch import launch
from sortarm.sim import M1, M2, M3
from sortarm.simcs import SimCS

ap = argparse.ArgumentParser()
ap.add_argument("--method", default="m3", choices=["m1", "m2", "m3"])
ap.add_argument("--speed", type=float, default=0.25, help="belt speed in m/s")
ap.add_argument("--seed", type=int, default=3)
ap.add_argument("--n", type=int, default=10, help="number of parts")
ap.add_argument("--attach", action="store_true", help="connect to a running CoppeliaSim on port 23000")
ap.add_argument("--headless", action="store_true", help="no window (for tests)")
a = ap.parse_args()

m = {"m1": M1, "m2": M2, "m3": M3}[a.method]
proc, client = (None, None)
if not a.attach:
    proc, client = launch(23000, headless=a.headless)
sim = SimCS(m, a.speed, a.seed, n_obj=a.n, client=client, port=23000)
w = sim.w
if not a.headless:                                   # nice default view in the CoppeliaSim window
    cam = w.sim.getObject("/DefaultCamera")
    w._aim(cam, (0.95, -0.95, 0.9), (-0.06, 0.05, 0.05))

orig = sim._arm_step
state = {"grasps": 0}


def step(dt):
    orig(dt)
    if len(sim.grasps) > state["grasps"]:
        g = sim.grasps[-1]
        state["grasps"] = len(sim.grasps)
        tr = sim.target["tr"]
        kind = "cylinder" if tr.shape == "circle" else "cube"
        dest = "REJECT bin" if tr.shape == "circle" else tr.color + " bin"
        print("t=%5.1fs  pick %2d  detected: %-14s -> %-11s  tool-to-part error %.1f mm  %s" % (
            sim.t, state["grasps"], tr.color + " " + kind, dest, 1000 * g["err"], "OK" if g["ok"] else "MISS"))


sim._arm_step = step
print("CoppeliaSim | %s | belt %.2f m/s | %d parts (cubes and cylinders)" % (m.name, a.speed, a.n))
res = sim.run(t_max=300)
print({k: (round(x, 2) if isinstance(x, float) else x) for k, x in res.items()})
print("Parts physically in the correct bin: %d of %d  (false accepts %d, false rejects %d)" % (
    res["correct_phys"], res["n"], res["false_accept"], res["false_reject"]))
if proc is not None and not a.headless:
    input("Press Enter to close CoppeliaSim ...")
if proc is not None:
    from sortarm.cs_launch import stop
    stop(proc, client)
