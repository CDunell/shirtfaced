import { getSizeGuideContent } from "@/db/content-queries";
import { ContentForm, type ContentFieldDef } from "@/components/ContentForm";
import { updateSizeGuideAction } from "@/app/content/actions";

const FIELDS: ContentFieldDef[] = [
  { name: "intro", label: "Intro (under the page title)", type: "textarea" },
  { name: "sChest", label: "S — chest" },
  { name: "sLength", label: "S — length" },
  { name: "mChest", label: "M — chest" },
  { name: "mLength", label: "M — length" },
  { name: "lChest", label: "L — chest" },
  { name: "lLength", label: "L — length" },
  { name: "xlChest", label: "XL — chest" },
  { name: "xlLength", label: "XL — length" },
  { name: "xxlChest", label: "XXL — chest" },
  { name: "xxlLength", label: "XXL — length" },
  { name: "measureChest", label: '"How to measure" — Chest (after the word "Chest —")', type: "textarea", rows: 2 },
  { name: "measureLength", label: '"How to measure" — Length (after the word "Length —")', type: "textarea", rows: 2 },
  { name: "betweenSizesP1", label: '"Between sizes?" — paragraph 1', type: "textarea" },
  { name: "betweenSizesP2", label: '"Between sizes?" — paragraph 2', type: "textarea" },
  { name: "careP1", label: '"Care" — paragraph', type: "textarea" },
];

export default async function SizeGuideContentPage() {
  const c = await getSizeGuideContent();
  const initial = {
    intro: c?.intro ?? "",
    sChest: c?.sChest ?? "",
    sLength: c?.sLength ?? "",
    mChest: c?.mChest ?? "",
    mLength: c?.mLength ?? "",
    lChest: c?.lChest ?? "",
    lLength: c?.lLength ?? "",
    xlChest: c?.xlChest ?? "",
    xlLength: c?.xlLength ?? "",
    xxlChest: c?.xxlChest ?? "",
    xxlLength: c?.xxlLength ?? "",
    measureChest: c?.measureChest ?? "",
    measureLength: c?.measureLength ?? "",
    betweenSizesP1: c?.betweenSizesP1 ?? "",
    betweenSizesP2: c?.betweenSizesP2 ?? "",
    careP1: c?.careP1 ?? "",
  };

  return (
    <div className="flex flex-col gap-6">
      <h1 className="display text-[40px]">Size guide page</h1>
      <ContentForm fields={FIELDS} initial={initial} action={updateSizeGuideAction} />
    </div>
  );
}
