"""MuJoCo 3-D world: SCARA arm, conveyor, colour bins, free-body cubes and an orthographic overhead camera."""
import math

import mujoco
import numpy as np

from .vision import COLORS, BIN_NAMES

RGBA = {"red": "0.84 0.16 0.16 1", "green": "0.17 0.65 0.20 1", "blue": "0.12 0.40 0.80 1", "reject": "0.30 0.30 0.30 1"}
Z_ARM = 0.25          # height of the arm plane above the belt surface
CUBE_H = 0.015


def build_xml(cfg, n_cubes, color_seq):
    L1, L2 = cfg.L1, cfg.L2
    cx, cy = 0.5 * (cfg.cam_x0 + cfg.cam_x1), 0.5 * (cfg.cam_y0 + cfg.cam_y1)
    fovy = cfg.cam_y1 - cfg.cam_y0
    W = int(round((cfg.cam_x1 - cfg.cam_x0) / cfg.res))
    H = int(round(fovy / cfg.res))
    belt_cy = 0.5 * (cfg.belt_y_lo + cfg.belt_y_hi)
    belt_hy = 0.5 * (cfg.belt_y_hi - cfg.belt_y_lo)
    bins = ""
    for (bx, by), name in zip(cfg.bins, BIN_NAMES):
        r = RGBA[name].rsplit(" ", 1)[0] + " 0.55"
        bins += f"""
    <geom name="bin_{name}_f" type="box" pos="{bx} {by} -0.005" size="0.075 0.075 0.005" rgba="{r}" contype="1" conaffinity="1"/>
    <geom type="box" pos="{bx + 0.07} {by} 0.03" size="0.005 0.075 0.035" rgba="{r}" contype="1" conaffinity="1"/>
    <geom type="box" pos="{bx - 0.07} {by} 0.03" size="0.005 0.075 0.035" rgba="{r}" contype="1" conaffinity="1"/>
    <geom type="box" pos="{bx} {by + 0.07} 0.03" size="0.075 0.005 0.035" rgba="{r}" contype="1" conaffinity="1"/>
    <geom type="box" pos="{bx} {by - 0.07} 0.03" size="0.075 0.005 0.035" rgba="{r}" contype="1" conaffinity="1"/>"""
    cubes, eqs = "", ""
    for i in range(n_cubes):
        col = RGBA[color_seq[i]]
        cubes += f"""
    <body name="cube{i}" pos="{-3.0} {0.15 * i} {CUBE_H - 0.04}">
      <joint name="cj{i}" type="free" damping="0.02"/>
      <geom name="cg{i}" type="box" size="{CUBE_H} {CUBE_H} {CUBE_H}" mass="0.05" rgba="{col}" contype="1" conaffinity="1" friction="1 0.01 0.01"/>
      <geom name="yg{i}" type="cylinder" size="{cfg.cyl_r} {CUBE_H}" mass="0.0001" rgba="{col.rsplit(' ', 1)[0]} 0" contype="1" conaffinity="1" friction="1 0.01 0.01"/>
    </body>"""
        eqs += f'\n    <weld name="suck{i}" body1="tool" body2="cube{i}" active="false" solref="0.006 1"/>'
    return f"""
<mujoco model="sorting_cell">
  <compiler angle="radian"/>
  <option timestep="{cfg.dt}" gravity="0 0 -9.81" integrator="implicitfast"/>
  <visual>
    <global offwidth="{max(W, 1280)}" offheight="{max(H, 720)}"/>
    <quality shadowsize="2048"/>
    <headlight ambient="0.30 0.30 0.30" diffuse="0.25 0.25 0.25" specular="0 0 0"/>
  </visual>
  <asset>
    <texture name="sky" type="skybox" builtin="gradient" rgb1="0.55 0.70 0.88" rgb2="0.95 0.97 1.0" width="512" height="512"/>
    <texture name="grid" type="2d" builtin="checker" rgb1="0.80 0.82 0.85" rgb2="0.74 0.76 0.80" width="256" height="256"/>
    <material name="floor" texture="grid" texrepeat="12 12" specular="0" shininess="0"/>
    <material name="matte" specular="0" shininess="0"/>
  </asset>
  <default>
    <joint damping="0"/>
    <geom material="matte"/>
  </default>
  <worldbody>
    <light pos="0 0.3 2.0" dir="0 0 -1" diffuse="0.55 0.55 0.55" specular="0 0 0" castshadow="true"/>
    <light pos="-1 -1 1.5" dir="0.5 0.5 -1" diffuse="0.3 0.3 0.3" specular="0 0 0" castshadow="false"/>
    <geom name="floor" type="plane" pos="0 0 -0.04" size="3 3 0.1" material="floor" contype="1" conaffinity="1"/>
    <geom name="belt" type="box" pos="-0.225 {belt_cy} -0.02" size="0.675 {belt_hy} 0.02" rgba="0.35 0.35 0.37 1" contype="1" conaffinity="1"/>
    <geom type="box" pos="-0.225 {cfg.belt_y_lo - 0.01} 0.01" size="0.675 0.01 0.02" rgba="0.15 0.15 0.15 1" contype="0" conaffinity="0"/>
    <geom type="box" pos="-0.225 {cfg.belt_y_hi + 0.01} 0.01" size="0.675 0.01 0.02" rgba="0.15 0.15 0.15 1" contype="0" conaffinity="0"/>
    <geom type="cylinder" pos="0 0 {Z_ARM / 2 - 0.02}" size="0.045 {Z_ARM / 2 + 0.02}" rgba="0.25 0.25 0.28 1" contype="0" conaffinity="0"/>
    <camera name="top" pos="{cx} {cy} 1.0" xyaxes="1 0 0 0 1 0" fovy="{fovy}" resolution="{W} {H}" projection="orthographic"/>
    {bins}
    <body name="link1" pos="0 0 {Z_ARM}">
      <joint name="q1" type="hinge" axis="0 0 1" range="{cfg.q1_lim[0]} {cfg.q1_lim[1]}" damping="{cfg.B_nom[0]}" armature="0.02"/>
      <geom type="capsule" fromto="0 0 0 {L1} 0 0" size="0.035" mass="1.2" rgba="0.90 0.55 0.10 1" contype="0" conaffinity="0"/>
      <geom type="cylinder" pos="0 0 0" size="0.045 0.03" mass="0.6" rgba="0.2 0.2 0.22 1" contype="0" conaffinity="0"/>
      <body name="link2" pos="{L1} 0 0">
        <joint name="q2" type="hinge" axis="0 0 1" range="{cfg.q2_lim[0]} {cfg.q2_lim[1]}" damping="{cfg.B_nom[1]}" armature="0.01"/>
        <geom type="capsule" fromto="0 0 0 {L2} 0 0" size="0.03" mass="0.8" rgba="0.95 0.70 0.20 1" contype="0" conaffinity="0"/>
        <geom type="cylinder" pos="0 0 0" size="0.04 0.03" mass="0.3" rgba="0.2 0.2 0.22 1" contype="0" conaffinity="0"/>
        <body name="tool" pos="{L2} 0 0" gravcomp="1">
          <joint name="z" type="slide" axis="0 0 1" range="-0.24 0.0" damping="40"/>
          <geom type="cylinder" fromto="0 0 0.0 0 0 0.20" size="0.008" mass="0.15" rgba="0.15 0.15 0.15 1" contype="0" conaffinity="0"/>
          <geom type="cylinder" fromto="0 0 -0.003 0 0 0.006" size="0.012" mass="0.02" rgba="0.05 0.05 0.05 1" contype="0" conaffinity="0"/>
        </body>
      </body>
    </body>
    {cubes}
  </worldbody>
  <equality>{eqs}
  </equality>
  <actuator>
    <motor name="m1" joint="q1" ctrlrange="{-cfg.tau_max[0]} {cfg.tau_max[0]}"/>
    <motor name="m2" joint="q2" ctrlrange="{-cfg.tau_max[1]} {cfg.tau_max[1]}"/>
    <position name="mz" joint="z" kp="3000" ctrlrange="-0.24 0.0"/>
  </actuator>
</mujoco>
"""


