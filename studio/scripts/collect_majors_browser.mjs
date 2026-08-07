/**
 * Collecting the global majors, which refuse plain HTTP.
 *
 * Nike, Vans, Carhartt, Levi's, Patagonia, Uniqlo and the rest run custom
 * platforms that answer a scripted fetch with 403 and render their catalogue
 * client-side. They are also the brands that matter most to the question this
 * corpus exists to answer -- how the biggest brands present content -- so
 * leaving them out was not an option.
 *
 * A real browser gets them: Chrome renders the page as a person's would, and
 * the product tiles are read out of the finished DOM rather than guessed at
 * from markup. Slower than the Shopify path by a wide margin, which is why it
 * is reserved for the brands that need it.
 *
 * Writes the same schema as collect_design_corpus.py -- brand.json,
 * product.json, provenance.json, image files -- so the two collectors are
 * interchangeable downstream.
 *
 *   node scripts/collect_majors_browser.mjs
 *   node scripts/collect_majors_browser.mjs vans carhartt
 */

import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdirSync, writeFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const CORPUS = join(HERE, "..", "var", "design_corpus");
const CHROME = process.env.CHROME_PATH || "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT = 9491;

const PRODUCTS_PER_BRAND = 18;
const IMAGES_PER_PRODUCT = 2;
// Long enough for a client-rendered grid to settle, including lazy images.
const RENDER_WAIT_MS = 9000;

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/**
 * slug -> [display name, tradition, homepage]
 *
 * Homepages only. Deep category URLs were guessed the first time and every one
 * of them 404'd -- the browser reached Carhartt perfectly and was handed "Page
 * Not Found". These sites reorganise their taxonomy constantly, so the listing
 * pages are discovered from each site's own navigation at run time instead.
 */
const MAJORS = {
  vans: ["Vans", "major-skate", "https://www.vans.com"],
  carhartt: ["Carhartt", "major-workwear", "https://www.carhartt.com"],
  patagonia: ["Patagonia", "major-outdoor", "https://www.patagonia.com"],
  levis: ["Levi's", "major-heritage", "https://www.levi.com"],
  uniqlo: ["Uniqlo", "major-basics", "https://www.uniqlo.com/us/en"],
  nike: ["Nike", "major-sport", "https://www.nike.com"],
  adidas: ["Adidas", "major-sport", "https://www.adidas.com/us"],
  northface: ["The North Face", "major-outdoor", "https://www.thenorthface.com"],
  supreme: ["Supreme", "major-streetwear", "https://us.supreme.com"],
  hm: ["H&M", "major-highstreet", "https://www2.hm.com/en_us"],
  urbanoutfitters: ["Urban Outfitters", "major-highstreet", "https://www.urbanoutfitters.com"],
  timberland: ["Timberland", "major-outdoor", "https://www.timberland.com"],
};

/** Category links worth following, in preference order. */
const CATEGORY_PATTERNS = [
  /graphic[- ]?tee/i, /t-?shirt/i, /tees?/i, /hoodie/i, /sweatshirt/i, /sweats/i,
];

let nextId = 0;
const pending = new Map();
let socket;

function send(method, params = {}) {
  return new Promise((resolve) => {
    const id = ++nextId;
    pending.set(id, resolve);
    socket.send(JSON.stringify({ id, method, params }));
  });
}

