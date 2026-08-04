import { getShippingContent } from "@/db/content-queries";
import { ContentForm, type ContentFieldDef } from "@/components/ContentForm";
import { updateShippingAction } from "@/app/content/actions";

const FIELDS: ContentFieldDef[] = [
  { name: "intro", label: "Intro (under the page title)", type: "textarea" },
  { name: "standardName", label: "Standard rate — name" },
  { name: "standardTime", label: "Standard rate — delivery time" },
  { name: "standardPrice", label: "Standard rate — price" },
  { name: "expressName", label: "Express rate — name" },
  { name: "expressTime", label: "Express rate — delivery time" },
  { name: "expressPrice", label: "Express rate — price" },
  { name: "whereP1", label: '"Where we ship" — paragraph 1', type: "textarea" },
  { name: "whereP2", label: '"Where we ship" — paragraph 2', type: "textarea" },
  { name: "trackingP1", label: '"Tracking" — paragraph', type: "textarea" },
  { name: "packagingP1", label: '"Packaging" — paragraph', type: "textarea" },
];

export default async function ShippingContentPage() {
  const c = await getShippingContent();
  const initial = {
    intro: c?.intro ?? "",
    standardName: c?.standardName ?? "",
    standardTime: c?.standardTime ?? "",
    standardPrice: c?.standardPrice ?? "",
    expressName: c?.expressName ?? "",
    expressTime: c?.expressTime ?? "",
    expressPrice: c?.expressPrice ?? "",
    whereP1: c?.whereP1 ?? "",
    whereP2: c?.whereP2 ?? "",
    trackingP1: c?.trackingP1 ?? "",
    packagingP1: c?.packagingP1 ?? "",
  };

  return (
    <div className="flex flex-col gap-6">
      <h1 className="display text-[40px]">Shipping page</h1>
      <p className="max-w-2xl text-[13px] text-ink/50">
        The &ldquo;free standard&rdquo; rate isn&apos;t editable here — its
        price is always derived from the free-shipping threshold in the
        storefront&apos;s code, so it can&apos;t drift out of sync with the
        cart&apos;s own free-shipping logic.
      </p>
      <ContentForm fields={FIELDS} initial={initial} action={updateShippingAction} />
    </div>
  );
}
