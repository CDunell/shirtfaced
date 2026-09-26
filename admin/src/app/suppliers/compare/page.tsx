import Link from "next/link";
import { getSuppliersBySlugs, listBlanks } from "@/db/supplier-queries";
import type { Offering, SupplierWithOfferings } from "@/db/supplier-queries";
import { Card } from "@/components/ui";
import {
  KIND_LABEL,
  NotPublished,
  REGION_LABEL,
  RegionChip,
  STATUS_LABEL,
  StatusChip,
  TrustDot,
  VerificationBadge,
  coversA4,
  formatAud,
  formatPrintArea,
} from "@/components/suppliers/labels";

export const dynamic = "force-dynamic";

/* `k` is what the cell says in plain text, used to spot rows where every
   supplier is the same. */
type Cell = { node: React.ReactNode; k: string; score?: number | null };
type RowSpec = { label: string; cells: Cell[]; better?: "high" | "low" };

function bestIndexes(cells: Cell[], better?: "high" | "low"): Set<number> {
  if (!better) return new Set();
  const scored = cells.map((c, i) => [c.score, i] as const).filter((x): x is readonly [number, number] => x[0] != null);
  if (scored.length < 2) return new Set();
  const target = better === "high" ? Math.max(...scored.map(([s]) => s)) : Math.min(...scored.map(([s]) => s));
  return new Set(scored.filter(([s]) => s === target).map(([, i]) => i));
}

const np: Cell = { node: <NotPublished />, k: "n/p" };
const text = (s: string | null | undefined): Cell => (s ? { node: s, k: s } : np);

function area(w: number | null, h: number | null) {
  return w && h ? w * h : null;
}

