import os

r = r"C:\dd\Sensorik+Aktorik\pre-study\wokwi"
src = os.path.join(r, "diagram.json")
dst = os.path.join(r, "diagram.json.tpl")
d = open(src, encoding="utf-8").read()
tpl = d.replace('"value": "960"', '"value": "__POT__"')
assert "__POT__" in tpl, "placeholder substitution failed"
open(dst, "w", encoding="utf-8", newline="").write(tpl)
print("restored", dst)
for line in tpl.splitlines():
    if "value" in line:
        print("  ", line.strip())
