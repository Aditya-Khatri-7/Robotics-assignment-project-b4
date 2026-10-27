"""SCARA kinematics, minimum-jerk trajectories and the joint-level PID plant."""
import math
import numpy as np


class Scara:
    def __init__(self, cfg):
        self.c = cfg

    # D-H: (a, alpha, d, theta) = (L1,0,0,q1), (L2,0,0,q2), (0,0,-z,0)
    def fk(self, q):
        c = self.c
        a = q[0] + q[1]
        return (c.L1 * math.cos(q[0]) + c.L2 * math.cos(a),
                c.L1 * math.sin(q[0]) + c.L2 * math.sin(a))

    def jac(self, q):
        c = self.c
        a = q[0] + q[1]
        s1, c1 = math.sin(q[0]), math.cos(q[0])
        sa, ca = math.sin(a), math.cos(a)
        return ((-c.L1 * s1 - c.L2 * sa, -c.L2 * sa),
                (c.L1 * c1 + c.L2 * ca, c.L2 * ca))

    def jinv_mul(self, q, v):
        (a, b), (c, d) = self.jac(q)
        det = a * d - b * c
        return ((d * v[0] - b * v[1]) / det, (-c * v[0] + a * v[1]) / det)

    def ik(self, x, y, q_prev=None):
        c = self.c
        r2 = x * x + y * y
        c2 = (r2 - c.L1 ** 2 - c.L2 ** 2) / (2 * c.L1 * c.L2)
        if abs(c2) > 1.0:
            return None
        sols = []
        for s in (1.0, -1.0):
            q2 = s * math.acos(c2)
            q1 = math.atan2(y, x) - math.atan2(c.L2 * math.sin(q2), c.L1 + c.L2 * math.cos(q2))
            q1 = (q1 + math.pi) % (2 * math.pi) - math.pi
            if c.q1_lim[0] <= q1 <= c.q1_lim[1] and c.q2_lim[0] <= q2 <= c.q2_lim[1]:
                sols.append((q1, q2))
        if not sols:
            return None
        if q_prev is None:
            q_prev = c.q_home
        return min(sols, key=lambda s: (s[0] - q_prev[0]) ** 2 + (s[1] - q_prev[1]) ** 2)


def dh_matrix(a, alpha, d, theta):
    """Homogeneous D-H transformation A = Rot_z(theta) Trans_z(d) Trans_x(a) Rot_x(alpha) (4 x 4)."""
    ct, st, ca, sa = math.cos(theta), math.sin(theta), math.cos(alpha), math.sin(alpha)
    return np.array([[ct, -st * ca, st * sa, a * ct],
                     [st, ct * ca, -ct * sa, a * st],
                     [0.0, sa, ca, d],
                     [0.0, 0.0, 0.0, 1.0]])


def dh_chain(cfg, q, z=0.0):
    """T_0^3 = A1 A2 A3 for the SCARA D-H table (a, alpha, d, theta): (L1,0,0,q1), (L2,0,0,q2), (0,0,-z,0)."""
    return dh_matrix(cfg.L1, 0.0, 0.0, q[0]) @ dh_matrix(cfg.L2, 0.0, 0.0, q[1]) @ dh_matrix(0.0, 0.0, -z, 0.0)


def mj(tau):
    """Minimum-jerk blend s, ds/dtau, d2s/dtau2 for tau in [0, 1]."""
    if tau <= 0.0:
        return 0.0, 0.0, 0.0
    if tau >= 1.0:
        return 1.0, 0.0, 0.0
    s = 10 * tau ** 3 - 15 * tau ** 4 + 6 * tau ** 5
    ds = 30 * tau ** 2 - 60 * tau ** 3 + 30 * tau ** 4
    dds = 60 * tau - 180 * tau ** 2 + 120 * tau ** 3
    return s, ds, dds


def mj_time(q0, q1, cfg):
    """Shortest minimum-jerk duration respecting joint speed and acceleration limits."""
    T = 0.08
    for a, b in zip(q0, q1):
        d = abs(b - a)
        T = max(T, 1.875 * d / cfg.w_max, math.sqrt(5.7735 * d / cfg.a_max))
    return T


class JointPlant:
    """Two decoupled revolute joints with PID(+feedforward) control and torque saturation."""

    def __init__(self, cfg, q0, kp=None, kd=None, ki=None, use_ff=None, mismatch=True):
        self.c = cfg
        self.q = [q0[0], q0[1]]
        self.qd = [0.0, 0.0]
        self.I = [0.0, 0.0]
        s_j = cfg.J_true_scale if mismatch else 1.0
        s_b = cfg.B_true_scale if mismatch else 1.0
        self.Jt = [j * s_j for j in cfg.J_nom]
        self.Bt = [b * s_b for b in cfg.B_nom]
        wn, z = cfg.wn, cfg.zeta
        self.kp = kp or [j * wn * wn for j in cfg.J_nom]
        self.kd = kd or [2 * z * wn * j for j in cfg.J_nom]
        self.ki = ki or [cfg.ki_ratio * p * wn for p in self.kp]
        self.ff = cfg.use_ff if use_ff is None else use_ff

    def step(self, qr, qdr, qddr, dt):
        c = self.c
        for j in (0, 1):
            e = qr[j] - self.q[j]
            ed = qdr[j] - self.qd[j]
            self.I[j] += e * dt
            lim = 0.5 * c.tau_max[j] / max(self.ki[j], 1e-9)
            self.I[j] = max(-lim, min(lim, self.I[j]))
            tau = self.kp[j] * e + self.kd[j] * ed + self.ki[j] * self.I[j]
            if self.ff:
                tau += c.J_nom[j] * qddr[j] + c.B_nom[j] * qdr[j]
            tm = c.tau_max[j]
            tau = max(-tm, min(tm, tau))
            qdd = (tau - self.Bt[j] * self.qd[j]) / self.Jt[j]
            self.qd[j] += qdd * dt
            self.q[j] += self.qd[j] * dt
