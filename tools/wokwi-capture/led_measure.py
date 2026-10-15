from PIL import Image

BOX = (1470, 372, 1538, 455)  # led1 bounding box reported by the DOM
E = r"C:\dd\Sensorik+Aktorik\pre-study\wokwi\evidence"
T = r"C:\dd\Sensorik+Aktorik\.scratch\ledtest"

ROWS = [
    ("LED off (digitalWrite LOW)", T + r"\off.png"),
    ("analogWrite  32 (12.5%)", T + r"\pwm32.png"),
    ("analogWrite 255 (100%)", T + r"\pwm255.png"),
    ("digitalWrite HIGH", T + r"\constHIGH.png"),
    ("pot160 -> duty  39 (15.3%)", E + r"\12bit-pot160.png"),
    ("pot960 -> duty 239 (93.7%)", E + r"\12bit-pot960.png"),
    ("pot960 -> duty 240 (94.1%), 8-bit", E + r"\8bit-pot960.png"),
    ("pot960 -> duty 255 (100%), coarse", E + r"\12bit-coarse-pot960.png"),
]


def mean_r(path):
    im = Image.open(path).convert("RGB").crop(BOX)
    px = list(im.getdata())
    return sum(p[0] for p in px) / len(px)


print("mean red in the led1 box (higher = brighter LED)")
print("-" * 56)
for label, path in ROWS:
    print("%-38s %7.2f" % (label, mean_r(path)))
