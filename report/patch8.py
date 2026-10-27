R = 'D:/!aRobotics project/sortarm_project/'
p = R + 'report/build_report.py'
s = open(p, encoding='utf8').read()


def rep(a, b):
    global s
    assert a in s, a[:90]
    s = s.replace(a, b, 1)


# ---------------------------------------------------------------- references
rep('    "iso":', '''    "coppelia": 'E. Rohmer, S. P. N. Singh, and M. Freese, "CoppeliaSim (formerly V-REP): A versatile and scalable robot simulation framework," in <i>Proc. IEEE/RSJ Int. Conf. Intell. Robots Syst. (IROS)</i>, Tokyo, Japan, Nov. 2013, pp. 1321-1326.',
    "gw": 'R. C. Gonzalez and R. E. Woods, <i>Digital Image Processing</i>, 4th ed. New York, NY, USA: Pearson, 2018.',
    "dhorig": 'J. Denavit and R. S. Hartenberg, "A kinematic notation for lower-pair mechanisms based on matrices," <i>J. Appl. Mech.</i>, vol. 22, no. 2, pp. 215-221, Jun. 1955.',
    "iso":''')

# ---------------------------------------------------------------- numbers
rep('    vis["acc"] = 100 * vis.color_correct / vis.objects',
    '''    vis["acc"] = 100 * vis.color_correct / vis.objects
    vis["acc_shape"] = 100 * vis.shape_correct / vis.objects
    n_def, n_all = int(df.defects.sum()), int(df.n.sum())
    n_fa, n_fr, n_ce = int(df.false_accept.sum()), int(df.false_reject.sum()), int(df.colour_err.sum())
    n_good = n_all - n_def''')

# ---------------------------------------------------------------- abstract
a = s.index('    b.p("Conveyor-based sorting is common in logistics')
b_ = s.index('    kw = d.add_paragraph()')
s = s[:a] + '''    b.p("Quality inspection and sorting on moving conveyors is common in manufacturing, but a robot that must pick moving parts often needs the belt stopped, "
        "which wastes throughput. This project simulates a vision-guided sorting arm in the MuJoCo 3-D physics engine. An overhead camera detects parts by colour and shape: "
        "red, green and blue cubes go to colour bins and cylinders, which stand for wrong-shape parts, go to a reject bin. A SCARA arm with a suction gripper intercepts each part "
        "while the belt moves. The software chain is an OpenCV colour and shape detector with homography calibration, a Kalman tracker that fuses camera and belt-encoder data, "
        "a D-H based inverse-kinematics intercept planner with minimum-jerk motion, and joint PID control with feedforward. The novelty is a predictive visual-servo descent that keeps "
        "correcting the grasp point while the arm moves. In 560 runs, where a part counts only if it physically rests in the right bin, it reduced the mean grasp error "
        "from %.1f to %.1f mm, kept %.0f %% success at 15 %% belt-speed ripple against %.0f %% for plain prediction, and gave %.1f times the throughput of a stop-and-go cell." % (
            sp.loc[M2].err.mean(), sp.loc[M3].err.mean(), rip.loc[(M3, 0.15)].succ, rip.loc[(M2, 0.15)].succ,
            sp.loc[(M3, 0.25)].thr / sp.loc[(M1, 0.25)].thr))
''' + s[b_:]
rep('kw.add_run("SCARA arm, conveyor sorting, visual servoing, Kalman filter, D-H transformations, MuJoCo, OpenCV.")',
    'kw.add_run("vision-guided sorting, quality inspection, SCARA arm, D-H transformations, visual servoing, Kalman filter, MuJoCo, OpenCV.")')

