# GitHub guide: one repository, every member commits their own module

The project rules require ONE repository for the group and commits from EACH member's OWN account.
The contribution table (Section 10 of the report) says which module belongs to whom; the commits must match it.

## 1. Team lead: create the repository (once)

1. On github.com create a new repository, for example `Robotics-assignment-project-b4` (public or private, but give the evaluator access).
2. Add the four other members as collaborators (Settings > Collaborators).
3. Put the link in the report (Appendix A.1) and on slide 17. Replace the highlighted placeholder.

## 2. Team lead: first push (project skeleton)

```bash
cd sortarm_project
git add README.md requirements.txt .gitignore docs tests
git commit -m "Project skeleton: README, requirements, docs, tests"
git branch -M main
git remote add origin https://github.com/Aditya-Khatri-7/Robotics-assignment-project-b4.git
git push -u origin main
```

## 3. Every member: clone, commit your own files, push

Each member works on their own computer and their own GitHub login:

```bash
git clone https://github.com/Aditya-Khatri-7/Robotics-assignment-project-b4.git
cd Robotics-assignment-project-b4
git config user.name  "<your name>"
git config user.email "<the e-mail of your GitHub account>"
```

Copy the project files into the clone (or start from the project folder), then commit only YOUR files, in several small commits with clear messages:

| Member | Files to commit | Example commit messages |
|---|---|---|
| Aditya Khatri | `sortarm/arm.py` (kinematics, D-H, Jacobian, min-jerk), `sortarm/cs_world.py`, `sortarm/simcs.py`, `sortarm/mj_world.py`, `sortarm/sim3d.py`, `sortarm/config.py` | "SCARA FK/IK and D-H matrices", "MuJoCo cell with belt, bins and suction weld", "Visual-servo descent" |
| Simran Jeet Gill | `sortarm/vision.py`, vision part of `extra_experiments.py` | "HSV colour detector", "Contour shape classifier", "Vision noise study" |
| Divya Israni | `sortarm/tracker.py`, planner part of `sortarm/sim.py` | "Kalman filter with encoder fusion", "Intercept planner", "Ablation runs" |
| Amritanshi Singh | PID part of `sortarm/arm.py`, joint-callback controller in `sortarm/cs_world.py`, controller part of `sortarm/sim3d.py`, `extra_cs.py`, controller tests in `extra_experiments.py` | "Joint PID with feedforward", "Step and tracking tests" |
| Anchit Saxena | `experiments.py`, `experiments_cs.py`, `sortarm/cs_launch.py`, `make_figures.py`, `demo_cs.py`, `render_cs.py`, `demo.py`, `render_3d.py`, `check_ready.py`, `results/` | "Experiment harness", "Live 3-D demo", "Figures and renders" |

```bash
git add <your files>
git commit -m "<your message>"
git pull --rebase origin main
git push origin main
```

Tips: make at least 3 to 5 commits each over several days; never commit the same file text from two accounts at the same time (pull first); do not commit `results/*.mp4` larger than 100 MB.

## 4. Before the viva

* Open the repository's "Commits" page: every member must appear with real commits that match the contribution table.
* Every member should be able to explain every file (see `docs/VIVA_QA.md`).
* Run `python check_ready.py --tests` in the clone: it should report no failures.
