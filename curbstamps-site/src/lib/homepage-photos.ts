export type HomepagePhoto = {
  src: string;
  alt: string;
  category: "tee" | "hoodie";
};

/** Real composited lifestyle photos — a creature print placed on a blank-
 * garment photo, measured per-photo (collar position, torso centre) rather
 * than a fixed formula. Mixed tee/hoodie on purpose so hoodie actually shows
 * up in rotation instead of being crowded out by the larger tee set. */
export const HOMEPAGE_PHOTOS: HomepagePhoto[] = [
  { src: "/curbstamps/homepage/navy-twig.png", alt: "Kid wearing a Twig tee", category: "tee" },
  { src: "/curbstamps/homepage/green-grit.png", alt: "Kid wearing a Grit tee", category: "tee" },
  { src: "/curbstamps/homepage/black-zot.png", alt: "Kid wearing a Zot tee", category: "tee" },
  { src: "/curbstamps/homepage/orange-blob.png", alt: "Kid wearing a Blob tee", category: "tee" },
  { src: "/curbstamps/homepage/purple-snu.png", alt: "Kid wearing a Snu tee", category: "tee" },
  { src: "/curbstamps/homepage/white-puff.png", alt: "Kid wearing a Puff tee", category: "tee" },
  { src: "/curbstamps/homepage/orange2-mote.png", alt: "Kid wearing a Mote tee", category: "tee" },
  { src: "/curbstamps/homepage/pink-claw.png", alt: "Kid wearing a Claw tee", category: "tee" },
  { src: "/curbstamps/homepage/white2-nub.png", alt: "Kid wearing a Nub tee", category: "tee" },
  { src: "/curbstamps/homepage/blackhoodie-vol.png", alt: "Kid wearing a Vol hoodie", category: "hoodie" },
  { src: "/curbstamps/homepage/pinkhoodie-rex.png", alt: "Kid wearing a Rex hoodie", category: "hoodie" },
  { src: "/curbstamps/homepage/redhoodie-loam.png", alt: "Kid wearing a Loam hoodie", category: "hoodie" },
  { src: "/curbstamps/homepage/pinkhoodie2-squib.png", alt: "Kid wearing a Squib hoodie", category: "hoodie" },
];

function shuffled<T>(items: T[]): T[] {
  const copy = [...items];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

/** One distinct photo per homepage slot, reshuffled on every request (the
 * homepage is rendered dynamically — see `export const dynamic` in
 * app/page.tsx — specifically so this rotates instead of freezing at
 * whatever the first build happened to pick). */
export function pickHomepagePhotos(count: number): HomepagePhoto[] {
  return shuffled(HOMEPAGE_PHOTOS).slice(0, count);
}
