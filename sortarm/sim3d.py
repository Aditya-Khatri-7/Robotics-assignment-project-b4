"""3-D closed-loop simulation in MuJoCo. Same perception / planning / control software as sim.Sim,
but the arm is a rigid-body model driven by joint torques, the camera image is rendered by MuJoCo and
the cubes are rigid bodies that fall into the bins."""
import math
from dataclasses import replace

import mujoco
import numpy as np

from .arm import JointPlant
from .config import Config
from .mj_world import World, RGBA
from .sim import Sim, TRANS, REL
from .vision import COLORS


class JointPlantMJ(JointPlant):
    """Same PID + feedforward law as JointPlant, but the plant is the MuJoCo rigid-body arm."""

    def __init__(self, cfg, world):
        super().__init__(cfg, cfg.q_home, mismatch=False)
        self.w = world
        self.z_cmd = world.z_to_rel(cfg.z_hover)
        self._read()

    def _read(self):
        d = self.w.data
        self.q = [d.qpos[a] for a in self.w.q_adr]
        self.qd = [d.qvel[a] for a in self.w.qd_adr]

    def step(self, qr, qdr, qddr, dt):
        c = self.c
        d = self.w.data
        self._read()
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
            d.ctrl[j] = max(-tm, min(tm, tau))
        d.ctrl[2] = self.z_cmd
        mujoco.mj_step(self.w.model, d)
        self._read()


class Sim3D(Sim):
    def __init__(self, method, v_nom, seed, n_obj=12, cfg=None, record=False, light_amp=0.12):
        cfg = cfg or Config()
        world = World(cfg, n_obj, ["red"] * n_obj)
        J = world.nominal_inertia((0.3, 1.5))
        cfg = replace(cfg, J_nom=(float(J[0]), float(J[1])))
        super().__init__(method, v_nom, seed, n_obj=n_obj, cfg=cfg, record=record, light_amp=light_amp)
        self.w = world
        self.plant = JointPlantMJ(cfg, world)
        self.cube_geom = [world.model.geom("cg%d" % i).id for i in range(n_obj)]
        self.frames3d = []

    # ---------------------------------------------------------------- hooks
    def _spawn(self):
        super()._spawn()
        o = self.objs[-1]
        i = o["id"]
        self.w.set_part(i, o["color"], o["shape"])
        self.w.place_cube(i, o["x"], o["y"], o["th"])

    def _cam_frame(self, t, light):
        c = self.c
        img = self.w.top_image().astype(np.float32) * light + self.cam._bg_tex[..., None]
        img += self.rng.normal(0, c.img_noise, img.shape).astype(np.float32)
        dets = self.cam.detect(np.clip(img, 0, 255).astype(np.uint8))
        if self.held is not None or self.state in (TRANS, REL):
            ex, ey = self.arm.fk(self.plant.q)
            dets = [d for d in dets if math.hypot(d[0] - ex, d[1] - ey) > 0.07]   # mask the carried cube
        return dets

    def _arm_step(self, dt):
        w, c = self.w, self.c
        for o in self.objs:
            if o["state"] == "belt":
                w.drive_cube(o["id"], o["x"], self.vb)
            elif o["state"] == "lost":
                x, _ = w.cube_xy(o["id"])
                if x < 0.50:
                    w.drive_cube(o["id"], x + self.vb * dt, self.vb)
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

    def _log(self, t):
        super()._log(t)

    def run(self, t_max=400.0):
        r = super().run(t_max)
        # let released cubes fall and settle before the physical check
        for _ in range(int(1.5 / self.c.dt)):
            self._arm_step(self.c.dt)
        return self.summary()

    def summary(self):
        r = super().summary()
        # check physics: a cube counts as sorted only if it really rests in the bin of its colour
        ok = 0
        for o in self.objs:
            if o["state"] == "placed":
                x, y = self.w.cube_xy(o["id"])
                bx, by = self.c.bins[3 if o["shape"] == "circle" else COLORS.index(o["color"])]
                if abs(x - bx) < 0.075 and abs(y - by) < 0.075:
                    ok += 1
        r["correct_phys"] = ok
        return r
