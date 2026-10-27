"""Held-out robustness study: conditions never used for tuning (strong lighting swing, unseen belt speeds, 50 % defects).
Uses the fast planar simulation. Output: results/heldout.csv

    python heldout_study.py [--seeds N]
"""
import csv
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace

from sortarm.config import Config
from sortarm.sim import M2, M3, Sim

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "heldout.csv")
CASES = [("baseline", 0.22, {}, 0.12), ("strong_light", 0.22, {}, 0.35), ("unseen_speed", 0.17, {}, 0.12),
         ("many_defects", 0.22, {"p_defect": 0.5}, 0.12), ("low_fps", 0.22, {"fps": 10.0}, 0.12)]


def job(a):
    case, m, v, over, light, seed = a
    s = Sim(m, v, seed, n_obj=12, cfg=replace(Config(), **over), light_amp=light).run()
    s.update(case=case, seed=seed)
    return s


def main():
    n = int(sys.argv[sys.argv.index("--seeds") + 1]) if "--seeds" in sys.argv else 8
    jobs = [(c, m, v, o, l, sd) for c, v, o, l in CASES for m in (M2, M3) for sd in range(200, 200 + n)]
    with ProcessPoolExecutor() as ex:
        rows = list(ex.map(job, jobs, chunksize=2))
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=sorted(rows[0]))
        w.writeheader()
        w.writerows(rows)
    import pandas as pd
    d = pd.DataFrame(rows)
    d["rate"] = 100 * d["correct"] / d["n"]
    print(d.groupby(["case", "method"])[["rate", "false_accept", "colour_err", "grasp_err_mm"]].mean().round(2))


if __name__ == "__main__":
    main()
