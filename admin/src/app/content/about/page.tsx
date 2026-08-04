import { getAboutContent } from "@/db/content-queries";
import { ContentForm, type ContentFieldDef } from "@/components/ContentForm";
import { updateAboutAction } from "@/app/content/actions";

const FIELDS: ContentFieldDef[] = [
  { name: "intro", label: "Intro (under the page title)", type: "textarea" },
  { name: "ideaP1", label: '"The idea" — paragraph 1', type: "textarea" },
  { name: "ideaP2", label: '"The idea" — paragraph 2', type: "textarea" },
  { name: "howMadeP1", label: '"How they\'re made" — paragraph 1', type: "textarea" },
  { name: "howMadeP2", label: '"How they\'re made" — paragraph 2', type: "textarea" },
  { name: "wontDoP1", label: '"What we won\'t do" — paragraph', type: "textarea" },
  { name: "whoP1", label: '"Who\'s behind it" — paragraph', type: "textarea" },
];

export default async function AboutContentPage() {
  const c = await getAboutContent();
  const initial = {
    intro: c?.intro ?? "",
    ideaP1: c?.ideaP1 ?? "",
    ideaP2: c?.ideaP2 ?? "",
    howMadeP1: c?.howMadeP1 ?? "",
    howMadeP2: c?.howMadeP2 ?? "",
    wontDoP1: c?.wontDoP1 ?? "",
    whoP1: c?.whoP1 ?? "",
  };

  return (
    <div className="flex flex-col gap-6">
      <h1 className="display text-[40px]">About page</h1>
      <ContentForm fields={FIELDS} initial={initial} action={updateAboutAction} />
    </div>
  );
}
