"""Search the real course sources (syllabus.md, pre-study.md) for the rules the
user needs: how work is submitted, and whether anything must be presented."""
import os
import re

DIR = r"C:\dd\Sensorik+Aktorik\.scratch"
FILES = ["syllabus.md", "pre-study.md"]

KEYS = {
    "PORTFOLIO / GIT TEMPLATE": ["portfolio", "iot-portfolio", "template", "git", "github", "repo"],
    "SUBMISSION / ABGABE": ["submit", "submission", "abgabe", "hand in", "upload", "einreich",
                            "elearning", "ilias", "moodle", "lms"],
    "PRESENTATION / VORTRAG": ["present", "presentation", "vortrag", "präsentation", "referat",
                               "oral", "defend", "prüfung", "exam"],
    "ASSESSMENT / GRADING": ["assess", "grade", "grading", "note", "punkte", "point",
                             "credit", "leistungsnachweis", "schein", "bonus"],
    "DEADLINE / WHEN": ["deadline", "due", "frist", "first session", "second session",
                        "erste", "zweite", "week", "woche"],
}

for fn in FILES:
    path = os.path.join(DIR, fn)
    if not os.path.exists(path):
        continue
    text = open(path, encoding="utf-8").read()
    flat = re.sub(r"\s*\n\s*", " ", text)
    sentences = re.split(r"(?<=[.!?])\s+", flat)
    print("#" * 74)
    print("#", fn)
    print("#" * 74)
    for group, keys in KEYS.items():
        hits = [s.strip() for s in sentences
                if any(k in s.lower() for k in keys) and len(s) > 30]
        if not hits:
            continue
        print("\n---", group, f"({len(hits)} hits) ---")
        seen = set()
        for s in hits[:14]:
            k = s[:70]
            if k in seen:
                continue
            seen.add(k)
            print("  *", s[:400])
    print()
