"""Verify the regenerated figure draws the staircase it claims.

Counts rows that contain a horizontal run of the coloured line. Each plateau of
the staircase produces one band of such rows, so the number of clusters should
equal the number of distinct codes the panel advertises (5 and 75).
"""
import os

from PIL import Image

FIG = r"C:\dd\Sensorik+Aktorik\pre-study\figures\adc_staircase.png"

W, H = 1160, 620
MARGIN_L, MARGIN_R, MARGIN_T, MARGIN_B = 92, 34, 130, 118
GAP = 74
PANEL_W = (W - MARGIN_L - MARGIN_R - GAP) / 2
PLOT_H = H - MARGIN_T - MARGIN_B
Y0, Y1 = MARGIN_T, MARGIN_T + PLOT_H
MIN_RUN = 5

PANELS = [
    ("8-bit", 5, (198, 40, 40), MARGIN_L),
    ("12-bit", 75, (20, 90, 200), MARGIN_L + PANEL_W + GAP),
]


def near(p, c, tol=60):
    return abs(p[0] - c[0]) < tol and abs(p[1] - c[1]) < tol and abs(p[2] - c[2]) < tol


im = Image.open(FIG).convert("RGB")
pix = im.load()
print("image size:", im.size, "expected:", (W, H))
assert im.size == (W, H), "geometry drifted from adc_math.py"

ok = True
for name, expected, colour, x0f in PANELS:
    x0, x1 = int(x0f), int(x0f + PANEL_W)
    plateau_rows = []
    for y in range(Y0 - 4, Y1 + 5):
        run = best = 0
        for x in range(x0 - 2, x1 + 3):
            if near(pix[x, y], colour):
                run += 1
                best = max(best, run)
            else:
                run = 0
        if best >= MIN_RUN:
            plateau_rows.append(y)

    clusters = []
    for y in plateau_rows:
        if clusters and y - clusters[-1][-1] <= 1:
            clusters[-1].append(y)
        else:
            clusters.append([y])

    span = (max(plateau_rows) - min(plateau_rows)) if plateau_rows else 0
    got = len(clusters)
    flag = "OK  " if got == expected else "CHECK"
    if got != expected:
        ok = False
    print(f"{flag} {name:7s} plateaus = {got:3d} (advertised {expected:3d})  "
          f"rows={len(plateau_rows):3d}  vertical span={span:3d}px of {PLOT_H}")

# nothing should be clipped at the canvas edge
edge = []
for x in range(W):
    for y in (0, 1, H - 2, H - 1):
        if pix[x, y] != (255, 255, 255):
            edge.append((x, y))
for y in range(H):
    for x in (0, 1, W - 2, W - 1):
        if pix[x, y] != (255, 255, 255):
            edge.append((x, y))
print(f"\nnon-white pixels touching the canvas border: {len(edge)} (want 0)")
if edge:
    ok = False

print("RESULT:", "figure matches its claims" if ok else "review needed")
