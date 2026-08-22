import type { Category } from "@/lib/products";

/**
 * Stand-in product art. There's no real garment photography for Curb Stamps
 * yet (nothing has shipped), so rather than fake a photo this renders an
 * honest flat illustration: a thick-outline garment silhouette in the chosen
 * colourway with the creature print composited on top. Same "sticker" line
 * weight as the creature marks themselves, so it reads as one system rather
 * than a placeholder. Swap for real photography per docs/curbstamps/
 * CURB_STAMPS_SPEC.md §7 once samples exist — nothing else needs to change,
 * `art`/`colours` stay the same shape.
 */
const SHAPES: Record<Category, { d: string; extra?: string }> = {
  tee: {
    d: "M62 18 L86 8 Q100 22 114 8 L138 18 L178 52 L152 76 L140 64 L140 190 L60 190 L60 64 L48 76 L22 52 Z",
  },
  hoodie: {
    d: "M56 42 L80 16 Q100 2 120 16 L144 42 L184 70 L158 92 L146 78 L146 192 L54 192 L54 78 L42 92 L16 70 Z",
    extra:
      "M72 16 Q100 -14 128 16 Q116 40 100 40 Q84 40 72 16 Z M84 150 Q100 162 116 150 M96 108 L94 128 M104 108 L106 128",
  },
  cap: {
    d: "M42 96 Q42 30 100 30 Q158 30 158 96 Z",
    extra: "M24 96 Q100 122 196 90 Q196 108 100 132 Q28 112 24 96 Z M100 26 L100 34",
  },
};

/** True if a hex garment colour is light enough that the cream-ink artwork
 * would barely show — cream print needs a mid-to-dark body, same as a real
 * screen print needs dark ink on a light shirt and light ink on a dark one. */
function isLightColour(hex: string): boolean {
  const n = parseInt(hex.replace("#", ""), 16);
  const r = (n >> 16) & 255;
  const g = (n >> 8) & 255;
  const b = n & 255;
  // Perceived luminance (ITU-R BT.601).
  return (r * 299 + g * 587 + b * 114) / 1000 > 170;
}

export function GarmentArt({
  category,
  bodyColour,
  art,
  artDark,
  creatureName,
  className,
}: {
  category: Category;
  bodyColour: string;
  art: string;
  artDark: string;
  creatureName: string;
  className?: string;
}) {
  const shape = SHAPES[category];
  const printBox =
    category === "cap"
      ? { left: "32%", top: "44%", width: "36%" }
      : category === "hoodie"
        ? { left: "26%", top: "46%", width: "48%" }
        : { left: "26%", top: "38%", width: "48%" };
  const printSrc = isLightColour(bodyColour) ? artDark : art;

  return (
    <div className={`relative overflow-hidden bg-paper-2 ${className ?? ""}`}>
      <svg viewBox="0 0 200 200" className="absolute inset-0 h-full w-full" aria-hidden="true">
        <path d={shape.d} fill={bodyColour} stroke="#1c1a17" strokeWidth={6} strokeLinejoin="round" />
        {shape.extra && (
          <path d={shape.extra} fill="none" stroke="#1c1a17" strokeWidth={5} strokeLinecap="round" />
        )}
      </svg>
      {/* eslint-disable-next-line @next/next/no-img-element -- static, unoptimized art; next/image adds nothing here */}
      <img
        src={printSrc}
        alt={`${creatureName} print`}
        className="absolute drop-shadow-sm"
        style={{ left: printBox.left, top: printBox.top, width: printBox.width }}
      />
    </div>
  );
}
