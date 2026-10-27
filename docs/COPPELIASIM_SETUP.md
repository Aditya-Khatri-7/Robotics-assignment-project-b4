# CoppeliaSim set-up (the platform assigned to Group G10)

The Project List assigns **CoppeliaSim (vision sensor + arm + conveyor), Python + OpenCV** to project P14.
Our demo, video and cross-platform validation run in CoppeliaSim V4.10.0 (EDU, free for education).

## 1. Install CoppeliaSim EDU (Windows, no admin rights needed)

1. Download `CoppeliaSim_Edu_V4_10_0_rev0_Win.zip` (about 240 MB) from https://www.coppeliarobotics.com/downloads
   (direct link: https://downloads.coppeliarobotics.com/V4_10_0_rev0/CoppeliaSim_Edu_V4_10_0_rev0_Win.zip).
2. Unzip it, for example to `D:\tools\CoppeliaSim_Edu` (the folder that contains `coppeliaSim.exe`).
3. Tell our scripts where it is (once per terminal, or set it permanently in Windows settings):

```bash
set COPPELIASIM_PATH=D:\tools\CoppeliaSim_Edu
```

(If the folder is `tools/CoppeliaSim_Edu` next to this repository, nothing needs to be set.)

## 2. Install the Python packages

```bash
pip install -r requirements.txt
```

This installs `coppeliasim-zmqremoteapi-client`, the library that lets Python talk to CoppeliaSim.

## 3. Run

```bash
python demo_cs.py                         # live demo: opens the CoppeliaSim window (use this in the video)
python demo_cs.py --method m2 --speed 0.3 # baseline method
python render_cs.py --stills              # stills and an MP4 video from the CoppeliaSim vision sensor
python experiments_cs.py                  # cross-platform study (about 105 runs on 8 headless instances, about 25 min)
```

## 4. How the cell is built in CoppeliaSim

| CoppeliaSim element | What we create (all through the remote API, see `sortarm/cs_world.py`) |
|---|---|
| Vision sensor | orthographic sensor above the belt, 800 x 173 px (1.5 mm/pixel); every frame goes to OpenCV |
| Arm | base, two dynamic revolute joints, two links, kinematic vertical axis and a suction tool (D-H table of the report) |
| Joint control | a joint-callback script (Lua) evaluates the PID + feedforward law inside every physics step |
| Conveyor | belt shape; parts are moved along it each step (kinematic conveyor with speed ripple) |
| Parts and bins | cubes and cylinders (rigid bodies, Bullet engine), four open bins (red, green, blue, reject) |
| Suction | the picked part is attached to the tool tip and released over the bin; it then falls by physics |

## 5. Troubleshooting

* "CoppeliaSim not found": set `COPPELIASIM_PATH` as above.
* Port 23000 busy: close other CoppeliaSim windows, or use `python demo_cs.py --attach` after starting CoppeliaSim yourself.
* No window appears: run `python demo_cs.py` from a normal terminal (not over remote desktop without a GPU).
