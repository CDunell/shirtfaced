import { getContactContent } from "@/db/content-queries";
import { ContentForm, type ContentFieldDef } from "@/components/ContentForm";
import { updateContactAction } from "@/app/content/actions";

const FIELDS: ContentFieldDef[] = [
  { name: "intro", label: "Intro (under the page title)", type: "textarea" },
  { name: "email", label: "Contact email address" },
  { name: "wholesaleP1", label: '"Wholesale & stockists" — paragraph', type: "textarea" },
  { name: "pressP1", label: '"Press & collabs" — paragraph', type: "textarea" },
  { name: "bottomBlurb", label: "Bottom callout line" },
];

export default async function ContactContentPage() {
  const c = await getContactContent();
  const initial = {
    intro: c?.intro ?? "",
    email: c?.email ?? "",
    wholesaleP1: c?.wholesaleP1 ?? "",
    pressP1: c?.pressP1 ?? "",
    bottomBlurb: c?.bottomBlurb ?? "",
  };

  return (
    <div className="flex flex-col gap-6">
      <h1 className="display text-[40px]">Contact page</h1>
      <ContentForm fields={FIELDS} initial={initial} action={updateContactAction} />
    </div>
  );
}
