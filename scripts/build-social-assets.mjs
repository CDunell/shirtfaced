import { readFile, mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";

const OUT = "public/social-assets";
const COLORS = { ink: "#0d0d0d", paper: "#f2f0ed", lime: "#c6ff33" };

const [lockupSrc, wordmarkSrc, smileySrc] = await Promise.all([
  readFile("DEV/logo-lockup.svg", "utf8"),
  readFile("DEV/shirtfaced.svg", "utf8"),
  readFile("DEV/smiley.svg", "utf8"),
]);

function brandFromSvg(source, id) {
  const viewBox = source.match(/viewBox="([^"]+)"/)?.[1];
  if (!viewBox) throw new Error(`Missing viewBox in ${id}`);
  const [minX, minY, width, height] = viewBox.split(/\s+/).map(Number);
  if (![minX, minY, width, height].every(Number.isFinite) || width <= 0 || height <= 0) {
    throw new Error(`Invalid viewBox in ${id}: ${viewBox}`);
  }
  const inner = source
    .replace(/^.*?<svg[^>]*>/s, "")
    .replace(/<\/svg>\s*$/s, "")
    .replace(/\sfill="(?!none)[^"]*"/gi, ' fill="currentColor"')
    .replace(/\sstroke="(?!none)[^"]*"/gi, ' stroke="currentColor"');
  return { id, minX, minY, width, height, inner };
}

const LOCKUP = brandFromSvg(lockupSrc, "brand-lockup");
const WORDMARK = brandFromSvg(wordmarkSrc, "brand-wordmark");
const SMILEY = brandFromSvg(smileySrc, "brand-smiley");

