import os
import re

ROOT = r"C:\dd\Sensorik+Aktorik"
MD = os.path.join(ROOT, "pre-study", "README.md")
base = os.path.dirname(MD)

t = open(MD, encoding="utf-8").read()
print("chars:", len(t), " lines:", t.count("\n") + 1)

print("\n-- local links --")
bad = 0
for m in re.finditer(r"\]\((?!http)([^)]+)\)", t):
    target = m.group(1).split("#")[0]
    if not target:
        continue
    p = os.path.normpath(os.path.join(base, target))
    ok = os.path.exists(p)
    if not ok:
        bad += 1
    print(("OK   " if ok else "MISS "), m.group(1))
print("broken links:", bad)

print("\n-- anchors --")
heads = re.findall(r"^#{1,6} (.+)$", t, re.M)


def slug(h):
    """Match github-slugger: lowercase, drop punctuation, then turn EACH space
    into a hyphen (runs are NOT collapsed, so 'a - b' -> 'a--b')."""
    s = h.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    return s.replace(" ", "-")


slugs = {slug(h) for h in heads}
for m in re.finditer(r"\]\((#[^)]+)\)", t):
    a = m.group(1)[1:]
    print(("OK   " if a in slugs else "MISS "), "#" + a)

print("\n-- leftovers --")
for bad_tok in ["<!--", "SECTION3", "«capture»", "«paste", "TODO", "FIXME", "wokwi-circuit"]:
    if bad_tok in t:
        print("  FOUND:", bad_tok)
print("  (none listed above = clean)")

print("\n-- key numbers present --")
for n in ["3843", "960", "240", "4096", "1024", "256", "142 mV", "681 mV", "3067 mV", "85.6", "70.0"]:
    print(f"  {n:10s} {'yes' if n in t else 'NO'}")

print("\n-- evidence files referenced exist --")
for f in ["12bit-pot160", "12bit-pot960", "10bit-pot960", "8bit-pot960", "12bit-coarse-pot960"]:
    for ext in [".png", "-serial.txt"]:
        p = os.path.join(ROOT, "pre-study", "wokwi", "evidence", f + ext)
        print(("OK   " if os.path.exists(p) else "MISS "), f + ext)
