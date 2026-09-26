import Link from "next/link";
import { listBlanks, listSuppliersWithOfferings } from "@/db/supplier-queries";
import type { Blank } from "@/db/supplier-queries";
import { Card } from "@/components/ui";
import { BlankForm } from "@/components/suppliers/BlankForm";
import { CATEGORY_LABEL, NotPublished, formatAud } from "@/components/suppliers/labels";

export const dynamic = "force-dynamic";

type Cheapest = { cents: number; supplier: string; slug: string } | null;

const SPEC_ROWS: Array<{ label: string; get: (b: Blank) => React.ReactNode }> = [
  { label: "Weight", get: (b) => (b.gsm ? `${b.gsm} gsm` : null) },
  { label: "Fibre", get: (b) => b.fibre },
  { label: "Yarn", get: (b) => b.yarn },
  { label: "Fit", get: (b) => b.fit },
  { label: "Build", get: (b) => b.construction },
  { label: "Dye", get: (b) => b.dye },
  { label: "How it prints", get: (b) => b.printNotes },
];

export default async function BlanksPage() {
  const [blanks, suppliers] = await Promise.all([listBlanks(), listSuppliersWithOfferings()]);

  /* Cheapest confirmed one-tee-with-print price among suppliers printing it in Australia. */
  const auInfo = (blankId: string) => {
    let cheapest: Cheapest = null;
    let count = 0;
    for (const s of suppliers) {
      const o = s.offerings.find((x) => x.blankId === blankId && x.status === "yes");
      if (!o) continue;
      const where = o.printedIn !== "unknown" ? o.printedIn : s.printsIn;
      if (where !== "au") continue;
      count++;
      const cents = o.priceCents ?? o.standardPriceCents;
      if (cents != null && (!cheapest || cents < cheapest.cents)) cheapest = { cents, supplier: s.name, slug: s.slug };
    }
    return { cheapest, count };
  };

  const priceNode = (c: Cheapest) =>
    c ? (
      <>
        <span className="font-semibold">{formatAud(c.cents)}</span>{" "}
        <Link href={`/suppliers/${c.slug}`} className="text-ink/60 underline">{c.supplier}</Link>
      </>
    ) : <NotPublished>No AU price</NotPublished>;

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-2">
        <Link href="/suppliers" className="text-[13px] text-ink/50 hover:text-ink">← All suppliers</Link>
        <h1 className="display text-[40px]">Blanks</h1>
        <p className="max-w-[65ch] text-[14px] text-ink/70">
          How each blank is built and how it takes a print, from the maker&rsquo;s spec page and from printers&rsquo; and
          wearers&rsquo; reports. The price is the cheapest shortlisted Australian printer for one tee with one print.
        </p>
      </div>

      {/* Phones: one card per blank. */}
      <ul className="flex flex-col gap-3 md:hidden">
        {blanks.map((b) => {
          const { cheapest, count } = auInfo(b.id);
          return (
            <li key={b.id} className="rounded-[var(--radius-card)] border border-ink/10 bg-white/60 p-4">
              <Link href={`/suppliers?blank=${encodeURIComponent(b.slug)}`} className="text-[16px] font-semibold hover:underline">
                {b.brand} {b.styleCode}
              </Link>
              <div className="text-[12px] text-ink/50">{b.name} · {CATEGORY_LABEL[b.category]}</div>
              <dl className="mt-3 flex flex-col gap-2 text-[13px]">
                {SPEC_ROWS.map((r) => {
                  const v = r.get(b);
                  return v ? (
                    <div key={r.label}>
                      <dt className="text-[10px] font-bold uppercase tracking-wide text-ink/50">{r.label}</dt>
                      <dd>{v}</dd>
                    </div>
                  ) : null;
                })}
                <div>
                  <dt className="text-[10px] font-bold uppercase tracking-wide text-ink/50">Cheapest AU print · {count} printer{count === 1 ? "" : "s"}</dt>
                  <dd>{priceNode(cheapest)}</dd>
                </div>
              </dl>
              {b.notes && <p className="mt-3 text-[12px] text-ink/60">{b.notes}</p>}
              {b.specUrl && <a href={b.specUrl} target="_blank" rel="noopener noreferrer" className="mt-2 inline-block text-[12px] underline">Maker spec ↗</a>}
            </li>
          );
        })}
      </ul>

      {/* Wider screens: blanks side by side, one row per spec. */}
      <div className="hidden max-h-[80vh] overflow-auto rounded-[var(--radius-card)] border border-ink/10 bg-paper md:block">
        <table className="w-full border-collapse text-left text-[13px] [font-variant-numeric:tabular-nums]">
          <thead>
            <tr>
              <th className="sticky left-0 top-0 z-20 border-b border-ink/10 bg-paper px-3 py-3" />
              {blanks.map((b) => (
                <th key={b.id} className="sticky top-0 z-10 min-w-[180px] border-b border-ink/10 bg-paper px-3 py-3 align-bottom">
                  <Link href={`/suppliers?blank=${encodeURIComponent(b.slug)}`} className="text-[14px] font-bold hover:underline">
                    {b.brand} {b.styleCode}
                  </Link>
                  <div className="text-[12px] font-normal text-ink/50">{b.name}</div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {SPEC_ROWS.map((r) => (
              <tr key={r.label} className="align-top hover:bg-paper-2 [&>*]:border-b [&>*]:border-ink/5">
                <th scope="row" className="sticky left-0 w-[120px] bg-paper px-3 py-3 text-[11px] font-bold uppercase tracking-wide text-ink/50">{r.label}</th>
                {blanks.map((b) => (
                  <td key={b.id} className="px-3 py-3">{r.get(b) ?? <NotPublished />}</td>
                ))}
              </tr>
            ))}
            <tr className="align-top hover:bg-paper-2 [&>*]:border-b [&>*]:border-ink/5">
              <th scope="row" className="sticky left-0 bg-paper px-3 py-3 text-[11px] font-bold uppercase tracking-wide text-ink/50">Cheapest AU print</th>
              {blanks.map((b) => {
                const { cheapest, count } = auInfo(b.id);
                return (
                  <td key={b.id} className="px-3 py-3">
                    {priceNode(cheapest)}
                    <div className="text-[12px] text-ink/50">{count} shortlisted printer{count === 1 ? "" : "s"}</div>
                  </td>
                );
              })}
            </tr>
            <tr className="align-top [&>*]:border-b [&>*]:border-ink/5">
              <th scope="row" className="sticky left-0 bg-paper px-3 py-3 text-[11px] font-bold uppercase tracking-wide text-ink/50">Notes</th>
              {blanks.map((b) => (
                <td key={b.id} className="px-3 py-3 text-[12px] text-ink/70">
                  {b.notes ?? <NotPublished />}
                  {b.specUrl && <div><a href={b.specUrl} target="_blank" rel="noopener noreferrer" className="underline">Maker spec ↗</a></div>}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>

      <section className="flex flex-col gap-3">
        <h2 className="display text-[24px]">Add a blank</h2>
        <Card><BlankForm /></Card>
      </section>
    </div>
  );
}
