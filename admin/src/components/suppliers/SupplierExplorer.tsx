"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import type { Blank, Offering, SupplierWithOfferings } from "@/db/supplier-queries";
import type { Verification } from "@/db/schema";
import { Checkbox, Input, Select } from "@/components/ui";
import {
  KIND_LABEL,
  NotPublished,
  RegionChip,
  StatusChip,
  TrustDot,
  coversA4,
  formatAud,
  formatPrintArea,
} from "./labels";

type SortKey = "name" | "print" | "min" | "price";
type SortDir = "asc" | "desc";
/* Compare on the print the base price includes, or the largest they can do. */
type Basis = "standard" | "largest";

const REGIONS = ["QLD", "NSW", "ACT", "VIC", "TAS", "WA", "SA", "NT", "AU", "NZ", "INTL"];
const REGION_NAME = (r: string) => (r === "AU" ? "Australia (national)" : r === "INTL" ? "Overseas" : r);
const MAX_COMPARE = 4;
const MIN_ORDER_CAPS = [1, 10, 25, 50];
/* "Best" is only awarded when at least this many confirmed figures compete. */
const BEST_MIN_FIELD = 3;
const DEFAULT_DIR: Record<SortKey, SortDir> = { print: "desc", min: "asc", price: "asc", name: "asc" };

type Filters = {
  q: string;
  kind: string;
  region: string;
  basis: Basis;
  au: boolean;
  offers: boolean;
  a4: boolean;
  sized: boolean;
  confirmed: boolean;
  account: boolean;
  maxMin: number | null;
  sort: SortKey;
  dir: SortDir;
};

const CLEARED: Omit<Filters, "basis" | "sort" | "dir"> = {
  q: "",
  kind: "",
  region: "",
  au: false,
  offers: false,
  a4: false,
  sized: false,
  confirmed: false,
  account: false,
  maxMin: null,
};

export type ExplorerParams = Partial<Record<string, string>>;

function readFilters(p: ExplorerParams): Filters {
  const sort = (["name", "print", "min", "price"] as const).find((k) => k === p.sort) ?? "print";
  const maxMin = Number(p.min);
  return {
    q: p.q ?? "",
    kind: p.kind ?? "",
    region: p.region ?? "",
    basis: p.basis === "standard" ? "standard" : "largest",
    au: p.au === "1",
    offers: p.offers !== "0",
    a4: p.a4 === "1",
    sized: p.sized === "1",
    confirmed: p.confirmed === "1",
    account: p.account === "1",
    maxMin: MIN_ORDER_CAPS.includes(maxMin) ? maxMin : null,
    sort,
    dir: p.dir === "asc" || p.dir === "desc" ? p.dir : DEFAULT_DIR[sort],
  };
}

/* Only non-default values go in the URL, so links stay short. */
function filterQuery(f: Filters): URLSearchParams {
  const u = new URLSearchParams();
  if (f.q) u.set("q", f.q);
  if (f.kind) u.set("kind", f.kind);
  if (f.region) u.set("region", f.region);
  if (f.basis === "standard") u.set("basis", "standard");
  if (f.au) u.set("au", "1");
  if (!f.offers) u.set("offers", "0");
  if (f.a4) u.set("a4", "1");
  if (f.sized) u.set("sized", "1");
  if (f.confirmed) u.set("confirmed", "1");
  if (f.account) u.set("account", "1");
  if (f.maxMin != null) u.set("min", String(f.maxMin));
  if (f.sort !== "print") u.set("sort", f.sort);
  if (f.dir !== DEFAULT_DIR[f.sort]) u.set("dir", f.dir);
  return u;
}

function suppliersHref(f: Filters, blankSlug: string | null): string {
  const u = filterQuery(f);
  if (blankSlug) u.set("blank", blankSlug);
  const qs = u.toString();
  return qs ? `/suppliers?${qs}` : "/suppliers";
}

