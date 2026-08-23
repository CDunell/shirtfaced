#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import sharp from "../node_modules/sharp/lib/index.js";

const ROOT = path.resolve(import.meta.dirname, "..");
const LOCKUPS = path.join(ROOT, "public/creatures/lockups");
const SHOP_ID = process.env.PRINTIFY_SHOP_ID;
const TOKEN = process.env.PRINTIFY_API_TOKEN;
const API = "https://api.printify.com/v1";

if (!SHOP_ID || !TOKEN) {
  throw new Error("PRINTIFY_SHOP_ID and PRINTIFY_API_TOKEN are required");
}

const headers = {
  Authorization: `Bearer ${TOKEN}`,
  "Content-Type": "application/json;charset=utf-8",
};

async function api(method, url, body) {
  const res = await fetch(`${API}${url}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await res.text();
  let json = null;
  try { json = text ? JSON.parse(text) : null; } catch {}
  if (!res.ok) throw new Error(`${method} ${url} failed ${res.status}: ${text}`);
  return json;
}

function slugFromTitle(title) {
  const m = title.match(/^(.+?)\s+(Tee|Hoodie|Crewneck|Bucket Hat)\b/i);
  return m ? m[1].trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") : null;
}

function isLight(hex) {
  if (!hex || !/^#[0-9a-f]{6}$/i.test(hex)) return false;
  const n = parseInt(hex.slice(1), 16);
  const r = (n >> 16) & 255;
  const g = (n >> 8) & 255;
  const b = n & 255;
  return (r * 299 + g * 587 + b * 114) / 1000 > 170;
}

function toneForPrintArea(product, area) {
  const colourOption = product.options?.find((o) => o.type === "color");
  if (!colourOption) return "light";
  const colourById = new Map((colourOption.values ?? []).map((v) => [v.id, v]));
  const variantById = new Map((product.variants ?? []).map((v) => [v.id, v]));
  const lightVotes = [];
  for (const variantId of area.variant_ids ?? []) {
    const variant = variantById.get(variantId);
    if (!variant) continue;
    for (const optionId of variant.options ?? []) {
      const colour = colourById.get(optionId);
      if (!colour) continue;
      lightVotes.push(isLight(colour.colors?.[0]));
      break;
    }
  }
  if (!lightVotes.length) return "light";
  return lightVotes.filter(Boolean).length > lightVotes.length / 2 ? "dark" : "light";
}

async function uploadArtwork(slug, tone) {
  const svgPath = path.join(LOCKUPS, `${slug}-${tone}.svg`);
  const svg = await fs.readFile(svgPath);
  const png = await sharp(svg, { density: 300 }).resize(2400, 1100, { fit: "contain" }).png().toBuffer();
  const fileName = `${slug}-${tone}-5px.png`;
  const uploaded = await api("POST", "/uploads/images.json", {
    file_name: fileName,
    contents: png.toString("base64"),
  });
  if (!uploaded?.id) throw new Error(`Upload returned no id for ${fileName}`);
  console.log(`Uploaded ${fileName}: ${uploaded.id}`);
  return uploaded.id;
}

async function listProducts() {
  const products = [];
  for (let page = 1;; page += 1) {
    const json = await api("GET", `/shops/${SHOP_ID}/products.json?limit=50&page=${page}`);
    products.push(...(json?.data ?? []));
    if (!json?.last_page || page >= json.last_page) break;
  }
  return products;
}

const products = await listProducts();
const cands = products.map((p) => ({ product: p, slug: slugFromTitle(p.title ?? "") })).filter((x) => x.slug);
if (!cands.length) throw new Error("No Curb Stamps Printify products matched expected titles");

const uploadCache = new Map();
async function artworkId(slug, tone) {
  const key = `${slug}:${tone}`;
  if (!uploadCache.has(key)) uploadCache.set(key, uploadArtwork(slug, tone));
  return uploadCache.get(key);
}

let updatedCount = 0;
for (const { product: summary, slug } of cands) {
  const product = await api("GET", `/shops/${SHOP_ID}/products/${summary.id}.json`);
  const lockupLight = path.join(LOCKUPS, `${slug}-light.svg`);
  const lockupDark = path.join(LOCKUPS, `${slug}-dark.svg`);
  try {
    await fs.access(lockupLight);
    await fs.access(lockupDark);
  } catch {
    console.log(`Skipping ${product.title}: no local lockups for ${slug}`);
    continue;
  }

  const printAreas = structuredClone(product.print_areas ?? []);
  let changed = false;
  for (const area of printAreas) {
    const inferredTone = toneForPrintArea(product, area);
    for (const placeholder of area.placeholders ?? []) {
      if (!Array.isArray(placeholder.images) || placeholder.images.length === 0) continue;
      for (const image of placeholder.images) {
        if (!String(image.type ?? "").startsWith("image/")) continue;
        const namedTone = /dark/i.test(image.name ?? "") ? "dark" : null;
        const tone = namedTone ?? inferredTone;
        image.id = await artworkId(slug, tone);
        delete image.src;
        delete image.name;
        delete image.type;
        delete image.height;
        delete image.width;
        changed = true;
      }
    }
  }

  if (!changed) {
    console.log(`Skipping ${product.title}: no raster image layers found`);
    continue;
  }

  await api("PUT", `/shops/${SHOP_ID}/products/${product.id}.json`, { print_areas: printAreas });
  updatedCount += 1;
  console.log(`Updated ${product.title}`);
}

if (!updatedCount) throw new Error("No Printify products were updated");
console.log(`Updated ${updatedCount} Printify products with 5px creature artwork`);
