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
const CORPUS = process.argv.includes("--flat")
  ? join(HERE, "..", "var", "design_corpus_flat")
  : join(HERE, "..", "var", "design_corpus");
const CHROME = process.env.CHROME_PATH || "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT = 9491;

// 18 is a polite sample of one brand's catalogue. A marketplace is not a brand
// -- it is the control population the brand corpus gets checked against, and a
// control of 18 checks nothing -- so `--limit` raises it there.
const limitArg = process.argv.indexOf("--limit");
const PRODUCTS_PER_BRAND = limitArg > -1 ? Number(process.argv[limitArg + 1]) : 18;
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
const USER_AGENT =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36";

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

/**
 * Print-on-demand marketplaces, where the design *is* the product and is
 * published flat and isolated rather than photographed on a garment. Every
 * measurement taken off a brand photograph is an inference around a collar, a
 * fold and a shadow; here there is no garment in the frame at all.
 *
 * Kept apart from MAJORS and written to a separate corpus, because this is a
 * different design population and its register must not leak into ours. What is
 * wanted from it is placement and combination -- see POSITIONING.md on why those
 * are a different question from what a design depicts.
 *
 * These carry their listing URLs directly. Brand taxonomies move constantly,
 * which is why MAJORS discovers listings from each site's own navigation; a
 * marketplace search URL is a stable interface and does not need finding.
 */
/**
 * What to sample, and why these words.
 *
 * Queries about the kind of garment and the kind of treatment, never about
 * subject matter -- subject is the one thing this corpus must not teach us
 * (POSITIONING.md). Breadth matters more than depth: a run that repeats three
 * queries re-scrapes the same tiles and dedupes every one of them away, which
 * is what "nothing new (18 already held)" meant.
 */
const FLAT_QUERIES = [
  "graphic", "typography", "vintage", "minimal", "retro",
  "lettering", "monogram", "collegiate", "workwear", "band",
];

const MARKETPLACE_PAGES = 3;

/** Every query crossed with every page, in the shape each site wants. */
function listings(build) {
  const out = [];
  for (const query of FLAT_QUERIES) {
    for (let page = 1; page <= MARKETPLACE_PAGES; page++) out.push(build(query, page));
  }
  return out;
}

/**
 * TeePublic is deliberately absent.
 *
 * It collected 17 designs earlier and now answers a headless browser with a
 * Cloudflare interstitial -- "Performing security verification". That is the
 * site declining, and working around it is not on the table. The 17 already
 * held stay; nothing here goes back for more.
 *
 *   teepublic: ["TeePublic", "flat_artwork",
 *     listings((q, p) => `https://www.teepublic.com/t-shirts?query=${q}&page=${p}`)],
 */
const MARKETPLACES = {
  threadless: ["Threadless", "flat_artwork",
    listings((q, p) => `https://www.threadless.com/search?q=${q}&page=${p}`)],
  // Not `flat_artwork`: the render fits every design into a fixed square, so
  // its geometry describes Redbubble's layout rather than the artwork's. The
  // tradition carries that distinction into the mine, where compare_corpora.py
  // uses it to keep normalised sources out of the geometry table -- a comment
  // warning about it was not enough, they were still being averaged in.
  redbubble: ["Redbubble", "flat_artwork_normalised",
    listings((q, p) => `https://www.redbubble.com/shop?query=${q}&iaCode=u-tees&page=${p}`)],
};

/**
 * The full-size asset behind a grid thumbnail.
 *
 * A marketplace search grid serves one derived size and every other value 404s,
 * so 313px is all a listing gives up. The product page requests 630 -- and the
 * URL is the same design, same timestamp, with the size token changed, so the
 * larger asset can be had without visiting the page at all. Verified on every
 * design collected so far: thirteen of thirteen.
 *
 * The watermarked variant carries a `wmk` token; the same URL without it is
 * clean. 630 is the ceiling and 1200 refuses either way.
 */
