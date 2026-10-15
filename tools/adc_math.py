"""Compute ADC resolution / step-size figures for the Module 0 portfolio.

Produces:
  - a markdown table (stdout)
  - figures/adc_staircase.png  (8-bit vs 12-bit transfer staircase)
"""
import os

from PIL import Image, ImageDraw

VREF = 3.3          # nominal ESP32 ADC full scale (ideal / simulator assumption)
VREF_DOC = 3.1      # upper end of the DOCUMENTED measurable range with ADC_11db
POT_DEG = 300.0     # mechanical rotation of a standard 10k panel pot

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

# --- figure: staircase, 8-bit vs 12-bit, first 0.4 V of the range -----------
W, H = 1000, 560
MARGIN_L, MARGIN_R, MARGIN_T, MARGIN_B = 90, 40, 70, 70
PLOT_W = W - MARGIN_L - MARGIN_R
PLOT_H = H - MARGIN_T - MARGIN_B
VMAX = 0.06  # volts shown - a narrow window so quantisation is visible

img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)


def x_of(v):
    return MARGIN_L + (v / VMAX) * PLOT_W


def y_of(code, levels):
    # normalised output, so 8-bit and 12-bit share one axis
    return MARGIN_T + PLOT_H - (code / (levels - 1)) * PLOT_H


# axes
d.line([(MARGIN_L, MARGIN_T), (MARGIN_L, MARGIN_T + PLOT_H)], fill="black", width=2)
d.line([(MARGIN_L, MARGIN_T + PLOT_H), (MARGIN_L + PLOT_W, MARGIN_T + PLOT_H)], fill="black", width=2)

# gridlines / ticks
for i in range(6):
    v = VMAX * i / 5
    x = x_of(v)
    d.line([(x, MARGIN_T + PLOT_H), (x, MARGIN_T + PLOT_H + 6)], fill="black", width=1)
    d.text((x - 18, MARGIN_T + PLOT_H + 12), f"{v * 1000:.0f}", fill="black")

d.text((MARGIN_L + PLOT_W / 2 - 110, H - 34), "input voltage at pin (mV)", fill="black")
d.text((MARGIN_L - 70, MARGIN_T - 30), "normalised ADC output", fill="black")
d.text((W / 2 - 230, 20), "Quantisation staircase over a 60 mV window: 8-bit vs 12-bit", fill="black")

colors = {8: (200, 40, 40), 12: (20, 90, 200)}
for b in (8, 12):
    r = by_bits[b]
    levels = r["levels"]
    step = r["step_v"]
    pts = []
    n_steps = int(VMAX / step) + 1
    for k in range(n_steps):
        v0 = k * step
        v1 = min((k + 1) * step, VMAX)
        pts.append((x_of(v0), y_of(k, levels)))
        pts.append((x_of(v1), y_of(k, levels)))
    d.line(pts, fill=colors[b], width=2)

# legend
for i, b in enumerate((8, 12)):
    yy = MARGIN_T + 16 + i * 22
    d.line([(MARGIN_L + PLOT_W - 210, yy), (MARGIN_L + PLOT_W - 170, yy)], fill=colors[b], width=3)
    d.text((MARGIN_L + PLOT_W - 160, yy - 6), f"{b}-bit  ({by_bits[b]['levels']} levels)", fill="black")

os.makedirs("pre-study/figures", exist_ok=True)
img.save(os.path.join("pre-study", "figures", "adc_staircase.png"))
print("\nwrote pre-study/figures/adc_staircase.png")
