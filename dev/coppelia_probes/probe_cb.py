from dataclasses import replace
from sortarm.config import Config
from sortarm.cs_world import CsWorld

cfg = replace(Config(), dt=Config().dt_cs)
w = CsWorld(cfg)
sim = w.sim
sim.stopSimulation()
while sim.getSimulationState() != sim.simulation_stopped:
    pass
lua = """
function sysCall_init()
    n = 0
end
function sysCall_jointCallback(inData)
    n = n + 1
    C = C or {}
    C[inData.handle] = (C[inData.handle] or 0) + 1
    if n < 3 then
        local s = ''
        for k, v in pairs(inData) do s = s .. tostring(k) .. '=' .. tostring(v) .. ' ' end
        print('CB ' .. s)
    end
    return {force = 0.0}
end
function probe()
    local s=''
    for k,v in pairs(C or {}) do s=s..k..':'..v..' ' end
    return s
end
"""
sc = sim.addScript(sim.scripttype_childscript)
sim.setScriptStringParam(sc, sim.scriptstringparam_text, lua)
import os
target = {'j1': w.j1, 'base': sim.getObjectParent(w.j1)}[os.environ.get('ATT','j1')]
sim.associateScriptWithObject(sc, target)
for j in (w.j1, w.j2):
    sim.setObjectInt32Param(j, sim.jointintparam_dynctrlmode, sim.jointdynctrl_callback)
sim.startSimulation()
for k in range(5):
    w.client.step()
print("calls", sim.callScriptFunction("probe", sc))
w.close()
