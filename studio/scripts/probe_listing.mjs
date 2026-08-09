/**
 * What a headless browser is actually served for a listing URL.
 *
 * A real browser renders 51 product tiles on a Threadless search page and the
 * collector finds none, so the question is not the extractor -- it is whether
 * headless gets the same page at all. Prints the landing URL after redirects,
 * the title, and the size distribution of every image, which is enough to tell
 * a bot challenge from a markup change from a viewport problem.
 *
 *   node scripts/probe_listing.mjs <url> [more urls...]
 */
import { spawn } from "node:child_process";

const CHROME = process.env.CHROME_PATH || "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT = 9497;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const chrome = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${PORT}`, "--disable-gpu",
  "--no-first-run", "--hide-scrollbars", "--disable-blink-features=AutomationControlled",
  "--disable-dev-shm-usage", "about:blank"], { stdio: "ignore" });

for (let i = 0; i < 80; i++) {
  try { await (await fetch(`http://127.0.0.1:${PORT}/json/version`)).json(); break }
  catch { await sleep(300) }
}

const tab = await (await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`, { method: "PUT" })).json();
const ws = new WebSocket(tab.webSocketDebuggerUrl);
let id = 0;
const pending = new Map();
ws.addEventListener("message", (event) => {
  const message = JSON.parse(event.data);
  if (message.id && pending.has(message.id)) { pending.get(message.id)(message); pending.delete(message.id) }
});
await new Promise((r) => ws.addEventListener("open", r));
const send = (method, params = {}) => new Promise((resolve) => {
  const n = ++id; pending.set(n, resolve); ws.send(JSON.stringify({ id: n, method, params }));
});

await send("Page.enable");
await send("Emulation.setDeviceMetricsOverride", { width: 1400, height: 1000, deviceScaleFactor: 1, mobile: false });
await send("Network.setUserAgentOverride", {
  userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
});

for (const url of process.argv.slice(2)) {
  await send("Page.navigate", { url });
  await sleep(6000);
  for (let i = 0; i < 4; i++) {
    await send("Runtime.evaluate", { expression: "window.scrollBy(0, window.innerHeight * 1.2)" });
    await sleep(1200);
  }
  const result = await send("Runtime.evaluate", {
    returnByValue: true,
    expression: `(() => {
      const imgs = [...document.querySelectorAll('img')];
      const measured = imgs.map(i => {
        const b = i.getBoundingClientRect();
        return { w: Math.round(b.width), h: Math.round(b.height),
                 alt: (i.alt || '').slice(0, 30),
                 src: (i.currentSrc || i.src || '').slice(0, 80),
                 linked: !!i.closest('a[href]') };
      });
      const big = measured.filter(m => m.w >= 150 && m.h >= 150);
      // The site's own names for its garment pages. Four listing URLs were
      // invented from memory once and every one 404'd, so the probe now reports
      // where the catalogue actually lives instead of leaving it to be guessed.
      const seen = new Set();
      const nav = [];
      for (const a of document.querySelectorAll('a[href]')) {
        const href = a.href || '';
        if (!/collections|\\/shop|t-?shirt|\\btees?\\b|hoodie|catalog|products/i.test(href)) continue;
        if (seen.has(href)) continue;
        seen.add(href);
        nav.push({ text: (a.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 24), href });
      }
      return {
        landed: location.href,
        title: document.title.slice(0, 80),
        bodyText: document.body.innerText.replace(/\\s+/g, ' ').slice(0, 200),
        imgs: imgs.length,
        big: big.length,
        bigSample: big.slice(0, 3),
        nav: nav.slice(0, 10),
      };
    })()`,
  });
  console.log(JSON.stringify(result.result?.result?.value ?? result.result?.value ?? result, null, 2));
  console.log("---");
}

chrome.kill();