# ---------------------------------------------------------------- section 1
rep('    b.h2("1.3 Scope of this project")', '''    b.h2("1.3 Application domain: quality inspection and sorting in manufacturing")
    b.p("The application domain of this project is quality inspection and sorting in manufacturing. On an assembly or packaging line, a camera checks every part that passes: "
        "the colour identifies the variant (for example the colour code of a component or of a cap) and the outline identifies whether the part has the correct shape. "
        "A part with the wrong outline is a reject and must be removed from the flow, while correct parts must be delivered to the bin of their variant. "
        "In our cell the correct parts are cubes in three colours and the rejects are cylinders (25 %% of all parts). A robot that does this on a moving belt without stopping it is attractive "
        "because every stop of the belt reduces the output of the whole line. The inspection quality is measured by two error rates: false accepts (a reject delivered to a colour bin) and false rejects (a correct part sent to the reject bin)." )
    b.h2("1.4 Scope of this project")''')
rep('"system recognises coloured cubes, tracks them, plans an intercept for a SCARA arm, executes the motion with a joint-level controller and "\n        "places each cube into the bin of its colour.',
    '"system recognises parts by colour and shape, tracks them, plans an intercept for a SCARA arm, executes the motion with a joint-level controller and "\n        "places each cube into the bin of its colour and each wrong-shape part into the reject bin.')
# 1.3 paragraph contains a literal %% but is not formatted: fix
s = s.replace('(25 %% of all parts)', '(25 % of all parts)')

# ---------------------------------------------------------------- section 2
rep('A conveyor moves at a nominal speed v between 0.05 and 0.35 m/s. Cubes of side 30 mm in one of three colours (red, green, blue) are "\n        "placed at random lateral positions and orientations with a random spacing of 0.35 to 0.55 m. A fixed overhead camera observes the belt. "\n        "A SCARA arm with a suction gripper stands beside the belt (Figure 1). The task is to pick every cube while the belt keeps moving and to "\n        "release it into the bin that matches its colour, with the highest possible success rate and throughput. {F:layout} shows the "\n        "layout, the camera field of view, the pick window and the three bins.")',
    'A conveyor moves at a nominal speed v between 0.05 and 0.35 m/s. Parts of height 30 mm are placed at random lateral positions and orientations with a random spacing of 0.35 to 0.55 m: "\n        "75 %% are cubes (side 30 mm) in red, green or blue and 25 %% are cylinders (diameter 36 mm) in any of the three colours. A fixed overhead camera observes the belt. "\n        "A SCARA arm with a suction gripper stands beside the belt (Figure 1). The task is to detect every part by colour and shape, pick it while the belt keeps moving and to "\n        "release cubes into the bin of their colour and cylinders into the reject bin, with the highest possible success rate and throughput. {F:layout} shows the "\n        "layout, the camera field of view, the pick window and the four bins.")')
rep('        ["O1", "Detect and classify cubes in the camera image", ">= 99 % correct at image noise up to 40 gray levels",\n         "%.0f %% (noise 40, nominal light)" % vis[(vis.noise == 40) & (vis.light == 1.0)].acc.iloc[0]],',
    '        ["O1", "Detect parts and classify colour and shape in the camera image", ">= 99 % correct at image noise up to 40 gray levels",\n         "colour %.0f %%, shape %.0f %% (noise 40, nominal light)" % (vis[(vis.noise == 40) & (vis.light == 1.0)].acc.iloc[0], vis[(vis.noise == 40) & (vis.light == 1.0)].acc_shape.iloc[0])],')
rep('''         "%.1f %% vs %.1f %%" % (rip.loc[(M3, 0.15)].succ, rip.loc[(M3, 0.03)].succ)],
    ], (1.1, 5.2, 5.0, 4.2), size=9.5)''', '''         "%.1f %% vs %.1f %%" % (rip.loc[(M3, 0.15)].succ, rip.loc[(M3, 0.03)].succ)],
        ["O6", "Inspection quality: no defective part accepted", "false accepts <= 1 %, false rejects <= 1 %",
         "false accepts %d of %d, false rejects %d of %d (all runs)" % (n_fa, n_def, n_fr, n_good)],
    ], (1.1, 5.2, 5.0, 4.2), size=9.5)''')
