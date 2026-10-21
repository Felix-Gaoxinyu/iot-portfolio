"""Diagnose markdown problems that would make GitHub drop table cells or values."""
import json
import re

MD = r"C:\dd\Sensorik+Aktorik\pre-study\README.md"
text = open(MD, encoding="utf-8").read()
lines = text.splitlines()

print("=== 1. fenced code blocks (markdown inside them is not rendered) ===")
in_fence = False
fence_ranges = []
start = 0
for i, l in enumerate(lines, 1):
    if l.strip().startswith("```"):
        if not in_fence:
            in_fence = True
            start = i
        else:
            in_fence = False
            fence_ranges.append((start, i))
print(f"  {len(fence_ranges)} fenced blocks; final fence balanced: {not in_fence}")

in_code = set()
for a, b in fence_ranges:
    in_code.update(range(a, b + 1))


def split_row(l):
    """Split a markdown table row on unescaped pipes outside code spans."""
    cells, cur, ticks = [], "", 0
    i = 0
    while i < len(l):
        c = l[i]
        if c == "\\" and i + 1 < len(l):
            cur += l[i:i + 2]
            i += 2
            continue
        if c == "`":
            ticks ^= 1
            cur += c
            i += 1
            continue
        if c == "|" and ticks == 0:
            cells.append(cur)
            cur = ""
            i += 1
            continue
        cur += c
        i += 1
    cells.append(cur)
    return cells


print("\n=== 2. table integrity ===")
bad = 0
i = 0
tbl_no = 0
while i < len(lines):
    if (i + 1) in in_code or not lines[i].lstrip().startswith("|"):
        i += 1
        continue
    # start of a table
    tbl_no += 1
    block = []
    while i < len(lines) and lines[i].lstrip().startswith("|") and (i + 1) not in in_code:
        block.append((i + 1, lines[i]))
        i += 1
    counts = {}
    for ln, l in block:
        n = len(split_row(l)) - 2  # drop the leading/trailing empty cells
        counts.setdefault(n, []).append(ln)
    header_n = len(split_row(block[0][1])) - 2
    if len(counts) > 1:
        bad += 1
        print(f"  !! table #{tbl_no} (line {block[0][0]}) has INCONSISTENT column counts {dict((k, len(v)) for k, v in counts.items())}")
        for n, lns in counts.items():
            if n != header_n:
                print(f"       {n} cols at lines {lns[:6]}")
print(f"  {tbl_no} tables checked, {bad} with inconsistent columns")

print("\n=== 3. raw '<' that GitHub could swallow as an HTML tag ===")
hits = 0
for i, l in enumerate(lines, 1):
    if i in in_code:
        continue
    for m in re.finditer(r"<(?=[A-Za-z/!])", l):
        frag = l[m.start():m.start() + 40]
        if re.match(r"</?(br|sub|sup|b|i|em|strong|p|div|a|img|code|pre|kbd|table|tr|td|th|ul|li|ol|details|summary|h[1-6])\b", frag, re.I):
            continue
        hits += 1
        print(f"  L{i}: {frag}")
print(f"  {hits} suspicious '<' occurrences")

print("\n=== 4. characters that often break rendering ===")
for name, ch in [("no-break space U+00A0", "\u00a0"), ("zero-width space U+200B", "\u200b"),
                 ("guillemets", "\u00ab"), ("non-ASCII dash U+2013", "\u2013")]:
    print(f"  {name:28s} {text.count(ch)}")

print("\n=== 5. summary.json contents ===")
sj = json.load(open(r"C:\dd\Sensorik+Aktorik\pre-study\wokwi\evidence\summary.json", encoding="utf-8"))
for e in sj:
    print("  ", {k: e.get(k) for k in ("name", "bits", "pot", "running", "lines", "last")})
