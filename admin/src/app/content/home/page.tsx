import { getHomeContent } from "@/db/content-queries";
import { ContentForm, type ContentFieldDef } from "@/components/ContentForm";
import { updateHomeAction } from "@/app/content/actions";

const FIELDS: ContentFieldDef[] = [
  { name: "trust1", label: "Trust bar — item 1" },
  { name: "trust2", label: "Trust bar — item 2" },
  { name: "trust3", label: "Trust bar — item 3" },
  { name: "promoHeading", label: "Promo banner heading", type: "textarea", rows: 2 },
  { name: "promoAlt", label: "Promo banner image alt text", hint: "Not shown on the page — read by screen readers" },
  { name: "newsletterHeading", label: "Newsletter block heading", type: "textarea", rows: 2 },
];

export default async function HomeContentPage() {
  const c = await getHomeContent();
  const initial = {
    trust1: c?.trust1 ?? "",
    trust2: c?.trust2 ?? "",
    trust3: c?.trust3 ?? "",
    promoHeading: c?.promoHeading ?? "",
    promoAlt: c?.promoAlt ?? "",
    newsletterHeading: c?.newsletterHeading ?? "",
  };

  return (
    <div className="flex flex-col gap-6">
      <h1 className="display text-[40px]">Home page</h1>
      <p className="max-w-2xl text-[13px] text-ink/50">
        The rotating hero taglines and collection tile images aren&apos;t
        editable here — they&apos;re tightly paired with specific photos in{" "}
        <code>src/lib/taglines.ts</code> that admin doesn&apos;t manage yet.
      </p>
      <ContentForm fields={FIELDS} initial={initial} action={updateHomeAction} />
    </div>
  );
}