rep('rendered from the 3-D scene at 2.5 mm/pixel, 20 frames per second', 'rendered from the 3-D scene at 1.5 mm/pixel, 20 frames per second')
rep('"Cubes are free rigid bodies with contact and friction; they must physically come to rest inside the bin of their colour to count as sorted.",',
    '"Parts are free rigid bodies with contact and friction; a part counts as sorted only if it physically comes to rest inside the correct bin (cubes: colour bin, cylinders: reject bin). Cylinders stand for defective, wrong-shape parts and appear with a probability of 25 %.",')
rep('"Only three colours are sorted and objects never touch each other on the belt.', '"Only three colours and two shapes are used and objects never touch each other on the belt.')

# ---------------------------------------------------------------- section 5: syllabus table (official topics of P14)
a = s.index('    b.table("syl", "AISR syllabus topics used in the project and where they are used.", [')
b_ = s.index('    b.h2("5.1 Kinematics of the SCARA arm")')
s = s[:a] + '''    b.table("syl", "AISR syllabus topics of Project P14 and where they are used.", [
        ["AISR topic (Project List)", "Used for", "Section"],
        ["Robotic Perception", "Rendered camera, homography calibration, HSV colour segmentation, contour-based shape classification, Kalman tracking", "5.5, 5.6"],
        ["D-H Transformations", "D-H table and homogeneous matrices A1 A2 A3 of the SCARA arm, forward and inverse kinematics, Jacobian", "5.1, 5.2"],
        ["Closed-Loop Control", "Joint PID with feedforward, minimum-jerk reference, visual-servo descent (vision in the loop)", "5.3, 5.4"],
        ["Application Domains", "Quality inspection and sorting in manufacturing: colour and shape inspection, reject bin, throughput", "1.3, 5.7"],
    ], (4.4, 9.5, 1.6), size=9.5)
''' + s[b_:]

# ---------------------------------------------------------------- 5.1 D-H
rep('"The Denavit-Hartenberg parameters {c:craig} are listed in {T:dh}. The planar tip position follows from the forward kinematics:")',
    '"The Denavit-Hartenberg parameters {c:dhorig,craig} are listed in {T:dh}. With the D-H convention each link is described by the homogeneous transformation A<sub>i</sub> = Rot<sub>z</sub>(&#952;<sub>i</sub>) Trans<sub>z</sub>(d<sub>i</sub>) Trans<sub>x</sub>(a<sub>i</sub>) Rot<sub>x</sub>(&#945;<sub>i</sub>):")')
rep('''        (2.5, 3.0, 3.0, 3.0, 3.5), size=10, align_left=False)
    b.eq("x = L₁ cos q₁ + L₂ cos(q₁ + q₂),     y = L₁ sin q₁ + L₂ sin(q₁ + q₂)")''', '''        (2.5, 3.0, 3.0, 3.0, 3.5), size=10, align_left=False)
    b.eq("A<sub>i</sub> = [cθ<sub>i</sub>  −sθ<sub>i</sub>cα<sub>i</sub>  sθ<sub>i</sub>sα<sub>i</sub>  a<sub>i</sub>cθ<sub>i</sub>;  sθ<sub>i</sub>  cθ<sub>i</sub>cα<sub>i</sub>  −cθ<sub>i</sub>sα<sub>i</sub>  a<sub>i</sub>sθ<sub>i</sub>;  0  sα<sub>i</sub>  cα<sub>i</sub>  d<sub>i</sub>;  0  0  0  1]")
    b.p("For the SCARA table (all &#945;<sub>i</sub> = 0) the chain T<sub>0</sub><super>3</super> = A<sub>1</sub> A<sub>2</sub> A<sub>3</sub> gives the pose of the tool frame:")
    b.eq("T = [c₁₂  −s₁₂  0  L₁c₁ + L₂c₁₂;  s₁₂  c₁₂  0  L₁s₁ + L₂s₁₂;  0  0  1  −z;  0  0  0  1],     c₁₂ = cos(q₁ + q₂)")
    b.p("Its position column is the forward kinematics of the tip, and its rotation part shows that the tool turns by q<sub>1</sub> + q<sub>2</sub> about the vertical axis. A unit test confirms that the matrix chain equals the closed-form tip position for 100 random poses:")
    b.eq("x = L₁ cos q₁ + L₂ cos(q₁ + q₂),     y = L₁ sin q₁ + L₂ sin(q₁ + q₂)")''')