/**
 * Threadless builds its thumbnail from ops encoded as base64 JSON in `d`:
 *
 *   [["trim"], ["resize",[344,424]], ["canvas_centered",[400,480,"#121212"]],
 *    ["encode",["webp",65]]]
 *
 * Two things there are fatal to measuring layout. It arrives at 313x375, and
 * `canvas_centered` pastes the design onto a dark field of the grid's choosing
 * -- so a miner reading that file measures Threadless's padding, not the
 * design. The parameter is ours to rewrite: asking for trim and resize alone
 * returns the artwork at its own bounds, 1050x1200, no canvas. Confirmed
 * against the CDN.
 *
 * Trim is deliberately NOT requested, and the first pass got this wrong.
 *
 * Trimming crops to the design's own bounding box, so a single-element design
 * then fills its field by construction -- the comparison came back with a flat
 * height of 0.801 against the brand corpus's 0.281 and that difference measured
 * nothing at all, because the two numbers had different denominators. The brand
 * figure is a share of the garment's print area. To answer the same question,
 * the flat figure has to be a share of the artwork's own canvas, which for a
 * print-on-demand upload *is* the print area.
 */
function threadlessFullSize(url) {
  const parsed = new URL(url);
  const encoded = parsed.searchParams.get("d");
  if (!encoded) return url;
  try {
    const ops = JSON.parse(Buffer.from(encoded, "base64").toString("utf8"));
    // Only rewrite a pipeline shaped the way we understand. If Threadless
    // changes it, leave the URL alone rather than request something invalid.
    if (!Array.isArray(ops?.ops)) return url;
  } catch {
    return url;
  }
  const wanted = {
    ops: [["resize", [1200, 1200], {}], ["encode", ["png", 95], {}]],
    force: false,
    only_meta: false,
  };
  parsed.searchParams.set("d", Buffer.from(JSON.stringify(wanted)).toString("base64"));
  return parsed.toString();
}

/**
 * Redbubble's grid tile is a photograph, not artwork.
 *
 * This one nearly got past. The tiles arrive 600x600 on a white field, 146 of
 * them, perfectly uniform -- and every one is a cropped torso shot of a model
 * wearing the tee. Mining those as the flat-artwork control would have checked
 * the brand corpus against a second helping of itself and reported the
 * agreement as proof. Only looking at them caught it.
 *
 * The render is chosen by tokens in the last path segment:
 *
 *   ssrco,classic_tee,mens_02,fafafa:ca443f4786,front,product_square,x600.jpg
 *
 * `flat,...,f-pad,...` returns the artwork alone on near-white at 1000x1000.
 * The sticker render (`st,...-pad,...`) also isolates it but draws a die-cut
 * halo around the design, which would read as a stroke -- so, flat.
 *
 * The pad colour is not ours to choose: f8f8f8 serves, 808080 and bfbfbf both
 * 400. So white artwork lands on near-white and disappears -- 5.5% of the
 * Redbubble sample measures as blank and is refused. That is a property of the
 * CDN rather than something to engineer around, and it is a loss of light
 * designs specifically. Threadless loses none, because its transparent PNGs are
 * read through their alpha channel instead.
 */
function redbubbleFullSize(url) {
  const cut = url.lastIndexOf("/");
  if (cut < 0) return url;
  const segment = url.slice(cut + 1);
  // Only rewrite the product-render token we recognise. Anything else is left
  // alone rather than turned into a guess.
  if (!segment.startsWith("ssrco,")) return url;
  return `${url.slice(0, cut)}/flat,1000x1000,075,f-pad,1000x1000,f8f8f8.jpg`;
}

function fullSize(url) {
  if (url.includes("redbubble.net")) return redbubbleFullSize(url);
  if (url.includes("cdn-images.threadless.com")) return threadlessFullSize(url);
  if (!url.includes("images.teepublic.com")) return url;
  return url.replace(/s_313/, "s_630").replace(/,wmk,/, ",").replace(/\.webp/, ".jpg");
}

