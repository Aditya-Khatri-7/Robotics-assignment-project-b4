# Submission checklist (deadline 29 October 2026; 10 % penalty per day late)

## Things only you can do (highlighted yellow in the report / slides)
- [x] Title page: the report is built directly on the official `AISR_Sample_Project_Report.docx` template (UPES logo, layout, border, numbering); only title, P14/G10/B4 and members changed. Add the faculty name under 'Submitted to' if your faculty wants it.
- [ ] **GitHub**: create one repository, push this folder. **Every member must commit their own module from their own account** (see README owner table). Put the link in the Appendix and slide 17.
- [ ] **Contribution table (Section 10)**: the table assumes the module split in the README. If your real split differs, edit it. Each claim must be traceable to your commits and to the video. Each member signs their own row.
- [ ] **Section 11 reflections**: replace the drafts with your own words (5 to 8 lines each).
- [ ] **Meeting log**: fill real dates, durations and decisions (at least a few real meetings).
- [ ] **Peer-assessment sheets**: each member fills one for every team-mate and attaches it.
- [ ] **References [2] FANUC and [3] ABB**: open the product pages, confirm title and URL, fill the access date (or replace them with other industry sources).
- [ ] Declaration: all five sign.
- [ ] Record the **video** (18 to 22 min, all visible, camera on, live demo), upload to YouTube as **Unlisted**, paste the link.
- [ ] **Print** the report single-sided and bind it (spiral or soft). A printed copy is mandatory (without it, report marks = 0).
- [ ] The team lead submits the Google Form: report PDF, slides PDF, GitHub link, YouTube link.

## Files in this folder
| File | Use |
|---|---|
| `AISR_G10_Project_Report.docx` / `.pdf` | report (34 pages). Edit the .docx, then in Word press Ctrl+A, F9 (update fields) and export PDF |
| `AISR_G10_Slides.pptx` / `.pdf` | 17 slides; submit the PDF |
| `demo.py`, `sortarm/`, `experiments.py`, `tests/`, ... | code for GitHub (run `python demo_cs.py` for the live CoppeliaSim demo) |
| `results/demo_cs_m3.mp4` | CoppeliaSim render (backup if the live demo fails) |
| `docs/COPPELIASIM_SETUP.md` | how to install CoppeliaSim EDU on the demo laptop (needed for `python demo_cs.py`) |
| `docs/SPEAKER_SCRIPT.md` | who says what in the 20-minute video |
| `docs/VIDEO_RUNSHEET.md` | minute-by-minute run sheet and demo commands for the video |
| `docs/GITHUB_GUIDE.md` | how every member commits their own module from their own account |
| `check_ready.py` | run `python check_ready.py --tests`: verifies the rules of the instruction PDF and lists what is still open |
| `docs/VIVA_QA.md` | questions for the viva |

## What the P14 description asks for (all covered in the report)
Detect objects by **colour and shape** (HSV + contour shape, reject bin for cylinders); arm computes the grasp point with **inverse kinematics / D-H transformations** (Section 5.1); sorts into bins; syllabus topics Robotic Perception, D-H Transformations, Closed-Loop Control, Application Domains (Table 5); domain: quality inspection and sorting in manufacturing (Section 1.3). The assigned platform is CoppeliaSim: the demo, video and a cross-platform study run in CoppeliaSim (Sections 8.1 and 9.7); MuJoCo is used for the large statistics.

## Format rules already met (verify once after editing)
A4, margins 3.0 / 2.5 / 2.5 / 2.5 cm, border on every page, Times New Roman 12 pt 1.5 spacing justified, headings 14 / 12 pt bold,
page numbers bottom centre (roman for front pages, arabic from Section 1), index + list of figures + list of tables,
writing allocation after the index, 16 IEEE references all cited, Sections 4 and 10 present, 34 pages (limit 25-35), 17 slides.

## If you edit the report
Keep the page count between 25 and 35, keep every figure and table referenced in the text, and keep every reference cited.