# ---------------------------------------------------------------- 5.5 perception
rep('b.h2("5.5 Camera model, calibration and colour detection")', 'b.h2("5.5 Camera model, calibration, colour and shape detection")')
rep('''"of each connected component gives the cube position with sub-pixel accuracy.")''', '''"of each connected component gives the part position with sub-pixel accuracy {c:gw}.")
    b.p("The shape is decided from the contour of each component. A circle has the same distance from its centroid to every contour point, a square has "
        "distances between half the side and half the diagonal. The coefficient of variation of the contour radius r is therefore a simple, rotation-invariant shape feature:")
    b.eq("CV = σ<sub>r</sub> / μ<sub>r</sub>,     circle if CV < 0.06,  square otherwise")
    b.p("At 1.5 mm/pixel the measured values are about 0.02 for the cylinders (pixels spread over 0.019 to 0.026) and 0.09 to 0.11 for the cubes, so the threshold lies far from both classes. "
        "At 2.5 mm/pixel the two classes overlapped, which is why the camera resolution was raised.")''')

# ---------------------------------------------------------------- 6.2
rep('which gives an image of 480 x 104 pixels at 2.5 mm per pixel. Three bins for red, green and blue cubes lie on the opposite "\n        "side of the arm at (-0.25, -0.30), (0, -0.35) and (0.25, -0.30) m.',
    'which gives an image of 800 x 173 pixels at 1.5 mm per pixel. Three bins for red, green and blue cubes lie on the opposite "\n        "side of the arm at (-0.25, -0.30), (0, -0.35) and (0.25, -0.30) m; the reject bin for cylinders is at (0.48, -0.12) m.')
rep('["Camera", "Resolution, frame rate, latency", "2.5 mm/pixel, 20 fps, 80 ms"],', '["Camera", "Resolution, frame rate, latency", "1.5 mm/pixel (800 x 173), 20 fps, 80 ms"],')
rep('["Objects", "Cube size, spacing", "30 mm, 0.35-0.55 m"],', '["Objects", "Cube side, cylinder diameter, share of cylinders", "30 mm, 36 mm, 25 %"],\n        ["Objects", "Spacing on the belt", "0.35-0.55 m"],')

# ---------------------------------------------------------------- 7.2
rep('"thresholds, removes noise by opening, labels connected components and discards blobs with fewer than 45 pixels or touching the image border (partly visible cubes would bias the centroid). "',
    '"thresholds, removes noise by opening, labels connected components and discards blobs that are too small or touch the image border (partly visible parts would bias the centroid). "\n        "For every remaining blob the contour is extracted and the shape feature CV of Section 5.5 gives the class square or circle. "')

# ---------------------------------------------------------------- 8.1 platform justification
rep('b.h2("8.2 Experiments")', '''b.p("**Choice of simulator.** The Project List suggests CoppeliaSim {c:coppelia} (vision sensor, arm and conveyor) with Python and OpenCV, and the project instructions allow any simulator "
        "or Python simulation library. We used MuJoCo because it is installed with one command, runs headless and in parallel on many cores (560 runs in about 15 minutes), is deterministic for a given seed, and gives "
        "direct access to the rigid-body state for the physical sorting check. {T:map} shows how each element of the suggested CoppeliaSim set-up is realised in our cell; the perception, planning and control code is plain Python and OpenCV and would "
        "run unchanged against a CoppeliaSim scene through its remote API, which is listed as future work.")
    b.table("map", "Elements of the suggested CoppeliaSim set-up and their counterparts in this project.", [
        ["CoppeliaSim element", "This project (MuJoCo + Python)"],
        ["Vision sensor", "Orthographic camera rendered by MuJoCo, 800 x 173 px, 20 fps, noise and latency added"],
        ["Robot arm (SCARA / serial arm)", "Torque-driven rigid-body SCARA arm with the D-H table of Table 5"],
        ["Conveyor belt", "Kinematic conveyor with speed ripple and an encoder signal"],
        ["Objects, bins", "Free rigid bodies (cubes, cylinders); four bins with real contact physics"],
        ["Python + OpenCV control code", "Identical: detector, tracker, planner and controller are Python and OpenCV"],
    ], (5.0, 10.5), size=9.5)
    b.h2("8.2 Experiments")''')
