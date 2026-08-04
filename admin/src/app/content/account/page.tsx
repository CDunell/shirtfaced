import { getAccountContent } from "@/db/content-queries";
import { ContentForm, type ContentFieldDef } from "@/components/ContentForm";
import { updateAccountAction } from "@/app/content/actions";

const FIELDS: ContentFieldDef[] = [
  { name: "intro", label: "Intro (under the page title)", type: "textarea" },
  { name: "benefit1A", label: "Benefit 1 — line 1" },
  { name: "benefit1B", label: "Benefit 1 — line 2" },
  { name: "benefit2A", label: "Benefit 2 — line 1" },
  { name: "benefit2B", label: "Benefit 2 — line 2" },
  { name: "benefit3A", label: "Benefit 3 — line 1" },
  { name: "benefit3B", label: "Benefit 3 — line 2" },
];

export default async function AccountContentPage() {
  const c = await getAccountContent();
  const initial = {
    intro: c?.intro ?? "",
    benefit1A: c?.benefit1A ?? "",
    benefit1B: c?.benefit1B ?? "",
    benefit2A: c?.benefit2A ?? "",
    benefit2B: c?.benefit2B ?? "",
    benefit3A: c?.benefit3A ?? "",
    benefit3B: c?.benefit3B ?? "",
  };

  return (
    <div className="flex flex-col gap-6">
      <h1 className="display text-[40px]">Account page</h1>
      <ContentForm fields={FIELDS} initial={initial} action={updateAccountAction} />
    </div>
  );
}
