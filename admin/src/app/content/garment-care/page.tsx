import { getGarmentCareContent } from "@/db/content-queries";
import { ContentForm, type ContentFieldDef } from "@/components/ContentForm";
import { updateGarmentCareAction } from "@/app/content/actions";

const FIELDS: ContentFieldDef[] = [
  { name: "intro", label: "Intro (under the page title)", type: "textarea" },
  { name: "washingP1", label: '"Washing" — paragraph', type: "textarea" },
  { name: "dryingP1", label: '"Drying" — paragraph', type: "textarea" },
  { name: "printCareP1", label: '"Print care" — paragraph', type: "textarea" },
  { name: "storageP1", label: '"Storage" — paragraph', type: "textarea" },
];

export default async function GarmentCareContentPage() {
  const c = await getGarmentCareContent();
  const initial = {
    intro: c?.intro ?? "",
    washingP1: c?.washingP1 ?? "",
    dryingP1: c?.dryingP1 ?? "",
    printCareP1: c?.printCareP1 ?? "",
    storageP1: c?.storageP1 ?? "",
  };

  return (
    <div className="flex flex-col gap-6">
      <h1 className="display text-[40px]">Garment care page</h1>
      <ContentForm fields={FIELDS} initial={initial} action={updateGarmentCareAction} />
    </div>
  );
}