rep('TAB_ORDER = ["alloc", "obj", "lit", "nov", "syl", "dh", "par", "meth", "sim", "val",', 'TAB_ORDER = ["alloc", "obj", "lit", "nov", "syl", "dh", "par", "meth", "map", "sim", "val",')

# ---------------------------------------------------------------- 9.2 shape accuracy + 9.3 inspection
rep('"The position RMSE is about %.1f mm.', '"Shape classification is correct for %.0f %% of the parts at noise 40 and %.0f %% at noise 60 with light x0.7. "\n        "The position RMSE is about %.1f mm.')
rep('"because the tracker keeps extrapolating the object." % (vis.objects.iloc[0], v40.acc.iloc[0],', '"because the tracker keeps extrapolating the object." % (vis.objects.iloc[0], v40.acc.iloc[0],')
rep('v60.acc.iloc[0], v80.acc.iloc[0], vis[vis.noise == 8].rmse_mm.mean()))', 'v60.acc.iloc[0], v80.acc.iloc[0], v40.acc_shape.iloc[0], v60.acc_shape.iloc[0], vis[vis.noise == 8].rmse_mm.mean()))')
rep('    b.fig("speed", "(a) Sorting success, (b) throughput and (c) grasp error versus belt speed.", 15.0)',
    '''    b.fig("speed", "(a) Sorting success, (b) throughput and (c) grasp error versus belt speed.", 15.0)
    b.p("**Inspection quality.** Over all 560 runs (%d parts, of which %d cylinders) %d defective parts were accepted into a colour bin (false accepts) and %d of the %d cubes were sent to the reject bin (false rejects); "
        "%d cubes were delivered to a wrong colour bin. Every mistake of this kind therefore comes from a part that was not handled at all (lost from the belt), not from a wrong classification, "
        "and the colour and shape classification of the parts that were handled was correct." % (n_all, n_def, n_fa, n_fr, n_good, n_ce))''')

# ---------------------------------------------------------------- conclusion
rep('and an unscented filter for varying belt speed, a ROS integration', 'and an unscented filter for varying belt speed, a port of the cell to CoppeliaSim through its remote API, a ROS integration') if 'and an unscented filter for varying belt speed, a ROS integration' in s else None
s = s.replace('an unscented filter for varying belt speed, a ROS integration and a hardware-in-the-loop test on a real SCARA arm.', 'an unscented filter for varying belt speed, a port of the cell to CoppeliaSim through its remote API, a ROS integration and a hardware-in-the-loop test on a real SCARA arm.')
rep('"**Industrial use.** The same structure applies to parcel and component sorting, food grading and recycling lines.', '"**Industrial use.** The same structure applies to quality inspection and sorting in manufacturing (the application domain of this project), parcel and component sorting, food grading and recycling lines.')
open(p, 'w', encoding='utf8').write(s)

f = R + 'make_figures.py'
t = open(f, encoding='utf8').read()
t = t.replace('("HSV blobs -> colour + world (x, y)", 10.5)', '("HSV blobs -> colour, shape, world (x, y)", 10.5)')
t = t.replace('("|p_tip - p_cube| < 10 mm?  Grasp,\\ntransport to colour bin, release", 1.2)', '("|p_tip - p_part| < 10 mm?  Grasp, transport to\\ncolour bin (cube) or reject bin (cylinder)", 1.2)')
open(f, 'w', encoding='utf8').write(t)
print('ok')
