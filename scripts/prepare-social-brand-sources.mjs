import { readFile, writeFile } from "node:fs/promises";

const path = "DEV/smiley.svg";
const source = await readFile(path, "utf8");

// The canonical smiley SVG declares fill="none" on the root and uses stroked
// paths. build-social-assets extracts the root contents into a coloured group;
// without an explicit fill on each path, the group's fill turns the smiley into
// solid blobs. Preserve the canonical root behaviour before extraction.
const prepared = source.replace(/<path(?![^>]*\sfill=)/g, '<path fill="none"');

if (prepared === source) {
  console.log("Canonical smiley already has explicit path fills.");
} else {
  await writeFile(path, prepared, "utf8");
  console.log("Prepared canonical smiley for Social asset generation.");
}
