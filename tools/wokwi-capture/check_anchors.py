import os
import re

MD = r"C:\dd\Sensorik+Aktorik\pre-study\README.md"
raw = open(MD, "rb").read()
print("CRLF present:", b"\r\n" in raw)
t = raw.decode("utf-8")

heads = re.findall(r"^#{1,6} (.+)$", t, re.M)


def slug(h):
    s = h.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    return re.sub(r"\s+", "-", s.strip())


print("\nappendix / section-3 headings and their computed slugs:")
for h in heads:
    if "Appendix" in h or "VL53L0X" in h:
        print(repr(h), "->", "#" + slug(h))

targets = [
    "appendix-a--wokwi-sketch-listing",
    "appendix-b--sources",
    "32-vl53l0x--time-of-flight-distance",
]
slugs = {slug(h) for h in heads}
print("\nanchor check:")
for a in targets:
    print(("OK   " if a in slugs else "MISS "), "#" + a)
