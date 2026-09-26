"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import type { Blank, Offering, SupplierWithOfferings } from "@/db/supplier-queries";
import { Checkbox, Input, Select } from "@/components/ui";
import {
  KIND_LABEL,
  RegionChip,
  StatusChip,
  VerificationBadge,
  coversA4,
  formatAud,
  formatPrintArea,
} from "./labels";

type SortKey = "name" | "print" | "min" | "price";
/* Compare on the print the base price includes, or the largest they can do. */
type Basis = "standard" | "largest";

const REGIONS = ["QLD", "NSW", "ACT", "VIC", "TAS", "WA", "SA", "NT", "AU", "NZ", "INTL"];
const MAX_COMPARE = 4;

type Row = {
  supplier: SupplierWithOfferings;
  offering: Offering | null;
  widthMm: number | null;
  heightMm: number | null;
  stated: string | null;
  areaMm2: number | null;
  minQty: number | null;
  priceCents: number | null;
};

function confirmed(v: string): boolean {
  return v === "api" || v === "page";
}

/* The print dimensions for a row on the chosen basis: the blank-specific
   figure first, then the supplier-wide one. */
function printFor(supplier: SupplierWithOfferings, offering: Offering | null, basis: Basis) {
  if (basis === "standard") {
    return {
      w: offering?.standardPrintWidthMm ?? supplier.standardPrintWidthMm,
      h: offering?.standardPrintHeightMm ?? supplier.standardPrintHeightMm,
      stated: offering?.standardPrint ?? supplier.standardPrint,
      price: offering?.standardPriceCents ?? null,
    };
  }
  return {
    w: offering?.maxPrintWidthMm ?? supplier.maxPrintWidthMm,
    h: offering?.maxPrintHeightMm ?? supplier.maxPrintHeightMm,
    stated: offering?.maxFront ?? supplier.maxPrint,
    price: offering?.priceCents ?? null,
  };
}

