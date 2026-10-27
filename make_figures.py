"""Create every figure used in the report and slides (figures/*.png)."""
import math
import os
import pickle

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle, FancyArrowPatch
import numpy as np
import pandas as pd

from sortarm.arm import Scara
from sortarm.config import Config
from sortarm.vision import Camera, COLORS, BIN_NAMES

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
RES = os.path.join(HERE, "results")
os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
                     "font.size": 10, "axes.grid": True, "grid.alpha": 0.3, "figure.dpi": 110,
                     "savefig.dpi": 200, "savefig.bbox": "tight"})
CC = {"red": "#d62728", "green": "#2ca02c", "blue": "#1f77b4", "reject": "#555555"}
MC = {"M1 Stop-and-go": "#7f7f7f", "M2 Predictive": "#ff7f0e", "M3 Proposed": "#1f4e9c"}
cfg = Config()
arm = Scara(cfg)


def save(name):
    plt.savefig(os.path.join(FIG, name + ".png"))
    plt.close()


def box(ax, x, y, w, h, text, fc="#e8eef7", ec="#1f4e9c", fs=9):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec=ec, lw=1.3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)


def arrow(ax, p, q, text=None):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=12, lw=1.2, color="#333"))
    if text:
        ax.text((p[0] + q[0]) / 2, (p[1] + q[1]) / 2 + 0.12, text, ha="center", fontsize=7.5, style="italic")


def fig_block():
    import figs_block
    figs_block.draw(plt, box, arrow, save)


def fig_layout():
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    ax.add_patch(Rectangle((cfg.cam_x0, cfg.cam_y0), cfg.cam_x1 - cfg.cam_x0, cfg.cam_y1 - cfg.cam_y0,
                           fc="none", ec="#8a5a1c", ls="--", lw=1.2, label="camera field of view"))
    ax.add_patch(Rectangle((-0.9, cfg.belt_y_lo), 1.3, cfg.belt_y_hi - cfg.belt_y_lo, fc="#cfcfcf", ec="#555", label="conveyor"))
    ax.add_patch(Rectangle((-0.30, cfg.belt_y_lo), 0.60, cfg.belt_y_hi - cfg.belt_y_lo, fc="#9ec5e8", alpha=0.6, ec="none", label="pick window"))
    ax.add_patch(Circle((0, 0), cfg.L1 + cfg.L2, fc="none", ec="#1f4e9c", ls=":", label="max reach"))
    for (bx, by), c in zip(cfg.bins, BIN_NAMES):
        ax.add_patch(Rectangle((bx - 0.06, by - 0.06), 0.12, 0.12, fc=CC[c], ec="k", alpha=0.8))
        ax.text(bx, by + 0.08, c, ha="center", fontsize=8)
    q = arm.ik(0.1, 0.33)
    p1 = (cfg.L1 * math.cos(q[0]), cfg.L1 * math.sin(q[0]))
    p2 = arm.fk(q)
    ax.plot([0, p1[0], p2[0]], [0, p1[1], p2[1]], "-o", color="#222", lw=4, ms=7, label="SCARA (example pose)")
    ax.annotate("belt direction", xy=(-0.4, 0.43), xytext=(-0.75, 0.43), arrowprops=dict(arrowstyle="-|>"), va="center", fontsize=8)
    ax.set_aspect("equal"); ax.set_xlim(-0.95, 0.8); ax.set_ylim(-0.5, 0.7)
    ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)"); ax.legend(loc="upper left", bbox_to_anchor=(0.0, -0.18), fontsize=7, ncol=3)
    save("fig_layout")


