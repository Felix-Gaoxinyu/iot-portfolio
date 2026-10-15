"""Compute ADC resolution / step-size figures for the Module 0 portfolio.

Produces:
  - a markdown table (stdout)
  - figures/adc_staircase.png, a two-panel comparison

The figure deliberately gives each panel its OWN y-axis. Plotting a 0..255 code
range and a 0..4095 code range against a shared normalised axis makes both
curves look flat over a narrow voltage window, which hides the whole point.
"""
import os

from PIL import Image, ImageDraw

VREF = 3.3          # nominal ESP32 ADC full scale (ideal / simulator assumption)
VREF_DOC = 3.1      # upper end of the DOCUMENTED measurable range with ADC_11db
POT_DEG = 300.0     # mechanical rotation of a standard 10k panel pot
WINDOW_V = 0.060    # 60 mV of pot travel shown in the figure

BITS = [8, 10, 12]

rows = []
for b in BITS:
    levels = 2 ** b
    step_v = VREF / levels
    rows.append(
        {
            "bits": b,
            "codes": f"0 .. {levels - 1}",
            "levels": levels,
            "step_v": step_v,
            "step_mv": step_v * 1000,
            "step_mv_doc": VREF_DOC / levels * 1000,
            "step_deg": POT_DEG / levels,
        }
    )

print("| ADC resolution | Code range | Discrete levels (steps) | Step size, ideal 3.3 V span | Step size, documented 3.1 V span | Pot angle per step (300° pot) |")
print("|---|---|---|---|---|---|")
for r in rows:
    print(
        f"| {r['bits']}-bit | {r['codes']} | {r['levels']} | "
        f"{r['step_mv']:.3f} mV | {r['step_mv_doc']:.3f} mV | {r['step_deg']:.3f}° |"
    )

by_bits = {r["bits"]: r for r in rows}
print()
print(f"12-bit / 8-bit level ratio : {by_bits[12]['levels'] / by_bits[8]['levels']:.0f}x")
print(f"12-bit / 10-bit level ratio: {by_bits[12]['levels'] / by_bits[10]['levels']:.1f}x")
print()
print(f"Documented ADC_11db measurable window: 150 .. 3100 mV "
      f"(span {VREF_DOC * 1000 - 150:.0f} mV = {(VREF_DOC * 1000 - 150) / (VREF_DOC * 1000) * 100:.1f}% of the 3.1 V span)")
print(f"Sub-150 mV dead zone as a fraction of a 12-bit scale: {150 / (VREF_DOC * 1000 / 4096):.0f} codes")

# ---------------------------------------------------------------------------
# figure: two panels, one per resolution, each with its own code axis
# ---------------------------------------------------------------------------
PANELS = [8, 12]
COLORS = {8: (198, 40, 40), 12: (20, 90, 200)}

W, H = 1160, 620
MARGIN_L, MARGIN_R, MARGIN_T, MARGIN_B = 92, 34, 130, 118
GAP = 74
PANEL_W = (W - MARGIN_L - MARGIN_R - GAP) / 2
PLOT_H = H - MARGIN_T - MARGIN_B

img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)

# per-panel stats, computed so the captions cannot drift from the drawing
stats = {}
for b in PANELS:
    step = by_bits[b]["step_v"]
    n_codes = int(WINDOW_V / step) + 1     # codes 0 .. floor(window/step)
    stats[b] = {"step": step, "n_codes": n_codes, "max_code": n_codes - 1}


def panel_box(i):
    x0 = MARGIN_L + i * (PANEL_W + GAP)
    return x0, MARGIN_T, x0 + PANEL_W, MARGIN_T + PLOT_H


def nice_ticks(max_code):
    """Return a readable tick step for a 0..max_code axis."""
    for t in (1, 2, 5, 10, 20, 25, 50, 100):
        if max_code / t <= 8:
            return t
    return 100


d.text((26, 18), "Same 60 mV of potentiometer travel, two ADC resolutions", fill=(17, 17, 17))
d.text((26, 40), "Each panel has its own code axis, so the step size is directly visible.",
       fill=(110, 110, 110))

for i, b in enumerate(PANELS):
    x0, y0, x1, y1 = panel_box(i)
    step = stats[b]["step"]
    max_code = stats[b]["max_code"]
    color = COLORS[b]

    def X(v):
        return x0 + (v / WINDOW_V) * (x1 - x0)

    def Y(code):
        return y1 - (code / max_code) * (y1 - y0)

    # plot frame
    d.rectangle([x0, y0, x1, y1], outline=(205, 205, 205))
    d.line([(x0, y0), (x0, y1)], fill="black", width=2)
    d.line([(x0, y1), (x1, y1)], fill="black", width=2)

    # horizontal gridlines at each code level (8-bit) or every tick (12-bit)
    tick = nice_ticks(max_code)
    level = 0
    while level <= max_code:
        yy = Y(level)
        if level in (0, max_code) or level % tick == 0:
            d.line([(x0, yy), (x0 - 7, yy)], fill="black", width=1)
            d.text((x0 - 34, yy - 7), str(level), fill=(60, 60, 60))
            d.line([(x0, yy), (x1, yy)], fill=(238, 238, 238))
        level += 1

    # x ticks in mV
    for k in range(5):
        v = WINDOW_V * k / 4
        xx = X(v)
        d.line([(xx, y1), (xx, y1 + 6)], fill="black", width=1)
        label = f"{v * 1000:.0f}"
        d.text((xx - 12, y1 + 12), label, fill=(60, 60, 60))
    d.text(((x0 + x1) / 2 - 78, y1 + 38), "input voltage at pin (mV)", fill=(60, 60, 60))

    # ideal (infinite resolution) ramp, for reference
    d.line([(X(0), Y(0)), (X(WINDOW_V), Y(WINDOW_V / step))], fill=(185, 185, 185), width=2)

    # the quantised staircase the ADC actually produces
    pts = []
    for code in range(0, max_code + 2):
        v0 = code * step
        v1 = min((code + 1) * step, WINDOW_V)
        if v0 > WINDOW_V:
            break
        pts.append((X(v0), Y(code)))
        pts.append((X(v1), Y(code)))
    d.line(pts, fill=color, width=3)

    # captions (right-aligned inside the panel so long text cannot overflow)
    d.text((x0, y0 - 60), f"{b}-bit ADC", fill=color)
    d.text((x0, y0 - 40), f"code range 0 .. {2 ** b - 1}", fill=(90, 90, 90))
    d.text((x0, y0 - 22), f"step = {step * 1000:.3f} mV", fill=(90, 90, 90))

    line1 = f"{stats[b]['n_codes']} possible values"
    line2 = "in this 60 mV window"
    d.text((x1 - d.textlength(line1), y0 - 60), line1, fill=color)
    d.text((x1 - d.textlength(line2), y0 - 40), line2, fill=(90, 90, 90))

# shared footnote
d.text((26, H - 24),
       "Grey line = the ideal, infinite-resolution transfer. The coloured staircase is what the converter can actually report.",
       fill=(110, 110, 110))

os.makedirs("pre-study/figures", exist_ok=True)
out = os.path.join("pre-study", "figures", "adc_staircase.png")
img.save(out)
print()
print("figure panels:")
for b in PANELS:
    print(f"  {b}-bit: {stats[b]['n_codes']} distinct codes over {WINDOW_V * 1000:.0f} mV "
          f"(codes 0..{stats[b]['max_code']}), step {stats[b]['step'] * 1000:.3f} mV")
print(f"\nwrote {out}")
