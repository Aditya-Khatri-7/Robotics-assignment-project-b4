# Vision-Guided Sorting Arm on a Conveyor (AISR Project P14, Group G10, Batch B4)

A vision sensor detects parts on a moving conveyor **by colour and shape**; a SCARA arm computes the grasp point with inverse kinematics (D-H model),
picks each part while the belt keeps moving and sorts it into a bin: cubes into the red / green / blue bin, cylinders (wrong-shape parts) into a reject bin.
Application domain: quality inspection and sorting in manufacturing.

**Platform: CoppeliaSim V4.10 (assigned to G10 in the Project List) + Python + OpenCV.**
The demo, the video and a cross-platform validation study run in CoppeliaSim. The identical software also runs on the **MuJoCo** physics engine,
which is about five times faster and is used for the large statistical studies (560 + 330 runs).
Success counts only parts that physically rest in the correct bin (read from the physics engine, not from the planner).

## Pipeline

vision-sensor frame -> HSV colour + contour shape detector + homography -> Kalman tracker (camera + belt encoder, 80 ms latency compensation)
-> intercept planner (D-H inverse kinematics + minimum-jerk feasibility) -> joint PID with feedforward -> predictive visual-servo descent -> suction pick -> bin

Three strategies are compared: **M1** stop-and-go belt, **M2** predictive (line fit, open-loop descent), **M3** proposed (Kalman + encoder, visual-servo descent).

## Install and run

```bash
pip install -r requirements.txt          # Python libraries incl. the CoppeliaSim remote-API client
# install CoppeliaSim EDU once: see docs/COPPELIASIM_SETUP.md
python demo_cs.py                         # live demo in the CoppeliaSim window (use this in the video)
python demo_cs.py --method m2 --speed 0.3 # baseline method, other belt speed
python render_cs.py --stills              # CoppeliaSim stills + MP4 video
python demo.py                            # the same demo in the MuJoCo viewer
python -m pytest tests -q                 # 19 unit tests (kinematics, vision, tracker failure modes, end-to-end sims)
python run_all.py                         # tests + smoke study + readiness check (add --full to regenerate everything)
python check_ready.py --tests             # submission readiness checker
```

## Reproduce every result of the report

```bash
python experiments.py --quick             # 3-seed smoke test -> results/quick.csv (never touches the report data)
python experiments.py                     # 560 MuJoCo runs -> results/all_runs.csv (about 25 min on 24 cores)
python experiments.py --confirm           # 30-seed confirmation study -> results/confirm_runs.csv
python experiments_cs.py                  # 105 CoppeliaSim runs on 8 headless instances -> results/cs_runs.csv (about 25 min)
python extra_experiments.py               # controller + vision studies (MuJoCo) -> results/
python extra_cs.py                        # controller tests in CoppeliaSim -> results/cs_control.pkl
python ci_table.py                        # bootstrap 95 % confidence intervals -> results/ci_table.csv
python heldout_study.py                   # held-out robustness (strong lighting, unseen speed, 50 % defects, 10 fps) -> results/heldout.csv
python make_figures.py                    # all figures -> figures/
python report/build_report.py             # report .docx (built on the official sample template; then update fields in Word and export PDF)
python slides/build_slides.py             # 17-slide deck
```

## Files and owners (edit the owner column if your split differs)

| File | Content | Owner |
|---|---|---|
| `sortarm/arm.py` | SCARA FK / IK / Jacobian, D-H matrices, minimum-jerk, PID + feedforward law | Aditya (kinematics, D-H), Amritanshi (PID) |
| `sortarm/cs_world.py`, `simcs.py`, `cs_launch.py` | CoppeliaSim scene, arm, vision sensor, joint-callback controller, closed loop, launcher | Aditya, Amritanshi |
| `sortarm/mj_world.py`, `sim3d.py` | MuJoCo scene and closed loop | Aditya, Amritanshi |
| `sortarm/vision.py` | colour detector, contour shape classifier, homography | Simran |
| `sortarm/tracker.py` | association, Kalman filter, line-fit baseline, colour and shape voting | Divya |
| `sortarm/sim.py` | planner, arm state machine, visual servo, bin assignment | Aditya (state machine, servo), Divya (planner), Anchit (stop-and-go) |
| `experiments.py`, `experiments_cs.py`, `make_figures.py`, `demo_cs.py`, `demo.py`, `render_cs.py`, `render_3d.py`, `tests/`, `check_ready.py` | studies, figures, demos, renders, tests | Anchit |
| `extra_experiments.py`, `extra_cs.py` | step response, tracking, vision study | Amritanshi, Simran |

## Key results

See Section 9 of the report; all numbers in the report are generated from `results/*.csv`.

## Notes

- Tuning constants of the planner and visual servo live in `sortarm/config.py` (`servo_gain`, `x_reach_min`, `t_arr_min`, ...); defaults reproduce the reported results exactly.
- `COPPELIASIM_PATH` selects the CoppeliaSim installation; `dev/coppelia_probes/` holds the one-off probing scripts used while building the scene.
- CI (`.github/workflows/tests.yml`) runs the unit tests on every push.
