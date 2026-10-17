# Sensors and Actuators (Sensorik und Aktorik), HSBI

Personal course portfolio, 2026.

**Module 0 pre-study entry: [`pre-study/README.md`](pre-study/README.md)**

That is the assessed document. It covers the signal chain, the Wokwi mini-exercise, the VL53L0X
and MPR121 datasheet analysis, measurement and uncertainty, the actuators primer, my project
idea, and answers to the eight Guiding Questions from the Pre-Study Guide.

## What is in here

| Path | What it is |
|---|---|
| [`pre-study/README.md`](pre-study/README.md) | the pre-study portfolio itself, start here |
| [`pre-study/wokwi/`](pre-study/wokwi/) | the Wokwi project: `sketch.ino`, `diagram.json`, and five captured runs with their raw Serial Monitor logs |
| [`pre-study/figures/`](pre-study/figures/) | the quantisation figure used in the portfolio |
| `tools/` | the small scripts that generated the derived figures and captured the simulation evidence |

## Reproducing the Wokwi run

The exercise runs on [Wokwi](https://wokwi.com/). Open a new ESP32 project, paste the contents of
[`pre-study/wokwi/sketch.ino`](pre-study/wokwi/sketch.ino) and
[`pre-study/wokwi/diagram.json`](pre-study/wokwi/diagram.json), then press *Start the
simulation*. Change `ADC_BITS` between 8, 10 and 12 to reproduce the step-count comparison.

## Notes

The course materials are in English, so this portfolio is written in English. Per the course
policy I am allowed to use German, English or a mixture; I have kept it in English and in my own
words throughout.

No special hardware was needed for the pre-study: everything was done on a laptop with a browser.
