"""Render the 3-D simulation: still images for the report and an MP4 / GIF animation.

    python render_3d.py                       # stills + results/demo3d.mp4 (proposed method, 0.25 m/s)
    python render_3d.py --method m2 --speed 0.3 --out results/demo_m2.mp4
"""
import argparse
import os

import cv2
import numpy as np

from sortarm.sim import M1, M2, M3, DESC, MOVE, TRANS, IDLE
from sortarm.sim3d import Sim3D

HERE = os.path.dirname(os.path.abspath(__file__))
VIEW = dict(azimuth=68, elevation=-32, distance=1.25, lookat=(-0.06, 0.04, 0.04))


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
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--fps", type=int, default=25)
    ap.add_argument("--out", default=os.path.join(HERE, "results", "demo3d.mp4"))
    ap.add_argument("--stills", action="store_true", help="also save report stills")
    a = ap.parse_args()
    m = {"m1": M1, "m2": M2, "m3": M3}[a.method]
    sim = Sim3D(m, a.speed, a.seed, n_obj=a.n)
    names = {IDLE: "waiting for next target", MOVE: "moving to predicted intercept point",
             DESC: "descending with visual servo" if m.terminal else "descending (open loop)",
             TRANS: "carrying cube to its colour bin"}
    writer = None
    frames = []
    stills = {}
    orig = sim._arm_step
    next_frame = [0.0]
    count = [0]
    want = {MOVE: 3, DESC: 3, TRANS: 3}
    seen = {k: 0 for k in want}
    prev_state = [None]

    def step(dt):
        orig(dt)
        t = sim.t
        if sim.state != prev_state[0]:
            if sim.state in want:
                seen[sim.state] += 1
            prev_state[0] = sim.state
        if t >= next_frame[0]:
            next_frame[0] += 1.0 / a.fps
            img = sim.w.view_image(960, 540, **VIEW)
            lab = ["%s | belt %.2f m/s | t = %.1f s" % (m.name, sim.vb, t), "arm: " + names.get(sim.state, "placing cube"),
                   "sorted: %d / %d" % (len(sim.bin_log), sim.n_obj)]
            frame = caption(img[..., ::-1], lab)
            frames.append(frame)
            if a.stills and sim.state in want and seen[sim.state] == want[sim.state] and sim.state not in stills:
                if sim.state == DESC and (t - sim.t_state) < 0.1:
                    return
                stills[sim.state] = img.copy()
        count[0] += 1

    sim._arm_step = step
    res = sim.run(t_max=200)
    print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in res.items()})
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    h, w = frames[0].shape[:2]
    vw = cv2.VideoWriter(a.out, cv2.VideoWriter_fourcc(*"mp4v"), a.fps, (w, h))
    for f in frames:
        vw.write(f)
    vw.release()
    print("video", a.out, len(frames), "frames")
    if a.stills:
        names2 = {MOVE: "still_move", DESC: "still_descend", TRANS: "still_transport"}
        for st, img in stills.items():
            cv2.imwrite(os.path.join(HERE, "figures", names2[st] + ".png"), img[..., ::-1])
        print("stills", list(stills))


if __name__ == "__main__":
    main()
