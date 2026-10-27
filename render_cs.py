"""Render the CoppeliaSim cell: still images for the report and an MP4 video (perspective vision sensor).

    python render_cs.py                       # stills + results/demo_cs_m3.mp4 (proposed method, 0.25 m/s)
    python render_cs.py --method m2 --speed 0.3 --out results/demo_cs_m2.mp4
"""
import argparse
import os

import cv2
import numpy as np

from sortarm.cs_launch import launch, stop
from sortarm.sim import M1, M2, M3, DESC, MOVE, TRANS, IDLE
from sortarm.simcs import SimCS

HERE = os.path.dirname(os.path.abspath(__file__))
POS, LOOK = (0.95, -0.95, 0.9), (-0.06, 0.05, 0.05)


def caption(img, lines):
    img = np.ascontiguousarray(img)
    y = 28
    for ln in lines:
        cv2.putText(img, ln, (14, y), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(img, ln, (14, y), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 1, cv2.LINE_AA)
        y += 26
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--method", default="m3", choices=["m1", "m2", "m3"])
    ap.add_argument("--speed", type=float, default=0.25)
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--fps", type=int, default=25)
    ap.add_argument("--stills", action="store_true")
    ap.add_argument("--out", default=os.path.join(HERE, "results", "demo_cs_m3.mp4"))
    ap.add_argument("--port", type=int, default=23200)
    a = ap.parse_args()
    m = {"m1": M1, "m2": M2, "m3": M3}[a.method]
    proc, client = launch(a.port)
    try:
        sim = SimCS(m, a.speed, a.seed, n_obj=a.n, client=client, port=a.port)
        names = {IDLE: "waiting for next target", MOVE: "moving to predicted intercept point",
                 DESC: "descending with visual servo" if m.terminal else "descending (open loop)", TRANS: "carrying part to its bin"}
        frames, stills = [], {}
        want = {MOVE: 2, DESC: 2, TRANS: 2}
        seen = {k: 0 for k in want}
        prev = [None]
        nxt = [0.0]
        orig = sim._arm_step

        def step(dt):
            orig(dt)
            t = sim.t
            if sim.state != prev[0]:
                if sim.state in want:
                    seen[sim.state] += 1
                prev[0] = sim.state
            if t >= nxt[0]:
                nxt[0] += 1.0 / a.fps
                img = sim.w.view_image(960, 540, POS, LOOK)
                lab = ["CoppeliaSim | %s | belt %.2f m/s | t = %.1f s" % (m.name, sim.vb, t), "arm: " + names.get(sim.state, "placing part"),
                       "sorted: %d / %d" % (len(sim.bin_log), sim.n_obj)]
                frames.append(caption(img[..., ::-1], lab))
                if a.stills and sim.state in want and seen[sim.state] == want[sim.state] and sim.state not in stills \
                        and not (sim.state == DESC and (t - sim.t_state) < 0.1):
                    stills[sim.state] = img.copy()

        sim._arm_step = step
        res = sim.run(t_max=200)
        print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in res.items() if k in ("n", "placed", "correct_phys", "lost", "grasp_err_mm", "time")})
        os.makedirs(os.path.dirname(a.out), exist_ok=True)
        h, w = frames[0].shape[:2]
        vw = cv2.VideoWriter(a.out, cv2.VideoWriter_fourcc(*"mp4v"), a.fps, (w, h))
        for f in frames:
            vw.write(f)
        vw.release()
        print("video", a.out, len(frames), "frames")
        if a.stills:
            nm = {MOVE: "cs_still_move", DESC: "cs_still_descend", TRANS: "cs_still_transport"}
            for st, img in stills.items():
                cv2.imwrite(os.path.join(HERE, "figures", nm[st] + ".png"), img[..., ::-1])
            print("stills", list(stills))
        sim.close()
    finally:
        stop(proc, client)


if __name__ == "__main__":
    main()