export default async function ComparePage({
  searchParams,
}: {
  searchParams: Promise<{ s?: string; blank?: string; diff?: string }>;
}) {
  const { s = "", blank: blankSlug, diff } = await searchParams;
  const diffOnly = diff === "1";
  const slugs = s.split(",").map((x) => x.trim()).filter(Boolean).slice(0, 4);
  const [found, blanks] = await Promise.all([getSuppliersBySlugs(slugs), listBlanks()]);
  const suppliers = slugs
    .map((slug) => found.find((f) => f.slug === slug))
    .filter((x): x is SupplierWithOfferings => Boolean(x));
  const backHref = blankSlug ? `/suppliers?blank=${encodeURIComponent(blankSlug)}` : "/suppliers";

  if (suppliers.length < 2) {
    return (
      <div className="flex flex-col gap-4">
        <h1 className="display text-[40px]">Compare</h1>
        <Card>
          <p className="text-ink/70">
            Tick two to four suppliers on the <Link href={backHref} className="underline">Suppliers</Link> page, then choose Compare.
          </p>
        </Card>
      </div>
    );
  }

  const withDot = (label: string, v: SupplierWithOfferings["verification"]) => (
    <span className="inline-flex items-center gap-1.5"><TrustDot value={v} />{label}</span>
  );

  const groups: Array<{ title: string; rows: RowSpec[] }> = [
    {
      title: "Who they are",
      rows: [
        { label: "Type", cells: suppliers.map((x) => text(KIND_LABEL[x.kind])) },
        { label: "Location", cells: suppliers.map((x) => text(x.location)) },
        { label: "Prints AU orders in", cells: suppliers.map((x) => ({ node: <RegionChip value={x.printsIn} />, k: REGION_LABEL[x.printsIn] })) },
        { label: "Methods", cells: suppliers.map((x) => text(x.methods.join(", "))) },
        { label: "Orders reach them by", cells: suppliers.map((x) => text(x.integration)) },
        { label: "Our account", cells: suppliers.map((x) => text(x.hasAccount ? "Yes" : "No")) },
        { label: "Overall trust", cells: suppliers.map((x) => ({ node: <VerificationBadge value={x.verification} />, k: x.verification })) },
      ],
    },
    {
      title: "Print size and minimums (all blanks)",
      rows: [
        {
          label: "Standard print",
          better: "high",
          cells: suppliers.map((x) => {
            const cm = formatPrintArea(x.standardPrintWidthMm, x.standardPrintHeightMm);
            if (!cm) return text(x.standardPrint);
            const label = `${cm}${coversA4(x.standardPrintWidthMm, x.standardPrintHeightMm) ? " · covers A4" : ""}`;
            return { node: withDot(label, x.verification), k: label, score: area(x.standardPrintWidthMm, x.standardPrintHeightMm) };
          }),
        },
        {
          label: "Largest print",
          better: "high",
          cells: suppliers.map((x) => {
            const cm = formatPrintArea(x.maxPrintWidthMm, x.maxPrintHeightMm);
            if (!cm) return text(x.maxPrint);
            return { node: withDot(cm, x.verification), k: cm, score: area(x.maxPrintWidthMm, x.maxPrintHeightMm) };
          }),
        },
        {
          label: "Minimum order",
          better: "low",
          cells: suppliers.map((x) => {
            const label = x.minOrder ?? (x.minOrderQty != null ? String(x.minOrderQty) : null);
            return label ? { node: label, k: label, score: x.minOrderQty } : np;
          }),
        },
      ],
    },
  ];

  /* The blank chosen on the Suppliers page, otherwise every blank any of
     these suppliers has a record for. */
  const relevantBlanks = blanks.filter((b) =>
    blankSlug ? b.slug === blankSlug : suppliers.some((x) => x.offerings.some((o) => o.blankId === b.id)),
  );

  for (const b of relevantBlanks) {
    const get = (x: SupplierWithOfferings): Offering | undefined => x.offerings.find((o) => o.blankId === b.id);
    const perSupplier = (fn: (o: Offering) => Cell) => suppliers.map((x) => { const o = get(x); return o ? fn(o) : np; });
    groups.push({
      title: `${b.brand} ${b.styleCode} · ${b.name}`,
      rows: [
        { label: "Offers it", cells: perSupplier((o) => ({ node: <StatusChip value={o.status} />, k: STATUS_LABEL[o.status] })) },
        { label: "Printed in", cells: perSupplier((o) => ({ node: <RegionChip value={o.printedIn} />, k: REGION_LABEL[o.printedIn] })) },
        {
          label: "Standard print",
          better: "high",
          cells: perSupplier((o) => {
            const cm = formatPrintArea(o.standardPrintWidthMm, o.standardPrintHeightMm);
            return cm ? { node: withDot(cm, o.verification), k: cm, score: area(o.standardPrintWidthMm, o.standardPrintHeightMm) } : text(o.standardPrint);
          }),
        },
        {
          label: "Largest print",
          better: "high",
          cells: perSupplier((o) => {
            const cm = formatPrintArea(o.maxPrintWidthMm, o.maxPrintHeightMm);
            return cm ? { node: withDot(cm, o.verification), k: cm, score: area(o.maxPrintWidthMm, o.maxPrintHeightMm) } : text(o.maxFront);
          }),
        },
        {
          label: "AUD · 1 tee + standard print",
          better: "low",
          cells: perSupplier((o) => {
            const aud = formatAud(o.standardPriceCents);
            return aud ? { node: withDot(aud, o.verification), k: aud, score: o.standardPriceCents } : np;
          }),
        },
        {
          label: "AUD · 1 tee + largest print",
          better: "low",
          cells: perSupplier((o) => {
            const aud = formatAud(o.priceCents);
            return aud ? { node: withDot(aud, o.verification), k: aud, score: o.priceCents } : np;
          }),
        },
        { label: "Price as stated", cells: perSupplier((o) => text(o.price)) },
        {
          label: "Source",
          cells: perSupplier((o) => ({
            node: (
              <span className="flex flex-col items-start gap-1">
                <VerificationBadge value={o.verification} />
                {o.sourceUrl && <a href={o.sourceUrl} target="_blank" rel="noopener noreferrer" className="text-[12px] underline">Source ↗</a>}
              </span>
            ),
            k: `${o.verification} ${o.sourceUrl ?? ""}`,
          })),
        },
      ],
    });
  }

  const same = (row: RowSpec) => row.cells.every((c) => c.k === row.cells[0].k);
  let hidden = 0;

  const renderRows = (rows: RowSpec[]) =>
    rows
      .filter((row) => {
        if (diffOnly && same(row)) { hidden++; return false; }
        return true;
      })
      .map((row) => {
        const best = bestIndexes(row.cells, row.better);
        return (
          <tr key={row.label} className="align-top hover:bg-paper-2 [&>*]:border-b [&>*]:border-ink/5">
            <th scope="row" className="sticky left-0 w-[190px] bg-paper px-3 py-3 text-left text-[11px] font-bold uppercase tracking-wide text-ink/50">
              {row.label}
            </th>
            {row.cells.map((cell, i) => (
              <td key={i} className={`px-3 py-3 ${best.has(i) ? "bg-lime/30 font-semibold" : ""}`}>
                {cell.node}
              </td>
            ))}
          </tr>
        );
      });

  const bodies = groups.map((g) => {
    const rows = renderRows(g.rows);
    return rows.length ? (
      <tbody key={g.title}>
        <tr>
          <th colSpan={suppliers.length + 1} className="sticky left-0 border-y border-ink/10 bg-paper-2 px-3 py-2 text-left text-[13px] font-bold">
            {g.title}
          </th>
        </tr>
        {rows}
      </tbody>
    ) : null;
  });

  const toggleHref = (on: boolean) =>
    `/suppliers/compare?s=${slugs.map(encodeURIComponent).join(",")}${blankSlug ? `&blank=${encodeURIComponent(blankSlug)}` : ""}${on ? "&diff=1" : ""}`;
  const activeBlank = blankSlug ? blanks.find((b) => b.slug === blankSlug) : null;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <Link href={backHref} className="text-[13px] text-ink/50 hover:text-ink">← Back to suppliers</Link>
        <h1 className="display text-[40px]">Compare</h1>
        <p className="text-[13px] text-ink/60">
          {activeBlank ? <>For the <span className="font-semibold text-ink">{activeBlank.brand} {activeBlank.styleCode} {activeBlank.name}</span>. </> : "Every blank these suppliers have a record for. "}
          Highlighted cells are the best figure in their row; the dot shows where each figure came from.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div role="radiogroup" aria-label="Rows to show" className="inline-flex rounded-[14px] bg-paper-2 p-1">
          {[false, true].map((on) => (
            <Link
              key={String(on)}
              href={toggleHref(on)}
              role="radio"
              aria-checked={diffOnly === on}
              className={`press rounded-[10px] px-4 py-2 text-[13px] font-semibold ${diffOnly === on ? "bg-ink text-paper" : "text-ink/60 hover:text-ink"}`}
            >
              {on ? "Differences only" : "All rows"}
            </Link>
          ))}
        </div>
        {diffOnly && hidden > 0 && (
          <span className="text-[12px] text-ink/50">{hidden} identical row{hidden === 1 ? "" : "s"} hidden</span>
        )}
      </div>

      <div className="max-h-[80vh] overflow-auto rounded-[var(--radius-card)] border border-ink/10 bg-paper">
        <table className="w-full min-w-[720px] border-collapse text-[13px] [font-variant-numeric:tabular-nums]">
          <thead>
            <tr>
              <th className="sticky left-0 top-0 z-20 border-b border-ink/10 bg-paper px-3 py-3" />
              {suppliers.map((x) => (
                <th key={x.id} className="sticky top-0 z-10 border-b border-ink/10 bg-paper px-3 py-3 text-left">
                  <Link href={`/suppliers/${x.slug}`} className="text-[15px] font-bold hover:underline">{x.name}</Link>
                  <div className="text-[12px] font-normal text-ink/50">{KIND_LABEL[x.kind]}</div>
                </th>
              ))}
            </tr>
          </thead>
          {bodies}
        </table>
      </div>
    </div>
  );
}
