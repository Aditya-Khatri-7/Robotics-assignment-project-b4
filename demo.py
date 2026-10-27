"""Live 3-D demonstration (MuJoCo viewer window).

    python demo.py                      # proposed method M3, belt 0.25 m/s, real-time
    python demo.py --method m2 --speed 0.35
    python demo.py --method m1          # stop-and-go baseline
    python demo.py --slow 2             # half speed (useful while talking)

Mouse: left-drag rotates the camera, right-drag pans, wheel zooms, ESC / close the window to stop.
The console prints every pick (tool-to-cube error, bin) and the final result.
"""
import argparse
import time

import mujoco
import mujoco.viewer

from sortarm.sim import M1, M2, M3, IDLE, MOVE, DESC, TRANS
from sortarm.sim3d import Sim3D

ap = argparse.ArgumentParser()
ap.add_argument("--method", default="m3", choices=["m1", "m2", "m3"])
ap.add_argument("--speed", type=float, default=0.25, help="belt speed in m/s")
ap.add_argument("--seed", type=int, default=3)
ap.add_argument("--n", type=int, default=10, help="number of cubes")
ap.add_argument("--slow", type=float, default=1.0, help="slow-motion factor (2 = half speed)")
a = ap.parse_args()

m = {"m1": M1, "m2": M2, "m3": M3}[a.method]
sim = Sim3D(m, a.speed, a.seed, n_obj=a.n)
STATE = {IDLE: "waiting", MOVE: "moving to predicted intercept", DESC: "descending (visual servo)" if m.terminal else "descending",
         TRANS: "carrying to bin"}
orig = sim._arm_step
t0 = time.time()
last = {"sync": 0.0, "grasps": 0, "print": 0.0}

with mujoco.viewer.launch_passive(sim.w.model, sim.w.data, show_left_ui=False, show_right_ui=False) as v:
    v.cam.azimuth, v.cam.elevation, v.cam.distance = 68, -32, 1.3
    v.cam.lookat[:] = (-0.06, 0.04, 0.04)

    def step(dt):
        orig(dt)
        if not v.is_running():
            raise KeyboardInterrupt
        t = sim.t
        if t - last["sync"] >= 0.02:
            last["sync"] = t
            wait = t * a.slow - (time.time() - t0)
            if wait > 0:
                time.sleep(wait)
            v.sync()
        if len(sim.grasps) > last["grasps"]:
            g = sim.grasps[-1]
            last["grasps"] = len(sim.grasps)
            tr = sim.target["tr"]
            kind = "cylinder" if tr.shape == "circle" else "cube"
            dest = "REJECT bin" if tr.shape == "circle" else tr.color + " bin"
            print("t=%5.1fs  pick %2d  detected: %-14s -> %-11s  tool-to-part error %.1f mm  %s" % (
                t, last["grasps"], tr.color + " " + kind, dest, 1000 * g["err"], "OK" if g["ok"] else "MISS"))

    sim._arm_step = step
    print("%s | belt %.2f m/s | %d parts (cubes and cylinders)  (close the window to stop)" % (m.name, a.speed, a.n))
    try:
        res = sim.run(t_max=300)
        print({k: (round(x, 2) if isinstance(x, float) else x) for k, x in res.items()})
        print("Parts physically in the correct bin: %d of %d  (false accepts %d, false rejects %d)" % (res["correct_phys"], res["n"], res["false_accept"], res["false_reject"]))
        t_end = time.time()
        while v.is_running() and time.time() - t_end < 20:     # keep the window open to look around
            v.sync()
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
