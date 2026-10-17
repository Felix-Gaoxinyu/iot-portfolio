"""Search the extracted Pre-Study Guide for anything about assessment,
presentation, or how work is handed over."""
import re

PATH = r"C:\dd\Sensorik+Aktorik\tools\guide.txt"
text = open(PATH, encoding="utf-8").read()

# join the wrapped lines into logical sentences so the quotes read properly
flat = re.sub(r"\s*\n\s*", " ", text)
flat = re.sub(r"===== PAGE[^=]*=====", " ", flat)
sentences = re.split(r"(?<=[.!?:])\s+", flat)

GROUPS = {
    "presentation / speaking": ["present", "vortrag", "defend", "oral", "talk about",
                                "explain it", "walk through"],
    "assessment": ["assess", "grad", "point", "credit", "mark", "schein"],
    "when": ["first session", "second session", "session 2", "day 1", "syllabus"],
    "handover": ["submit", "upload", "hand in", "share", "send", "link", "lms",
                 "instructor", "repo", "template", "github"],
}

for group, keys in GROUPS.items():
    print("=" * 70)
    print("##", group)
    print("=" * 70)
    seen = set()
    for s in sentences:
        low = s.lower()
        if any(k in low for k in keys) and len(s) > 25:
            key = s[:90]
            if key in seen:
                continue
            seen.add(key)
            s2 = s.strip()
            print("  *", s2[:430])
            print()
