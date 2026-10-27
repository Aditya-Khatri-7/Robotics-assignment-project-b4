R = 'D:/!aRobotics project/sortarm_project/sortarm/'
p = R + 'cs_world.py'
s = open(p, encoding='utf8').read()


def rep(a, b):
    global s
    assert a in s, a[:80]
    s = s.replace(a, b, 1)


rep('j3 = sim.createJoint(sim.joint_prismatic_subtype, sim.jointmode_dynamic, 0, [0.30, 0.01])', 'j3 = sim.createJoint(sim.joint_prismatic_subtype, sim.jointmode_kinematic, 0, [0.30, 0.01])')
rep('[c.L1 + c.L2, 0, Z_ARM + 0.10], [0.12, 0.12, 0.12], mass=0.17, static=False)', '[c.L1 + c.L2, 0, Z_ARM + 0.10], [0.12, 0.12, 0.12], static=True)')
rep('[c.L1 + c.L2, 0, Z_ARM], [0.05, 0.05, 0.05], mass=0.02, static=False)', '[c.L1 + c.L2, 0, Z_ARM], [0.05, 0.05, 0.05], static=True)')
rep('''        sim.setObjectInt32Param(j3, sim.jointintparam_dynctrlmode, sim.jointdynctrl_position)
        sim.setJointMaxForce(j3, 600.0)
        sim.setObjectFloatParam(j3, sim.jointfloatparam_pid_p, 3000.0)
        sim.setObjectFloatParam(j3, sim.jointfloatparam_pid_d, 120.0)
''', '')
rep('    sim.setJointTargetPosition(J3, zt)', '    sim.setJointPosition(J3, zt)')
rep('        sim.setJointInterval(j3, False, [-0.24, 0.24])', '        sim.setJointInterval(j3, False, [-0.30, 0.30])')
open(p, 'w', encoding='utf8').write(s)
print('ok')
