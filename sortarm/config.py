"""Global parameters of the vision-guided sorting arm simulation (SI units)."""
from dataclasses import dataclass


@dataclass
class Config:
    # ---- SCARA arm (base at world origin, joints 1 and 2 revolute, joint 3 prismatic) ----
    L1: float = 0.35
    L2: float = 0.30
    q1_lim: tuple = (-2.97, 2.97)
    q2_lim: tuple = (-2.53, 2.53)
    q_home: tuple = (-0.5, 1.2)
    z_hover: float = 0.10
    z_pick: float = 0.0
    # nominal model used by the controller, true plant is heavier (model mismatch)
    J_nom: tuple = (0.80, 0.25)
    B_nom: tuple = (0.50, 0.20)
    J_true_scale: float = 1.15
    B_true_scale: float = 1.30
    tau_max: tuple = (45.0, 18.0)
    w_max: float = 6.0       # rad/s joint speed limit used by the planner
    a_max: float = 40.0      # rad/s^2 joint accel limit used by the planner
    # PID (wn = 50 rad/s, zeta = 1)
    wn: float = 50.0
    zeta: float = 1.0
    ki_ratio: float = 0.2    # Ki = ki_ratio * Kp * wn
    use_ff: bool = True

    # ---- conveyor ----
    belt_y_lo: float = 0.26
    belt_y_hi: float = 0.40
    belt_ripple: float = 0.03      # +-3 % speed ripple
    belt_ripple_period: float = 6.0
    belt_acc: float = 1.0          # m/s^2 (stop and go ramp)
    enc_noise: float = 0.003       # m/s encoder noise
    spawn_x: float = -0.80
    gap_range: tuple = (0.35, 0.55)  # distance between consecutive objects
    cube: float = 0.030
    x_reach_max: float = 0.30
    x_lost: float = 0.33

    # ---- camera ----
    cam_x0: float = -0.85
    cam_x1: float = 0.35
    cam_y0: float = 0.20
    cam_y1: float = 0.46
    res: float = 0.0015            # m / pixel
    fps: float = 20.0
    latency: float = 0.08          # capture + processing delay
    img_noise: float = 8.0         # gray-level sigma
    calib_noise: float = 0.0008    # m, error of calibration points

    # ---- grasp ----
    t_descend: float = 0.20
    t_rise: float = 0.12
    r_cap: float = 0.010           # suction cup capture radius
    t_plan: float = 0.02
    max_attempts: int = 2
    x_reach_min: float = -0.30     # parts upstream of this x are not yet planned
    x_stop_min: float = -0.25      # stop-and-go: belt stops once a part is beyond this x
    stop_margin: float = 0.03      # stop-and-go: margin before the reach limit
    t_arr_min: float = 0.08        # earliest intercept after planning
    t_arr_step: float = 0.02       # intercept search step
    t_margin: float = 0.01         # slack between move time and intercept time
    plan_period: float = 0.02      # planner call period when idle
    servo_gain: float = 15.0       # visual-servo proportional gain during descent (1/s)
    t_release: float = 0.05        # dwell after suction release
    t_transfer_pad: float = 0.05   # extra time added to the transport move
    bins: tuple = ((-0.25, -0.30), (0.0, -0.35), (0.25, -0.30), (0.48, -0.12))  # red, green, blue, reject
    p_defect: float = 0.25         # share of cylinders (wrong-shape parts) that must go to the reject bin
    cyl_r: float = 0.018           # cylinder radius (cube half side is 0.015)

    dt: float = 0.002
    dt_cs: float = 0.005           # CoppeliaSim physics / control step
    wn_cs: float = 50.0            # joint loop bandwidth used with the 5 ms CoppeliaSim step