export function SupplierExplorer({
  blanks,
  suppliers,
  activeBlankSlug,
}: {
  blanks: Blank[];
  suppliers: SupplierWithOfferings[];
  activeBlankSlug: string | null;
}) {
  const activeBlank = blanks.find((b) => b.slug === activeBlankSlug) ?? null;
  const blankById = useMemo(() => new Map(blanks.map((b) => [b.id, b])), [blanks]);

  const [query, setQuery] = useState("");
  const [kind, setKind] = useState("");
  const [region, setRegion] = useState("");
  const [basis, setBasis] = useState<Basis>("largest");
  const [auOnly, setAuOnly] = useState(false);
  const [offersOnly, setOffersOnly] = useState(true);
  const [a4Only, setA4Only] = useState(false);
  const [sizedOnly, setSizedOnly] = useState(false);
  const [confirmedOnly, setConfirmedOnly] = useState(false);
  const [accountOnly, setAccountOnly] = useState(false);
  const [sort, setSort] = useState<SortKey>("print");
  const [selected, setSelected] = useState<string[]>([]);

  const rows: Row[] = useMemo(() => {
    const q = query.trim().toLowerCase();
    const out: Row[] = [];
    for (const supplier of suppliers) {
      const offering = activeBlank
        ? (supplier.offerings.find((o) => o.blankId === activeBlank.id) ?? null)
        : null;

      if (activeBlank) {
        if (!offering) continue;
        if (offersOnly && offering.status !== "yes") continue;
      }
      if (q && !`${supplier.name} ${supplier.location ?? ""} ${supplier.notes ?? ""}`.toLowerCase().includes(q)) continue;
      if (kind && supplier.kind !== kind) continue;
      if (region && supplier.region !== region) continue;

      const printedIn = offering && offering.printedIn !== "unknown" ? offering.printedIn : supplier.printsIn;
      if (auOnly && printedIn !== "au") continue;
      if (accountOnly && !supplier.hasAccount) continue;

      const { w, h, stated, price } = printFor(supplier, offering, basis);
      const areaMm2 = w && h ? w * h : null;
      if (sizedOnly && areaMm2 == null) continue;
      if (a4Only && !coversA4(w, h)) continue;

      const verification = offering?.verification ?? supplier.verification;
      if (confirmedOnly && !confirmed(verification)) continue;

      out.push({
        supplier,
        offering,
        widthMm: w,
        heightMm: h,
        stated,
        areaMm2,
        minQty: offering?.minOrderQty ?? supplier.minOrderQty,
        priceCents: price,
      });
    }

    const nullsLast = (a: number | null, b: number | null, dir: 1 | -1) => {
      if (a == null && b == null) return 0;
      if (a == null) return 1;
      if (b == null) return -1;
      return (a - b) * dir;
    };
    const byName = (a: Row, b: Row) => a.supplier.name.localeCompare(b.supplier.name);
    out.sort((a, b) => {
      if (sort === "print") return nullsLast(a.areaMm2, b.areaMm2, -1) || byName(a, b);
      if (sort === "min") return nullsLast(a.minQty, b.minQty, 1) || byName(a, b);
      if (sort === "price") return nullsLast(a.priceCents, b.priceCents, 1) || byName(a, b);
      return byName(a, b);
    });
    return out;
  }, [suppliers, activeBlank, query, kind, region, basis, auOnly, offersOnly, a4Only, sizedOnly, confirmedOnly, accountOnly, sort]);

  const best = useMemo(() => {
    const pick = (values: Array<number | null>, fn: (...n: number[]) => number) => {
      const real = values.filter((v): v is number => v != null);
      return real.length ? fn(...real) : null;
    };
    return {
      area: pick(rows.map((r) => r.areaMm2), Math.max),
      min: pick(rows.map((r) => r.minQty), Math.min),
      price: pick(rows.map((r) => r.priceCents), Math.min),
    };
  }, [rows]);

  const printsInAu = rows.filter((r) => {
    const p = r.offering && r.offering.printedIn !== "unknown" ? r.offering.printedIn : r.supplier.printsIn;
    return p === "au";
  }).length;
  const withConfirmed = rows.filter((r) => confirmed(r.offering?.verification ?? r.supplier.verification)).length;
  const a4Count = rows.filter((r) => coversA4(r.widthMm, r.heightMm)).length;

  function toggle(slug: string) {
    setSelected((prev) =>
      prev.includes(slug) ? prev.filter((s) => s !== slug) : prev.length >= MAX_COMPARE ? prev : [...prev, slug],
    );
  }

  const bestTag = <span className="ml-1.5 rounded-full bg-lime px-1.5 py-0.5 text-[9px] font-bold uppercase">Best</span>;
  const printHeading = basis === "standard" ? "Standard print" : "Largest print";

  return (
    <div className="flex flex-col gap-5">
      {/* Tabs: every supplier, then one per blank */}
      <nav aria-label="Blanks" className="-mx-1 flex gap-2 overflow-x-auto px-1 pb-1">
        <Link
          href="/suppliers"
          aria-current={!activeBlank ? "page" : undefined}
          className={`press shrink-0 rounded-[14px] px-4 py-2.5 text-[13px] font-semibold ${!activeBlank ? "bg-ink text-paper" : "border border-ink/15 hover:bg-paper-2"}`}
        >
          All suppliers
        </Link>
        {blanks.map((b) => (
          <Link
            key={b.id}
            href={`/suppliers?blank=${encodeURIComponent(b.slug)}`}
            aria-current={activeBlank?.id === b.id ? "page" : undefined}
            className={`press shrink-0 rounded-[14px] px-4 py-2.5 text-[13px] ${activeBlank?.id === b.id ? "bg-ink text-paper" : "border border-ink/15 hover:bg-paper-2"}`}
          >
            <span className="font-semibold">{b.brand} {b.styleCode}</span>
            <span className={activeBlank?.id === b.id ? "text-paper/60" : "text-ink/50"}> · {b.name}</span>
          </Link>
        ))}
        <Link
          href="/suppliers/blanks"
          className="press shrink-0 rounded-[14px] border border-dashed border-ink/25 px-4 py-2.5 text-[13px] font-semibold text-ink/60 hover:bg-paper-2"
        >
          + Blank
        </Link>
      </nav>

      {activeBlank && (
        <p className="text-[14px] text-ink/70">
          Everyone who prints the <span className="font-semibold text-ink">{activeBlank.brand} {activeBlank.styleCode} {activeBlank.name}</span>
          {activeBlank.gsm ? ` (${activeBlank.gsm} GSM${activeBlank.fit ? `, ${activeBlank.fit}` : ""})` : ""}.
        </p>
      )}

      {/* Compare-on switch */}
      <div className="flex flex-wrap items-center gap-3">
        <span className="text-[12px] font-semibold uppercase tracking-wide text-ink/60">Compare on</span>
        <div role="radiogroup" aria-label="Compare on" className="inline-flex rounded-[14px] bg-paper-2 p-1">
          {(["standard", "largest"] as const).map((b) => (
            <button
              key={b}
              type="button"
              role="radio"
              aria-checked={basis === b}
              onClick={() => setBasis(b)}
              className={`press rounded-[10px] px-4 py-2 text-[13px] font-semibold ${basis === b ? "bg-ink text-paper" : "text-ink/60 hover:text-ink"}`}
            >
              {b === "standard" ? "Standard print (e.g. A4, base price)" : "Largest print"}
            </button>
          ))}
        </div>
      </div>

      {/* Filters */}
      <div className="grid gap-3 sm:grid-cols-[2fr_1fr_1fr_1fr]">
        <Input
          id="supplier-search"
          placeholder="Search name, suburb, notes"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Select id="supplier-kind" value={kind} onChange={(e) => setKind(e.target.value)} aria-label="Type">
          <option value="">All types</option>
          {Object.entries(KIND_LABEL).map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </Select>
        <Select id="supplier-region" value={region} onChange={(e) => setRegion(e.target.value)} aria-label="Region">
          <option value="">All regions</option>
          {REGIONS.map((r) => (
            <option key={r} value={r}>{r === "AU" ? "Australia (national)" : r === "INTL" ? "Overseas" : r}</option>
          ))}
        </Select>
        <Select id="supplier-sort" value={sort} onChange={(e) => setSort(e.target.value as SortKey)} aria-label="Sort">
          <option value="print">Largest {basis === "standard" ? "standard " : ""}print first</option>
          <option value="min">Lowest minimum first</option>
          <option value="price">Lowest price first</option>
          <option value="name">Name</option>
        </Select>
      </div>

      <div className="flex flex-wrap gap-x-5 gap-y-2 text-[13px]">
        <label className="flex items-center gap-2"><Checkbox id="f-au" checked={auOnly} onChange={(e) => setAuOnly(e.target.checked)} />Prints in Australia</label>
        {activeBlank && (
          <label className="flex items-center gap-2"><Checkbox id="f-offers" checked={offersOnly} onChange={(e) => setOffersOnly(e.target.checked)} />Confirmed they offer it</label>
        )}
        <label className="flex items-center gap-2"><Checkbox id="f-a4" checked={a4Only} onChange={(e) => setA4Only(e.target.checked)} />{basis === "standard" ? "Standard print covers A4" : "Can print A4 or bigger"}</label>
        <label className="flex items-center gap-2"><Checkbox id="f-sized" checked={sizedOnly} onChange={(e) => setSizedOnly(e.target.checked)} />Publishes a {basis === "standard" ? "standard" : "maximum"} print size</label>
        <label className="flex items-center gap-2"><Checkbox id="f-confirmed" checked={confirmedOnly} onChange={(e) => setConfirmedOnly(e.target.checked)} />Confirmed figures only</label>
        <label className="flex items-center gap-2"><Checkbox id="f-account" checked={accountOnly} onChange={(e) => setAccountOnly(e.target.checked)} />We have an account</label>
      </div>

      <p className="text-[13px] text-ink/60 [font-variant-numeric:tabular-nums]">
        {rows.length} supplier{rows.length === 1 ? "" : "s"} · {printsInAu} print in Australia · {a4Count} {basis === "standard" ? "include an A4 print" : "can print A4 or bigger"} · {withConfirmed} with confirmed figures
      </p>

      {rows.length === 0 ? (
        <p className="rounded-[var(--radius-card)] border border-ink/10 bg-white/60 p-5 text-ink/60">
          Nothing matches. Loosen a filter{activeBlank && offersOnly ? ', or untick "Confirmed they offer it"' : ""}.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-[var(--radius-card)] border border-ink/10 bg-white/60">
          <table className="w-full min-w-[900px] border-collapse text-left text-[13px] [font-variant-numeric:tabular-nums]">
            <thead>
              <tr className="border-b border-ink/10 text-[11px] font-bold uppercase tracking-wide text-ink/50">
                <th className="w-10 px-3 py-3"><span className="sr-only">Compare</span></th>
                <th className="px-3 py-3">Supplier</th>
                <th className="px-3 py-3">Prints in</th>
                {activeBlank && <th className="px-3 py-3">Offers it</th>}
                <th className="px-3 py-3">{printHeading}</th>
                <th className="px-3 py-3">A4</th>
                {activeBlank ? (
                  <th className="px-3 py-3">Price ({basis === "standard" ? "standard" : "largest"})</th>
                ) : (
                  <th className="px-3 py-3">Blanks</th>
                )}
                <th className="px-3 py-3">Minimum</th>
                <th className="px-3 py-3">Trust</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(({ supplier, offering, widthMm, heightMm, stated, areaMm2, minQty, priceCents }) => {
                const isSelected = selected.includes(supplier.slug);
                const printedIn = offering && offering.printedIn !== "unknown" ? offering.printedIn : supplier.printsIn;
                const printCm = formatPrintArea(widthMm, heightMm);
                const a4 = coversA4(widthMm, heightMm);
                const offered = supplier.offerings
                  .filter((o) => o.status === "yes")
                  .map((o) => blankById.get(o.blankId))
                  .filter((b): b is Blank => Boolean(b));
                return (
                  <tr key={supplier.id} className={`border-b border-ink/5 align-top last:border-0 ${isSelected ? "bg-lime/15" : ""}`}>
                    <td className="px-3 py-3">
                      <Checkbox
                        id={`cmp-${supplier.slug}`}
                        aria-label={`Compare ${supplier.name}`}
                        checked={isSelected}
                        disabled={!isSelected && selected.length >= MAX_COMPARE}
                        onChange={() => toggle(supplier.slug)}
                      />
                    </td>
                    <td className="px-3 py-3">
                      <Link href={`/suppliers/${supplier.slug}`} className="font-semibold hover:underline">
                        {supplier.name}
                      </Link>
                      {supplier.hasAccount && (
                        <span className="ml-1.5 rounded-full border border-ink/20 px-1.5 py-0.5 text-[9px] font-bold uppercase text-ink/60">Our account</span>
                      )}
                      <div className="text-[12px] text-ink/50">
                        {KIND_LABEL[supplier.kind]}{supplier.location ? ` · ${supplier.location}` : ""}
                      </div>
                    </td>
                    <td className="px-3 py-3"><RegionChip value={printedIn} /></td>
                    {activeBlank && offering && (
                      <td className="px-3 py-3"><StatusChip value={offering.status} /></td>
                    )}
                    <td className="px-3 py-3">
                      {printCm ? <span className="font-semibold">{printCm}</span> : <span className="text-ink/35">n/p</span>}
                      {printCm && areaMm2 === best.area && bestTag}
                      {stated && <div className="text-[12px] text-ink/50">{stated}</div>}
                      {basis === "largest" && offering?.maxBack && <div className="text-[12px] text-ink/50">Back: {offering.maxBack}</div>}
                    </td>
                    <td className="px-3 py-3">
                      {printCm ? (
                        a4 ? <span className="font-semibold">Yes</span> : <span className="text-ink/50">Smaller</span>
                      ) : <span className="text-ink/35">?</span>}
                    </td>
                    {activeBlank ? (
                      <td className="px-3 py-3">
                        {priceCents != null && (
                          <div className="font-semibold">{formatAud(priceCents)}{priceCents === best.price && bestTag}</div>
                        )}
                        <div className={priceCents != null ? "text-[12px] text-ink/50" : ""}>
                          {offering?.price ?? (priceCents == null ? <span className="text-ink/35">n/p</span> : null)}
                        </div>
                      </td>
                    ) : (
                      <td className="px-3 py-3">
                        <div className="flex max-w-[220px] flex-wrap gap-1">
                          {offered.length ? offered.map((b) => (
                            <span key={b.id} className="rounded-full bg-paper-2 px-2 py-0.5 text-[11px] font-semibold">{b.styleCode}</span>
                          )) : <span className="text-ink/35">None confirmed</span>}
                        </div>
                      </td>
                    )}
                    <td className="px-3 py-3">
                      {minQty != null ? <span className="font-semibold">{minQty}{minQty === best.min && bestTag}</span> : null}
                      <div className={minQty != null ? "text-[12px] text-ink/50" : ""}>
                        {supplier.minOrder ?? (minQty == null ? <span className="text-ink/35">n/p</span> : null)}
                      </div>
                    </td>
                    <td className="px-3 py-3">
                      <VerificationBadge value={offering?.verification ?? supplier.verification} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {selected.length > 0 && (
        <div className="sticky bottom-[env(safe-area-inset-bottom,0px)] z-20 flex flex-wrap items-center gap-3 rounded-[var(--radius-card)] bg-ink p-4 text-paper shadow-lg">
          <span className="text-[13px]">{selected.length} of {MAX_COMPARE} selected</span>
          <button type="button" onClick={() => setSelected([])} className="press text-[13px] text-paper/60 underline">
            Clear
          </button>
          <Link
            href={`/suppliers/compare?s=${selected.map(encodeURIComponent).join(",")}${activeBlank ? `&blank=${encodeURIComponent(activeBlank.slug)}` : ""}`}
            className="press ml-auto inline-flex h-11 items-center rounded-[var(--radius-btn)] bg-lime px-5 text-[13px] font-semibold uppercase tracking-wide text-ink"
          >
            Compare side by side
          </Link>
        </div>
      )}
    </div>
  );
}