type Figure = { v: Verification | null };
type Row = {
  supplier: SupplierWithOfferings;
  offering: Offering | null;
  printedIn: SupplierWithOfferings["printsIn"];
  widthMm: number | null;
  heightMm: number | null;
  stated: string | null;
  areaMm2: number | null;
  minQty: number | null;
  priceCents: number | null;
  /* Where each figure came from: the blank-specific record or the supplier. */
  printV: Figure["v"];
  minV: Figure["v"];
  priceV: Figure["v"];
};

function isConfirmed(v: Verification | null): boolean {
  return v === "api" || v === "page";
}

/* The print dimensions for a row on the chosen basis: the blank-specific
   figure first, then the supplier-wide one. */
function printFor(supplier: SupplierWithOfferings, offering: Offering | null, basis: Basis) {
  const std = basis === "standard";
  const ow = std ? offering?.standardPrintWidthMm : offering?.maxPrintWidthMm;
  const oh = std ? offering?.standardPrintHeightMm : offering?.maxPrintHeightMm;
  const fromOffering = ow != null && oh != null;
  const w = fromOffering ? ow : std ? supplier.standardPrintWidthMm : supplier.maxPrintWidthMm;
  const h = fromOffering ? oh : std ? supplier.standardPrintHeightMm : supplier.maxPrintHeightMm;
  const price = (std ? offering?.standardPriceCents : offering?.priceCents) ?? null;
  return {
    w,
    h,
    stated: (std ? offering?.standardPrint ?? supplier.standardPrint : offering?.maxFront ?? supplier.maxPrint) ?? null,
    price,
    printV: w && h ? (fromOffering ? offering!.verification : supplier.verification) : null,
    priceV: price != null ? offering!.verification : null,
  };
}

