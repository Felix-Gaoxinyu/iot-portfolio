// Capture the Module 0 Wokwi evidence set headlessly in Edge.
// One fresh browser per scenario (navigating away from a live simulation hangs).
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { launchEdge, connect, sleep, shutdown } from "./cdp.mjs";

const ROOT = "C:\\dd\\Sensorik+Aktorik\\pre-study\\wokwi";
const OUT = `${ROOT}\\evidence`;
mkdirSync(OUT, { recursive: true });

const sketchTpl = readFileSync(`${ROOT}\\sketch.ino.tpl`, "utf8");
const diagramTpl = readFileSync(`${ROOT}\\diagram.json.tpl`, "utf8");

const SCENARIOS = [
  { name: "12bit-pot160", bits: 12, coarse: false, pot: 160 },
  { name: "12bit-pot960", bits: 12, coarse: false, pot: 960 },
  { name: "10bit-pot960", bits: 10, coarse: false, pot: 960 },
  { name: "8bit-pot960", bits: 8, coarse: false, pot: 960 },
  { name: "12bit-coarse-pot960", bits: 12, coarse: true, pot: 960 },
];

const results = [];

for (let i = 0; i < SCENARIOS.length; i++) {
  const sc = SCENARIOS[i];
  const sketch = sketchTpl
    .replace("__ADC_BITS__", String(sc.bits))
    .replace("__COARSE__", sc.coarse ? "true" : "false");
  const diagram = diagramTpl.replace("__POT__", String(sc.pot));

  console.log(`\n=== ${sc.name} (bits=${sc.bits}, coarse=${sc.coarse}, pot=${sc.pot}) ===`);

  const edge = await launchEdge(9500 + i);
  const s = await connect(edge.base);
  try {
    await s.send("Page.enable");
    await s.send("Runtime.enable");
    await s.send("Page.navigate", { url: "https://wokwi.com/projects/new/esp32" });
    await sleep(17000);

    const okSketch = await s.eval(`(() => {
      const m = window.monaco.editor.getModels().find(m => m.uri.toString() === "vfs:sketch.ino");
      if (!m) return "missing";
      m.setValue(${JSON.stringify(sketch)});
      return "ok";
    })()`);

    await s.eval(
      `[...document.querySelectorAll("button")].find(b => b.innerText.trim() === "diagram.json")?.click() ?? null`
    );
    await sleep(1200);
    const okDiagram = await s.eval(`(() => {
      const m = window.monaco.editor.getModels().find(m => m.uri.toString().includes("diagram"));
      if (!m) return "missing";
      m.setValue(${JSON.stringify(diagram)});
      return "ok";
    })()`);
    console.log(`  files: sketch=${okSketch} diagram=${okDiagram}`);

    await s.eval(
      `[...document.querySelectorAll("button")].find(x => (x.getAttribute("aria-label")||"") === "Start the simulation")?.click() ?? null`
    );

    let running = false;
    for (let k = 0; k < 80; k++) {
      await sleep(1500);
      const st = await s.eval(
        `[...document.querySelectorAll("button")].some(x => (x.getAttribute("aria-label")||"") === "Stop the simulation") ? "running" : "starting"`
      );
      if (st === "running") {
        running = true;
        break;
      }
    }
    console.log(`  running: ${running}`);

    await sleep(16000);

    const serial = await s.eval(`(() => {
      const el = [...document.querySelectorAll("div,pre,section,textarea")]
        .filter(e => e.offsetParent !== null)
        .find(e => (e.innerText||"").includes("Module 0 pre-study") && (e.innerText||"").includes("raw="));
      return el ? el.innerText : "";
    })()`);

    await s.screenshot(`${OUT}\\${sc.name}.png`);
    writeFileSync(`${OUT}\\${sc.name}-serial.txt`, serial || "(no serial text captured)", "utf8");

    const rawLines = (serial || "").split("\n").filter((l) => l.includes("raw="));
    const last = (rawLines[rawLines.length - 1] || "").trim();
    console.log(`  lines=${rawLines.length}  last: ${last}`);
    results.push({ ...sc, running, lines: rawLines.length, last });
  } catch (err) {
    console.log(`  FAILED: ${err.message}`);
    results.push({ ...sc, error: err.message });
  } finally {
    s.close();
    shutdown(edge);
    await sleep(2500);
  }
}

writeFileSync(`${OUT}\\summary.json`, JSON.stringify(results, null, 2), "utf8");
console.log("\n=== SUMMARY ===");
for (const r of results) console.log(`${r.name.padEnd(24)} ${r.last ?? "ERROR: " + r.error}`);
