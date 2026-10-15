// Minimal Chrome DevTools Protocol client — no npm dependencies.
// Node 24 provides global fetch + WebSocket.

import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync, mkdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const EDGE = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";

export async function launchEdge(port = 9222) {
  const profile = mkdtempSync(join(tmpdir(), "dsh-edge-"));
  const proc = spawn(
    EDGE,
    [
      "--headless=new",
      "--disable-gpu",
      "--no-first-run",
      "--no-default-browser-check",
      "--disable-extensions",
      "--disable-background-networking",
      "--mute-audio",
      `--remote-debugging-port=${port}`,
      `--user-data-dir=${profile}`,
      "--window-size=1600,1000",
      "about:blank",
    ],
    { stdio: "ignore", detached: false }
  );

  // wait for the debugging endpoint
  const base = `http://127.0.0.1:${port}`;
  for (let i = 0; i < 120; i++) {
    try {
      const r = await fetch(`${base}/json/version`);
      if (r.ok) return { proc, base, profile };
    } catch {}
    await new Promise((r) => setTimeout(r, 250));
  }
  throw new Error("Edge did not open the debugging port");
}

export class Session {
  constructor(ws) {
    this.ws = ws;
    this.id = 0;
    this.pending = new Map();
    this.events = [];
    this.listeners = [];
    ws.addEventListener("message", (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.id !== undefined && this.pending.has(msg.id)) {
        const { resolve, reject } = this.pending.get(msg.id);
        this.pending.delete(msg.id);
        msg.error ? reject(new Error(JSON.stringify(msg.error))) : resolve(msg.result);
      } else if (msg.method) {
        this.events.push(msg);
        for (const l of this.listeners) l(msg);
      }
    });
  }

  on(fn) {
    this.listeners.push(fn);
  }

  send(method, params = {}, timeoutMs = 60000) {
    const id = ++this.id;
    return new Promise((resolve, reject) => {
      const t = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`CDP timeout: ${method}`));
      }, timeoutMs);
      this.pending.set(id, {
        resolve: (v) => {
          clearTimeout(t);
          resolve(v);
        },
        reject: (e) => {
          clearTimeout(t);
          reject(e);
        },
      });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  async eval(expression, awaitPromise = true) {
    const r = await this.send("Runtime.evaluate", {
      expression,
      awaitPromise,
      returnByValue: true,
      userGesture: true,
    });
    if (r.exceptionDetails) {
      throw new Error(
        "JS error: " +
          (r.exceptionDetails.exception?.description || r.exceptionDetails.text)
      );
    }
    return r.result.value;
  }

  async screenshot(path, { fullPage = false } = {}) {
    const r = await this.send("Page.captureScreenshot", {
      format: "png",
      captureBeyondViewport: fullPage,
    });
    mkdirSync(join(path, ".."), { recursive: true });
    writeFileSync(path, Buffer.from(r.data, "base64"));
    return path;
  }

  close() {
    try {
      this.ws.close();
    } catch {}
  }
}

export async function connect(base, { matchUrl } = {}) {
  for (let i = 0; i < 60; i++) {
    const list = await (await fetch(`${base}/json/list`)).json();
    const pages = list.filter((t) => t.type === "page");
    const target = matchUrl ? pages.find((p) => p.url.includes(matchUrl)) : pages[0];
    if (target?.webSocketDebuggerUrl) {
      const ws = new WebSocket(target.webSocketDebuggerUrl);
      await new Promise((res, rej) => {
        ws.addEventListener("open", res, { once: true });
        ws.addEventListener("error", rej, { once: true });
      });
      return new Session(ws);
    }
    await new Promise((r) => setTimeout(r, 250));
  }
  throw new Error("no page target found");
}

export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export function shutdown({ proc, profile }) {
  try {
    proc.kill();
  } catch {}
  setTimeout(() => {
    try {
      rmSync(profile, { recursive: true, force: true });
    } catch {}
  }, 3000);
}
