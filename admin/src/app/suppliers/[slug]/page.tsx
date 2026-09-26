import Link from "next/link";
import { notFound } from "next/navigation";
import { getSupplierBySlug, listBlanks } from "@/db/supplier-queries";
import { saveOfferingAction, updateSupplierAction } from "@/app/suppliers/actions";
import { Card } from "@/components/ui";
import { SupplierForm } from "@/components/suppliers/SupplierForm";
import { OfferingForm } from "@/components/suppliers/OfferingForm";
import {
  KIND_LABEL,
  RegionChip,
  StatusChip,
  VERIFICATION_LABEL,
  VerificationBadge,
  coversA4,
  formatAud,
  formatPrintArea,
} from "@/components/suppliers/labels";

export const dynamic = "force-dynamic";

function checked(date: Date | null): string {
  return date ? date.toLocaleDateString("en-AU", { day: "numeric", month: "short", year: "numeric" }) : "never";
}

export default async function SupplierPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const [supplier, blanks] = await Promise.all([getSupplierBySlug(slug), listBlanks()]);
  if (!supplier) notFound();

  const blankById = new Map(blanks.map((b) => [b.id, b]));
  const offerings = supplier.offerings
    .map((o) => ({ offering: o, blank: blankById.get(o.blankId) }))
    .filter((x): x is { offering: typeof x.offering; blank: NonNullable<typeof x.blank> } => Boolean(x.blank))
    .sort((a, b) => a.blank.sortOrder - b.blank.sortOrder);
  const addable = blanks.filter((b) => !supplier.offerings.some((o) => o.blankId === b.id));

  const largest = formatPrintArea(supplier.maxPrintWidthMm, supplier.maxPrintHeightMm);
  const standard = formatPrintArea(supplier.standardPrintWidthMm, supplier.standardPrintHeightMm);

  const facts: Array<[string, React.ReactNode]> = [
    ["Standard print", standard ?? supplier.standardPrint ?? "Not published"],
    ["Largest print", largest ?? supplier.maxPrint ?? "Not published"],
    ["Minimum order", supplier.minOrder ?? (supplier.minOrderQty != null ? String(supplier.minOrderQty) : "Not published")],
    ["Methods", supplier.methods.length ? supplier.methods.join(", ") : "Not published"],
    ["Orders reach them by", supplier.integration ?? "Not published"],
    ["Last checked", checked(supplier.checkedAt)],
  ];

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-3">
        <Link href="/suppliers" className="text-[13px] text-ink/50 hover:text-ink">← All suppliers</Link>
        <h1 className="display text-[40px] leading-none">{supplier.name}</h1>
        <div className="flex flex-wrap items-center gap-2 text-[13px] text-ink/60">
          <span>{KIND_LABEL[supplier.kind]}</span>
          {supplier.location && <span>· {supplier.location}</span>}
          <RegionChip value={supplier.printsIn} />
          <VerificationBadge value={supplier.verification} />
          {supplier.hasAccount && (
            <span className="rounded-full border border-ink/20 px-2 py-0.5 text-[10px] font-bold uppercase">Our account</span>
          )}
          {supplier.website && (
            <a href={supplier.website} target="_blank" rel="noopener noreferrer" className="underline hover:text-ink">
              Website ↗
            </a>
          )}
        </div>
      </div>

      <dl className="grid gap-x-8 gap-y-4 sm:grid-cols-3">
        {facts.map(([label, value]) => (
          <div key={label} className="flex flex-col gap-1">
            <dt className="text-[11px] font-bold uppercase tracking-wide text-ink/50">{label}</dt>
            <dd className="text-[15px]">{value}</dd>
          </div>
        ))}
      </dl>

      {supplier.notes && (
        <Card><p className="whitespace-pre-line text-[14px] text-ink/80">{supplier.notes}</p></Card>
      )}

      <section className="flex flex-col gap-3">
        <h2 className="display text-[24px]">Blanks they print</h2>
        {offerings.length === 0 ? (
          <Card><p className="text-ink/60">Nothing recorded yet. Add a blank below.</p></Card>
        ) : (
          <div className="overflow-x-auto rounded-[var(--radius-card)] border border-ink/10 bg-white/60">
            <table className="w-full min-w-[820px] border-collapse text-left text-[13px] [font-variant-numeric:tabular-nums]">
              <thead>
                <tr className="border-b border-ink/10 text-[11px] font-bold uppercase tracking-wide text-ink/50">
                  <th className="px-3 py-3">Blank</th>
                  <th className="px-3 py-3">Offers it</th>
                  <th className="px-3 py-3">Printed in</th>
                  <th className="px-3 py-3">Standard print</th>
                  <th className="px-3 py-3">Largest print</th>
                  <th className="px-3 py-3">Price</th>
                  <th className="px-3 py-3">Trust</th>
                </tr>
              </thead>
              <tbody>
                {offerings.map(({ offering: o, blank: b }) => {
                  const std = formatPrintArea(o.standardPrintWidthMm, o.standardPrintHeightMm);
                  const max = formatPrintArea(o.maxPrintWidthMm, o.maxPrintHeightMm);
                  return (
                    <tr key={o.id} className="border-b border-ink/5 align-top last:border-0">
                      <td className="px-3 py-3">
                        <Link href={`/suppliers?blank=${encodeURIComponent(b.slug)}`} className="font-semibold hover:underline">
                          {b.brand} {b.styleCode}
                        </Link>
                        <div className="text-[12px] text-ink/50">{b.name}</div>
                      </td>
                      <td className="px-3 py-3"><StatusChip value={o.status} /></td>
                      <td className="px-3 py-3"><RegionChip value={o.printedIn} /></td>
                      <td className="px-3 py-3">
                        {std && <div className="font-semibold">{std}{coversA4(o.standardPrintWidthMm, o.standardPrintHeightMm) ? " · A4+" : ""}</div>}
                        <div className={std ? "text-[12px] text-ink/50" : ""}>{o.standardPrint ?? (std ? null : <span className="text-ink/35">n/p</span>)}</div>
                        {o.standardPriceCents != null && <div className="text-[12px]">{formatAud(o.standardPriceCents)}</div>}
                      </td>
                      <td className="px-3 py-3">
                        {max && <div className="font-semibold">{max}</div>}
                        <div className={max ? "text-[12px] text-ink/50" : ""}>{o.maxFront ?? (max ? null : <span className="text-ink/35">n/p</span>)}</div>
                        {o.maxBack && <div className="text-[12px] text-ink/50">Back: {o.maxBack}</div>}
                      </td>
                      <td className="px-3 py-3">
                        {o.priceCents != null && <div className="font-semibold">{formatAud(o.priceCents)}</div>}
                        <div className={o.priceCents != null ? "text-[12px] text-ink/50" : ""}>{o.price ?? (o.priceCents == null ? <span className="text-ink/35">n/p</span> : null)}</div>
                      </td>
                      <td className="px-3 py-3">
                        <VerificationBadge value={o.verification} />
                        {o.sourceUrl && (
                          <a href={o.sourceUrl} target="_blank" rel="noopener noreferrer" className="mt-1 block text-[12px] text-ink/50 underline hover:text-ink">
                            Source ↗
                          </a>
                        )}
                        <div className="mt-1 text-[11px] text-ink/40">Checked {checked(o.checkedAt)}</div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="display text-[24px]">Sources</h2>
        {supplier.sourceUrls.length === 0 ? (
          <p className="text-[14px] text-ink/60">None recorded.</p>
        ) : (
          <ul className="flex flex-col gap-1 text-[13px]">
            {supplier.sourceUrls.map((url) => (
              <li key={url}>
                <a href={url} target="_blank" rel="noopener noreferrer" className="break-all underline hover:text-ink">{url}</a>
              </li>
            ))}
          </ul>
        )}
        <p className="text-[12px] text-ink/50">
          Supplier-level trust: {VERIFICATION_LABEL[supplier.verification]}.
        </p>
      </section>

      <section className="flex flex-col gap-4">
        <h2 className="display text-[24px]">Update</h2>
        {offerings.map(({ offering: o, blank: b }) => (
          <details key={o.id} className="rounded-[var(--radius-card)] border border-ink/10 bg-white/60 p-5">
            <summary className="cursor-pointer text-[14px] font-semibold">
              Edit {b.brand} {b.styleCode} · {b.name}
            </summary>
            <div className="mt-4">
              <OfferingForm offering={o} blank={b} action={saveOfferingAction.bind(null, supplier.id, supplier.slug)} />
            </div>
          </details>
        ))}
        {addable.length > 0 && (
          <details className="rounded-[var(--radius-card)] border border-dashed border-ink/20 p-5">
            <summary className="cursor-pointer text-[14px] font-semibold">+ Add a blank they print</summary>
            <div className="mt-4">
              <OfferingForm addableBlanks={addable} action={saveOfferingAction.bind(null, supplier.id, supplier.slug)} />
            </div>
          </details>
        )}
        <details className="rounded-[var(--radius-card)] border border-ink/10 bg-white/60 p-5">
          <summary className="cursor-pointer text-[14px] font-semibold">Edit supplier details</summary>
          <div className="mt-4">
            <SupplierForm supplier={supplier} action={updateSupplierAction.bind(null, supplier.id, supplier.slug)} />
          </div>
        </details>
      </section>
    </div>
  );
}
