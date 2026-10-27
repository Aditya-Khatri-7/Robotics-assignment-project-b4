# Video script (about 20 min: about 14 min slides + 6 min live demo; timeline in VIDEO_RUNSHEET.md)

Record the whole meeting on Meet / Teams / Zoom, everyone on camera in grid view. Each member starts by saying name and SAP ID.
Every member should talk about 4 minutes. Change the wording into your own; do not read the slides.

## 0:00 Introductions (1 min)
All five: "I am <name>, SAP ID <id>."

## Aditya Khatri, slides 1-3 (about 2.5 min, see VIDEO_RUNSHEET.md)
* Problem: detect parts by colour and shape on a moving belt; quality inspection and sorting in manufacturing; cubes to colour bins, cylinders to the reject bin; why stopping the belt wastes throughput.
* The difficulty: the cube moves during the 80 ms vision delay and the arm motion; belt ripple; noise.
* Objectives O1-O5 and what we achieved (read the Achieved column).

## Simran Jeet Gill, slides 4-6 (about 2.5 min, see VIDEO_RUNSHEET.md)
* Existing solutions: stop-and-go, encoder line tracking, visual servoing, Kalman tracking; the gap.
* Novelty N1-N5 with the numbers (success 59 to 71 % from the servo, 84 vs 41 % at 15 % ripple, 2.2 x throughput). Mention the negative result N5.
* Syllabus mapping table.
* Your module: how the camera image is made, how HSV gives the colour, the contour feature gives the shape, and the homography gives world coordinates.
* Platform: CoppeliaSim is the assigned platform; the same software also ran on MuJoCo for the large statistics (Section 8.1).

## Divya Israni, slides 7-9 (about 2.5 min, see VIDEO_RUNSHEET.md)
* Architecture block diagram: follow one cube from camera to bin.
* Robot and environment model.
* Algorithm 1: Kalman filter with encoder, latency compensation, earliest feasible intercept time, why some objects are skipped.

## Amritanshi Singh, slides 10-12 (about 2 min + live demo)
* Visual-servo law and why we aim at the predicted contact point, not the present position (our first version chased the cube and failed).
* PID gains from wn and zeta, step and tracking plots (P-only oscillates, PD smooth, feedforward lowers the PID error by 28 %).
* Simulation setup and commands.
* **Live demo (6 min)**: `python demo_cs.py --method m3 --speed 0.25`; show the arm waiting ahead of the cube, descending, placing in the matching bin. Then `--method m2 --speed 0.3` to show misses, and `--speed 0.35` to show the capacity limit. Rotate the CoppeliaSim view with the mouse. (Anchit can run the commands while Amritanshi explains.)

## Anchit Saxena, slides 13-15 (about 2.5 min, see VIDEO_RUNSHEET.md)
* Speed study figure: stop-and-go 100 % but slow; M3 3.6 to 4.0 mm error with a 3 mm perception floor; why success drops above 0.25 m/s (single arm cycle about 2 s).
* Robustness figure and ablation: servo gives the largest gain; Kalman gives accuracy margin; scheduling did not help.
* Team contribution table.

## All, slides 16-17 (about 1 min)
Conclusion, industry use, what we learned together, thank you and Q&A.

## Before recording
1. Run `python demo_cs.py --n 3` once to check the window opens; close other heavy programs.
2. Everyone: camera on for the full recording; stay visible when not speaking.
3. Do not edit out parts; only trim the start and end. Check the length is between 18 and 22 minutes.
4. Upload to YouTube as **Unlisted** (not Public, not Private).
