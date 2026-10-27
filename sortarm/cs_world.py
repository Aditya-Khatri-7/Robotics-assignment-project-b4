"""CoppeliaSim world: SCARA arm, conveyor, bins, parts and an orthographic vision sensor, driven through the ZMQ remote API.

The perception, planning and control software of the project is plain Python + OpenCV and talks to this world only
through the small interface below (same as mj_world.World), so the same cell runs in CoppeliaSim and in MuJoCo.
"""
import math
import time

import numpy as np
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

from .vision import BIN_NAMES

COL = {"red": [0.84, 0.16, 0.16], "green": [0.17, 0.65, 0.20], "blue": [0.12, 0.40, 0.80], "reject": [0.30, 0.30, 0.30]}
Z_ARM = 0.25
CUBE_H = 0.015
EYE = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0]          # centre-of-mass frame (identity)

LUA_JOINT = """
function sysCall_init()
    P = nil
    I = 0
end
function setup(kp, kd, ki, jn, bn, tmax, key)
    P = {kp = kp, kd = kd, ki = ki, jn = jn, bn = bn, tmax = tmax, key = key}
    I = 0
    return true
end
-- joint-level PID with model feedforward, evaluated inside every physics step (exact timing)
function sysCall_jointCallback(inData)
    if not P then return {force = 0.0} end
    local qr  = sim.getFloatSignal('qr' .. P.key) or inData.pos
    local qdr = sim.getFloatSignal('qd' .. P.key) or 0.0
    local qdd = sim.getFloatSignal('qdd' .. P.key) or 0.0
    local e, ed = qr - inData.pos, qdr - inData.vel
    I = I + e * inData.dt
    local lim = 0.5 * P.tmax / math.max(P.ki, 1e-9)
    if I > lim then I = lim elseif I < -lim then I = -lim end
    local tau = P.kp * e + P.kd * ed + P.ki * I + P.jn * qdd + P.bn * qdr
    if tau > P.tmax then tau = P.tmax elseif tau < -P.tmax then tau = -P.tmax end
    return {force = tau}
end
"""

LUA_IO = """
function setup(j1, j2, j3, zpart)
    J1, J2, J3, ZP = j1, j2, j3, zpart
    return true
end
-- one batched call per control step: set references, move the conveyor parts, return the joint state
function io(r, zt, hs, xs, ys)
    sim.setFloatSignal('qr1', r[1]); sim.setFloatSignal('qr2', r[2])
    sim.setFloatSignal('qd1', r[3]); sim.setFloatSignal('qd2', r[4])
    sim.setFloatSignal('qdd1', r[5]); sim.setFloatSignal('qdd2', r[6])
    sim.setJointPosition(J3, zt)
    for i = 1, #hs do sim.setObjectPosition(hs[i], {xs[i], ys[i], ZP}, sim.handle_world) end
    return {sim.getJointPosition(J1), sim.getJointPosition(J2), sim.getJointVelocity(J1), sim.getJointVelocity(J2)}
end
"""