def fig_camera():
    import cv2
    import mujoco
    from sortarm.mj_world import World, RGBA
    rng = np.random.default_rng(3)
    cam = Camera(cfg, rng)
    w = World(cfg, 3, ["red"] * 3)
    spec = [(-0.55, 0.31, 0.4, "red", "square"), (-0.28, 0.36, 1.0, "green", "circle"), (0.02, 0.29, 0.2, "blue", "square")]
    for k, (x, y, th, c, sh) in enumerate(spec):
        w.set_part(k, c, sh)
        w.place_cube(k, x, y, th)
    mujoco.mj_forward(w.model, w.data)
    raw = w.top_image()
    img = np.clip(raw.astype(np.float32) + cam._bg_tex[..., None] + rng.normal(0, cfg.img_noise, raw.shape), 0, 255).astype(np.uint8)
    dets = cam.detect(img)
    vis = img.copy()
    for x, y, c, a, sh in dets:
        u, v = cam.w2pix(x, y)
        cv2.rectangle(vis, (int(u) - 18, int(v) - 18), (int(u) + 18, int(v) + 18), (255, 255, 255), 1)
        cv2.putText(vis, c + " " + sh, (int(u) - 30, int(v) - 24), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    fig, axs = plt.subplots(2, 1, figsize=(6.6, 3.2))
    for a_, im, t in zip(axs, (img, vis), ("(a) frame rendered by the MuJoCo overhead camera (800 x 173 px, noise added)", "(b) detected blobs: colour, shape and centroid")):
        a_.imshow(im[..., ::-1]); a_.set_title(t, fontsize=9); a_.axis("off")
    save("fig_camera")


def fig_scene():
    import mujoco
    from sortarm.mj_world import World, RGBA
    w = World(cfg, 6, ["red"] * 6)
    spec = [(-0.70, 0.30, 0.3, "red", "square"), (-0.52, 0.36, 0.9, "blue", "circle"), (-0.30, 0.31, 0.1, "green", "square"), (-0.08, 0.35, 0.7, "red", "circle"), (0.14, 0.30, 1.2, "green", "square")]
    for k, (x, y, th, c, sh) in enumerate(spec):
        w.set_part(k, c, sh)
        w.place_cube(k, x, y, th)
    w.data.qpos[w.q_adr[0]], w.data.qpos[w.q_adr[1]] = 0.55, -1.1
    mujoco.mj_forward(w.model, w.data)
    img = w.view_image(1100, 560, azimuth=62, elevation=-30, distance=1.45, lookat=(-0.10, 0.02, 0.03))
    import cv2
    csf = os.path.join(FIG, "cs_still_transport.png")
    if os.path.exists(csf):
        csimg = cv2.imread(csf)[..., ::-1]
        fig, axs = plt.subplots(1, 2, figsize=(7.4, 2.5))
        for ax, im, t in zip(axs, (csimg, img), ("(a) CoppeliaSim", "(b) MuJoCo")):
            ax.imshow(im); ax.set_title(t, fontsize=9); ax.axis("off"); ax.grid(False)
        plt.tight_layout()
    else:
        fig, ax = plt.subplots(figsize=(7.0, 3.6))
        ax.imshow(img); ax.axis("off"); ax.grid(False)
    save("fig_scene")


def fig_flow():
    fig, ax = plt.subplots(figsize=(6.4, 6.0))
    ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 12.6); ax.grid(False)
    steps = [("Capture frame (20 fps); +80 ms latency", 11.8),
             ("HSV blobs -> colour, shape, world (x, y)", 10.5),
             ("Associate to track; Kalman update\n(camera position + encoder speed)", 9.1),
             ("Arm idle and track confirmed (>= 3 hits)?", 7.8),
             ("Predict p(t), search earliest t_a:\nIK exists and min-jerk time fits", 6.4),
             ("Choose shortest-cycle target; claim it", 5.1),
             ("Move to hover above p(t_g) (min-jerk)", 3.9),
             ("Descend 0.2 s with visual servo\nv = Kt (p_hat(t_g) - p_tip)", 2.6),
             ("|p_tip - p_part| < 10 mm?  Grasp, transport to\ncolour bin (cube) or reject bin (cylinder)", 1.2)]
    hs = [1.05 if "\n" in t else 0.85 for t, _ in steps]
    for (txt, y), h in zip(steps, hs):
        box(ax, 0.6, y - h / 2, 8.8, h, txt, fs=11)
    for i in range(len(steps) - 1):
        arrow(ax, (5, steps[i][1] - hs[i] / 2), (5, steps[i + 1][1] + hs[i + 1] / 2))
    save("fig_flowchart")


def fig_dh():
    fig, ax = plt.subplots(figsize=(5.2, 3.0))
    ax.axis("off"); ax.grid(False)
    rows = [["Joint i", "a_i (m)", "alpha_i", "d_i (m)", "theta_i"], ["1", "0.35", "0", "0", "q1"], ["2", "0.30", "0", "0", "q2"],
            ["3", "0", "0", "-z", "0 (prismatic)"]]
    tb = ax.table(cellText=rows[1:], colLabels=rows[0], loc="center", cellLoc="center")
    tb.auto_set_font_size(False); tb.set_fontsize(9); tb.scale(1, 1.6)
    save("fig_dh_table")


