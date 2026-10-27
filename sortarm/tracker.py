"""Multi-object tracker: nearest-neighbour association + Kalman filter (with conveyor-encoder
fusion) or a plain least-squares line fit (baseline)."""
import numpy as np


class Track:
    def __init__(self, tid, t, x, y, color, v_enc, use_kf, sig=0.003, shape="square"):
        self.id = tid
        self.hist = [(t, x, y)]
        self.votes = {color: 1}
        self.shape_votes = {shape: 1}
        self.last_t = t
        self.hits = 1
        self.fails = 0
        self.use_kf = use_kf
        self.R = np.diag([sig ** 2, sig ** 2, 0.004 ** 2, 0.002 ** 2])
        self.s = np.array([x, y, v_enc, 0.0])
        self.P = np.diag([sig ** 2, sig ** 2, 0.01 ** 2, 0.005 ** 2])
        self.kt = t
        self.claimed = False

    @property
    def color(self):
        return max(self.votes, key=self.votes.get)

    @property
    def shape(self):
        return max(self.shape_votes, key=self.shape_votes.get)

    def _F(self, dt):
        F = np.eye(4)
        F[0, 2] = F[1, 3] = dt
        return F

    def _Q(self, dt, sa=0.08):
        q = sa ** 2
        Q = np.zeros((4, 4))
        Q[0, 0] = Q[1, 1] = q * dt ** 4 / 4
        Q[0, 2] = Q[2, 0] = Q[1, 3] = Q[3, 1] = q * dt ** 3 / 2
        Q[2, 2] = Q[3, 3] = q * dt ** 2
        return Q

    def update(self, t, x, y, color, v_enc, shape="square"):
        self.hist.append((t, x, y))
        if len(self.hist) > 200:                 # bounded memory; only the last 12 samples are used by the line fit
            del self.hist[:-100]
        self.votes[color] = self.votes.get(color, 0) + 1
        self.shape_votes[shape] = self.shape_votes.get(shape, 0) + 1
        self.last_t = t
        self.hits += 1
        dt = t - self.kt
        F = self._F(dt)
        self.s = F @ self.s
        self.P = F @ self.P @ F.T + self._Q(dt)
        self.kt = t
        z = np.array([x, y, v_enc, 0.0])
        S = self.P + self.R
        K = self.P @ np.linalg.inv(S)
        self.s = self.s + K @ (z - self.s)
        self.P = (np.eye(4) - K) @ self.P

    def estimate(self, t, v_hint=None):
        """Return (x, y, vx, vy) predicted at absolute time t."""
        if self.use_kf:
            dt = t - self.kt
            x, y, vx, vy = self.s
            return x + vx * dt, y + vy * dt, vx, vy
        h = self.hist[-12:]
        if len(h) < 2:
            tt, x, y = h[-1]
            return x + (v_hint or 0.0) * (t - tt), y, v_hint or 0.0, 0.0
        T = np.array([a[0] for a in h])
        X = np.array([a[1] for a in h])
        Y = np.array([a[2] for a in h])
        px = np.polyfit(T - T[-1], X, 1)
        py = np.polyfit(T - T[-1], Y, 1)
        dt = t - T[-1]
        return px[1] + px[0] * dt, py[1] + py[0] * dt, px[0], py[0]

    def static_pos(self, t_after):
        """Mean of measurements captured after t_after (belt stopped)."""
        h = [a for a in self.hist if a[0] >= t_after]
        if len(h) < 2:
            return None
        return (float(np.mean([a[1] for a in h])), float(np.mean([a[2] for a in h])))


class Tracker:
    def __init__(self, use_kf, gate=0.05):
        self.tracks = []
        self.use_kf = use_kf
        self.gate = gate
        self.nid = 0

    def process(self, t, dets, v_enc, now):
        free = list(self.tracks)
        for det in dets:
            x, y, color = det[0], det[1], det[2]
            shape = det[4] if len(det) > 4 else "square"
            best, bd = None, self.gate
            for tr in free:
                ex, ey, _, _ = tr.estimate(t)
                d = ((ex - x) ** 2 + (ey - y) ** 2) ** 0.5
                if d < bd:
                    best, bd = tr, d
            if best is not None:
                free.remove(best)
                best.update(t, x, y, color, v_enc, shape)
            else:
                self.tracks.append(Track(self.nid, t, x, y, color, v_enc, self.use_kf, shape=shape))
                self.nid += 1
        self.tracks = [tr for tr in self.tracks if now - tr.last_t < 0.6]