class CsWorld:
    def __init__(self, cfg, client=None, view=False, port=23000):
        self.c = cfg
        self.client = client or RemoteAPIClient(port=port, cntport=port + 1)
        self.sim = self.client.require("sim")
        self.client.setStepping(True)
        self.parts = {}
        self._build()

    # ------------------------------------------------------------------ helpers
    def _clear(self):
        sim = self.sim
        try:
            sim.stopSimulation()
        except Exception:
            pass
        while sim.getSimulationState() != sim.simulation_stopped:
            time.sleep(0.02)
        objs = sim.getObjectsInTree(sim.handle_scene, sim.handle_all, 1)
        keep = (sim.object_camera_type, sim.object_light_type)
        objs = [h for h in objs if sim.getObjectType(h) not in keep]      # keep the GUI's default camera and lights
        if objs:
            sim.removeObjects(objs)

    def _shape(self, kind, size, pos, color, mass=None, static=True, resp=False, euler=None):
        sim = self.sim
        h = sim.createPrimitiveShape(kind, size, 0)
        sim.setObjectPosition(h, pos, sim.handle_world)
        if euler is not None:
            sim.setObjectOrientation(h, euler, sim.handle_world)
        sim.setShapeColor(h, None, sim.colorcomponent_ambient_diffuse, color)
        sim.setShapeColor(h, None, sim.colorcomponent_specular, [0.0, 0.0, 0.0])
        sim.setObjectInt32Param(h, sim.shapeintparam_respondable, 1 if resp else 0)
        sim.setObjectInt32Param(h, sim.shapeintparam_static, 1 if static else 0)
        if mass:
            sim.setShapeMass(h, mass)
            sx, sy, sz = size
            if kind == sim.primitiveshape_cylinder:
                ixx = iyy = mass / 12 * (3 * (sx / 2) ** 2 + sz ** 2)
                izz = 0.5 * mass * (sx / 2) ** 2
            else:
                ixx, iyy, izz = mass / 12 * (sy * sy + sz * sz), mass / 12 * (sx * sx + sz * sz), mass / 12 * (sx * sx + sy * sy)
            sim.setShapeInertia(h, [ixx, 0, 0, 0, iyy, 0, 0, 0, izz], EYE)
        return h

    # ------------------------------------------------------------------ scene
    def _build(self):
        sim, c = self.sim, self.c
        self._clear()
        sim.setFloatParam(sim.floatparam_simulation_time_step, c.dt_cs)
        sim.setInt32Param(sim.intparam_dynamic_engine, sim.physics_bullet)
        sim.setArrayParam(sim.arrayparam_ambient_light, [0.62, 0.62, 0.62])
        sim.setArrayParam(sim.arrayparam_gravity, [0.0, 0.0, -9.81])
        P, C = sim.primitiveshape_cuboid, sim.primitiveshape_cylinder
        gray = [0.50, 0.53, 0.58]
        self.floor = self._shape(P, [6.0, 6.0, 0.02], [0, 0, -0.05], gray, static=True, resp=True)
        belt_cy = 0.5 * (c.belt_y_lo + c.belt_y_hi)
        belt_hy = c.belt_y_hi - c.belt_y_lo
        self.belt = self._shape(P, [1.35, belt_hy, 0.04], [-0.225, belt_cy, -0.02], [0.35, 0.35, 0.37], static=True, resp=True)
        for yy in (c.belt_y_lo - 0.01, c.belt_y_hi + 0.01):
            self._shape(P, [1.35, 0.02, 0.04], [-0.225, yy, 0.0], [0.15, 0.15, 0.15], static=True, resp=False)
        # bins (open boxes with four walls)
        self.bins = []
        for (bx, by), name in zip(c.bins, BIN_NAMES):
            col = COL[name]
            self._shape(P, [0.20, 0.20, 0.01], [bx, by, -0.005], col, static=True, resp=True)
            for dx, dy, sx, sy in ((0.095, 0, 0.01, 0.20), (-0.095, 0, 0.01, 0.20), (0, 0.095, 0.20, 0.01), (0, -0.095, 0.20, 0.01)):
                self._shape(P, [sx, sy, 0.07], [bx + dx, by + dy, 0.03], col, static=True, resp=True)
        # arm: base, joint 1, link 1, joint 2, link 2, prismatic joint 3 with the tool
        base = self._shape(C, [0.09, 0.09, Z_ARM], [0, 0, Z_ARM / 2], [0.25, 0.25, 0.28], static=True, resp=False)
        j1 = sim.createJoint(sim.joint_revolute_subtype, sim.jointmode_dynamic, 0, [0.06, 0.01])
        sim.setObjectPosition(j1, [0, 0, Z_ARM], sim.handle_world)
        sim.setObjectParent(j1, base, True)
        l1 = self._shape(P, [c.L1, 0.05, 0.04], [c.L1 / 2, 0, Z_ARM], [0.90, 0.55, 0.10], mass=1.8, static=False)
        sim.setObjectParent(l1, j1, True)
        j2 = sim.createJoint(sim.joint_revolute_subtype, sim.jointmode_dynamic, 0, [0.06, 0.01])
        sim.setObjectPosition(j2, [c.L1, 0, Z_ARM], sim.handle_world)
        sim.setObjectParent(j2, l1, True)
        l2 = self._shape(P, [c.L2, 0.045, 0.035], [c.L1 + c.L2 / 2, 0, Z_ARM], [0.95, 0.70, 0.20], mass=1.1, static=False)
        sim.setObjectParent(l2, j2, True)
        j3 = sim.createJoint(sim.joint_prismatic_subtype, sim.jointmode_kinematic, 0, [0.30, 0.01])
        sim.setObjectPosition(j3, [c.L1 + c.L2, 0, Z_ARM], sim.handle_world)
        sim.setObjectParent(j3, l2, True)
        tool = self._shape(C, [0.016, 0.016, 0.20], [c.L1 + c.L2, 0, Z_ARM + 0.10], [0.12, 0.12, 0.12], static=True)
        sim.setObjectParent(tool, j3, True)
        cup = self._shape(C, [0.024, 0.024, 0.01], [c.L1 + c.L2, 0, Z_ARM], [0.05, 0.05, 0.05], static=True)
        sim.setObjectParent(cup, j3, True)
        self.tip = sim.createDummy(0.01)
        sim.setObjectPosition(self.tip, [c.L1 + c.L2, 0, Z_ARM], sim.handle_world)
        sim.setObjectParent(self.tip, j3, True)
        self.j1, self.j2, self.j3 = j1, j2, j3
        for j in (j1, j2):
            sim.setJointMaxForce(j, 1000.0)
            sim.setObjectInt32Param(j, sim.jointintparam_dynctrlmode, sim.jointdynctrl_callback)
            sim.setJointInterval(j, False, [c.q1_lim[0] if j == j1 else c.q2_lim[0], (c.q1_lim[1] - c.q1_lim[0]) if j == j1 else (c.q2_lim[1] - c.q2_lim[0])])
        sim.setJointInterval(j3, False, [-0.30, 0.30])
        # orthographic top camera (vision sensor): image right = +x, image up = +y
        W = int(round((c.cam_x1 - c.cam_x0) / c.res))
        H = int(round((c.cam_y1 - c.cam_y0) / c.res))
        self.W, self.H = W, H
        self.vs = sim.createVisionSensor(1, [W, H, 0, 0], [0.01, 3.0, c.cam_x1 - c.cam_x0, 0.1, 0, 0, 0, 0, 0, 0, 0])
        sim.setObjectPosition(self.vs, [0.5 * (c.cam_x0 + c.cam_x1), 0.5 * (c.cam_y0 + c.cam_y1), 1.0], sim.handle_world)
        sim.setObjectOrientation(self.vs, [math.pi, 0, 0], sim.handle_world)
        self.view = None
        self.joint_scripts = []
        for j in (j1, j2):
            sc = sim.addScript(sim.scripttype_childscript)
            sim.setScriptStringParam(sc, sim.scriptstringparam_text, LUA_JOINT)
            sim.associateScriptWithObject(sc, j)
            self.joint_scripts.append(sc)
        self.io_script = sim.addScript(sim.scripttype_childscript)
        sim.setScriptStringParam(self.io_script, sim.scriptstringparam_text, LUA_IO)
        sim.associateScriptWithObject(self.io_script, base)
        sim.startSimulation()
        self.client.step()
        sim.callScriptFunction("setup", self.io_script, j1, j2, j3, CUBE_H)
        self.t_wall = time.time()

    def configure_controller(self, kp, kd, ki, jn, bn, tmax):
        """load the PID + feedforward gains into the two joint callback scripts"""
        for k, sc in enumerate(self.joint_scripts):
            self.sim.callScriptFunction("setup", sc, kp[k], kd[k], ki[k], jn[k], bn[k], tmax[k], str(k + 1))

    def set_initial_pose(self, q):
        sim = self.sim
        sim.setJointPosition(self.j1, q[0])
        sim.setJointPosition(self.j2, q[1])

    # ------------------------------------------------------------------ arm I/O
    def io(self, qr, qdr, qddr, z_rel, belt):
        """set joint references, move the belt parts (list of (handle, x, y)) and return (q1, q2, qd1, qd2)"""
        hs = [h for h, _, _ in belt]
        xs = [x for _, x, _ in belt]
        ys = [y for _, _, y in belt]
        return self.sim.callScriptFunction("io", self.io_script, [qr[0], qr[1], qdr[0], qdr[1], qddr[0], qddr[1]], z_rel, hs, xs, ys)

    def step(self):
        self.client.step()

    @staticmethod
    def z_to_rel(z):
        return (2 * CUBE_H + z) - Z_ARM

    def nominal_inertia(self, q=None):
        """effective joint inertias used by the controller (from the link data, at a representative pose)"""
        c = self.c
        m1, m2, mt = 1.8, 1.1, 0.19
        l1c, l2c = c.L1 / 2, c.L1 + c.L2 / 2
        # inertia about the joint-1 axis at q2 = 1.5 rad
        ang = 1.5
        x2 = c.L1 + 0.5 * c.L2 * math.cos(ang)
        y2 = 0.5 * c.L2 * math.sin(ang)
        xt = c.L1 + c.L2 * math.cos(ang)
        yt = c.L2 * math.sin(ang)
        J1 = m1 * (c.L1 ** 2 / 12 + (c.L1 / 2) ** 2) + m2 * (c.L2 ** 2 / 12 + x2 ** 2 + y2 ** 2) + mt * (xt ** 2 + yt ** 2)
        J2 = m2 * (c.L2 ** 2 / 12 + (c.L2 / 2) ** 2) + mt * c.L2 ** 2
        return J1, J2

    # ------------------------------------------------------------------ parts
    def spawn_part(self, idx, color, shape, x, y, th):
        sim, c = self.sim, self.c
        if shape == "circle":
            h = self._shape(sim.primitiveshape_cylinder, [2 * c.cyl_r, 2 * c.cyl_r, 2 * CUBE_H], [x, y, CUBE_H], COL[color], mass=0.05, static=True, resp=True)
        else:
            h = self._shape(sim.primitiveshape_cuboid, [c.cube, c.cube, c.cube], [x, y, CUBE_H], COL[color], mass=0.05, static=True, resp=True)
        sim.setObjectOrientation(h, [0, 0, th], sim.handle_world)
        self.parts[idx] = h
        return h

    def drive_part(self, idx, x, y):
        self.sim.setObjectPosition(self.parts[idx], [x, y, CUBE_H], self.sim.handle_world)

    def part_xy(self, idx):
        p = self.sim.getObjectPosition(self.parts[idx], self.sim.handle_world)
        return p[0], p[1]

    def attach(self, idx):
        sim = self.sim
        sim.setObjectParent(self.parts[idx], self.tip, True)

    def detach(self, idx):
        sim = self.sim
        h = self.parts[idx]
        sim.setObjectParent(h, -1, True)
        sim.setObjectInt32Param(h, sim.shapeintparam_static, 0)
        sim.resetDynamicObject(h)

    # ------------------------------------------------------------------ images
    def top_image(self):
        """BGR image with image right = +x and image down = -y (same convention as vision.Camera)"""
        sim = self.sim
        sim.handleVisionSensor(self.vs)
        img, res = sim.getVisionSensorImg(self.vs)
        a = np.frombuffer(img, dtype=np.uint8).reshape(res[1], res[0], 3)
        return np.ascontiguousarray(a[:, ::-1, ::-1])      # mirror columns to image-right = +x, RGB -> BGR

    def view_image(self, w=960, h=540, pos=(0.9, -0.95, 0.85), look=(-0.06, 0.05, 0.05)):
        sim = self.sim
        if self.view is None:
            self.view = sim.createVisionSensor(2 | 1, [w, h, 0, 0], [0.02, 8.0, 0.9, 0.1, 0, 0, 0, 0, 0, 0, 0])   # perspective, explicit handling
            self._aim(self.view, pos, look)
        sim.handleVisionSensor(self.view)
        img, res = sim.getVisionSensorImg(self.view)
        a = np.frombuffer(img, dtype=np.uint8).reshape(res[1], res[0], 3)
        return np.ascontiguousarray(a[::-1])

    def _aim(self, handle, pos, look):
        """orient a camera at pos so that it looks at look (z up)"""
        sim = self.sim
        f = np.array(look) - np.array(pos)
        f /= np.linalg.norm(f)
        up = np.array([0, 0, 1.0])
        r = np.cross(f, up); r /= np.linalg.norm(r)
        u = np.cross(r, f)
        # CoppeliaSim camera looks along +z, image up = +y, image right = +x
        m = [r[0], u[0], f[0], pos[0], r[1], u[1], f[1], pos[1], r[2], u[2], f[2], pos[2]]
        sim.setObjectMatrix(handle, m, sim.handle_world)

    def close(self):
        try:
            self.sim.stopSimulation()
        except Exception:
            pass
