import Link from "next/link";
import { listBlanks, listSuppliersWithOfferings } from "@/db/supplier-queries";
import { Card } from "@/components/ui";
import { BlankForm } from "@/components/suppliers/BlankForm";
import { CATEGORY_LABEL } from "@/components/suppliers/labels";

export const dynamic = "force-dynamic";

export default async function BlanksPage() {
  const [blanks, suppliers] = await Promise.all([listBlanks(), listSuppliersWithOfferings()]);
  const offers = (blankId: string) =>
    suppliers.filter((s) => s.offerings.some((o) => o.blankId === blankId && o.status === "yes"));

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-2">
        <Link href="/suppliers" className="text-[13px] text-ink/50 hover:text-ink">← All suppliers</Link>
        <h1 className="display text-[40px]">Blanks</h1>
        <p className="max-w-[65ch] text-[14px] text-ink/70">
          Each blank here is a tab on the Suppliers page. Add one, then record who prints it from each supplier&rsquo;s page.
        </p>
      </div>

      <div className="overflow-x-auto rounded-[var(--radius-card)] border border-ink/10 bg-white/60">
        <table className="w-full min-w-[640px] border-collapse text-left text-[13px] [font-variant-numeric:tabular-nums]">
          <thead>
            <tr className="border-b border-ink/10 text-[11px] font-bold uppercase tracking-wide text-ink/50">
              <th className="px-3 py-3">Blank</th>
              <th className="px-3 py-3">Type</th>
              <th className="px-3 py-3">GSM</th>
              <th className="px-3 py-3">Fit</th>
              <th className="px-3 py-3">Confirmed suppliers</th>
            </tr>
          </thead>
          <tbody>
            {blanks.map((b) => {
              const confirmed = offers(b.id);
              const inAu = confirmed.filter((s) => {
                const o = s.offerings.find((x) => x.blankId === b.id);
                return (o && o.printedIn !== "unknown" ? o.printedIn : s.printsIn) === "au";
              }).length;
              return (
                <tr key={b.id} className="border-b border-ink/5 align-top last:border-0">
                  <td className="px-3 py-3">
                    <Link href={`/suppliers?blank=${encodeURIComponent(b.slug)}`} className="font-semibold hover:underline">
                      {b.brand} {b.styleCode}
                    </Link>
                    <div className="text-[12px] text-ink/50">{b.name}</div>
                  </td>
                  <td className="px-3 py-3">{CATEGORY_LABEL[b.category]}</td>
                  <td className="px-3 py-3">{b.gsm ?? <span className="text-ink/35">n/p</span>}</td>
                  <td className="px-3 py-3">{b.fit ?? <span className="text-ink/35">n/p</span>}</td>
                  <td className="px-3 py-3">
                    {confirmed.length} ({inAu} in Australia)
                  </td>
                </tr>
              );
            })}
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
