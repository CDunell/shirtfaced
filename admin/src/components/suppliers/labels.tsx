import type {
  BlankCategory,
  OfferStatus,
  PrintRegion,
  SupplierKind,
  Verification,
} from "@/db/schema";

export const KIND_LABEL: Record<SupplierKind, string> = {
  pod: "Print on demand",
  print_shop: "Print shop",
  wholesaler: "Blank wholesaler",
  transfers: "Transfers only",
};

export const REGION_LABEL: Record<PrintRegion, string> = {
  au: "Prints in AU",
  nz: "Prints in NZ",
  overseas: "Prints overseas",
  unknown: "Print location unknown",
};

export const STATUS_LABEL: Record<OfferStatus, string> = {
  yes: "Offers it",
  no: "Doesn't offer it",
  brand_only: "Brand listed, style unconfirmed",
  unknown: "Not published",
};

export const CATEGORY_LABEL: Record<BlankCategory, string> = {
  tee: "Tee",
  tank: "Tank",
  crop: "Crop",
  v_neck: "V-neck",
  long_sleeve: "Long sleeve",
  hoodie: "Hoodie",
  other: "Other",
};

/* How far a figure can be trusted, strongest first. */
export const VERIFICATION_LABEL: Record<Verification, string> = {
  api: "Confirmed via API",
  page: "Confirmed on their page",
  summary: "From a page summary",
  not_published: "Not published",
};

const VERIFICATION_STYLE: Record<Verification, string> = {
  api: "bg-lime text-ink",
  page: "bg-ink text-paper",
  summary: "border border-ink/20 text-ink/70",
  not_published: "border border-dashed border-ink/20 text-ink/40",
};

export function VerificationBadge({ value }: { value: Verification }) {
  return (
    <span
      title={VERIFICATION_LABEL[value]}
      className={`inline-flex whitespace-nowrap rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${VERIFICATION_STYLE[value]}`}
    >
      {value === "not_published" ? "n/p" : value}
    </span>
  );
}

const STATUS_STYLE: Record<OfferStatus, string> = {
  yes: "bg-lime text-ink",
  no: "bg-coral/20 text-ink/70",
  brand_only: "bg-cream text-ink",
  unknown: "border border-dashed border-ink/20 text-ink/40",
};

export function StatusChip({ value }: { value: OfferStatus }) {
  const short: Record<OfferStatus, string> = {
    yes: "Yes",
    no: "No",
    brand_only: "Brand only",
    unknown: "n/p",
  };
  return (
    <span
      title={STATUS_LABEL[value]}
      className={`inline-flex whitespace-nowrap rounded-full px-2 py-0.5 text-[11px] font-bold uppercase tracking-wide ${STATUS_STYLE[value]}`}
    >
      {short[value]}
    </span>
  );
}

const REGION_STYLE: Record<PrintRegion, string> = {
  au: "bg-ink text-paper",
  nz: "bg-cream text-ink",
  overseas: "bg-paper-2 text-ink/70",
  unknown: "border border-dashed border-ink/20 text-ink/40",
};

export function RegionChip({ value }: { value: PrintRegion }) {
  const short: Record<PrintRegion, string> = {
    au: "AU",
    nz: "NZ",
    overseas: "Overseas",
    unknown: "?",
  };
  return (
    <span
      title={REGION_LABEL[value]}
      className={`inline-flex whitespace-nowrap rounded-full px-2 py-0.5 text-[11px] font-bold uppercase tracking-wide ${REGION_STYLE[value]}`}
    >
      {short[value]}
    </span>
  );
}

export function formatPrintArea(widthMm: number | null, heightMm: number | null): string | null {
  if (!widthMm || !heightMm) return null;
  return `${(widthMm / 10).toFixed(0)} × ${(heightMm / 10).toFixed(0)} cm`;
}

/* A4 is 210 × 297 mm; a print area covers it in either orientation. */
export function coversA4(widthMm: number | null, heightMm: number | null): boolean {
  if (!widthMm || !heightMm) return false;
  const [short, long] = widthMm < heightMm ? [widthMm, heightMm] : [heightMm, widthMm];
  return short >= 210 && long >= 297;
}

export function formatAud(cents: number | null): string | null {
  if (cents == null) return null;
  return `A$${(cents / 100).toFixed(2)}`;
}