export function SupplierExplorer({
  blanks,
  suppliers,
  activeBlankSlug,
  params,
}: {
  blanks: Blank[];
  suppliers: SupplierWithOfferings[];
  activeBlankSlug: string | null;
  params: ExplorerParams;
}) {
  const activeBlank = blanks.find((b) => b.slug === activeBlankSlug) ?? null;
  const blankById = useMemo(() => new Map(blanks.map((b) => [b.id, b])), [blanks]);
  const nameBySlug = useMemo(() => new Map(suppliers.map((s) => [s.slug, s.name])), [suppliers]);

  const [f, setF] = useState<Filters>(() => readFilters(params));
  const set = <K extends keyof Filters>(key: K, value: Filters[K]) => setF((prev) => ({ ...prev, [key]: value }));
  const [selected, setSelected] = useState<string[]>([]);

  /* Keep the URL in step so a view can be refreshed or shared. */
  useEffect(() => {
    window.history.replaceState(null, "", suppliersHref(f, activeBlank?.slug ?? null));
  }, [f, activeBlank]);

  const { rows, total } = useMemo(() => {
    const q = f.q.trim().toLowerCase();
    const out: Row[] = [];
    let total = 0;
    for (const supplier of suppliers) {
      const offering = activeBlank
        ? (supplier.offerings.find((o) => o.blankId === activeBlank.id) ?? null)
        : null;
      if (activeBlank && !offering) continue;
      total++;

      if (activeBlank && f.offers && offering!.status !== "yes") continue;
      if (q && !`${supplier.name} ${supplier.location ?? ""} ${supplier.notes ?? ""}`.toLowerCase().includes(q)) continue;
      if (f.kind && supplier.kind !== f.kind) continue;
      if (f.region && supplier.region !== f.region) continue;

      const printedIn = offering && offering.printedIn !== "unknown" ? offering.printedIn : supplier.printsIn;
      if (f.au && printedIn !== "au") continue;
      if (f.account && !supplier.hasAccount) continue;

      const { w, h, stated, price, printV, priceV } = printFor(supplier, offering, f.basis);
      const areaMm2 = w && h ? w * h : null;
      if (f.sized && areaMm2 == null) continue;
      if (f.a4 && !coversA4(w, h)) continue;

      const minFromOffering = offering?.minOrderQty != null;
      const minQty = minFromOffering ? offering!.minOrderQty : supplier.minOrderQty;
      if (f.maxMin != null && (minQty == null || minQty > f.maxMin)) continue;

      if (f.confirmed && !isConfirmed(offering?.verification ?? supplier.verification)) continue;

      out.push({
        supplier,
        offering,
        printedIn,
        widthMm: w,
        heightMm: h,
        stated,
        areaMm2,
        minQty,
        priceCents: price,
        printV,
        priceV,
        minV: minQty != null ? (minFromOffering ? offering!.verification : supplier.verification) : null,
      });
    }

    /* Missing figures sort last whichever way the column runs. */
    const cmp = (a: number | null, b: number | null) => {
      if (a == null && b == null) return 0;
      if (a == null) return 1;
      if (b == null) return -1;
      return (a - b) * (f.dir === "asc" ? 1 : -1);
    };
    const byName = (a: Row, b: Row) => a.supplier.name.localeCompare(b.supplier.name);
    out.sort((a, b) => {
      if (f.sort === "print") return cmp(a.areaMm2, b.areaMm2) || byName(a, b);
      if (f.sort === "min") return cmp(a.minQty, b.minQty) || byName(a, b);
      if (f.sort === "price") return cmp(a.priceCents, b.priceCents) || byName(a, b);
      return byName(a, b) * (f.dir === "asc" ? 1 : -1);
    });
    return { rows: out, total };
  }, [suppliers, activeBlank, f]);

  /* Best is judged only on confirmed figures, and only when enough compete. */
  const best = useMemo(() => {
    const pick = (values: Array<[number | null, Verification | null]>, fn: (...n: number[]) => number) => {
      const real = values.filter(([n, v]) => n != null && isConfirmed(v)).map(([n]) => n as number);
      return real.length >= BEST_MIN_FIELD ? { value: fn(...real), of: real.length } : null;
    };
    return {
      area: pick(rows.map((r) => [r.areaMm2, r.printV]), Math.max),
      min: pick(rows.map((r) => [r.minQty, r.minV]), Math.min),
      price: pick(rows.map((r) => [r.priceCents, r.priceV]), Math.min),
    };
  }, [rows]);

  const printsInAu = rows.filter((r) => r.printedIn === "au").length;
  const a4Count = rows.filter((r) => coversA4(r.widthMm, r.heightMm)).length;
  const withPrice = rows.filter((r) => r.priceCents != null).length;

  function toggle(slug: string) {
    setSelected((prev) =>
      prev.includes(slug) ? prev.filter((s) => s !== slug) : prev.length >= MAX_COMPARE ? prev : [...prev, slug],
    );
  }

  function sortBy(key: SortKey) {
    setF((prev) =>
      prev.sort === key
        ? { ...prev, dir: prev.dir === "asc" ? "desc" : "asc" }
        : { ...prev, sort: key, dir: DEFAULT_DIR[key] },
    );
  }

  const printLabel = f.basis === "standard" ? "standard" : "largest";

  /* One chip per active filter, each removable on its own. */
  const chips: Array<{ label: string; clear: () => void }> = [];
  if (f.q) chips.push({ label: `Search: “${f.q}”`, clear: () => set("q", "") });
  if (f.kind) chips.push({ label: `Type: ${KIND_LABEL[f.kind as keyof typeof KIND_LABEL]}`, clear: () => set("kind", "") });
  if (f.region) chips.push({ label: `Region: ${REGION_NAME(f.region)}`, clear: () => set("region", "") });
  if (activeBlank && f.offers) chips.push({ label: "Offers it: confirmed", clear: () => set("offers", false) });
  if (f.au) chips.push({ label: "Prints in: Australia", clear: () => set("au", false) });
  if (f.a4) chips.push({ label: f.basis === "standard" ? "Standard print: A4 or bigger" : "Largest print: A4 or bigger", clear: () => set("a4", false) });
  if (f.maxMin != null) chips.push({ label: f.maxMin === 1 ? "Minimum: single tees" : `Minimum: ${f.maxMin} or fewer`, clear: () => set("maxMin", null) });
  if (f.account) chips.push({ label: "Our account", clear: () => set("account", false) });
  if (f.sized) chips.push({ label: `Publishes a ${printLabel} print size`, clear: () => set("sized", false) });
  if (f.confirmed) chips.push({ label: "Confirmed figures only", clear: () => set("confirmed", false) });
  const clearAll = () => setF((prev) => ({ ...prev, ...CLEARED }));

  const chipList = (
    <div className="flex flex-wrap items-center gap-2">
      {chips.map((c) => (
        <button
          key={c.label}
          type="button"
          onClick={c.clear}
          aria-label={`Remove filter ${c.label}`}
          className="press inline-flex items-center gap-1.5 rounded-full bg-ink px-3 py-1 text-[12px] font-semibold text-paper hover:bg-ink-soft"
        >
          {c.label} <span aria-hidden className="text-paper/60">×</span>
        </button>
      ))}
      {chips.length > 1 && (
        <button type="button" onClick={clearAll} className="press text-[12px] font-semibold text-ink/60 underline hover:text-ink">
          Clear all
        </button>
      )}
    </div>
  );

  const bestTag = (of: number) => (
    <span
      title={`Best confirmed figure of ${of} in view`}
      className="ml-1.5 rounded-full bg-lime px-1.5 py-0.5 align-middle text-[9px] font-bold uppercase not-italic"
    >
      Best
    </span>
  );

  const th = "sticky top-0 bg-paper px-3 py-3";
  const sortHeader = (k: SortKey, children: React.ReactNode, align: "left" | "right" = "left") => {
    const active = f.sort === k;
    return (
      <th
        scope="col"
        aria-sort={active ? (f.dir === "asc" ? "ascending" : "descending") : "none"}
        className={`${th} z-10 ${align === "right" ? "text-right" : ""}`}
      >
        <button
          type="button"
          onClick={() => sortBy(k)}
          className={`inline-flex items-center gap-1 uppercase tracking-wide hover:text-ink ${active ? "text-ink" : ""}`}
        >
          {children}
          <span aria-hidden className={active ? "" : "opacity-30"}>{active ? (f.dir === "asc" ? "↑" : "↓") : "↕"}</span>
        </button>
      </th>
    );
  };

  return (
    <div className="flex flex-col gap-5">
      {/* Tabs: every supplier, then one per blank. Filters carry across. */}
      <nav aria-label="Blanks" className="-mx-1 flex gap-2 overflow-x-auto px-1 pb-1">
        <Link
          href={suppliersHref(f, null)}
          aria-current={!activeBlank ? "page" : undefined}
          className={`press shrink-0 rounded-[14px] px-4 py-2.5 text-[13px] font-semibold ${!activeBlank ? "bg-ink text-paper" : "border border-ink/15 hover:bg-paper-2"}`}
        >
          All suppliers
        </Link>
        {blanks.map((b) => (
          <Link
            key={b.id}
            href={suppliersHref(f, b.slug)}
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
          Everyone with a record for the <span className="font-semibold text-ink">{activeBlank.brand} {activeBlank.styleCode} {activeBlank.name}</span>
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
              aria-checked={f.basis === b}
              onClick={() => set("basis", b)}
              className={`press rounded-[10px] px-4 py-2 text-[13px] font-semibold ${f.basis === b ? "bg-ink text-paper" : "text-ink/60 hover:text-ink"}`}
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
          type="search"
          placeholder="Search name, suburb, notes"
          aria-label="Search suppliers"
          value={f.q}
          onChange={(e) => set("q", e.target.value)}
        />
        <Select id="supplier-kind" value={f.kind} onChange={(e) => set("kind", e.target.value)} aria-label="Type">
          <option value="">All types</option>
          {Object.entries(KIND_LABEL).map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </Select>
        <Select id="supplier-region" value={f.region} onChange={(e) => set("region", e.target.value)} aria-label="Region">
          <option value="">All regions</option>
          {REGIONS.map((r) => (
            <option key={r} value={r}>{REGION_NAME(r)}</option>
          ))}
        </Select>
        <Select
          id="supplier-min"
          value={f.maxMin ?? ""}
          onChange={(e) => set("maxMin", e.target.value ? Number(e.target.value) : null)}
          aria-label="Minimum order"
        >
          <option value="">Any minimum order</option>
          {MIN_ORDER_CAPS.map((n) => (
            <option key={n} value={n}>{n === 1 ? "Single tees (min 1)" : `Minimum ${n} or fewer`}</option>
          ))}
        </Select>
      </div>

      <div className="flex flex-col gap-2 text-[13px] sm:flex-row sm:gap-8">
        <fieldset className="flex flex-wrap items-center gap-x-5 gap-y-2">
          <legend className="float-left mr-3 text-[11px] font-bold uppercase tracking-wide text-ink/50">Can they</legend>
          <label className="flex items-center gap-2"><Checkbox id="f-au" checked={f.au} onChange={(e) => set("au", e.target.checked)} />Print in Australia</label>
          {activeBlank && (
            <label className="flex items-center gap-2"><Checkbox id="f-offers" checked={f.offers} onChange={(e) => set("offers", e.target.checked)} />Print this blank (confirmed)</label>
          )}
          <label className="flex items-center gap-2"><Checkbox id="f-a4" checked={f.a4} onChange={(e) => set("a4", e.target.checked)} />{f.basis === "standard" ? "Include an A4 print" : "Print A4 or bigger"}</label>
          <label className="flex items-center gap-2"><Checkbox id="f-account" checked={f.account} onChange={(e) => set("account", e.target.checked)} />We have an account</label>
        </fieldset>
        <fieldset className="flex flex-wrap items-center gap-x-5 gap-y-2">
          <legend className="float-left mr-3 text-[11px] font-bold uppercase tracking-wide text-ink/50">Data</legend>
          <label className="flex items-center gap-2"><Checkbox id="f-sized" checked={f.sized} onChange={(e) => set("sized", e.target.checked)} />Publishes a {printLabel} print size</label>
          <label className="flex items-center gap-2"><Checkbox id="f-confirmed" checked={f.confirmed} onChange={(e) => set("confirmed", e.target.checked)} />Confirmed figures only</label>
        </fieldset>
      </div>

      <div className="flex flex-col gap-2">
        <p className="text-[14px] [font-variant-numeric:tabular-nums]" aria-live="polite">
          Showing <span className="font-bold">{rows.length}</span> of {total} supplier{total === 1 ? "" : "s"}
          <span className="text-ink/55">
            {" "}· {printsInAu} print in Australia · {a4Count} {f.basis === "standard" ? "include an A4 print" : "can print A4 or bigger"} · {withPrice} with a comparable price
          </span>
        </p>
        {chips.length > 0 && chipList}
      </div>

      {rows.length === 0 ? (
        <div className="flex flex-col gap-3 rounded-[var(--radius-card)] border border-ink/10 bg-white/60 p-5">
          <p className="font-semibold">No suppliers match all of these filters.</p>
          <p className="text-[13px] text-ink/60">Remove one to widen the list:</p>
          {chipList}
        </div>
      ) : (
        <div className="max-h-[75vh] overflow-auto rounded-[var(--radius-card)] border border-ink/10 bg-paper">
          <table className="w-full min-w-[860px] border-collapse text-left text-[13px] [font-variant-numeric:tabular-nums]">
            <thead>
              <tr className="text-[11px] font-bold uppercase tracking-wide text-ink/50 [&>th]:border-b [&>th]:border-ink/10">
                <th scope="col" className={`${th} left-0 z-20 min-w-[240px]`}>
                  <button
                    type="button"
                    onClick={() => sortBy("name")}
                    aria-label="Sort by supplier name"
                    className={`inline-flex items-center gap-1 pl-8 uppercase tracking-wide hover:text-ink ${f.sort === "name" ? "text-ink" : ""}`}
                  >
                    Supplier
                    <span aria-hidden className={f.sort === "name" ? "" : "opacity-30"}>{f.sort === "name" ? (f.dir === "asc" ? "↑" : "↓") : "↕"}</span>
                  </button>
                </th>
                <th scope="col" className={`${th} z-10`}>Prints in</th>
                {activeBlank && <th scope="col" className={`${th} z-10`}>Offers it</th>}
                {sortHeader("print", f.basis === "standard" ? "Standard print (W × H)" : "Largest print (W × H)", "right")}
                <th scope="col" className={`${th} z-10 text-center`}>Covers A4</th>
                {activeBlank ? (
                  sortHeader("price", `AUD · 1 tee + ${printLabel} print`, "right")
                ) : (
                  <th scope="col" className={`${th} z-10`}>Blanks they print</th>
                )}
                {sortHeader("min", "Min order (units)", "right")}
              </tr>
            </thead>
            <tbody>
              {rows.map(({ supplier, offering, printedIn, widthMm, heightMm, stated, areaMm2, minQty, priceCents, printV, minV, priceV }) => {
                const isSelected = selected.includes(supplier.slug);
                const printCm = formatPrintArea(widthMm, heightMm);
                const offered = supplier.offerings
                  .filter((o) => o.status === "yes")
                  .map((o) => blankById.get(o.blankId))
                  .filter((b): b is Blank => Boolean(b));
                const rowBg = isSelected ? "bg-[#eaf5c9]" : "bg-paper group-hover:bg-paper-2";
                return (
                  <tr key={supplier.id} className={`group align-top [&>td]:border-b [&>td]:border-ink/5 ${isSelected ? "bg-[#eaf5c9]" : "hover:bg-paper-2"}`}>
                    <td className={`sticky left-0 z-[5] px-3 py-3 ${rowBg}`}>
                      <div className="flex gap-3">
                        <Checkbox
                          id={`cmp-${supplier.slug}`}
                          aria-label={`Compare ${supplier.name}`}
                          checked={isSelected}
                          disabled={!isSelected && selected.length >= MAX_COMPARE}
                          onChange={() => toggle(supplier.slug)}
                        />
                        <div>
                          <Link href={`/suppliers/${supplier.slug}`} className="font-semibold hover:underline">
                            {supplier.name}
                          </Link>
                          {supplier.hasAccount && (
                            <span className="ml-1.5 rounded-full border border-ink/20 px-1.5 py-0.5 text-[9px] font-bold uppercase text-ink/60">Our account</span>
                          )}
                          <div className="text-[12px] text-ink/50">
                            {KIND_LABEL[supplier.kind]}{supplier.location ? ` · ${supplier.location}` : ""}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-3 py-3"><RegionChip value={printedIn} /></td>
                    {activeBlank && offering && (
                      <td className="px-3 py-3"><StatusChip value={offering.status} /></td>
                    )}
                    <td className="px-3 py-3 text-right">
                      {printCm ? (
                        <span className="inline-flex items-center gap-1.5 font-semibold">
                          {printV && <TrustDot value={printV} />}
                          {printCm}
                          {best.area && areaMm2 === best.area.value && isConfirmed(printV) && bestTag(best.area.of)}
                        </span>
                      ) : <NotPublished />}
                      {stated && <div className="ml-auto max-w-[240px] text-[12px] text-ink/50">{stated}</div>}
                      {f.basis === "largest" && offering?.maxBack && <div className="text-[12px] text-ink/50">Back: {offering.maxBack}</div>}
                    </td>
                    <td className="px-3 py-3 text-center">
                      {printCm ? (
                        coversA4(widthMm, heightMm) ? <span className="font-semibold">Yes</span> : <span className="text-ink/50">Smaller</span>
                      ) : <NotPublished>?</NotPublished>}
                    </td>
                    {activeBlank ? (
                      <td className="px-3 py-3 text-right">
                        {priceCents != null && (
                          <div className="inline-flex items-center gap-1.5 font-semibold">
                            {priceV && <TrustDot value={priceV} />}
                            {formatAud(priceCents)}
                            {best.price && priceCents === best.price.value && isConfirmed(priceV) && bestTag(best.price.of)}
                          </div>
                        )}
                        {offering?.price ? (
                          <div className={`ml-auto max-w-[260px] ${priceCents != null ? "text-[12px] text-ink/50" : ""}`}>{offering.price}</div>
                        ) : priceCents == null ? <NotPublished /> : null}
                      </td>
                    ) : (
                      <td className="px-3 py-3">
                        <div className="flex max-w-[220px] flex-wrap gap-1">
                          {offered.length ? offered.map((b) => (
                            <span key={b.id} title={`${b.brand} ${b.styleCode} ${b.name}`} className="rounded-full bg-paper-2 px-2 py-0.5 text-[11px] font-semibold">{b.styleCode}</span>
                          )) : <NotPublished>None confirmed</NotPublished>}
                        </div>
                      </td>
                    )}
                    <td className="px-3 py-3 text-right">
                      {minQty != null && (
                        <span className="inline-flex items-center gap-1.5 font-semibold">
                          {minV && <TrustDot value={minV} />}
                          {minQty}
                          {best.min && minQty === best.min.value && isConfirmed(minV) && bestTag(best.min.of)}
                        </span>
                      )}
                      {supplier.minOrder ? (
                        <div className={`ml-auto max-w-[200px] ${minQty != null ? "text-[12px] text-ink/50" : ""}`}>{supplier.minOrder}</div>
                      ) : minQty == null ? <NotPublished /> : null}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <div className="sticky bottom-[env(safe-area-inset-bottom,0px)] z-30 flex flex-wrap items-center gap-2 rounded-[var(--radius-card)] bg-ink p-3 text-paper shadow-lg">
        {selected.length === 0 ? (
          <span className="px-1 text-[13px] text-paper/60">Tick up to {MAX_COMPARE} suppliers to compare them side by side.</span>
        ) : (
          selected.map((slug) => (
            <button
              key={slug}
              type="button"
              onClick={() => toggle(slug)}
              aria-label={`Remove ${nameBySlug.get(slug) ?? slug} from comparison`}
              className="press inline-flex items-center gap-1.5 rounded-full bg-paper/10 px-3 py-1.5 text-[12px] font-semibold hover:bg-paper/20"
            >
              {nameBySlug.get(slug) ?? slug} <span aria-hidden className="text-paper/50">×</span>
            </button>
          ))
        )}
        {selected.length >= 2 ? (
          <Link
            href={`/suppliers/compare?s=${selected.map(encodeURIComponent).join(",")}${activeBlank ? `&blank=${encodeURIComponent(activeBlank.slug)}` : ""}`}
            className="press ml-auto inline-flex h-10 items-center rounded-[var(--radius-btn)] bg-lime px-5 text-[13px] font-semibold uppercase tracking-wide text-ink"
          >
            Compare {selected.length}
          </Link>
        ) : selected.length === 1 ? (
          <span className="ml-auto text-[12px] text-paper/60">Pick at least one more</span>
        ) : null}
      </div>
    </div>
  );
}
