import { getMoreContent } from "@/db/content-queries";
import { ContentForm, type ContentFieldDef } from "@/components/ContentForm";
import { updateMoreAction } from "@/app/content/actions";

const FIELDS: ContentFieldDef[] = [
  { name: "blurbHeading", label: "Footer callout — heading" },
  { name: "blurbSubline", label: "Footer callout — subline" },
];

export default async function MoreContentPage() {
  const c = await getMoreContent();
  const initial = {
    blurbHeading: c?.blurbHeading ?? "",
    blurbSubline: c?.blurbSubline ?? "",
  };

  return (
    <div className="flex flex-col gap-6">
      <h1 className="display text-[40px]">More page</h1>
      <p className="max-w-2xl text-[13px] text-ink/50">
        The link list itself (About, Size guide, Shipping, Returns, Contact)
        isn&apos;t editable here — it&apos;s fixed site navigation, not page
        copy.
      </p>
      <ContentForm fields={FIELDS} initial={initial} action={updateMoreAction} />
    </div>
  );
}