def agg(df, by, col="success"):
    g = df.groupby(by)
    return g


def fig_control(ex):
    import pickle
    csp = os.path.join(RES, "cs_control.pkl")
    cs = pickle.load(open(csp, "rb")) if os.path.exists(csp) else None
    col = {"P": "#1f77b4", "PD": "#ff7f0e", "PID": "#2ca02c", "PID+FF": "#d62728"}
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.9))
    for k, (t, y) in ex["step"].items():
        axs[0].plot(t, y, color=col[k], label=k)
        if cs:
            axs[0].plot(cs["step"][k][0], cs["step"][k][1], color=col[k], ls="--", lw=1.0)
    axs[0].axhline(0.5, color="k", lw=0.6, ls=":")
    axs[0].set(xlabel="time (s)", ylabel="joint 1 angle (rad)", title="(a) 0.5 rad step"); axs[0].legend(fontsize=7)
    axs[0].set_ylim(-0.05, 1.1)
    for k, (t, e) in ex["track"].items():
        axs[1].plot(t, 1000 * e, color=col[k], label=k)
        if cs:
            axs[1].plot(cs["track"][k][0], 1000 * cs["track"][k][1], color=col[k], ls="--", lw=1.0)
    axs[1].set(xlabel="time (s)", ylabel="tracking error (mrad)", title="(b) minimum-jerk tracking, 1.2 rad in 0.8 s")
    axs[1].legend(fontsize=7)
    axs[1].plot([], [], "k-", lw=1, label="MuJoCo"); axs[1].plot([], [], "k--", lw=1, label="CoppeliaSim")
    axs[1].legend(fontsize=7, ncol=2)
    plt.tight_layout(); save("fig_control")


def fig_vision(ex):
    v = pd.read_csv(os.path.join(RES, "vision_study.csv"))
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.7))
    for light, g in v.groupby("light"):
        axs[0].plot(g.noise, 100 * g.color_correct / g.objects, "-o", ms=4, label="colour, light x%.2f" % light)
        axs[0].plot(g.noise, 100 * g.shape_correct / g.objects, "--s", ms=3, label="shape, light x%.2f" % light)
        axs[1].plot(g.noise, g.rmse_mm, "-o", ms=4, label="light x%.2f" % light)
    axs[0].set(xlabel="image noise sigma (gray levels)", ylabel="correct classification (%)", title="(a) colour and shape accuracy")
    axs[1].set(xlabel="image noise sigma (gray levels)", ylabel="position RMSE (mm)", title="(b) centroid position error")
    axs[0].legend(fontsize=6, ncol=2)
    plt.tight_layout(); save("fig_vision")


def errbar(g, col):
    m = g[col].mean(); s = g[col].std()
    return m, s


def fig_speed(df):
    d = df[df.tag == "speed"].copy()
    d["succ"] = 100 * d.correct / d.n
    d["lostp"] = 100 * d.lost / d.n
    fig, axs = plt.subplots(1, 3, figsize=(7.4, 2.7))
    for m, g in d.groupby("method"):
        gg = g.groupby("v")
        for ax, col in zip(axs, ("succ", "throughput", "grasp_err_mm")):
            mu, sd = gg[col].mean(), gg[col].std()
            ax.errorbar(mu.index, mu.values, sd.values, marker="o", ms=4, capsize=2, label=m, color=MC[m], lw=1.3)
    axs[0].set(xlabel="belt speed (m/s)", ylabel="objects sorted correctly (%)", title="(a) sorting success")
    axs[1].set(xlabel="belt speed (m/s)", ylabel="throughput (objects/min)", title="(b) throughput")
    axs[2].set(xlabel="belt speed (m/s)", ylabel="grasp position error (mm)", title="(c) tip-to-object error")
    axs[0].legend(fontsize=7, loc="lower left")
    plt.tight_layout(); save("fig_speed")


def fig_stress(df):
    fig, axs = plt.subplots(1, 3, figsize=(7.4, 2.7))
    for ax, tag, col, xl in zip(axs, ("latency", "ripple", "noise"), ("latency", "belt_ripple", "img_noise"),
                                ("vision latency (s)", "belt speed ripple (fraction)", "image noise sigma")):
        d = df[df.tag == tag].copy()
        d["succ"] = 100 * d.correct / d.n
        for m, g in d.groupby("method"):
            gg = g.groupby(col)["succ"]
            ax.errorbar(gg.mean().index, gg.mean().values, gg.std().values, marker="o", ms=4, capsize=2, label=m, color=MC[m])
        ax.set(xlabel=xl, ylabel="sorted correctly (%)")
    axs[0].legend(fontsize=7)
    plt.tight_layout(); save("fig_stress")


