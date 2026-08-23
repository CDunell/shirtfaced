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
  crewneck: {
    d: "M58 20 L84 8 Q100 20 116 8 L142 20 L180 54 L154 78 L142 66 L142 192 L58 192 L58 66 L46 78 L20 54 Z",
    extra: "M50 70 L66 70 M134 70 L150 70 M70 184 L130 184",
  },
  "bucket-hat": {
    d: "M50 100 Q50 30 100 30 Q150 30 150 100 Z",
    extra: "M20 100 Q100 130 180 100 Q180 118 100 148 Q20 118 20 100 Z",
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
  photoSrc,
  className,
}: {
  category: Category;
  bodyColour: string;
  art: string;
  artDark: string;
  creatureName: string;
  /** Real Printify garment mockup for this colourway, when the catalog has
   * one. Takes over rendering entirely — no SVG stand-in underneath. */
  photoSrc?: string;
  className?: string;
}) {
  if (photoSrc) {
    return (
      <div className={`relative overflow-hidden bg-paper-2 ${className ?? ""}`}>
        {/* eslint-disable-next-line @next/next/no-img-element -- external Printify-hosted mockup */}
        <img src={photoSrc} alt={`${creatureName} — product photo`} className="absolute inset-0 h-full w-full object-cover" />
      </div>
    );
  }

  const shape = SHAPES[category];
  const printBox =
    category === "bucket-hat"
      ? { left: "32%", top: "50%", width: "36%" }
      : category === "hoodie"
        ? { left: "26%", top: "46%", width: "48%" }
        : category === "crewneck"
          ? { left: "26%", top: "42%", width: "48%" }
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
