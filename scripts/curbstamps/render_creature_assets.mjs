#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import sharp from "sharp";

const root = path.resolve(import.meta.dirname, "../..");
const creatures = path.join(root, "curbstamps-site/public/creatures");
const masters = path.join(creatures, "masters");
const lockups = path.join(creatures, "lockups");

for (const filename of (await fs.readdir(masters))
  .filter((name) => /^[-a-z]+\.svg$/.test(name) && !name.endsWith("-qa-vector.svg"))
  .sort()) {
  const slug = path.basename(filename, ".svg");
  await sharp(path.join(masters, filename), { density: 192 })
    .resize(1200, 500, { fit: "contain" })
    .png()
    .toFile(path.join(creatures, `${slug}-icon.png`));
  await sharp(path.join(lockups, `${slug}-light.svg`), { density: 192 })
    .resize(1200, 550, { fit: "contain" })
    .png()
    .toFile(path.join(creatures, `${slug}-logo.png`));
  await sharp(path.join(lockups, `${slug}-dark.svg`), { density: 192 })
    .resize(1200, 550, { fit: "contain" })
    .png()
    .toFile(path.join(creatures, `${slug}-logo-dark.png`));
}