class World:
    def __init__(self, cfg, n_cubes, color_seq):
        self.c = cfg
        self.n = n_cubes
        self.model = mujoco.MjModel.from_xml_string(build_xml(cfg, n_cubes, color_seq))
        self.data = mujoco.MjData(self.model)
        m = self.model
        self.q_adr = [m.joint("q1").qposadr[0], m.joint("q2").qposadr[0]]
        self.qd_adr = [m.joint("q1").dofadr[0], m.joint("q2").dofadr[0]]
        self.z_adr = m.joint("z").qposadr[0]
        self.cube_adr = [m.joint("cj%d" % i).qposadr[0] for i in range(n_cubes)]
        self.cube_dof = [m.joint("cj%d" % i).dofadr[0] for i in range(n_cubes)]
        self.eq_id = [m.equality("suck%d" % i).id for i in range(n_cubes)]
        self.tool_site_body = m.body("tool").id
        self._renderer = None
        self.reset(cfg.q_home)

    def reset(self, q0):
        d = self.data
        mujoco.mj_resetData(self.model, d)
        d.qpos[self.q_adr[0]], d.qpos[self.q_adr[1]] = q0
        d.qpos[self.z_adr] = self.z_to_rel(self.c.z_hover)
        d.ctrl[2] = d.qpos[self.z_adr]
        for i in range(self.n):
            a = self.cube_adr[i]
            d.qpos[a:a + 3] = (-3.0, 0.15 * i, CUBE_H - 0.04)
            d.qpos[a + 3:a + 7] = (1, 0, 0, 0)
        mujoco.mj_forward(self.model, d)

    @staticmethod
    def z_to_rel(z):
        """tool height above the cube-top plane (0 = suction contact) -> slide joint coordinate"""
        return (2 * CUBE_H + z) - Z_ARM

    def nominal_inertia(self, q):
        d = self.data
        save = d.qpos.copy()
        d.qpos[self.q_adr[0]], d.qpos[self.q_adr[1]] = q
        mujoco.mj_forward(self.model, d)
        M = np.zeros((self.model.nv, self.model.nv))
        mujoco.mj_fullM(self.model, d, M)
        d.qpos[:] = save
        mujoco.mj_forward(self.model, d)
        return M[self.qd_adr[0], self.qd_adr[0]], M[self.qd_adr[1], self.qd_adr[1]]

    # -------------------------------------------------------------- cubes
    def set_part(self, i, color, shape):
        """make slot i a cube or a cylinder of the given colour (only one of the two geoms is visible and solid)"""
        m = self.model
        cg, yg = m.geom("cg%d" % i).id, m.geom("yg%d" % i).id
        rgb = [float(v) for v in RGBA[color].split()][:3]
        on, off = (yg, cg) if shape == "circle" else (cg, yg)
        m.geom_rgba[on] = rgb + [1.0]
        m.geom_rgba[off] = rgb + [0.0]
        m.geom_contype[on] = m.geom_conaffinity[on] = 1
        m.geom_contype[off] = m.geom_conaffinity[off] = 0
    def place_cube(self, i, x, y, th):
        d = self.data
        a, dof = self.cube_adr[i], self.cube_dof[i]
        d.qpos[a:a + 3] = (x, y, CUBE_H)
        d.qpos[a + 3:a + 7] = (math.cos(th / 2), 0, 0, math.sin(th / 2))
        d.qvel[dof:dof + 6] = 0

    def drive_cube(self, i, x, vb):
        """kinematic conveyor: the cube rides the belt at speed vb"""
        d = self.data
        a, dof = self.cube_adr[i], self.cube_dof[i]
        d.qpos[a] = x
        d.qpos[a + 2] = CUBE_H
        d.qvel[dof:dof + 6] = (vb, 0, 0, 0, 0, 0)

    def cube_xy(self, i):
        a = self.cube_adr[i]
        return self.data.qpos[a], self.data.qpos[a + 1]

    def attach(self, i):
        m, d = self.model, self.data
        e = self.eq_id[i]
        tool, cube = self.tool_site_body, m.body("cube%d" % i).id
        qt_inv, rel_p, rel_q = np.zeros(4), np.zeros(3), np.zeros(4)
        mujoco.mju_negQuat(qt_inv, d.xquat[tool])
        mujoco.mju_rotVecQuat(rel_p, d.xpos[cube] - d.xpos[tool], qt_inv)
        mujoco.mju_mulQuat(rel_q, qt_inv, d.xquat[cube])
        m.eq_data[e, 0:3] = 0
        m.eq_data[e, 3:6] = rel_p
        m.eq_data[e, 6:10] = rel_q
        m.eq_data[e, 10] = 1.0
        d.eq_active[e] = 1

    def detach(self, i):
        self.data.eq_active[self.eq_id[i]] = 0

    # -------------------------------------------------------------- rendering
    def renderer(self, w, h):
        if not isinstance(self._renderer, dict):
            self._renderer = {}
        if (w, h) not in self._renderer:
            self._renderer[(w, h)] = mujoco.Renderer(self.model, height=h, width=w)
        return self._renderer[(w, h)]

    def top_image(self):
        c = self.c
        W = int(round((c.cam_x1 - c.cam_x0) / c.res))
        H = int(round((c.cam_y1 - c.cam_y0) / c.res))
        r = self.renderer(W, H)
        r.update_scene(self.data, camera="top")
        return r.render()[..., ::-1].copy()       # RGB -> BGR for OpenCV

    def view_image(self, w=960, h=540, azimuth=135, elevation=-32, distance=1.75, lookat=(-0.1, 0.05, 0.05)):
        r = self.renderer(w, h)
        cam = mujoco.MjvCamera()
        cam.type = mujoco.mjtCamera.mjCAMERA_FREE
        cam.lookat[:] = lookat
        cam.distance, cam.azimuth, cam.elevation = distance, azimuth, elevation
        r.update_scene(self.data, camera=cam)
        return r.render()