async function openTab() {
  const tab = await (await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`, { method: "PUT" })).json();
  socket = new WebSocket(tab.webSocketDebuggerUrl);
  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) {
      pending.get(message.id)(message.result);
      pending.delete(message.id);
    }
  });
  await new Promise((r) => socket.addEventListener("open", r));
  await send("Page.enable");
  await send("Emulation.setDeviceMetricsOverride", { width: 1500, height: 1400, deviceScaleFactor: 1, mobile: false });
  return tab.id;
}

/**
 * Read product tiles out of the rendered page.
 *
 * Deliberately structural rather than per-brand: find images big enough to be
 * product shots, then take the nearest enclosing link and its text as the
 * product. Every one of these sites uses a different class vocabulary, and
 * per-brand selectors would rot the moment any of them redesigned.
 */
const EXTRACT = `(() => {
  const out = [];
  const seen = new Set();
  for (const img of document.querySelectorAll('img')) {
    const src = img.currentSrc || img.src || '';
    if (!/^https?:/.test(src)) continue;
    if (!/\\.(jpe?g|png|webp)/i.test(src) && !/image|media|asset|product/i.test(src)) continue;
    const box = img.getBoundingClientRect();
    if (box.width < 150 || box.height < 150) continue;
    if (/logo|icon|sprite|badge|flag|payment|placeholder/i.test(src)) continue;
    const link = img.closest('a[href]');
    const href = link ? link.href : '';
    const name = (img.alt || link?.getAttribute('aria-label') || link?.textContent || '')
      .replace(/\\s+/g, ' ').trim().slice(0, 120);
    if (!name || name.length < 3) continue;
    const key = href || src;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({ name, href, src });
  }
  return out;
})()`;

/**
 * Find this site's own tee and hoodie listing pages from its navigation.
 *
 * Reads every link on the homepage, keeps those whose text or href names a
 * garment we care about, and prefers the most specific match. Self-correcting
 * when a brand reshuffles its taxonomy, which they all do.
 */
async function discoverListings(homepage) {
  await send("Page.navigate", { url: homepage });
  await sleep(RENDER_WAIT_MS);
  const result = await send("Runtime.evaluate", {
    returnByValue: true,
    expression: `[...document.querySelectorAll('a[href]')]
      .map(a => ({ href: a.href, text: (a.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 60) }))
      .filter(l => /^https?:/.test(l.href))`,
  });
  const links = result.result?.value ?? [];
  const picked = [];
  for (const pattern of CATEGORY_PATTERNS) {
    for (const link of links) {
      if (picked.length >= 3) break;
      if (!pattern.test(link.text) && !pattern.test(link.href)) continue;
      if (/gift|card|sale|clearance|account|help|size|guide/i.test(link.href)) continue;
      if (picked.some((p) => p === link.href)) continue;
      picked.push(link.href);
    }
  }
  if (picked.length > 0) return picked;

  // Fall back to the site's own search. Several majors build their navigation
  // as a hover-driven mega-menu, so the category links are not in the initial
  // DOM and reading anchors finds nothing -- Vans and Patagonia both failed
  // this way. Search is a plain URL on effectively every storefront.
  const origin = new URL(homepage).origin;
  for (const path of ["/search?q=graphic+t-shirt", "/search?query=t-shirt", "/search?q=t-shirt", "/s?q=t-shirt"]) {
    const candidate = origin + path;
    await send("Page.navigate", { url: candidate });
    await sleep(RENDER_WAIT_MS);
    const check = await send("Runtime.evaluate", {
      returnByValue: true,
      expression: `[...document.querySelectorAll('img')].filter(i => i.getBoundingClientRect().width > 150).length`,
    });
    if ((check.result?.value ?? 0) >= 4) return [candidate];
  }
  return [];
}

async function scrapeListing(url) {
  await send("Page.navigate", { url });
  await sleep(RENDER_WAIT_MS);
  // Scroll to trigger lazy loading, then let the images arrive.
  for (let i = 0; i < 4; i++) {
    await send("Runtime.evaluate", { expression: `window.scrollBy(0, window.innerHeight * 1.2)` });
    await sleep(1400);
  }
  const result = await send("Runtime.evaluate", { returnByValue: true, expression: EXTRACT });
  return result.result?.value ?? [];
}

/** Fetch bytes inside the page context, so cookies and headers match the session. */
async function fetchImage(url) {
  const result = await send("Runtime.evaluate", {
    awaitPromise: true,
    returnByValue: true,
    expression: `(async () => {
      try {
        const response = await fetch(${JSON.stringify(url)});
        if (!response.ok) return null;
        const buffer = await response.arrayBuffer();
        if (buffer.byteLength < 4000) return null;
        let binary = '';
        const bytes = new Uint8Array(buffer);
        for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
        return btoa(binary);
      } catch { return null; }
    })()`,
  });
  const encoded = result.result?.value;
  return encoded ? Buffer.from(encoded, "base64") : null;
}

const slugify = (text) =>
  text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 60) || "product";

async function collectBrand(slug, [name, tradition, homepage]) {
  const listings = await discoverListings(homepage);
  if (listings.length === 0) return { slug, status: "skipped", reason: "no garment categories found in navigation" };
  console.log(`    ${listings.length} listing(s): ${listings[0].slice(0, 70)}`);
  const found = [];
  for (const listing of listings) {
    if (found.length >= PRODUCTS_PER_BRAND) break;
    try {
      found.push(...(await scrapeListing(listing)));
    } catch (error) {
      console.log(`    listing failed: ${error.message}`);
    }
  }

  // One entry per product, by link where the site gives one.
  const unique = [];
  const seen = new Set();
  for (const item of found) {
    const key = item.href || item.name;
    if (seen.has(key)) continue;
    seen.add(key);
    unique.push(item);
  }

  if (unique.length === 0) return { slug, status: "skipped", reason: "no product tiles rendered" };

  const brandDir = join(CORPUS, slug);
  mkdirSync(join(brandDir, "products"), { recursive: true });
  writeFileSync(
    join(brandDir, "brand.json"),
    JSON.stringify(
      { brand_slug: slug, brand_name: name, site_url: homepage,
        design_tradition: tradition, acquired_at: new Date().toISOString().replace(/\.\d+Z$/, "Z"),
        notes: "Collected via headless browser; this store refuses scripted HTTP." },
      null, 2,
    ),
  );

  let products = 0;
  let images = 0;
  for (const item of unique.slice(0, PRODUCTS_PER_BRAND)) {
    const handle = slugify(item.name);
    const productDir = join(brandDir, "products", handle);
    if (existsSync(join(productDir, "product.json"))) continue;
    mkdirSync(productDir, { recursive: true });

    const saved = [];
    const provenance = [];
    const candidates = [item.src].slice(0, IMAGES_PER_PRODUCT);
    for (const [index, url] of candidates.entries()) {
      const bytes = await fetchImage(url);
      if (!bytes) continue;
      const extension = /\.png/i.test(url) ? ".png" : ".jpg";
      const filename = `image-0${index + 1}${extension}`;
      writeFileSync(join(productDir, filename), bytes);
      saved.push(filename);
      provenance.push({
        provenance_id: `${slug}/${handle}/image-0${index + 1}`,
        source_id: `${slug}/${handle}`,
        acquired_at: new Date().toISOString().replace(/\.\d+Z$/, "Z"),
        acquisition_method: "headless_browser",
        content_hash: `sha256:${createHash("sha256").update(bytes).digest("hex")}`,
        byte_size: bytes.length,
        content_type: extension === ".png" ? "image/png" : "image/jpeg",
        source_url: url,
        shot_hint: "",
      });
    }
    if (saved.length === 0) continue;

    writeFileSync(
      join(productDir, "product.json"),
      JSON.stringify(
        { product_id: `${slug}/${handle}`, brand_slug: slug, name: item.name,
          source_url: item.href || listings[0], category: "unknown", price: "",
          description: "", images: saved,
          acquired_at: new Date().toISOString().replace(/\.\d+Z$/, "Z") },
        null, 2,
      ),
    );
    writeFileSync(join(productDir, "provenance.json"), JSON.stringify(provenance, null, 2));
    products++;
    images += saved.length;
  }

  return products === 0
    ? { slug, status: "skipped", reason: "no images could be fetched" }
    : { slug, status: "collected", products, images };
}

const wanted = process.argv.slice(2).filter((a) => a in MAJORS);
const brands = wanted.length ? wanted : Object.keys(MAJORS);

const chrome = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${PORT}`, "--disable-gpu",
  "--no-first-run", "--hide-scrollbars", "--disable-blink-features=AutomationControlled",
  "--disable-dev-shm-usage", "about:blank"], { stdio: "ignore" });
for (let i = 0; i < 80; i++) {
  try { await (await fetch(`http://127.0.0.1:${PORT}/json/version`)).json(); break }
  catch { await sleep(300) }
}

const results = [];
for (const slug of brands) {
  await openTab();
  try {
    const result = await collectBrand(slug, MAJORS[slug]);
    results.push(result);
    console.log(
      result.status === "collected"
        ? `  ${slug.padEnd(18)} ${String(result.products).padStart(3)} products ${String(result.images).padStart(3)} images`
        : `  ${slug.padEnd(18)} skipped — ${result.reason}`,
    );
  } catch (error) {
    console.log(`  ${slug.padEnd(18)} failed — ${error.message}`);
    results.push({ slug, status: "skipped", reason: error.message });
  }
  try { socket.close() } catch {}
}

const ok = results.filter((r) => r.status === "collected");
console.log(`\n${ok.length}/${results.length} brands, ` +
  `${ok.reduce((t, r) => t + r.products, 0)} products, ` +
  `${ok.reduce((t, r) => t + r.images, 0)} images`);
chrome.kill();
