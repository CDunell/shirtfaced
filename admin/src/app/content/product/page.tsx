import { getProductPageContent } from "@/db/content-queries";
import { ContentForm, type ContentFieldDef } from "@/components/ContentForm";
import { updateProductPageAction } from "@/app/content/actions";

const FIELDS: ContentFieldDef[] = [
  { name: "feature1A", label: "Feature 1 — line 1" },
  { name: "feature1B", label: "Feature 1 — line 2" },
  { name: "feature2A", label: "Feature 2 — line 1" },
  { name: "feature2B", label: "Feature 2 — line 2" },
  { name: "feature3A", label: "Feature 3 — line 1" },
  { name: "feature3B", label: "Feature 3 — line 2" },
  { name: "feature4A", label: "Feature 4 — line 1" },
  { name: "feature4B", label: "Feature 4 — line 2" },
];

export default async function ProductPageContentPage() {
  const c = await getProductPageContent();
  const initial = {
    feature1A: c?.feature1A ?? "",
    feature1B: c?.feature1B ?? "",
    feature2A: c?.feature2A ?? "",
    feature2B: c?.feature2B ?? "",
    feature3A: c?.feature3A ?? "",
    feature3B: c?.feature3B ?? "",
    feature4A: c?.feature4A ?? "",
    feature4B: c?.feature4B ?? "",
  };

  return (
    <div className="flex flex-col gap-6">
      <h1 className="display text-[40px]">Product page</h1>
      <p className="max-w-2xl text-[13px] text-ink/50">
        The four-item feature list shown under every product&apos;s
        description (same one on every product — not per-product).
      </p>
      <ContentForm fields={FIELDS} initial={initial} action={updateProductPageAction} />
    </div>
  );
}
