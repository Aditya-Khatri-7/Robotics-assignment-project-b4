"""Bootstrap 95 % confidence intervals of the success rate (correct / n) per study condition -> results/ci_table.csv
    python ci_table.py
"""
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))


def boot_ci(x, n_boot=5000, seed=0):
    rng = np.random.default_rng(seed)
    m = rng.choice(x, (n_boot, len(x))).mean(axis=1)
    return np.percentile(m, [2.5, 97.5])


def main():
    df = pd.concat([pd.read_csv(os.path.join(HERE, "results", f)) for f in ("all_runs.csv", "confirm_runs.csv")], ignore_index=True)
    df["rate"] = 100.0 * df["correct"] / df["n"]
    keys = [k for k in ("tag", "method", "v", "latency", "belt_ripple", "img_noise") if k in df]
    rows = []
    for g, d in df.groupby(keys, dropna=False):
        lo, hi = boot_ci(d["rate"].to_numpy())
        rows.append(dict(zip(keys, g), runs=len(d), mean=d["rate"].mean(), ci_lo=lo, ci_hi=hi))
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(HERE, "results", "ci_table.csv"), index=False)
    print(out.round(1).to_string(index=False))


if __name__ == "__main__":
    main()
