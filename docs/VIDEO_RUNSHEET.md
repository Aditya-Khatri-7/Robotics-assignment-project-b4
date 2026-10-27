# Video run sheet (target 20 minutes, accepted range 18 to 22)

Platform: Google Meet / Teams / Zoom. Record the WHOLE meeting. Every member on camera in grid view for the entire recording.

## Before you press record (10 minutes)

1. Everyone: charge laptop, close heavy programs, camera on, microphone test.
2. The presenter of the demo (Amritanshi) runs `python demo_cs.py --n 3` once to check that the CoppeliaSim window opens and the arm moves (CoppeliaSim must be installed, see `docs/COPPELIASIM_SETUP.md`), then closes it.
3. Open `AISR_G10_Slides.pdf` (or .pptx in presenter view, the speaker notes show what to say).
4. Keep a second terminal ready with the three demo commands (below).
5. Backup if the live window fails: play `results/demo_cs_m3.mp4` (CoppeliaSim render) and say that it is a recording of the same simulation; `python demo.py` shows the same cell in the MuJoCo viewer.

## Timeline

| Time | Who | What | Slide |
|---|---|---|---|
| 0:00 to 1:00 | all five | each says name and SAP ID on camera | 1 |
| 1:00 to 3:30 | Aditya | problem, domain, objectives | 1 to 3 |
| 3:30 to 6:00 | Simran | existing work, novelty, syllabus mapping, vision | 4 to 6 |
| 6:00 to 8:30 | Divya | architecture, robot model, planning algorithm | 7 to 9 |
| 8:30 to 10:30 | Amritanshi | controller and visual servo, set-up | 10 to 11 |
| 10:30 to 16:00 | Amritanshi explains, Anchit types | LIVE DEMO (screen share the 3-D window) | 12 |
| 16:00 to 18:30 | Anchit | results and contributions | 13 to 15 |
| 18:30 to 19:30 | all | conclusion and thanks | 16 to 17 |

Total about 19.5 minutes. Each member speaks about 3.5 to 5 minutes.
If you run long, shorten the demo; if short, run the third demo command. The recording must be 18 to 22 minutes.

## Demo commands (type them live)

```bash
python demo_cs.py --method m3 --speed 0.25
```
What to say: the arm waits ahead of the part, descends while correcting; cubes go to their colour bin; cylinders go to the dark reject bin; the console prints what the camera detected for every pick.
Rotate the view with the mouse in the CoppeliaSim window. Press Enter in the terminal at the end to close CoppeliaSim.

```bash
python demo_cs.py --method m2 --speed 0.3
```
What to say: the baseline misses parts more often (watch for MISS in the console), because it holds the planned point during the descent.

```bash
python demo_cs.py --method m3 --speed 0.35
```
What to say: at 0.35 m/s one arm cannot serve every part; that is the capacity limit, not an accuracy problem.

Say once that the platform assigned to the group is CoppeliaSim and that the same software also ran on MuJoCo for the large statistics.

## After recording

1. Check the length (18 to 22 minutes), check that everyone is visible and spoke.
2. Do not cut parts out; you may trim the very start and end.
3. Upload to YouTube, visibility **Unlisted** (not Public, not Private).
4. Paste the link into the report (Appendix A.1), slide 17 and the Google Form.
