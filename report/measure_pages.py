"""Measure how many pages each member's sections occupy in the exported PDF -> report/pages.json."""
import json
import os
import re
import sys

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
pdf = sys.argv[1]
doc = pymupdf.open(pdf)
HEADS = ["1.  Introduction", "2.  Problem Statement and Objectives", "3.  Literature and Industry Review", "4.  Novelty",
         "5.  Syllabus Mapping and Theory", "6.  System Design", "7.  Methodology and Algorithms", "8.  Simulation Setup",
         "9.  Results and Analysis", "9.3 Comparison of the three strategies", "10.  Contribution", "11.  Co-learning Reflection", "12.  Conclusion and Future Scope",
         "References", "Appendix: Links and Logs"]
pos = {}
for pi, page in enumerate(doc):
    txt = page.get_text()
    if "Index (Table of Contents)" in txt or "List of Figures" in txt or "List of Tables" in txt:
        continue
    for h in HEADS:
        if h in pos:
            continue
        for b in page.get_text("blocks"):
            if " ".join(b[4].strip().split("\n")[0].split()) == " ".join(h.split()):
                pos[h] = pi + b[1] / page.rect.height
                break
end = len(doc)
last_page = doc[-1]
words = last_page.get_text("blocks")
end_pos = len(doc) - 1 + max(b[3] for b in words if b[3] < last_page.rect.height - 60) / last_page.rect.height
pos["END"] = end_pos


def span(a, b):
    return pos[b] - pos[a]


groups = {
    "alloc0": [("1.  Introduction", "3.  Literature and Industry Review"), ("12.  Conclusion and Future Scope", "References"), ("Appendix: Links and Logs", "END")],
    "alloc1": [("3.  Literature and Industry Review", "5.  Syllabus Mapping and Theory"), ("8.  Simulation Setup", "9.  Results and Analysis"),
               ("References", "Appendix: Links and Logs")],
    "alloc2": [("5.  Syllabus Mapping and Theory", "7.  Methodology and Algorithms")],
    "alloc3": [("7.  Methodology and Algorithms", "8.  Simulation Setup"), ("9.  Results and Analysis", "9.3 Comparison of the three strategies"), ("References", "Appendix: Links and Logs")],
    "alloc4": [("9.3 Comparison of the three strategies", "10.  Contribution")],
}
out = {}
for k, spans in groups.items():
    tot = sum(span(a, b) for a, b in spans)
    if k == "alloc0":
        tot += 0.5  # abstract
    out[k] = "%.1f" % (round(tot * 2) / 2)
json.dump(out, open(os.path.join(HERE, "pages.json"), "w"))
print(out, {k: round(v, 2) for k, v in pos.items()})
