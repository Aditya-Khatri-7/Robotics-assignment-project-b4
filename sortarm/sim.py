"""Closed-loop simulation: conveyor + camera + tracker + planner + SCARA arm with PID joints."""
import math
from collections import deque
from dataclasses import dataclass, replace

import numpy as np

from .arm import Scara, JointPlant, mj, mj_time
from .config import Config
from .tracker import Tracker
from .vision import Camera, COLORS, BIN_NAMES


@dataclass(frozen=True)
class Method:
    name: str
    stop_belt: bool = False      # stop-and-go conveyor
    kalman: bool = False         # Kalman + encoder fusion (else least-squares line fit)
    terminal: bool = False       # visual servo (resolved rate) during descent
    sched: str = "fifo"          # "fifo" or "sct" (shortest cycle time among feasible)


M1 = Method("M1 Stop-and-go", stop_belt=True)
M2 = Method("M2 Predictive", kalman=False, terminal=False, sched="fifo")
M3 = Method("M3 Proposed", kalman=True, terminal=True, sched="sct")

IDLE, MOVE, DESC, TRANS, REL, RISE = range(6)


class Sim:
    def __init__(self, method, v_nom, seed, n_obj=12, cfg=None, record=False, light_amp=0.12):
        self.m = method
        self.c = cfg or Config()
        self.v_nom = v_nom
        self.n_obj = n_obj
        self.rng = np.random.default_rng(seed)
        self.arm = Scara(self.c)
        self.cam = Camera(self.c, self.rng)
        self.plant = JointPlant(self.c, self.c.q_home)
        self.tracker = Tracker(method.kalman)
        self.record = record
        self.light_amp = light_amp
        self.frames = []
        self.objs = []
        self.spawned = 0
        self.since_spawn = 0.0
        self.next_gap = 0.0
        self.vb = 0.0 if method.stop_belt else v_nom
        self.t = 0.0
        self.t_stopped = None
        self.events = deque()
        self.next_cam = 0.0
        self.last_dets = []
        # arm state
        self.state = IDLE
        self.qr = list(self.c.q_home)
        self.qdr = [0.0, 0.0]
        self.qddr = [0.0, 0.0]
        self.z = self.c.z_hover
        self.seg = None
        self.zseg = None
        self.target = None
        self.held = None
        self.bin_count = [0, 0, 0, 0]
        self.bin_idx = 0
        self.next_plan = 0.0
        self.t_state = 0.0
        # logs
        self.grasps = []
        self.bin_log = []
        self.cycle_starts = []
        self.ts = []
        self.err_log = []
        self.q_log = []

    # ------------------------------------------------------------------ world
    def _spawn(self):
        c = self.c
        col = COLORS[int(self.rng.integers(3))]
        y = float(self.rng.uniform(c.belt_y_lo + 0.03, c.belt_y_hi - 0.03))
        shape = "circle" if self.rng.random() < c.p_defect else "square"
        self.objs.append(dict(id=self.spawned, color=col, shape=shape, x=c.spawn_x, y=y,
                              th=float(self.rng.uniform(0, math.pi / 2)), state="belt"))
        self.spawned += 1
        self.since_spawn = 0.0
        self.next_gap = float(self.rng.uniform(*c.gap_range))

    @staticmethod
    def _cls(tr):
        """bin index of a track: cylinders (wrong shape) go to the reject bin, cubes to their colour bin"""
        return 3 if tr.shape == "circle" else COLORS.index(tr.color)

    def _belt_speed_target(self, t):
        c = self.c
        if self.m.stop_belt:
            busy = self.state != IDLE
            cand = [tr for tr in self.tracker.tracks
                    if tr.hits >= 3 and tr.fails < c.max_attempts and not tr.claimed and
                    tr.estimate(t)[0] > c.x_stop_min and tr.estimate(t)[0] < c.x_reach_max - c.stop_margin]
            if busy or cand:
                return 0.0
        return self.v_nom * (1 + c.belt_ripple * math.sin(2 * math.pi * t / c.belt_ripple_period))

    # ------------------------------------------------------------------ planning
    def _estimate(self, tr, t):
        if self.m.stop_belt:
            if self.t_stopped is None:
                return None
            p = tr.static_pos(self.t_stopped)
            if p is None:
                return None
            return (p[0], p[1], 0.0, 0.0)
        return tr.estimate(t)

    def _intercept(self, est, t, q_now):
        c = self.c
        x, y, vx, vy = est
        t0 = t + c.t_plan
        for k in range(0, 100):
            t_arr = t0 + c.t_arr_min + c.t_arr_step * k
            tg = t_arr + c.t_descend
            gx, gy = x + vx * (tg - t), y + vy * (tg - t)
            if gx > c.x_reach_max:
                return None
            if gx < c.x_reach_min:
                continue
            q = self.arm.ik(gx, gy, q_now)
            if q is None:
                continue
            T = mj_time(q_now, q, c)
            if t_arr - t0 >= T + c.t_margin or (self.m.stop_belt and k == 0):
                return t_arr, (gx, gy), q, max(T, t_arr - t0)
        return None

    def _plan(self, t):
        c = self.c
        if self.m.stop_belt and self.vb > 1e-4:
            return
        q_now = tuple(self.plant.q)
        cands = []
        for tr in self.tracker.tracks:
            if tr.hits < 3 or tr.fails >= c.max_attempts or tr.claimed:
                continue
            est = self._estimate(tr, t)
            if est is None:
                continue
            if est[0] < c.x_reach_min or est[0] > c.x_reach_max:
                continue
            cands.append((est[0], tr, est))
        if not cands:
            return
        cands.sort(key=lambda a: -a[0])
        best = None
        for _, tr, est in cands:
            plan = self._intercept(est, t, q_now)
            if plan is None:
                continue
            if self.m.sched == "fifo":
                best = (tr, plan)
                break
            t_arr, p, q, T = plan
            qb = self.arm.ik(*c.bins[self._cls(tr)], q)
            cyc = t_arr + c.t_descend + (mj_time(q, qb, c) if qb else 1.0)
            if best is None or cyc < best[2]:
                best = (tr, plan, cyc)
        if best is None:
            return
        tr, (t_arr, p, q, T) = best[0], best[1]
        tr.claimed = True
        self.target = dict(tr=tr, t_arr=t_arr, p=p, q=q)
        self.seg = (t + c.t_plan, T, tuple(self.qr), q)
        self.zseg = (t + c.t_plan, T, self.z, c.z_hover)
        self.state = MOVE
        self.t_state = t
        self.cycle_starts.append(t)

    # ------------------------------------------------------------------ arm step
    def _set_mj(self, t, seg):
        t0, T, q0, q1 = seg
        s, ds, dds = mj((t - t0) / T)
        for j in (0, 1):
            d = q1[j] - q0[j]
            self.qr[j] = q0[j] + d * s
            self.qdr[j] = d * ds / T
            self.qddr[j] = d * dds / (T * T)

    def _z_at(self, t):
        t0, T, z0, z1 = self.zseg
        s = mj((t - t0) / T)[0]
        return z0 + (z1 - z0) * s

    def _hold(self):
        self.qdr[0] = self.qdr[1] = 0.0
        self.qddr[0] = self.qddr[1] = 0.0

    def _arm(self, t):
        c = self.c
        if self.state == IDLE:
            self._hold()
            if t >= self.next_plan:
                self.next_plan = t + c.plan_period
                self._plan(t)
            return
        if self.state == MOVE:
            if t < self.seg[0]:
                self._hold()
            else:
                self._set_mj(t, self.seg)
                self.z = self._z_at(t)
            if t >= self.seg[0] + self.seg[1]:
                self.state = DESC
                self.t_state = t
                self.zseg = (t, c.t_descend, c.z_hover, c.z_pick)
                self._hold()
            return
        if self.state == DESC:
            self.z = self._z_at(t)
            tr = self.target["tr"]
            if self.m.terminal and tr in self.tracker.tracks:
                # predictive visual servo: drive the tip to the refined grasp point p_hat(t_grasp)
                tg = self.t_state + c.t_descend
                ex, ey, vx, vy = tr.estimate(tg)
                px, py = self.arm.fk(self.plant.q)
                vcx, vcy = c.servo_gain * (ex - px), c.servo_gain * (ey - py)
                d1, d2 = self.arm.jinv_mul(self.qr, (vcx, vcy))
                self.qr[0] += d1 * c.dt
                self.qr[1] += d2 * c.dt
                self.qdr[0], self.qdr[1] = d1, d2
                self.qddr[0] = self.qddr[1] = 0.0
            else:
                self._hold()
            if t - self.t_state >= c.t_descend:
                self._grasp(t)
            return
        if self.state == TRANS:
            self._set_mj(t, self.seg)
            self.z = self._z_at(t)
            if t >= self.seg[0] + self.seg[1]:
                self._release(t)
            return
        if self.state == REL:
            self._hold()
            if t - self.t_state >= c.t_release:
                self.state = IDLE
            return
        if self.state == RISE:
            self._hold()
            self.z = self._z_at(t)
            if t - self.t_state >= c.t_rise:
                self.state = IDLE
            return

    def _grasp(self, t):
        c = self.c
        ex, ey = self.arm.fk(self.plant.q)
        best, bd = None, 1e9
        for o in self.objs:
            if o["state"] == "belt":
                d = math.hypot(o["x"] - ex, o["y"] - ey)
                if d < bd:
                    best, bd = o, d
        tr = self.target["tr"]
        ok = best is not None and bd < c.r_cap
        self.grasps.append(dict(t=t, err=bd, ok=ok, v=self.vb))
        if ok:
            best["state"] = "held"
            self.held = best
            tr.claimed = True
            if tr in self.tracker.tracks:
                self.tracker.tracks.remove(tr)
            qb = self.arm.ik(*self._bin_pos(self._cls(tr)), self.plant.q)
            if qb is None:                                    # bin slot out of reach: fall back to the bin centre
                qb = self.arm.ik(*self.c.bins[self._cls(tr)], self.plant.q)
            q0 = tuple(self.plant.q)
            T = mj_time(q0, qb, c) + c.t_transfer_pad
            self.seg = (t, T, tuple(self.qr), qb)
            self.zseg = (t, T, c.z_pick, c.z_hover)
            self.bin_idx = self._cls(tr)
            self.state = TRANS
        else:
            tr.fails += 1
            tr.claimed = False
            self.zseg = (t, c.t_rise, self.z, c.z_hover)
            self.state = RISE
            self.t_state = t

    SLOTS = ((0, 0), (-.04, -.04), (.04, -.04), (-.04, .04), (.04, .04), (0, -.045), (0, .045), (-.045, 0), (.045, 0))

    def _bin_pos(self, idx):
        """release point inside bin idx: a 3x3 grid of slots so that cubes do not pile up"""
        bx, by = self.c.bins[idx]
        k = self.bin_count[idx] % len(self.SLOTS)
        return bx + self.SLOTS[k][0], by + self.SLOTS[k][1]

    def _release(self, t):
        self.bin_count[self.bin_idx] += 1
        o = self.held
        o["state"] = "placed"
        o["bin"] = self.bin_idx
        true = "reject" if o["shape"] == "circle" else o["color"]
        self.bin_log.append(dict(t=t, true=true, bin=BIN_NAMES[self.bin_idx], shape=o["shape"]))
        self.held = None
        self.state = REL
        self.t_state = t

    # ------------------------------------------------------------------ main loop
    def run(self, t_max=400.0):
        c = self.c
        dt = c.dt
        n_steps = int(t_max / dt)
        rec_every = int(0.02 / dt)
        for i in range(n_steps):
            t = i * dt
            self.t = t
            # spawn
            if self.spawned < self.n_obj and self.since_spawn >= self.next_gap:
                self._spawn()
            # belt
            vt = self._belt_speed_target(t)
            dv = c.belt_acc * dt
            self.vb += max(-dv, min(dv, vt - self.vb))
            if self.m.stop_belt:
                if self.vb < 1e-4 and self.t_stopped is None:
                    self.t_stopped = t
                elif self.vb > 1e-4:
                    self.t_stopped = None
            self.since_spawn += self.vb * dt
            for o in self.objs:
                if o["state"] == "belt":
                    o["x"] += self.vb * dt
                    if o["x"] > c.x_lost:
                        o["state"] = "lost"
            # camera
            if t >= self.next_cam:
                self.next_cam += 1.0 / c.fps
                light = 1.0 + self.light_amp * math.sin(0.9 * t)
                dets = self._cam_frame(t, light)
                self.events.append((t + c.latency, t, dets, self.vb + float(self.rng.normal(0, c.enc_noise))))
            while self.events and self.events[0][0] <= t:
                _, tf, dets, ve = self.events.popleft()
                self.last_dets = dets
                self.tracker.process(tf, dets, ve, t)
            # arm
            self._arm(t)
            self._arm_step(dt)
            if self.held is not None:
                ex, ey = self.arm.fk(self.plant.q)
                self.held["x"], self.held["y"] = ex, ey
            if i % rec_every == 0:
                self._log(t)
            if self.spawned >= self.n_obj and all(o["state"] in ("placed", "lost") for o in self.objs):
                self.t_end = t
                break
        else:
            self.t_end = t_max
        return self.summary()

    # hooks overridden by the 3-D MuJoCo simulation
    def _cam_frame(self, t, light):
        img = self.cam.render([o for o in self.objs if o["state"] == "belt"], self.rng, light)
        return self.cam.detect(img)

    def _arm_step(self, dt):
        self.plant.step(self.qr, self.qdr, self.qddr, dt)

    def _log(self, t):
        ex, ey = self.arm.fk(self.plant.q)
        tgt_err = float("nan")
        if self.state == DESC and self.target is not None:
            tr = self.target["tr"]
            for o in self.objs:
                if o["state"] == "belt" and math.hypot(o["x"] - ex, o["y"] - ey) < 0.06:
                    tgt_err = math.hypot(o["x"] - ex, o["y"] - ey)
        self.ts.append(t)
        self.err_log.append(tgt_err)
        self.q_log.append((self.plant.q[0], self.plant.q[1], self.qr[0], self.qr[1], ex, ey, self.state))
        if self.record:
            self.frames.append(dict(
                t=t, q=tuple(self.plant.q), z=self.z, state=self.state, vb=self.vb,
                objs=[(o["x"], o["y"], o["th"], o["color"], o["state"]) for o in self.objs
                      if o["state"] in ("belt", "held", "placed")],
                dets=list(self.last_dets),
                tracks=[(tr.estimate(t)[0], tr.estimate(t)[1], tr.color) for tr in self.tracker.tracks
                        if tr.hits >= 3]))

    def summary(self):
        n_placed = sum(o["state"] == "placed" for o in self.objs)
        n_ok = sum(b["true"] == b["bin"] for b in self.bin_log)
        n_lost = sum(o["state"] == "lost" for o in self.objs)
        n_circ = sum(o["shape"] == "circle" for o in self.objs)
        false_acc = sum(b["shape"] == "circle" and b["bin"] != "reject" for b in self.bin_log)      # defective part accepted
        false_rej = sum(b["shape"] != "circle" and b["bin"] == "reject" for b in self.bin_log)      # good part rejected
        col_err = sum(b["shape"] != "circle" and b["bin"] not in ("reject", b["true"]) for b in self.bin_log)
        errs = [g["err"] for g in self.grasps if g["ok"]]
        T = self.t_end
        cyc = np.diff(self.cycle_starts) if len(self.cycle_starts) > 1 else []
        return dict(method=self.m.name, v=self.v_nom, n=self.spawned, placed=n_placed, correct=n_ok,
                    defects=n_circ, false_accept=false_acc, false_reject=false_rej, colour_err=col_err,
                    lost=n_lost, attempts=len(self.grasps), grasp_ok=len(errs),
                    grasp_err_mm=1000 * float(np.mean(errs)) if errs else float("nan"),
                    time=T, throughput=60.0 * n_ok / T if T > 0 else 0.0,
                    cycle=float(np.mean(cyc)) if len(cyc) else float("nan"))
