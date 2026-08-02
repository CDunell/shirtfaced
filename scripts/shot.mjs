/**
 * Full-page mobile screenshots via the Chrome DevTools Protocol.
 *
 * `chrome --headless --screenshot` lays the page out at its own default
 * viewport and then crops to --window-size, which produces convincing but
 * WRONG images (content looks clipped when it isn't). Driving CDP directly
 * lets us set real device metrics and capture beyond the viewport.
 *
 *   node scripts/shot.mjs <baseUrl> <outDir> <path...>
 *   node scripts/shot.mjs https://shirtfaced.wtf ./shots / /shop /cart
 */
import { spawn } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const CHROME =
  process.env.CHROME_PATH ||
  "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT = 9333;

const [baseUrl, outDir, ...paths] = process.argv.slice(2);
if (!baseUrl || !outDir || paths.length === 0) {
  console.error("usage: node scripts/shot.mjs <baseUrl> <outDir> <path...>");
  process.exit(1);
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const chrome = spawn(
  CHROME,
  [
    "--headless=new",
    `--remote-debugging-port=${PORT}`,
    "--disable-gpu",
    "--hide-scrollbars",
    "--no-first-run",
    "--user-data-dir=" + path.join(process.cwd(), ".chrome-shot-profile"),
    "about:blank",
  ],
  { stdio: "ignore" }
);

// Wait for the debugging endpoint to come up.
let version;
for (let i = 0; i < 40; i++) {
  try {
    version = await (await fetch(`http://127.0.0.1:${PORT}/json/version`)).json();
    break;
  } catch {
    await sleep(250);
  }
}
if (!version) {
  chrome.kill();
  throw new Error("Chrome debugging endpoint never came up");
}

await mkdir(outDir, { recursive: true });

/** Minimal CDP client over the built-in WebSocket. */
function connect(url) {
  const ws = new WebSocket(url);
  let id = 0;
  const pending = new Map();
  const waiters = [];

  ws.addEventListener("message", (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) {
      pending.get(msg.id)(msg.result);
      pending.delete(msg.id);
    } else if (msg.method) {
      for (let i = waiters.length - 1; i >= 0; i--) {
        if (waiters[i].method === msg.method) {
          waiters[i].resolve(msg.params);
          waiters.splice(i, 1);
        }
      }
    }
  });

  const ready = new Promise((r) => ws.addEventListener("open", r));

  return {
    ready,
    send: (method, params = {}) =>
      new Promise((resolve) => {
        const n = ++id;
        pending.set(n, resolve);
        ws.send(JSON.stringify({ id: n, method, params }));
      }),
    once: (method, timeout = 15000) =>
      Promise.race([
        new Promise((resolve) => waiters.push({ method, resolve })),
        sleep(timeout),
      ]),
    close: () => ws.close(),
  };
}

const target = await (
  await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`, { method: "PUT" })
).json();

const cdp = connect(target.webSocketDebuggerUrl);
await cdp.ready;
await cdp.send("Page.enable");

for (const p of paths) {
  const url = baseUrl.replace(/\/$/, "") + p;

  // Real device metrics — this is what --window-size fails to do.
  await cdp.send("Emulation.setDeviceMetricsOverride", {
    width: 390,
    height: 844,
    deviceScaleFactor: 2,
    mobile: true,
  });

  await cdp.send("Page.navigate", { url });
  await cdp.once("Page.loadEventFired");
  // Let fonts settle and lazy images below the fold decode.
  await cdp.send("Runtime.evaluate", {
    expression: "window.scrollTo(0, document.body.scrollHeight)",
  });
  await sleep(900);
  await cdp.send("Runtime.evaluate", { expression: "window.scrollTo(0,0)" });
  await sleep(600);

  // Full-page grabs render sticky/fixed chrome at its scrolled position, so
  // set VIEWPORT_ONLY=1 when you need to see the header or bottom nav in place.
  const { data } = await cdp.send("Page.captureScreenshot", {
    format: "png",
    captureBeyondViewport: !process.env.VIEWPORT_ONLY,
  });

  const name = (p === "/" ? "home" : p.replace(/^\//, "").replace(/\//g, "-")) + ".png";
  await writeFile(path.join(outDir, name), Buffer.from(data, "base64"));
  console.log(`${name}  ${(Buffer.from(data, "base64").length / 1024).toFixed(0)}KB`);
}

cdp.close();
chrome.kill();
