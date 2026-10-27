"""Closed-loop simulation in CoppeliaSim (assigned platform of the course project).

Same perception / planning / control software as sim.Sim; the world (arm physics, conveyor, bins, parts and the vision
sensor image) is CoppeliaSim, accessed through its ZMQ remote API."""
import math
from dataclasses import replace

import numpy as np

from .arm import JointPlant
from .config import Config
from .cs_world import CsWorld
from .sim import Sim, TRANS, REL
from .vision import COLORS


class JointPlantCS(JointPlant):
    """Joint control (PID + feedforward) runs inside CoppeliaSim's joint callback; this class sends the references each step."""

    def __init__(self, cfg, world):
        super().__init__(cfg, cfg.q_home, mismatch=False)
        self.w = world
        self.z_cmd = world.z_to_rel(cfg.z_hover)
        self.belt = []
        world.configure_controller(self.kp, self.kd, self.ki, cfg.J_nom, cfg.B_nom, cfg.tau_max)
        self.q = list(cfg.q_home)
        self.qd = [0.0, 0.0]

    def step(self, qr, qdr, qddr, dt):
        st = self.w.io(qr, qdr, qddr if self.ff else (0.0, 0.0), self.z_cmd, self.belt)
        self.w.step()
        self.q = [st[0], st[1]]
        self.qd = [st[2], st[3]]


class SimCS(Sim):
    def __init__(self, method, v_nom, seed, n_obj=12, cfg=None, record=False, light_amp=0.12, world=None, client=None, port=23000):
        cfg = cfg or Config()
        cfg = replace(cfg, dt=cfg.dt_cs, B_nom=(0.0, 0.0), wn=cfg.wn_cs)
        w = world or CsWorld(cfg, client=client, port=port)
        J = w.nominal_inertia()
        cfg = replace(cfg, J_nom=(float(J[0]), float(J[1])))
        super().__init__(method, v_nom, seed, n_obj=n_obj, cfg=cfg, record=record, light_amp=light_amp)
        self.w = w
        w.set_initial_pose(cfg.q_home)
        self.plant = JointPlantCS(cfg, w)

    # ---------------------------------------------------------------- hooks
    def _spawn(self):
        super()._spawn()
        o = self.objs[-1]
        self.w.spawn_part(o["id"], o["color"], o["shape"], o["x"], o["y"], o["th"])

    def _cam_frame(self, t, light):
        c = self.c
        img = self.w.top_image().astype(np.float32) * light + self.cam._bg_tex[..., None]
        img += self.rng.normal(0, c.img_noise, img.shape).astype(np.float32)
        dets = self.cam.detect(np.clip(img, 0, 255).astype(np.uint8))
        if self.held is not None or self.state in (TRANS, REL):
            ex, ey = self.arm.fk(self.plant.q)
            dets = [d for d in dets if math.hypot(d[0] - ex, d[1] - ey) > 0.07]
        return dets

    def _arm_step(self, dt):
        w = self.w
        belt = []
        for o in self.objs:
            if o["state"] == "belt":
                belt.append((w.parts[o["id"]], o["x"], o["y"]))
            elif o["state"] == "lost" and o["x"] < 0.55:
                o["x"] += self.vb * dt
                belt.append((w.parts[o["id"]], o["x"], o["y"]))
        self.plant.belt = belt
        self.plant.z_cmd = w.z_to_rel(self.z)
        self.plant.step(self.qr, self.qdr, self.qddr, dt)

    def _grasp(self, t):
        super()._grasp(t)
        if self.held is not None:
            self.w.attach(self.held["id"])

    def _release(self, t):
        i = self.held["id"]
        super()._release(t)
        self.w.detach(i)

    def run(self, t_max=400.0):
        super().run(t_max)
        for _ in range(int(1.5 / self.c.dt)):            # let released parts fall and settle
            self._arm_step(self.c.dt)
        return self.summary()

    def summary(self):
        r = super().summary()
        ok = 0
        for o in self.objs:
            if o["state"] == "placed":
                x, y = self.w.part_xy(o["id"])
                bx, by = self.c.bins[3 if o["shape"] == "circle" else COLORS.index(o["color"])]
                if abs(x - bx) < 0.075 and abs(y - by) < 0.075:
                    ok += 1
        r["correct_phys"] = ok
        return r

    def close(self):
        self.w.close()
