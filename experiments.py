"""Run all experiments of the report and store CSV files in results/.

    python experiments.py            # full study (about 10-15 minutes on 8 cores)
    python experiments.py --quick    # 3 seeds, for a smoke test
"""
import csv
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace

import numpy as np

from sortarm.config import Config
from sortarm.sim import M1, M2, M3, Method, Sim
from sortarm.sim3d import Sim3D

USE3D = "--2d" not in sys.argv     # default: MuJoCo 3-D physics simulation

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")

M3_NO_TERM = Method("M3 w/o visual servo", kalman=True, terminal=False, sched="sct")
M3_NO_KF = Method("M3 w/o Kalman (LS)", kalman=False, terminal=True, sched="sct")
M3_FIFO = Method("M3 w/o SCT scheduling", kalman=True, terminal=True, sched="fifo")


def job(args):
    tag, method, v, seed, over, n_obj = args
    cfg = replace(Config(), **over)
    r = (Sim3D if USE3D else Sim)(method, v, seed, n_obj=n_obj, cfg=cfg).run()
    if USE3D:
        r["correct_logic"] = r["correct"]
        r["correct"] = r["correct_phys"]      # only cubes that physically rest in the right bin count
    r["tag"] = tag
    r["seed"] = seed
    r.update({k: x for k, x in over.items()})
    return r


def main():
    quick = "--quick" in sys.argv
    seeds = range(3 if quick else 10)
    n_obj = 12 if quick else 15
    jobs = []
    speeds = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35]
    for m in (M1, M2, M3):
        for v in speeds:
            for s in seeds:
                jobs.append(("speed", m, v, s, {}, n_obj))
    # latency sweep at 0.25 m/s
    for m in (M2, M3):
        for lat in (0.0, 0.08, 0.16, 0.24, 0.32):
            for s in seeds:
                jobs.append(("latency", m, 0.25, s, {"latency": lat}, n_obj))
    # belt speed ripple sweep
    for m in (M2, M3):
        for rip in (0.0, 0.03, 0.06, 0.10, 0.15):
            for s in seeds:
                jobs.append(("ripple", m, 0.25, s, {"belt_ripple": rip}, n_obj))
    # camera noise sweep (affects centroid and colour classification)
    for m in (M2, M3):
        for nz in (4.0, 8.0, 20.0, 40.0, 60.0):
            for s in seeds:
                jobs.append(("noise", m, 0.25, s, {"img_noise": nz}, n_obj))
    # ablation at 0.30 m/s with harder conditions (ripple 6 %, latency 0.16 s)
    hard = {"belt_ripple": 0.06, "latency": 0.16}
    for m in (M2, M3_NO_TERM, M3_NO_KF, M3_FIFO, M3):
        for s in seeds:
            jobs.append(("ablation", m, 0.30, s, hard, n_obj))
    if "--confirm" in sys.argv:
        # confirmation study: 30 fresh seeds for the key comparisons (statistics in Section 9.6)
        jobs = []
        for m in (M2, M3_NO_TERM, M3_NO_KF, M3_FIFO, M3):
            for sd in range(100, 130):
                jobs.append(("confirm_ablation", m, 0.30, sd, hard, 15))
        for v in (0.25, 0.30):
            for m in (M2, M3):
                for sd in range(100, 130):
                    jobs.append(("confirm_speed", m, v, sd, {}, 15))
        for m in (M2, M3):
            for sd in range(100, 130):
                jobs.append(("confirm_ripple", m, 0.25, sd, {"belt_ripple": 0.15}, 15))
    t0 = time.time()
    print(len(jobs), "runs")
    with ProcessPoolExecutor() as ex:
        rows = list(ex.map(job, jobs, chunksize=4))
    print("done in %.0f s" % (time.time() - t0))
    os.makedirs(OUT, exist_ok=True)
    keys = sorted({k for r in rows for k in r})
    with open(os.path.join(OUT, "quick.csv" if quick else ("confirm_runs.csv" if "--confirm" in sys.argv else ("all_runs.csv" if USE3D else "all_runs_2d.csv"))), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
