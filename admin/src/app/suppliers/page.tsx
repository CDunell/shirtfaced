import { listBlanks, listSuppliersWithOfferings } from "@/db/supplier-queries";
import { SupplierExplorer, type ExplorerParams } from "@/components/suppliers/SupplierExplorer";
import { TrustDot, VERIFICATION_LABEL } from "@/components/suppliers/labels";
import { VERIFICATIONS } from "@/db/schema";

export const dynamic = "force-dynamic";

export default async function SuppliersPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const [raw, blanks, suppliers] = await Promise.all([
    searchParams,
    listBlanks(),
    listSuppliersWithOfferings(),
  ]);
  const params: ExplorerParams = Object.fromEntries(
    Object.entries(raw).map(([k, v]) => [k, Array.isArray(v) ? v[0] : v]),
  );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 className="display text-[40px]">Suppliers</h1>
        <p className="max-w-[65ch] text-[14px] text-ink/70">
          Who can print our blanks, how big, how many, and for how much. The dot beside each figure
          shows where it came from, so a choice rests on what&rsquo;s confirmed rather than what&rsquo;s assumed.
          &ldquo;Best&rdquo; is only awarded among confirmed figures. Prices are one tee (smallest size) with one
          print, in AUD including GST unless the stated price underneath says otherwise.
        </p>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-[12px] text-ink/60">
          {VERIFICATIONS.map((v) => (
            <span key={v} className="flex items-center gap-1.5">
              <TrustDot value={v} /> {VERIFICATION_LABEL[v]}
            </span>
          ))}
          <span className="flex items-center gap-1.5">
            <span className="italic text-ink/35">n/p</span> not published by the supplier
          </span>
        </div>
      </div>

      <SupplierExplorer
        blanks={blanks}
        suppliers={suppliers}
        activeBlankSlug={params.blank ?? null}
        params={params}
      />
    </div>
  );
}
