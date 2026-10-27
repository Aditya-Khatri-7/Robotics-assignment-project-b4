"""Feasibility probe: torque-controlled SCARA arm in CoppeliaSim (not part of the deliverable)."""
import math
import time
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

c = RemoteAPIClient()
sim = c.require("sim")
c.setStepping(True)

# clean scene
objs = sim.getObjectsInTree(sim.handle_scene, sim.handle_all, 1)
sim.removeObjects(objs)
sim.setStepping = None
sim.setFloatParam(sim.floatparam_simulation_time_step, 0.005)
ENG = int(__import__("os").environ.get("ENG", "0"))
sim.setInt32Param(sim.intparam_dynamic_engine, ENG)

Z, L1, L2 = 0.25, 0.35, 0.30


def box(size, pos, mass=None, static=False, resp=False, color=None):
    h = sim.createPrimitiveShape(sim.primitiveshape_cuboid, size, 0)
    sim.setObjectPosition(h, sim.handle_world, pos)
    sim.setObjectInt32Param(h, sim.shapeintparam_static, 1 if static else 0)
    sim.setObjectInt32Param(h, sim.shapeintparam_respondable, 1 if resp else 0)
    if mass:
        sim.setShapeMass(h, mass)
        sx, sy, sz = size
        ixx, iyy, izz = mass / 12 * (sy * sy + sz * sz), mass / 12 * (sx * sx + sz * sz), mass / 12 * (sx * sx + sy * sy)
        sim.setShapeInertia(h, [ixx, 0, 0, 0, iyy, 0, 0, 0, izz], [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0])
    if color:
        sim.setShapeColor(h, None, sim.colorcomponent_ambient_diffuse, color)
    return h


base = box([0.09, 0.09, Z], [0, 0, Z / 2], static=True, resp=False, color=[0.2, 0.2, 0.2])
j1 = sim.createJoint(sim.joint_revolute_subtype, sim.jointmode_dynamic, 0, [0.05, 0.01])
sim.setObjectPosition(j1, sim.handle_world, [0, 0, Z])
sim.setObjectParent(j1, base, True)
l1 = box([L1, 0.05, 0.04], [L1 / 2, 0, Z], mass=1.8, color=[0.9, 0.55, 0.1])
sim.setObjectParent(l1, j1, True)
j2 = sim.createJoint(sim.joint_revolute_subtype, sim.jointmode_dynamic, 0, [0.05, 0.01])
sim.setObjectPosition(j2, sim.handle_world, [L1, 0, Z])
sim.setObjectParent(j2, l1, True)
l2 = box([L2, 0.045, 0.035], [L1 + L2 / 2, 0, Z], mass=1.1, color=[0.95, 0.7, 0.2])
sim.setObjectParent(l2, j2, True)
for j in (j1, j2):
    sim.setObjectInt32Param(j, sim.jointintparam_dynctrlmode, sim.jointdynctrl_free)
    sim.setJointInterval(j, False, [-2.97, 5.94])
print("built", j1, j2)
sim.startSimulation()
t0 = time.time()
for k in range(200):
    sim.setJointTargetForce(j1, 5.0, True)
    sim.setJointTargetForce(j2, 0.0, True)
    c.step()
    if k % 40 == 0:
        print(k, round(sim.getJointPosition(j1), 4), round(sim.getJointVelocity(j1), 3), round(sim.getJointPosition(j2), 4))
print("steps/s", 200 / (time.time() - t0))
sim.stopSimulation()
