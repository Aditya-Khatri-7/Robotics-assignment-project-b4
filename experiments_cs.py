"""Experiments in CoppeliaSim (the assigned platform): cross-platform validation of the MuJoCo study.

    python experiments_cs.py             # about 105 runs, 8 parallel CoppeliaSim instances (about 25 min)
    python experiments_cs.py --quick     # 3 runs, smoke test

Every worker process starts its own headless CoppeliaSim instance on its own port.
"""
import csv
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace

from sortarm.config import Config
from sortarm.sim import M1, M2, M3, Method

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
NO_SERVO = Method("M3 w/o visual servo", kalman=True, terminal=False, sched="sct")
NO_KF = Method("M3 w/o Kalman (LS)", kalman=False, terminal=True, sched="sct")
NO_SCT = Method("M3 w/o SCT scheduling", kalman=True, terminal=True, sched="fifo")
BASE_PORT = 24000


def worker(args):
    wid, jobs = args
    from sortarm.cs_launch import launch, stop
    from sortarm.simcs import SimCS
    port = BASE_PORT + 10 * wid
    rows = []
    proc, client = launch(port)
    try:
        for tag, method, v, seed, over, n_obj in jobs:
            cfg = replace(Config(), **over)
            try:
                s = SimCS(method, v, seed, n_obj=n_obj, cfg=cfg, client=client, port=port)
                r = s.run(t_max=200)
                s.close()
            except Exception as e:                      # keep the study going, report the failure
                print("job failed", tag, method.name, v, seed, repr(e)[:120], flush=True)
                continue
            r["tag"], r["seed"] = tag, seed
            r.update(over)
            r["correct_logic"] = r["correct"]
            r["correct"] = r["correct_phys"]
            rows.append(r)
            print("done", tag, method.name, v, seed, "correct", r["correct"], "/", r["n"], flush=True)
    finally:
        stop(proc, client)
    return rows


def main():
    quick = "--quick" in sys.argv
    seeds = range(1) if quick else range(5)
    n_obj = 8 if quick else 12
    jobs = []
    for m in (M1, M2, M3):
        for v in ((0.25,) if quick else (0.10, 0.20, 0.25, 0.30)):
            for s in seeds:
                jobs.append(("speed", m, v, s, {}, n_obj))
    if not quick:
        for m in (M2, M3):
            for s in seeds:
                jobs.append(("ripple", m, 0.25, s, {"belt_ripple": 0.15}, n_obj))
                jobs.append(("latency", m, 0.25, s, {"latency": 0.32}, n_obj))
        hard = {"belt_ripple": 0.06, "latency": 0.16}
        for m in (M2, NO_SERVO, NO_KF, NO_SCT, M3):
            for s in seeds:
                jobs.append(("ablation", m, 0.30, s, hard, n_obj))
    nw = 1 if quick else 8
    chunks = [(i, jobs[i::nw]) for i in range(nw)]
    t0 = time.time()
    print(len(jobs), "runs on", nw, "CoppeliaSim instances", flush=True)
    with ProcessPoolExecutor(max_workers=nw) as ex:
        rows = [r for part in ex.map(worker, chunks) for r in part]
    print("done in %.0f s, %d rows" % (time.time() - t0, len(rows)))
    os.makedirs(OUT, exist_ok=True)
    keys = sorted({k for r in rows for k in r})
    with open(os.path.join(OUT, "cs_runs_quick.csv" if quick else "cs_runs.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