function svg(w, h, body, bg = "none") {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${bg !== "none" ? `<rect width="100%" height="100%" fill="${bg}"/>` : ""}${body}</svg>\n`;
}

function placeBrand(brand, x, y, w, h, c) {
  const scale = Math.min(w / brand.width, h / brand.height);
  const tx = x + (w - brand.width * scale) / 2 - brand.minX * scale;
  const ty = y + (h - brand.height * scale) / 2 - brand.minY * scale;
  return `<g transform="translate(${tx} ${ty}) scale(${scale})" color="${c}" fill="${c}">${brand.inner}</g>`;
}

const lockup = (x, y, w, h, c = COLORS.paper) => placeBrand(LOCKUP, x, y, w, h, c);
const wordmark = (x, y, w, h, c = COLORS.paper) => placeBrand(WORDMARK, x, y, w, h, c);
const smiley = (x, y, w, h, c = COLORS.lime) => placeBrand(SMILEY, x, y, w, h, c);
const line = (x1, y1, x2, y2, c = COLORS.paper, sw = 3, o = 1) =>
  `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${c}" stroke-width="${sw}" opacity="${o}"/>`;
const rect = (x, y, w, h, c, rx = 0, o = 1, stroke = "none", sw = 0) =>
  `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${rx}" fill="${c}" opacity="${o}" stroke="${stroke}" stroke-width="${sw}"/>`;
const assets = new Map();

// V1 — core
assets.set("v1/overlay-feed-4x5.svg", svg(1080, 1350, lockup(58, 55, 300, 82) + smiley(944, 1175, 76, 105)));
assets.set("v1/overlay-feed-square.svg", svg(1080, 1080, lockup(58, 52, 300, 82) + smiley(944, 905, 76, 105)));
assets.set("v1/overlay-reel-9x16.svg", svg(1080, 1920, lockup(58, 72, 300, 82) + smiley(944, 1715, 76, 105)));
assets.set("v1/reel-title-bug.svg", svg(1080, 1920, wordmark(64, 92, 320, 76) + rect(64, 188, 132, 6, COLORS.lime)));
assets.set("v1/reel-lower-third-blank.svg", svg(1080, 1920, rect(58, 1512, 500, 205, COLORS.ink, 18, .88) + rect(58, 1512, 10, 205, COLORS.lime) + wordmark(90, 1540, 210, 55) + line(90, 1624, 520, 1624, COLORS.paper, 2, .4) + line(90, 1662, 365, 1662, COLORS.paper, 2, .25)));
assets.set("v1/reel-endcard-white.svg", svg(1080, 1920, lockup(210, 790, 660, 175, COLORS.paper), COLORS.ink));
assets.set("v1/reel-endcard-lime.svg", svg(1080, 1920, lockup(210, 790, 660, 175, COLORS.lime), COLORS.ink));
assets.set("v1/overlay-drop-panel-4x5.svg", svg(1080, 1350, rect(0, 985, 1080, 365, COLORS.ink, 0, .94) + rect(0, 985, 12, 365, COLORS.lime) + wordmark(60, 1035, 280, 68) + smiley(914, 1022, 105, 140) + rect(60, 1160, 620, 8, COLORS.lime) + line(60, 1224, 505, 1224, COLORS.paper, 3, .4) + line(60, 1270, 395, 1270, COLORS.paper, 3, .25)));
assets.set("v1/notice-update-base-4x5.svg", svg(1080, 1350, lockup(64, 65, 360, 95) + rect(64, 292, 190, 8, COLORS.lime) + line(64, 425, 845, 425, COLORS.paper, 8) + line(64, 515, 690, 515, COLORS.paper, 8) + line(64, 760, 790, 760, COLORS.paper, 3, .38) + line(64, 810, 610, 810, COLORS.paper, 3, .24) + line(64, 860, 700, 860, COLORS.paper, 3, .24) + smiley(860, 1080, 150, 205), COLORS.ink));
assets.set("v1/guide-reel-safe-zone.svg", svg(1080, 1920, `<rect x="60" y="180" width="900" height="1420" fill="none" stroke="${COLORS.lime}" stroke-width="3" stroke-dasharray="18 18"/>` + lockup(82, 208, 270, 75)));

// V2 — campaign/story
assets.set("v2/reel-opener-overlay.svg", svg(1080, 1920, lockup(60, 72, 330, 90) + rect(60, 250, 12, 470, COLORS.lime) + rect(60, 250, 360, 12, COLORS.lime)));
assets.set("v2/reel-scene-stamp-blank.svg", svg(1080, 1920, rect(60, 1530, 440, 180, COLORS.ink, 18, .88) + rect(60, 1530, 10, 180, COLORS.lime) + wordmark(88, 1554, 175, 48) + line(88, 1622, 465, 1622, COLORS.paper, 2, .4) + line(88, 1658, 320, 1658, COLORS.paper, 2, .25)));
assets.set("v2/reel-timestamp-badge-blank.svg", svg(1080, 1920, rect(60, 1450, 310, 98, COLORS.ink, 14, .86) + rect(60, 1450, 8, 98, COLORS.lime) + smiley(84, 1464, 54, 72) + line(156, 1485, 340, 1485, COLORS.paper, 2, .42) + line(156, 1515, 292, 1515, COLORS.paper, 2, .25)));
assets.set("v2/story-drop-teaser-9x16.svg", svg(1080, 1920, lockup(60, 72, 340, 92) + smiley(820, 115, 190, 255) + `<rect x="60" y="380" width="960" height="940" rx="24" fill="none" stroke="${COLORS.paper}" stroke-width="3"/>` + rect(60, 1440, 300, 10, COLORS.lime) + line(60, 1518, 840, 1518, COLORS.paper, 10) + line(60, 1598, 650, 1598, COLORS.paper, 10) + line(60, 1698, 520, 1698, COLORS.paper, 3, .4), COLORS.ink));
assets.set("v2/drop-live-banner-4x5.svg", svg(1080, 1350, rect(0, 1050, 1080, 300, COLORS.ink, 0, .94) + rect(0, 1050, 14, 300, COLORS.lime) + lockup(60, 1090, 300, 80) + smiley(914, 1082, 105, 140) + rect(60, 1215, 700, 10, COLORS.lime) + line(60, 1270, 560, 1270, COLORS.paper, 3, .4)));
assets.set("v2/carousel-end-slide-4x5.svg", svg(1080, 1350, lockup(290, 145, 500, 135, COLORS.lime) + line(120, 450, 960, 450, COLORS.paper, 3, .15) + `<rect x="120" y="530" width="840" height="500" rx="24" fill="none" stroke="${COLORS.paper}" stroke-width="2" opacity=".4"/>` + smiley(470, 1080, 140, 190), COLORS.ink));
assets.set("v2/story-update-base-9x16.svg", svg(1080, 1920, lockup(60, 75, 340, 92) + rect(60, 340, 180, 10, COLORS.lime) + line(60, 478, 900, 478, COLORS.paper, 14) + line(60, 578, 740, 578, COLORS.paper, 14) + line(60, 885, 820, 885, COLORS.paper, 4, .38) + line(60, 943, 750, 943, COLORS.paper, 4, .3) + line(60, 1001, 860, 1001, COLORS.paper, 4, .25) + line(60, 1059, 600, 1059, COLORS.paper, 4, .2) + smiley(825, 1590, 185, 250), COLORS.ink));
assets.set("v2/reel-cut-card-brand.svg", svg(1080, 1920, wordmark(210, 710, 660, 155) + smiley(455, 930, 170, 230), COLORS.ink));
assets.set("v2/product-proof-slide-4x5.svg", svg(1080, 1350, wordmark(58, 52, 280, 68) + `<rect x="55" y="170" width="970" height="700" rx="22" fill="none" stroke="${COLORS.paper}" stroke-width="2" opacity=".45"/>` + rect(55, 930, 12, 310, COLORS.lime) + line(95, 972, 805, 972, COLORS.paper, 5) + line(95, 1037, 715, 1037, COLORS.paper, 5, .42) + line(95, 1102, 615, 1102, COLORS.paper, 5, .3) + line(95, 1167, 525, 1167, COLORS.paper, 5, .22) + smiley(870, 1100, 110, 150), COLORS.ink));
assets.set("v2/reel-cover-badge-4x5.svg", svg(1080, 1350, rect(55, 55, 380, 115, COLORS.ink, 16, .9) + wordmark(80, 78, 255, 60) + smiley(350, 70, 62, 84)));

// V3 — environment variants.
assets.set("v3/light-feed-4x5.svg", svg(1080, 1350, lockup(58, 55, 300, 82, COLORS.ink) + smiley(944, 1175, 76, 105, COLORS.ink)));
assets.set("v3/light-reel-9x16.svg", svg(1080, 1920, lockup(58, 72, 300, 82, COLORS.ink) + smiley(944, 1715, 76, 105, COLORS.ink)));
assets.set("v3/light-title-bug-9x16.svg", svg(1080, 1920, wordmark(64, 92, 320, 76, COLORS.ink) + rect(64, 188, 132, 6, COLORS.lime)));
assets.set("v3/light-cover-badge-4x5.svg", svg(1080, 1350, rect(55, 55, 380, 115, COLORS.paper, 16, .88) + wordmark(80, 78, 255, 60, COLORS.ink) + smiley(350, 70, 62, 84, COLORS.ink)));
assets.set("v3/dark-feed-4x5.svg", svg(1080, 1350, lockup(58, 55, 300, 82, COLORS.paper) + smiley(944, 1175, 76, 105, COLORS.lime)));
assets.set("v3/dark-reel-9x16.svg", svg(1080, 1920, lockup(58, 72, 300, 82, COLORS.paper) + smiley(944, 1715, 76, 105, COLORS.lime)));
assets.set("v3/dark-title-bug-9x16.svg", svg(1080, 1920, wordmark(64, 92, 320, 76, COLORS.paper) + rect(64, 188, 132, 6, COLORS.lime)));
assets.set("v3/adaptive-feed-badge-4x5.svg", svg(1080, 1350, rect(48, 45, 390, 125, COLORS.ink, 16, .78) + lockup(68, 65, 280, 76, COLORS.paper) + smiley(366, 65, 52, 72, COLORS.lime)));
assets.set("v3/adaptive-reel-badge-9x16.svg", svg(1080, 1920, rect(48, 62, 390, 125, COLORS.ink, 16, .78) + lockup(68, 82, 280, 76, COLORS.paper) + smiley(366, 82, 52, 72, COLORS.lime)));
assets.set("v3/adaptive-timestamp-9x16.svg", svg(1080, 1920, rect(60, 1450, 330, 102, COLORS.paper, 14, .86) + rect(60, 1450, 8, 102, COLORS.lime) + smiley(84, 1465, 54, 72, COLORS.ink) + line(156, 1486, 358, 1486, COLORS.ink, 2, .65) + line(156, 1518, 300, 1518, COLORS.ink, 2, .4)));
assets.set("v3/light-corner-mark-4x5.svg", svg(1080, 1350, wordmark(62, 1195, 220, 52, COLORS.ink)));
assets.set("v3/dark-corner-mark-4x5.svg", svg(1080, 1350, wordmark(62, 1195, 220, 52, COLORS.paper)));
assets.set("v3/adaptive-corner-mark-4x5.svg", svg(1080, 1350, rect(48, 1175, 270, 90, COLORS.ink, 12, .74) + wordmark(68, 1194, 220, 52, COLORS.paper)));

const indirectSvg = /data:image\/svg\+xml|<mask\b|<symbol\b|<use\b|<image\b/i;
for (const [relative, content] of assets) {
  if (indirectSvg.test(content)) {
    throw new Error(`Indirect/mobile-unsafe SVG content is not allowed: ${relative}`);
  }
  if (relative.startsWith("v3/") && !content.includes("<path")) {
    throw new Error(`Social overlay contains no literal brand paths: ${relative}`);
  }
  const path = join(OUT, relative);
  await mkdir(dirname(path), { recursive: true });
  await writeFile(path, content, "utf8");
}
const manifest = {
  generatedAt: new Date().toISOString(),
  palette: COLORS,
  sourceAssets: ["DEV/logo-lockup.svg", "DEV/shirtfaced.svg", "DEV/smiley.svg"],
  variants: {
    light: "bright/daylight imagery",
    dark: "night/dark imagery",
    adaptive: "mixed or changing contrast",
  },
  files: [...assets.keys()],
};
await writeFile(join(OUT, "manifest.json"), JSON.stringify(manifest, null, 2) + "\n", "utf8");
console.log(`Generated ${assets.size} literal-path Shirtfaced social assets in ${OUT}`);