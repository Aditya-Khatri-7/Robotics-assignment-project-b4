R = 'D:/!aRobotics project/sortarm_project/sortarm/'
p = R + 'cs_world.py'
s = open(p, encoding='utf8').read()

LUA = '''
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
    sim.setJointTargetPosition(J3, zt)
    for i = 1, #hs do sim.setObjectPosition(hs[i], {xs[i], ys[i], ZP}, sim.handle_world) end
    return {sim.getJointPosition(J1), sim.getJointPosition(J2), sim.getJointVelocity(J1), sim.getJointVelocity(J2)}
end
"""

'''
marker = "EYE = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0]          # centre-of-mass frame (identity)\n"
assert marker in s
s = s.replace(marker, marker + LUA, 1)

old = """        for j in (j1, j2):
            sim.setJointMaxForce(j, 1000.0)
            sim.setObjectInt32Param(j, sim.jointintparam_dynctrlmode, sim.jointdynctrl_force)"""
assert old in s
s = s.replace(old, """        for j in (j1, j2):
            sim.setJointMaxForce(j, 1000.0)
            sim.setObjectInt32Param(j, sim.jointintparam_dynctrlmode, sim.jointdynctrl_callback)""")

old2 = "        self.view = None\n        sim.startSimulation()\n        self.client.step()\n        self.t_wall = time.time()"
assert old2 in s
s = s.replace(old2, """        self.view = None
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
        \"\"\"load the PID + feedforward gains into the two joint callback scripts\"\"\"
        for k, sc in enumerate(self.joint_scripts):
            self.sim.callScriptFunction("setup", sc, kp[k], kd[k], ki[k], jn[k], bn[k], tmax[k], str(k + 1))""")

a = s.index("    def read_joints(self):")
b = s.index("    def step(self):")
s = s[:a] + '''    def io(self, qr, qdr, qddr, z_rel, belt):
        """set joint references, move the belt parts (list of (handle, x, y)) and return (q1, q2, qd1, qd2)"""
        hs = [h for h, _, _ in belt]
        xs = [x for _, x, _ in belt]
        ys = [y for _, _, y in belt]
        return self.sim.callScriptFunction("io", self.io_script, [qr[0], qr[1], qdr[0], qdr[1], qddr[0], qddr[1]], z_rel, hs, xs, ys)

''' + s[b:]
open(p, 'w', encoding='utf8').write(s)

q = R + 'simcs.py'
t = open(q, encoding='utf8').read()
a = t.index("class JointPlantCS(JointPlant):")
b = t.index("class SimCS(Sim):")
t = t[:a] + '''class JointPlantCS(JointPlant):
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


''' + t[b:]
old = '''    def _arm_step(self, dt):
        w = self.w
        for o in self.objs:
            if o["state"] == "belt":
                w.drive_part(o["id"], o["x"], o["y"])
            elif o["state"] == "lost" and o["x"] < 0.55:
                o["x"] += self.vb * dt
                w.drive_part(o["id"], o["x"], o["y"])
        self.plant.z_cmd = w.z_to_rel(self.z)'''
assert old in t
t = t.replace(old, '''    def _arm_step(self, dt):
        w = self.w
        belt = []
        for o in self.objs:
            if o["state"] == "belt":
                belt.append((w.parts[o["id"]], o["x"], o["y"]))
            elif o["state"] == "lost" and o["x"] < 0.55:
                o["x"] += self.vb * dt
                belt.append((w.parts[o["id"]], o["x"], o["y"]))
        self.plant.belt = belt
        self.plant.z_cmd = w.z_to_rel(self.z)''')
open(q, 'w', encoding='utf8').write(t)
print('patched')
