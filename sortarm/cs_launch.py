"""Start (and stop) CoppeliaSim instances for the experiments and the demo.

The path of the CoppeliaSim installation is read from the environment variable COPPELIASIM_PATH
(default: ../tools/CoppeliaSim_Edu next to this project, see docs/COPPELIASIM_SETUP.md)."""
import os
import socket
import subprocess
import time

from coppeliasim_zmqremoteapi_client import RemoteAPIClient

DEFAULT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tools", "CoppeliaSim_Edu")
FALLBACK = os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "CoppeliaSimEdu")


def install_dir():
    for p in (os.environ.get("COPPELIASIM_PATH"), DEFAULT, FALLBACK):
        if p and os.path.exists(os.path.join(p, "coppeliaSim.exe")):
            return p
    raise FileNotFoundError("CoppeliaSim not found; set COPPELIASIM_PATH (see docs/COPPELIASIM_SETUP.md)")


def launch(port=23000, headless=True, wait=40.0):
    """start a CoppeliaSim process whose ZMQ remote API listens on `port`; returns (process, client)"""
    d = install_dir()
    args = [os.path.join(d, "coppeliaSim.exe")]
    if headless:
        args.append("-h")
    args += ["-GzmqRemoteApi.rpcPort=%d" % port, "-GzmqRemoteApi.cntPort=%d" % (port + 1), "-GwsRemoteApi.port=%d" % (port + 50)]
    log = open(os.path.join(os.environ.get("TEMP", d), "coppeliasim_%d.log" % port), "w")
    proc = subprocess.Popen(args, cwd=d, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    t0 = time.time()
    while time.time() - t0 < wait:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1.0):
                pass
        except OSError:
            time.sleep(0.5)
            continue
        time.sleep(1.5)                                   # let the add-on finish its start-up
        c = RemoteAPIClient(port=port, cntport=port + 1)
        return proc, c
    proc.kill()
    raise RuntimeError("CoppeliaSim did not start on port %d" % port)


def stop(proc, client=None):
    try:
        if client is not None:
            client.require("sim").quitSimulator()
    except Exception:
        pass
    try:
        proc.wait(timeout=8)
    except Exception:
        proc.kill()
