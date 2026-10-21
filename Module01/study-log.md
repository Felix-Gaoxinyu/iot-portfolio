# Study Log — Module 1

**Module:** [Module 1 – Foundations: Electronics, Arduino & Measurement](https://github.com/iotempire/iotempire-teaching/blob/main/full-classes/hsbi-sensors-actuators-10d/modules/01-foundations-measurement-and-sensor-chain.md)
**Pod:** **«my name»** and **«pod mate»**
**Session:** Day 1 (first session)

> **How to use this file.** Sections 1–5 are Task A from the module. The last section is Task B,
> filled in after talking to a neighbouring pod. Everything is meant to be filled in during and
> right after the session, while it is still fresh. Empty rows are placeholders, not failures.

---

## 1. References I used

The source, and the one concept I understood best from it.

| Source | One concept I understood best from it |
|---|---|
| | |
| | |
| | |

## 2. Things I googled

| Term | What I found | Source (URL) |
|---|---|---|
| | | |
| | | |
| | | |

## 3. Remarkable things

Surprises, "aha" moments, and counterexamples from my own reading. Short bullets are fine.

-
-
-

## 4. LLM Q&A — and how I verified it

The course rule is to treat every model answer as a **claim to test**, not a fact. For each prompt
I write down the prompt, a 2–3 line summary, **how I checked it against my own hardware or a
source**, and **where the model was wrong, vague or over-confident**.

| # | Prompt | Summary | How I verified it | Where it was wrong / vague |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

## 5. My two best found explanations or diagrams

### 5.1

- **Source:**
- **What it taught me:**

### 5.2

- **Source:**
- **What it taught me:**

---

## Vocabulary

Portfolio evidence item 8: define these **in my own words**, each with one example.

| Term | My definition | Example |
|---|---|---|
| Accuracy | | |
| Precision | | |
| Resolution | | |
| Sensitivity | | |
| Uncertainty | | |

---

## Lab results

### ADC: the precision dance

Measured on a potentiometer swept across its full range.

| Resolution | Raw codes observed (min … max) | Distinct steps | Step size | Theory: `Vref / 2ⁿ` | Difference / note |
|---|---|---|---|---|---|
| 12 bit | | | | | |
| 10 bit | | | | | |
| 8 bit | | | | | |

**Multimeter cross-check:**

| Pot position | Multimeter reading | MCU reading | Offset / gain error |
|---|---|---|---|
| | | | |
| | | | |

**Where the flat / erratic regions were:** *(note the voltage below which and above which the
readings became unreliable — the classic ESP32 board is most linear roughly between 0.15 V and
2.9 V, so I expect trouble near both ends)*

### LDR: the analog light sensor

Divider: 3.3 V → LDR → measurement node → 10 kΩ → GND *(or the swapped orientation)*

`R_LDR = R_fixed · (Vref − Vout) / Vout`

| Condition | Raw code (repeat 1) | Raw code (repeat 2) | Raw code (repeat 3) | Voltage | Approx. R_LDR |
|---|---|---|---|---|---|
| Dark (covered) | | | | | |
| Shade | | | | | |
| Bright (room / torch) | | | | | |

**The one worked example of the resistance calculation, with my assumptions:**

**Repeatability note:**

**Limitations:** LDRs are slow, non-linear and temperature dependent — note where I saw this.

### Filters: average, median, cutoff

Comparing four treatments of the same noisy signal.

| Treatment | Window / parameter | What it fixes | What it costs (lag / latency) |
|---|---|---|---|
| Raw | — | nothing | — |
| Moving average | N = 5 / 10 / 20 | | output settles in about N samples, group delay ≈ (N−1)/2 samples |
| Median | N = | | |
| Cutoff (validity gate + low-pass) | | | |

**The deliberate spike experiment:** *(a single spike — covering the LDR, tapping the pot — how did
the mean and the median each respond?)*

**Optional, if I got to it:** hysteresis / dead-zone behaviour, and one low-pass or high-pass result.

---

## Task B — Agreed learning (pod discussion)

Discussed with pod: **«neighbouring pod's names»**

### The 3–5 most noteworthy points

1.
2.
3.

### The learning we jointly stand behind

> *For example: "resolution is not accuracy."*

### What I changed in this log after talking to the other pod

### Our shared artefact

- **What it is:** *(the best diagram, a measurement table, or a new sketch the two pods made together)*
- **Posted in the course Discord:** *(yes / link)*
- **Why we chose it, in one sentence:**