def fig_ablation(df):
    d = df[df.tag == "ablation"].copy()
    d["succ"] = 100 * d.correct / d.n
    order = ["M2 Predictive", "M3 w/o visual servo", "M3 w/o Kalman (LS)", "M3 w/o SCT scheduling", "M3 Proposed"]
    g = d.groupby("method")
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 2.8))
    for ax, col, yl in zip(axs, ("succ", "grasp_err_mm"), ("sorted correctly (%)", "grasp error (mm)")):
        mu = g[col].mean().reindex(order); sd = g[col].std().reindex(order)
        ax.bar(range(len(order)), mu.values, yerr=sd.values, capsize=3, color=["#ff7f0e", "#9ecae1", "#9ecae1", "#9ecae1", "#1f4e9c"])
        ax.set_xticks(range(len(order)))
        ax.set_xticklabels(["M2", "no servo", "no Kalman", "no SCT", "M3 full"], fontsize=8)
        ax.set_ylabel(yl)
    axs[0].set_title("(a) success", fontsize=9); axs[1].set_title("(b) grasp error", fontsize=9)
    plt.tight_layout(); save("fig_ablation")


def fig_trace(ex):
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 2.8))
    for tag, name in (("m2", "M2 Predictive"), ("m3", "M3 Proposed")):
        ts, errs, qlog = ex["trial_" + tag]["log"]
        ts = np.array(ts); e = 1000 * np.array(errs)
        # align descents on grasp times
        for i, g in enumerate(ex["trial_" + tag]["grasps"]):
            m = (ts > g["t"] - 0.22) & (ts <= g["t"] + 0.001)
            axs[0].plot(ts[m] - g["t"], e[m], color=MC[name], alpha=0.7, lw=1.1, label=name if i == 0 else None)
        errs_g = [1000 * g["err"] for g in ex["trial_" + tag]["grasps"]]
        axs[1].plot(range(1, len(errs_g) + 1), errs_g, "-o", color=MC[name], ms=4, label=name)
    axs[0].axhline(10, color="k", ls="--", lw=0.8); axs[0].text(-0.21, 10.8, "capture radius 10 mm", fontsize=7)
    axs[0].set(xlabel="time to grasp (s)", ylabel="tip-to-object distance (mm)", title="(a) descent phase, v = 0.25 m/s")
    axs[1].axhline(10, color="k", ls="--", lw=0.8)
    axs[1].set(xlabel="pick number", ylabel="error at contact (mm)", title="(b) error at contact per pick")
    axs[0].legend(fontsize=8)
    plt.tight_layout(); save("fig_trace")


def fig_snapshots(ex):
    import cv2
    pre = "cs_" if os.path.exists(os.path.join(FIG, "cs_still_move.png")) else ""
    names = [(pre + "still_move", "(a) arm moving to the predicted intercept point"), (pre + "still_descend", "(b) descent with visual servo on the moving part"),
             (pre + "still_transport", "(c) transport of the grasped part to its bin")]
    fig, axs = plt.subplots(1, 3, figsize=(7.4, 1.9))
    for ax, (n, t) in zip(axs, names):
        im = cv2.imread(os.path.join(FIG, n + ".png"))[..., ::-1]
        h, w = im.shape[:2]
        ax.imshow(im[int(0.10 * h):int(0.90 * h), int(0.05 * w):int(0.95 * w)])
        ax.set_title(t, fontsize=6.5); ax.axis("off"); ax.grid(False)
    plt.tight_layout(); save("fig_snapshots")


def main():
    with open(os.path.join(RES, "extra.pkl"), "rb") as f:
        ex = pickle.load(f)
    df = pd.read_csv(os.path.join(RES, "all_runs.csv"))
    fig_block(); fig_layout(); fig_scene(); fig_camera(); fig_flow(); fig_dh()
    fig_control(ex); fig_vision(ex); fig_speed(df); fig_stress(df); fig_ablation(df); fig_trace(ex); fig_snapshots(ex)
    print("figures:", sorted(os.listdir(FIG)))


if __name__ == "__main__":
    main()
