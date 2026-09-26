import Link from "next/link";
import { getSuppliersBySlugs, listBlanks } from "@/db/supplier-queries";
import type { Offering, SupplierWithOfferings } from "@/db/supplier-queries";
import { Card } from "@/components/ui";
import {
  KIND_LABEL,
  RegionChip,
  StatusChip,
  VerificationBadge,
  coversA4,
  formatAud,
  formatPrintArea,
} from "@/components/suppliers/labels";

export const dynamic = "force-dynamic";

type Cell = { node: React.ReactNode; score?: number | null };
type RowSpec = { label: string; cells: Cell[]; better?: "high" | "low" };

function bestIndexes(cells: Cell[], better?: "high" | "low"): Set<number> {
  if (!better) return new Set();
  const scored = cells.map((c, i) => [c.score, i] as const).filter((x): x is readonly [number, number] => x[0] != null);
  if (scored.length < 2) return new Set();
  const target = better === "high" ? Math.max(...scored.map(([s]) => s)) : Math.min(...scored.map(([s]) => s));
  return new Set(scored.filter(([s]) => s === target).map(([, i]) => i));
}

const np = <span className="text-ink/35">n/p</span>;

function area(w: number | null, h: number | null) {
  return w && h ? w * h : null;
}

export default async function ComparePage({
  searchParams,
}: {
  searchParams: Promise<{ s?: string; blank?: string }>;
}) {
  const { s = "", blank: blankSlug } = await searchParams;
  const slugs = s.split(",").map((x) => x.trim()).filter(Boolean).slice(0, 4);
  const [found, blanks] = await Promise.all([getSuppliersBySlugs(slugs), listBlanks()]);
  const suppliers = slugs
    .map((slug) => found.find((f) => f.slug === slug))
    .filter((x): x is SupplierWithOfferings => Boolean(x));

  if (suppliers.length < 2) {
    return (
      <div className="flex flex-col gap-4">
        <h1 className="display text-[40px]">Compare</h1>
        <Card>
          <p className="text-ink/70">
            Tick two to four suppliers on the <Link href="/suppliers" className="underline">Suppliers</Link> page, then choose Compare side by side.
          </p>
        </Card>
      </div>
    );
  }

  const general: RowSpec[] = [
    { label: "Type", cells: suppliers.map((x) => ({ node: KIND_LABEL[x.kind] })) },
    { label: "Location", cells: suppliers.map((x) => ({ node: x.location ?? np })) },
    { label: "Prints AU orders in", cells: suppliers.map((x) => ({ node: <RegionChip value={x.printsIn} /> })) },
    { label: "Methods", cells: suppliers.map((x) => ({ node: x.methods.length ? x.methods.join(", ") : np })) },
    {
      label: "Minimum order",
      better: "low",
      cells: suppliers.map((x) => ({
        node: x.minOrder ?? (x.minOrderQty != null ? String(x.minOrderQty) : np),
        score: x.minOrderQty,
      })),
    },
    {
      label: "Standard print",
      better: "high",
      cells: suppliers.map((x) => {
        const cm = formatPrintArea(x.standardPrintWidthMm, x.standardPrintHeightMm);
        return {
          node: cm ? `${cm}${coversA4(x.standardPrintWidthMm, x.standardPrintHeightMm) ? " · A4+" : ""}` : (x.standardPrint ?? np),
          score: area(x.standardPrintWidthMm, x.standardPrintHeightMm),
        };
      }),
    },
    {
      label: "Largest print",
      better: "high",
      cells: suppliers.map((x) => ({
        node: formatPrintArea(x.maxPrintWidthMm, x.maxPrintHeightMm) ?? x.maxPrint ?? np,
        score: area(x.maxPrintWidthMm, x.maxPrintHeightMm),
      })),
    },
    { label: "Orders reach them by", cells: suppliers.map((x) => ({ node: x.integration ?? np })) },
    { label: "Our account", cells: suppliers.map((x) => ({ node: x.hasAccount ? "Yes" : "No" })) },
    { label: "Trust", cells: suppliers.map((x) => ({ node: <VerificationBadge value={x.verification} /> })) },
  ];

  /* The blank chosen on the Suppliers page, otherwise every blank any of
     these suppliers has a record for. */
  const relevantBlanks = blanks.filter((b) =>
    blankSlug ? b.slug === blankSlug : suppliers.some((x) => x.offerings.some((o) => o.blankId === b.id)),
  );

  const offeringRows = (blankId: string): RowSpec[] => {
    const get = (x: SupplierWithOfferings): Offering | undefined => x.offerings.find((o) => o.blankId === blankId);
    return [
      { label: "Offers it", cells: suppliers.map((x) => { const o = get(x); return { node: o ? <StatusChip value={o.status} /> : np }; }) },
      { label: "Printed in", cells: suppliers.map((x) => { const o = get(x); return { node: o ? <RegionChip value={o.printedIn} /> : np }; }) },
      {
        label: "Standard print",
        better: "high",
        cells: suppliers.map((x) => {
          const o = get(x);
          const cm = o ? formatPrintArea(o.standardPrintWidthMm, o.standardPrintHeightMm) : null;
          return { node: cm ?? o?.standardPrint ?? np, score: o ? area(o.standardPrintWidthMm, o.standardPrintHeightMm) : null };
        }),
      },
      {
        label: "Largest print",
        better: "high",
        cells: suppliers.map((x) => {
          const o = get(x);
          const cm = o ? formatPrintArea(o.maxPrintWidthMm, o.maxPrintHeightMm) : null;
          return { node: cm ?? o?.maxFront ?? np, score: o ? area(o.maxPrintWidthMm, o.maxPrintHeightMm) : null };
        }),
      },
      {
        label: "1 tee + standard print",
        better: "low",
        cells: suppliers.map((x) => { const o = get(x); return { node: formatAud(o?.standardPriceCents ?? null) ?? np, score: o?.standardPriceCents ?? null }; }),
      },
      {
        label: "1 tee + largest print",
        better: "low",
        cells: suppliers.map((x) => { const o = get(x); return { node: formatAud(o?.priceCents ?? null) ?? o?.price ?? np, score: o?.priceCents ?? null }; }),
      },
      {
        label: "Trust",
        cells: suppliers.map((x) => {
          const o = get(x);
          return {
            node: o ? (
              <span className="flex flex-col items-start gap-1">
                <VerificationBadge value={o.verification} />
                {o.sourceUrl && <a href={o.sourceUrl} target="_blank" rel="noopener noreferrer" className="text-[12px] underline">Source ↗</a>}
              </span>
            ) : np,
          };
        }),
      },
    ];
  };

  const renderRows = (rows: RowSpec[]) =>
    rows.map((row) => {
      const best = bestIndexes(row.cells, row.better);
      return (
        <tr key={row.label} className="border-b border-ink/5 align-top last:border-0">
          <th scope="row" className="w-[180px] px-3 py-3 text-left text-[11px] font-bold uppercase tracking-wide text-ink/50">
            {row.label}
          </th>
          {row.cells.map((cell, i) => (
            <td key={i} className={`px-3 py-3 ${best.has(i) ? "bg-lime/25 font-semibold" : ""}`}>
              {cell.node}
            </td>
          ))}
        </tr>
      );
    });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <Link href={blankSlug ? `/suppliers?blank=${encodeURIComponent(blankSlug)}` : "/suppliers"} className="text-[13px] text-ink/50 hover:text-ink">
          ← Back to suppliers
        </Link>
        <h1 className="display text-[40px]">Compare</h1>
        <p className="text-[13px] text-ink/60">Highlighted cells are the best figure in their row among these suppliers.</p>
      </div>

      <div className="overflow-x-auto rounded-[var(--radius-card)] border border-ink/10 bg-white/60">
        <table className="w-full min-w-[720px] border-collapse text-[13px] [font-variant-numeric:tabular-nums]">
          <thead>
            <tr className="border-b border-ink/10">
              <th className="px-3 py-3" />
              {suppliers.map((x) => (
                <th key={x.id} className="px-3 py-3 text-left">
                  <Link href={`/suppliers/${x.slug}`} className="text-[15px] font-bold hover:underline">{x.name}</Link>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>{renderRows(general)}</tbody>
          {relevantBlanks.map((b) => (
            <tbody key={b.id}>
              <tr className="border-y border-ink/10 bg-paper-2">
                <th colSpan={suppliers.length + 1} className="px-3 py-2 text-left text-[13px] font-bold">
                  {b.brand} {b.styleCode} · {b.name}
                </th>
              </tr>
              {renderRows(offeringRows(b.id))}
            </tbody>
          ))}
        </table>
      </div>
    </div>
  );
}