/** Category links worth following, in preference order. */
const CATEGORY_PATTERNS = [
  /graphic[- ]?tee/i, /t-?shirt/i, /\btees?\b/i, /hoodie/i, /sweatshirt/i, /sweats\b/i,
  // Some catalogues name the section rather than the garment, so nothing
  // above matches a page that is nonetheless full of tees -- Supreme is one.
  /\/shop\/(tops|shirts|sweatshirts|jackets)/i,
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
  // USER_AGENT was applied to the image fetch and never to the page, so every
  // listing was rendered announcing HeadlessChrome. Threadless and Redbubble
  // answer that with a shell -- the collector reported "no product tiles
  // rendered" while the same URL in a normal browser laid out 49 of them.
  await send("Network.setUserAgentOverride", { userAgent: USER_AGENT });
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
  if (encoded) return Buffer.from(encoded, "base64");

  // In-page fetch fails on image CDNs that serve no CORS header -- the request
  // succeeds but the page is not allowed to read the bytes. Uniqlo's whole
  // catalogue was lost this way. Image CDNs are static hosts and answer a
  // direct request happily; it is the HTML origin that guards itself.
  try {
    const response = await fetch(url, {
      headers: { "User-Agent": USER_AGENT, Referer: new URL(url).origin + "/" },
    });
    if (response.ok) {
      const buffer = Buffer.from(await response.arrayBuffer());
      if (buffer.byteLength >= 4000) return buffer;
    }
  } catch {
    // fall through to the browser
  }

  // Some CDNs answer neither: no CORS header for the page, 403 for the script.
  // Threadless is one -- 149 designs were located and one downloaded. What it
  // does answer is the browser, so let the browser make the request and read
  // the bytes back off the wire rather than out of the page.
  return browserFetch(url);
}

/**
 * Fetch by navigating to the asset and reading the response body over CDP.
 *
 * The bytes never pass through page script, so a missing CORS header is
 * irrelevant, and the request carries the browser's own headers and cookies,
 * so a CDN that 403s a scripted client serves it normally.
 */
async function browserFetch(url) {
  const wanted = new Promise((resolve) => {
    const listener = (event) => {
      const message = JSON.parse(event.data);
      if (message.method === "Network.responseReceived" && message.params?.response?.url === url) {
        socket.removeEventListener("message", listener);
        resolve(message.params.requestId);
      }
    };
    socket.addEventListener("message", listener);
    setTimeout(() => { socket.removeEventListener("message", listener); resolve(null) }, 20000);
  });

  await send("Network.enable");
  await send("Page.navigate", { url });
  const requestId = await wanted;
  if (!requestId) return null;

  // The body is only retrievable once the transfer has finished.
  for (let attempt = 0; attempt < 20; attempt++) {
    const body = await send("Network.getResponseBody", { requestId });
    if (body?.body) {
      const buffer = Buffer.from(body.body, body.base64Encoded ? "base64" : "utf8");
      return buffer.byteLength >= 4000 ? buffer : null;
    }
    await sleep(300);
  }
  return null;
}

const slugify = (text) =>
  text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 60) || "product";

async function collectBrand(slug, [name, tradition, homepage], listingUrls = null) {
  // A marketplace supplies its own listings; a brand's have to be found.
  const listings = listingUrls ?? (await discoverListings(homepage));
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
  let alreadyHeld = 0;
  for (const item of unique.slice(0, PRODUCTS_PER_BRAND)) {
    const handle = slugify(item.name);
    const productDir = join(brandDir, "products", handle);
    if (existsSync(join(productDir, "product.json"))) { alreadyHeld++; continue; }
    mkdirSync(productDir, { recursive: true });

    const saved = [];
    const provenance = [];
    const candidates = [fullSize(item.src)].slice(0, IMAGES_PER_PRODUCT);
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
    ? {
        slug,
        status: "skipped",
        // Nothing new is the ordinary outcome of a re-run, not a failure.
        // Reporting it as one sent me chasing a fetch bug that did not exist.
        reason: alreadyHeld > 0
          ? `nothing new (${alreadyHeld} already held)`
          : "no images could be fetched",
      }
    : { slug, status: "collected", products, images };
}

const flatMode = process.argv.includes("--flat");
const catalogue = flatMode ? MARKETPLACES : MAJORS;
const wanted = process.argv.slice(2).filter((a) => a in catalogue);
const brands = wanted.length ? wanted : Object.keys(catalogue);

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
    const entry = catalogue[slug];
    const result = flatMode
      ? await collectBrand(slug, [entry[0], entry[1], ""], entry[2])
      : await collectBrand(slug, entry);
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
