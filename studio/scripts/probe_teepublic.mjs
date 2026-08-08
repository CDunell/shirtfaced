/**
 * What image sizes a marketplace product page actually offers.
 *
 * The search grid serves one derived size and every other value 404s, so the
 * question is whether the detail page requests a larger one. Answering it by
 * fetching is not possible -- the site returns 403 to a scripted request -- so
 * this drives the same headless Chrome the majors collector uses.
 *
 *   node scripts/probe_teepublic.mjs <product-url>
 */
import { spawn } from "node:child_process";

const CHROME = process.env.CHROME_PATH || "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT = 9495;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const chrome = spawn(
  CHROME,
  [
    "--headless=new",
    `--remote-debugging-port=${PORT}`,
    "--disable-gpu",
    "--hide-scrollbars",
    "--no-first-run",
    "--incognito",
    "about:blank",
  ],
  { stdio: "ignore" },
);

for (let i = 0; i < 60; i++) {
  try {
    await (await fetch(`http://127.0.0.1:${PORT}/json/version`)).json();
    break;
  } catch {
    await sleep(250);
  }
}

const tab = await (await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`, { method: "PUT" })).json();
const ws = new WebSocket(tab.webSocketDebuggerUrl);
let id = 0;
const pending = new Map();
const waiters = [];
ws.addEventListener("message", (event) => {
  const message = JSON.parse(event.data);
  if (message.id && pending.has(message.id)) {
    pending.get(message.id)(message);
    pending.delete(message.id);
  } else if (message.method) {
    for (let i = waiters.length - 1; i >= 0; i--) {
      if (waiters[i].method === message.method) {
        waiters[i].resolve(message.params);
        waiters.splice(i, 1);
      }
    }
  }
});
await new Promise((r) => ws.addEventListener("open", r));

const send = (method, params = {}) =>
  new Promise((resolve) => {
    const n = ++id;
    pending.set(n, resolve);
    ws.send(JSON.stringify({ id: n, method, params }));
  });
const once = (method, ms = 25000) =>
  Promise.race([new Promise((resolve) => waiters.push({ method, resolve })), sleep(ms)]);

await send("Page.enable");
await send("Network.enable");
await send("Emulation.setDeviceMetricsOverride", {
  width: 1400,
  height: 1000,
  deviceScaleFactor: 1,
  mobile: false,
});

// Every image the page actually requests, which is more reliable than reading
// the markup: the largest asset is often fetched by script after load.
const requested = new Set();
ws.addEventListener("message", (event) => {
  const message = JSON.parse(event.data);
  if (message.method === "Network.requestWillBeSent") {
    const url = message.params?.request?.url || "";
    if (url.includes("images.teepublic.com")) requested.add(url);
  }
});

await send("Page.navigate", { url: process.argv[2] });
await once("Page.loadEventFired");
await sleep(7000);

const response = await send("Runtime.evaluate", {
  returnByValue: true,
  expression:
    "(function(){var out=[];var imgs=document.querySelectorAll('img');" +
    "for(var i=0;i<imgs.length;i++){var s=imgs[i].currentSrc||imgs[i].src||'';" +
    "if(s.indexOf('images.teepublic')>-1){out.push(s)}}" +
    "var srcs=document.querySelectorAll('source[srcset]');" +
    "for(var j=0;j<srcs.length;j++){var parts=srcs[j].srcset.split(',');" +
    "for(var k=0;k<parts.length;k++){var u=parts[k].trim().split(' ')[0];" +
    "if(u.indexOf('images.teepublic')>-1){out.push(u)}}}return out})()",
});

if (response.exceptionDetails) {
  console.log("page expression failed:", response.exceptionDetails.text);
}
const fromDom = response.result?.result?.value || [];
for (const url of fromDom) requested.add(url);

const sizes = {};
for (const url of requested) {
  const match = url.match(/s_(\d+)/);
  const key = match ? match[1] : "none";
  sizes[key] = (sizes[key] || 0) + 1;
}

console.log(`${requested.size} teepublic image urls`);
console.log("sizes:", JSON.stringify(sizes));
const sorted = [...requested].sort(
  (a, b) => Number(b.match(/s_(\d+)/)?.[1] || 0) - Number(a.match(/s_(\d+)/)?.[1] || 0),
);
for (const url of sorted.slice(0, 5)) console.log("  " + url);

chrome.kill();
