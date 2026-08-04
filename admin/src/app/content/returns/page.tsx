import { getReturnsContent } from "@/db/content-queries";
import { ContentForm, type ContentFieldDef } from "@/components/ContentForm";
import { updateReturnsAction } from "@/app/content/actions";

const FIELDS: ContentFieldDef[] = [
  { name: "intro", label: "Intro (under the page title)", type: "textarea" },
  { name: "step1Title", label: "Step 1 — title" },
  { name: "step1Body", label: "Step 1 — body", type: "textarea", rows: 2 },
  { name: "step2Title", label: "Step 2 — title" },
  { name: "step2Body", label: "Step 2 — body", type: "textarea", rows: 2 },
  { name: "step3Title", label: "Step 3 — title" },
  { name: "step3Body", label: "Step 3 — body", type: "textarea", rows: 2 },
  { name: "step4Title", label: "Step 4 — title" },
  { name: "step4Body", label: "Step 4 — body", type: "textarea", rows: 2 },
  { name: "exchangesP1", label: '"Exchanges" — paragraph 1', type: "textarea" },
  { name: "exchangesP2", label: '"Exchanges" — paragraph 2', type: "textarea" },
  { name: "wrongP1", label: '"If something\'s wrong with it" — paragraph 1', type: "textarea" },
  { name: "wrongP2", label: '"If something\'s wrong with it" — paragraph 2', type: "textarea" },
  { name: "cantTakeP1", label: '"What we can\'t take back" — paragraph', type: "textarea" },
];

export default async function ReturnsContentPage() {
  const c = await getReturnsContent();
  const initial = {
    intro: c?.intro ?? "",
    step1Title: c?.step1Title ?? "",
    step1Body: c?.step1Body ?? "",
    step2Title: c?.step2Title ?? "",
    step2Body: c?.step2Body ?? "",
    step3Title: c?.step3Title ?? "",
    step3Body: c?.step3Body ?? "",
    step4Title: c?.step4Title ?? "",
    step4Body: c?.step4Body ?? "",
    exchangesP1: c?.exchangesP1 ?? "",
    exchangesP2: c?.exchangesP2 ?? "",
    wrongP1: c?.wrongP1 ?? "",
    wrongP2: c?.wrongP2 ?? "",
    cantTakeP1: c?.cantTakeP1 ?? "",
  };

  return (
    <div className="flex flex-col gap-6">
      <h1 className="display text-[40px]">Returns page</h1>
      <ContentForm fields={FIELDS} initial={initial} action={updateReturnsAction} />
    </div>
  );
}
