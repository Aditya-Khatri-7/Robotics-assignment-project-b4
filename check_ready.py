"""Submission readiness checker: verifies the rules of the AISR project instructions and lists what is still open.

    python check_ready.py            # fast checks
    python check_ready.py --tests    # also run the unit tests
"""
import os
import re
import subprocess
import sys

import pymupdf
from docx import Document
from pptx import Presentation
from pptx.util import Pt

HERE = os.path.dirname(os.path.abspath(__file__))
REPORT_PDF = os.path.join(HERE, "AISR_G10_Project_Report.pdf")
REPORT_DOCX = os.path.join(HERE, "AISR_G10_Project_Report.docx")
SLIDES_PDF = os.path.join(HERE, "AISR_G10_Slides.pdf")
SLIDES_PPTX = os.path.join(HERE, "AISR_G10_Slides.pptx")

ok_count = 0
fails = []
todo = []


def check(name, cond, detail=""):
    global ok_count
    if cond:
        ok_count += 1
        print("  [ok]   %s %s" % (name, detail))
    else:
        fails.append(name)
        print("  [FAIL] %s %s" % (name, detail))


print("REPORT (PDF)")
for f in (REPORT_PDF, REPORT_DOCX, SLIDES_PDF, SLIDES_PPTX):
    check("file exists: " + os.path.basename(f), os.path.exists(f))
d = pymupdf.open(REPORT_PDF)
pages = len(d)
txt = " ".join(" ".join(p.get_text().split()) for p in d)
check("pages 25-35 (including front pages)", 25 <= pages <= 35, "(%d)" % pages)
m = re.search(r"Abstract (.*?) Keywords", txt)
words = len(m.group(1).split()) if m else 0
check("abstract 150-200 words", 150 <= words <= 200, "(%d)" % words)
check("page size A4", abs(d[0].rect.width - 595) < 3 and abs(d[0].rect.height - 842) < 3)
for sec in ("Declaration", "Abstract", "Index", "List of Figures", "List of Tables", "Writing Allocation", "Introduction", "Problem Statement and Objectives",
            "Literature and Industry Review", "Novelty", "Syllabus Mapping and Theory", "System Design", "Methodology and Algorithms", "Simulation Setup",
            "Results and Analysis", "Contribution", "Co-learning Reflection", "Conclusion and Future Scope", "References", "Appendix: Links and Logs"):
    check("section present: " + sec, sec in txt)
refs = sorted(set(int(x) for x in re.findall(r"\[(\d+)\]", txt)))
check(">= 8 references, all cited in order", len(refs) >= 8 and refs == list(range(1, max(refs) + 1)), "(%d)" % (max(refs) if refs else 0))
body = txt[txt.index("Writing Allocation The writing"):]
n_fig = len(set(re.findall(r"Figure (\d+):", txt)))
n_tab = len(set(re.findall(r"Table (\d+):", txt)))
unref_f = [k for k in range(1, n_fig + 1) if not re.search(r"Figure %d\b(?!:)" % k, body)]
unref_t = [k for k in range(1, n_tab + 1) if not re.search(r"Table %d\b(?!:)" % k, body)]
check("every figure referred to in the text", not unref_f, "(%d figures, unreferenced: %s)" % (n_fig, unref_f))
check("every table referred to in the text", not unref_t, "(%d tables, unreferenced: %s)" % (n_tab, unref_t))
check("no leftover markup", not any(t in txt for t in ("<sub>", "&#", "**", "{F:", "{T:", "{c:", "Error!")))
check("page numbers roman (front) then arabic (body)", bool(re.search(r"\bii\b", txt)) and bool(re.search(r"\biv\b", txt)) and bool(re.search(r"\b20\b", txt)))

print("REPORT (DOCX formatting)")
doc = Document(REPORT_DOCX)
sec = doc.sections[-1]
check("margins 3.0 / 2.5 / 2.5 / 2.5 cm", abs(sec.left_margin.cm - 3.0) < 0.05 and abs(sec.right_margin.cm - 2.5) < 0.05 and abs(sec.top_margin.cm - 2.5) < 0.05 and abs(sec.bottom_margin.cm - 2.5) < 0.05)
check("Times New Roman 12 pt, 1.5 spacing", doc.styles["Normal"].font.name == "Times New Roman" and doc.styles["Normal"].font.size.pt == 12 and doc.styles["Normal"].paragraph_format.line_spacing == 1.5)
borders = [s._sectPr.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pgBorders") is not None for s in doc.sections]
check("page border in every section", all(borders), "(%d sections)" % len(borders))

print("SLIDES")
prs = Presentation(SLIDES_PPTX)
check("slides <= 17", len(prs.slides) <= 17, "(%d)" % len(prs.slides))
small = 0
for sl in prs.slides:
    for shp in sl.shapes:
        if shp.has_text_frame and not shp.text_frame.text.startswith(("Presenter", "CSAI4014")) and not shp.text_frame.text.strip().isdigit():
            for p in shp.text_frame.paragraphs:
                for r in p.runs:
                    if r.font.size and r.font.size < Pt(20):
                        small += 1
check("no body text below 20 pt (instruction sheet)", small == 0, "(%d small runs)" % small)
check("presenter name on every slide", all(any(s.has_text_frame and s.text_frame.text.startswith("Presenter") for s in sl.shapes) for sl in prs.slides))
check("speaker notes on every slide", all(sl.has_notes_slide and sl.notes_slide.notes_text_frame.text.strip() for sl in prs.slides))
check("slides PDF page count", len(pymupdf.open(SLIDES_PDF)) == len(prs.slides))

print("CODE AND RESULTS")
for f in ("README.md", "requirements.txt", "demo.py", "experiments.py", "render_3d.py", "results/all_runs.csv", "results/confirm_runs.csv", "results/cs_runs.csv", "results/demo_cs_m3.mp4", "demo_cs.py", "docs/COPPELIASIM_SETUP.md",
          "docs/SPEAKER_SCRIPT.md", "docs/VIVA_QA.md", "docs/SUBMISSION_CHECKLIST.md"):
    check("exists: " + f, os.path.exists(os.path.join(HERE, f)))
if "--tests" in sys.argv:
    r = subprocess.run([sys.executable, os.path.join(HERE, "tests", "test_core.py")], capture_output=True, text=True)
    check("unit tests pass", r.returncode == 0 and r.stdout.count("ok ") >= 10, "(%d ok)" % r.stdout.count("ok "))

print("STILL OPEN (needs the team)")
body = doc.element.body
hl = []
for r in body.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r"):
    if r.find(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}highlight") is not None:
        t = "".join(x.text or "" for x in r.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"))
        if t.strip():
            hl.append(t.strip())
for t in dict.fromkeys(hl):
    todo.append("report: " + t[:90])
for sl in prs.slides:
    for shp in sl.shapes:
        if shp.has_text_frame and re.search(r"<[A-Za-z][^<>]*>", shp.text_frame.text):
            todo.append("slides: " + shp.text_frame.text.strip()[:90])
todo += ["each member: sign declaration and own contribution row (printed copy)", "each member: personal peer-assessment sheet", "video: 18-22 min, all visible, YouTube Unlisted",
         "print and bind the report (mandatory)", "GitHub: each member commits own module from own account"]
for t in todo:
    print("  [todo] " + t)

print("\nSUMMARY: %d checks passed, %d failed, %d open items for the team" % (ok_count, len(fails), len(todo)))
sys.exit(1 if fails else 0)
