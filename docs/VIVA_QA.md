# Viva preparation: questions every member should be able to answer

**Whole project (everyone)**
1. What is the task and what is the robot? Detect parts by colour and shape on a moving belt; SCARA arm with suction gripper picks them and sorts cubes into R/G/B bins and cylinders (wrong shape) into a reject bin. Domain: quality inspection and sorting in manufacturing.
2. What are the three methods compared? M1 stop-and-go, M2 predictive with line fit and fixed descent, M3 Kalman + encoder with visual-servo descent.
3. What is novel? Predictive visual-servo descent; latency-compensated Kalman + encoder fusion; the robustness and ablation study. The scheduling rule gave no gain (negative result).
4. Why does success fall above 0.25 m/s? The arm needs about 2 s per pick-and-place; objects arrive faster than served. This is capacity, not accuracy.
5. What are the limits of the simulation? Orthographic camera without lens distortion, kinematic conveyor, suction as a weld constraint, no collision avoidance with other equipment; the arm can occlude cubes and that is simulated.

**Kinematics and trajectory (Aditya)**
* Write the D-H table and the matrix A_i. Chain T = A1 A2 A3 gives the tip pose; the position column is x = L1 cos q1 + L2 cos(q1+q2), y = ...; the tool turns by q1+q2.
* Which CoppeliaSim objects did you create? Vision sensor (orthographic), two dynamic revolute joints with links, kinematic vertical axis with a suction tool, belt and bin shapes, parts as Bullet rigid bodies; all through the ZMQ remote API.
* Write FK and IK of the 2-link arm. Why two solutions? Elbow up / down; we pick the one nearest the current pose.
* What is det J? L1 L2 sin q2; singular at q2 = 0 or pi.
* Why minimum-jerk? Smooth, zero start/end velocity and acceleration; peak speed 1.875 d/T, peak accel 5.77 d/T^2.
* Why two platforms? CoppeliaSim is the assigned platform (demo, video, validation); MuJoCo is about five times faster and was used for 890 statistical runs. The same Python + OpenCV software ran on both, so the results are not an artefact of one engine.
* How is the joint control done in CoppeliaSim? A joint-callback script (Lua) evaluates the PID + feedforward law in every physics step; Python sends references once per step.
* What was the joint-range bug? MuJoCo reads ranges in degrees by default; we set the compiler to radians.
* Why a 3 x 3 release grid? Cubes released at one point stacked and overflowed the bin.
* Why did the first visual-servo version fail? The arm arrives ahead of the cube and waits, so chasing the current position moves it backwards; aim at the predicted contact point.

**Vision (Simran)**
* How is the shape decided? Contour radius coefficient of variation CV = std/mean: circle about 0.02, square about 0.10, threshold 0.06; needs 1.5 mm/pixel (at 2.5 mm/pixel the classes overlapped).
* Why a 5x5 Gaussian pre-blur? It makes the contour smooth under image noise; shape accuracy at noise 40 rose from 95 % to 99.7 %.
* Why HSV instead of RGB? Hue is nearly independent of brightness.
* How is pixel converted to metres? A homography from four marker points (getPerspectiveTransform).
* Why discard blobs at the image border? A partly visible cube biases the centroid.
* What limits position accuracy? About 2.5 mm RMSE: 1.9 mm from the detector itself (2.5 mm pixels, shadows), the rest from 0.8 mm calibration noise; image noise adds almost nothing; even stop-and-go has a 3 mm error floor.

**Tracking and planning (Divya)**
* State, model and measurements of the Kalman filter? x = [x, y, vx, vy], constant velocity; camera position, encoder speed and zero lateral speed.
* How is the 80 ms latency handled? The filter state is stamped at frame time; it is extrapolated to now with p + v dt.
* How is the intercept time found? Earliest t_a such that IK exists, point in window, and min-jerk time fits.
* Why no gain from SCT scheduling? All objects move at the same speed, so FIFO order is already the deadline order.

**Control (Amritanshi)**
* How were gains chosen? Kp = J wn^2, Kd = 2 zeta wn J, Ki = 0.2 Kp wn with wn = 50 rad/s.
* What does the step response show? P-only oscillates (78 % overshoot), PD has none, PID about 5 % with a small integral term; torque limits are 45 and 18 N m.
* What does the feedforward do? Cancels the nominal inertia and damping; max tracking error 7.9 to 5.7 mrad (28 % less); it cannot do more because the real inertia changes with the arm pose and the joints are coupled.

**Experiments (Anchit)**
* Why a confirmation study with 30 new seeds? With 10 seeds the Kalman gain had p = 0.20 (not significant); with 30 new seeds every gain except the scheduling rule is significant (Welch t-test, p < 0.001).
* What was the one false accept? M2 at 15 % ripple: the track followed a blue cube but the cup reached a neighbouring blue cylinder.
* What happens at very high image noise? Noise 60 (7.5 x default): shape accuracy 87 %, 22 cylinders accepted; colour stays 100 %.
* How many runs and which seeds? 560 runs; 10 seeds per point; same seeds for all methods.
* What is success rate, throughput, grasp error? See Section 8.3 of the report.
* Which result is the strongest evidence for the novelty? Ablation: removing the servo costs 12 points and removing the Kalman filter 5 points; the grasp error of the full method is the lowest.
