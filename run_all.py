"""One-command driver: python run_all.py [--quick | --full]

--quick (default): unit tests + readiness checker + a short MuJoCo smoke run (about 1 minute)
--full           : additionally regenerates every study, figure, report and slide deck (hours)
"""
import subprocess
import sys
import time

HERE = __import__("os").path.dirname(__import__("os").path.abspath(__file__))

QUICK = [
    ("unit tests", [sys.executable, "-m", "pytest", "tests", "-q"]),
    ("smoke experiments (3 seeds, MuJoCo)", [sys.executable, "experiments.py", "--quick"]),
    ("readiness checker", [sys.executable, "check_ready.py"]),
]
FULL = [
    ("MuJoCo study", [sys.executable, "experiments.py"]),
    ("confirmation study", [sys.executable, "experiments.py", "--confirm"]),
    ("controller/vision studies", [sys.executable, "extra_experiments.py"]),
    ("figures", [sys.executable, "make_figures.py"]),
    ("report", [sys.executable, "report/build_report.py"]),
    ("slides", [sys.executable, "slides/build_slides.py"]),
]


def main():
    steps = QUICK + (FULL if "--full" in sys.argv else [])
    failed = []
    for name, cmd in steps:
        t = time.time()
        print("==> %s" % name, flush=True)
        rc = subprocess.run(cmd, cwd=HERE).returncode
        print("    %s in %.0f s" % ("ok" if rc == 0 else "FAILED (%d)" % rc, time.time() - t), flush=True)
        if rc:
            failed.append(name)
    print("\nFAILED: %s" % ", ".join(failed) if failed else "\nall steps ok")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
