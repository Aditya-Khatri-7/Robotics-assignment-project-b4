"""Block diagram of the system (Figure 2 of the report)."""


def draw(plt, box, arrow, save):
    fig, ax = plt.subplots(figsize=(7.6, 3.9))
    ax.axis("off"); ax.set_xlim(0, 13); ax.set_ylim(0, 6.4); ax.grid(False)
    PH = ("#f3ece1", "#8a5a1c")
    box(ax, 0.1, 4.5, 2.3, 1.3, "Conveyor\n+ encoder", *PH, fs=9)
    box(ax, 3.2, 4.5, 2.6, 1.3, "Kalman tracker\n(camera + encoder)", fs=9)
    box(ax, 6.6, 4.5, 2.6, 1.3, "Intercept planner\n(IK + feasibility)", fs=9)
    box(ax, 10.1, 4.5, 2.8, 1.3, "SCARA arm (MuJoCo\nrigid body) + suction", *PH, fs=9)
    box(ax, 0.1, 1.6, 2.3, 1.3, "Overhead\ncamera (20 fps)", *PH, fs=9)
    box(ax, 3.2, 1.6, 2.6, 1.3, "Vision: colour + shape\n+ homography", fs=9)
    box(ax, 6.6, 1.6, 2.6, 1.3, "Min-jerk path +\nvisual servo", fs=9)
    box(ax, 10.1, 1.6, 2.8, 1.3, "Joint PID + FF\n(torque limits)", fs=9)
    box(ax, 10.1, 0.0, 2.8, 0.9, "Bins R / G / B / reject", *PH, fs=8.5)

    def lab(x, y, t, ha="left"):
        ax.text(x, y, t, fontsize=7.5, style="italic", ha=ha)

    arrow(ax, (1.25, 4.5), (1.25, 2.9)); lab(1.4, 3.65, "belt scene")
    arrow(ax, (2.4, 2.25), (3.2, 2.25)); lab(2.8, 2.4, "image", "center")
    arrow(ax, (4.5, 2.9), (4.5, 4.5)); lab(4.65, 3.65, "x, y, colour, shape")
    arrow(ax, (2.4, 5.15), (3.2, 5.15)); lab(2.8, 5.3, "v_enc", "center")
    arrow(ax, (5.8, 5.15), (6.6, 5.15)); lab(6.2, 5.3, "state", "center")
    arrow(ax, (7.9, 4.5), (7.9, 2.9)); lab(8.05, 3.65, "target, T")
    arrow(ax, (9.2, 2.25), (10.1, 2.25)); lab(9.65, 2.4, "q_ref", "center")
    arrow(ax, (11.1, 2.9), (11.1, 4.5)); lab(11.25, 3.65, "torque")
    arrow(ax, (12.4, 4.5), (12.4, 2.9)); lab(12.5, 3.65, "q")
    arrow(ax, (11.5, 1.6), (11.5, 0.9)); lab(11.65, 1.2, "release")
    save("fig_block_diagram")
