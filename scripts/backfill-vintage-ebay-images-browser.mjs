#!/usr/bin/env node
/**
 * Browser-based image backfill for vintage eBay evidence.
 *
 * Uses Chromium via Playwright rather than direct item-page HTTP fetches.
 * For each sold listing it first renders the eBay page and collects gallery
 * image resources from the live DOM/network. If eBay blocks the rendered page,
 * it falls back to search-index image results keyed by listing id + title.
 *
 * Provenance records whether an image came from the rendered eBay listing or
 * an indexed search thumbnail. Existing cached images are preserved.
 */
import { mkdir, readdir, readFile, stat, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import path from 'node:path';
import { chromium } from 'playwright';

const ROOT = process.env.VINTAGE_IMAGE_ROOT;
if (!ROOT) throw new Error('VINTAGE_IMAGE_ROOT is required');
const EVIDENCE = 'docs/research/vintage-market-evidence';
const MAX_IMAGES = Number(process.env.VINTAGE_MAX_IMAGES || 12);
const MAX_RECORDS = Number(process.env.VINTAGE_MAX_RECORDS || 0);
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function filesRecursive(dir) {
  const out = [];
  for (const ent of await readdir(dir, { withFileTypes: true })) {
    const p = path.join(dir, ent.name);
    if (ent.isDirectory()) out.push(...(await filesRecursive(p)));
    else if (ent.isFile() && ent.name.endsWith('.jsonl')) out.push(p);
  }
  return out;
}

async function existingImageNames(dir) {
  try {
    return (await readdir(dir)).filter((name) => /\.(jpe?g|png|webp)$/i.test(name));
  } catch {
    return [];
  }
}

function normaliseEbayImage(url) {
  if (!url) return null;
  try {
    const u = new URL(url);
    if (!/\.ebayimg\.com$/i.test(u.hostname)) return null;
    u.pathname = u.pathname.replace(/s-l\d+\.(jpg|jpeg|png|webp)$/i, 's-l1600.$1');
    return u.toString();
  } catch {
    return null;
  }
}

function uniqueUrls(values) {
  return [...new Set(values.filter(Boolean))];
}

async function collectRenderedEbay(page, record) {
  const network = new Set();
  const onResponse = (response) => {
    const url = normaliseEbayImage(response.url());
    if (url) network.add(url);
  };
  page.on('response', onResponse);
  try {
    await page.goto(record.source_url || `https://www.ebay.com/itm/${record.listing_id}`, {
      waitUntil: 'domcontentloaded',
      timeout: 30000,
    });
    await sleep(1800);
    const body = (await page.locator('body').innerText({ timeout: 5000 }).catch(() => '')) || '';
    if (/pardon our interruption|security measure|access denied|robot|captcha/i.test(body)) return [];

    const dom = await page.locator('img').evaluateAll((imgs) =>
      imgs.flatMap((img) => [img.currentSrc, img.src, img.getAttribute('data-zoom-src'), img.getAttribute('data-src')])
    );
    const html = await page.content();
    const embedded = [...html.matchAll(/https:\/\/i\.ebayimg\.com\/images\/g\/[A-Za-z0-9_-]+\/s-l\d+\.(?:jpg|jpeg|png|webp)/gi)].map((m) => m[0]);
    return uniqueUrls([...network, ...dom.map(normaliseEbayImage), ...embedded.map(normaliseEbayImage)]).slice(0, MAX_IMAGES);
  } finally {
    page.off('response', onResponse);
  }
}

async function collectIndexedImages(page, record) {
  const query = encodeURIComponent(`\"${record.listing_id}\" ebay ${record.brand || ''} ${record.title || ''}`.slice(0, 450));
  await page.goto(`https://www.google.com/search?tbm=isch&safe=active&q=${query}`, {
    waitUntil: 'domcontentloaded',
    timeout: 30000,
  }).catch(() => null);
  await sleep(1300);
  const urls = await page.locator('img').evaluateAll((imgs) =>
    imgs.map((img) => img.currentSrc || img.src).filter((url) => /^https?:\/\//i.test(url || ''))
  ).catch(() => []);
  return uniqueUrls(urls.filter((url) => !/googlelogo|gstatic\.com\/images\/branding|favicon/i.test(url))).slice(0, MAX_IMAGES);
}

async function saveImage(context, dir, url, index, sourceKind) {
  try {
    const response = await context.request.get(url, {
      timeout: 25000,
      headers: { referer: sourceKind === 'ebay-rendered' ? 'https://www.ebay.com/' : 'https://www.google.com/' },
    });
    if (!response.ok()) return null;
    const buf = await response.body();
    if (buf.length < 3500) return null;
    const contentType = response.headers()['content-type'] || 'image/jpeg';
    if (!contentType.startsWith('image/')) return null;
    const ext = contentType.includes('png') ? 'png' : contentType.includes('webp') ? 'webp' : 'jpg';
    const name = `image-${String(index).padStart(2, '0')}.${ext}`;
    await writeFile(path.join(dir, name), buf);
    return {
      file: name,
      source_url: url,
      source_kind: sourceKind,
      sha256: createHash('sha256').update(buf).digest('hex'),
      byte_size: buf.length,
      content_type: contentType,
      acquired_at: new Date().toISOString(),
    };
  } catch {
    return null;
  }
}

const files = await filesRecursive(EVIDENCE);
const records = new Map();
for (const file of files) {
  const text = await readFile(file, 'utf8');
  for (const line of text.split(/\n+/)) {
    if (!line.trim()) continue;
    try {
      const record = JSON.parse(line);
      if (record.listing_id && record.sold === true && !records.has(String(record.listing_id))) {
        records.set(String(record.listing_id), record);
      }
    } catch {}
  }
}

const browser = await chromium.launch({ headless: true, args: ['--disable-blink-features=AutomationControlled', '--no-sandbox'] });
const context = await browser.newContext({
  viewport: { width: 1440, height: 1200 },
  locale: 'en-AU',
  userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36',
});

let attempted = 0;
for (const [id, record] of records) {
  if (MAX_RECORDS && attempted >= MAX_RECORDS) break;
  const dir = path.join(ROOT, id);
  await mkdir(dir, { recursive: true });
  const existing = await existingImageNames(dir);
  if (existing.length) continue;
  attempted += 1;

  const page = await context.newPage();
  let urls = await collectRenderedEbay(page, record).catch(() => []);
  let sourceKind = 'ebay-rendered';
  if (!urls.length) {
    urls = await collectIndexedImages(page, record).catch(() => []);
    sourceKind = 'search-index-image';
  }

  const provenance = [];
  let index = 0;
  for (const url of urls) {
    if (index >= MAX_IMAGES) break;
    const saved = await saveImage(context, dir, url, index + 1, sourceKind);
    if (saved) {
      provenance.push(saved);
      index += 1;
    }
  }
  await writeFile(path.join(dir, 'record.json'), JSON.stringify({ ...record, stored_image_count: index }, null, 2));
  await writeFile(path.join(dir, 'provenance.json'), JSON.stringify(provenance, null, 2));
  await page.close();
  await sleep(180);
}
await browser.close();

let listingsWithImages = 0;
let imageCount = 0;
for (const id of records.keys()) {
  const names = await existingImageNames(path.join(ROOT, id));
  if (names.length) {
    listingsWithImages += 1;
    imageCount += names.length;
  }
}
const manifest = {
  generated_at: new Date().toISOString(),
  listing_count: records.size,
  listings_with_images: listingsWithImages,
  image_count: imageCount,
  failed: records.size - listingsWithImages,
  browser_backfill_attempted: attempted,
};
await writeFile(path.join(ROOT, 'manifest.json'), JSON.stringify(manifest, null, 2));
console.log(JSON.stringify(manifest, null, 2));
