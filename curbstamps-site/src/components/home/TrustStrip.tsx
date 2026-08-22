import { IconHeart, IconShield, IconReturn, IconSmile } from "@/components/Icons";

const ITEMS = [
  { icon: IconHeart, title: "SOFT STUFF", body: "Feels good." },
  { icon: IconShield, title: "MADE TO PLAY", body: "Built tough." },
  { icon: IconReturn, title: "EASY PEASY", body: "Easy returns." },
  { icon: IconSmile, title: "HAPPY MUMS", body: "We get you." },
];

/** Section D — trust strip (DESIGN_HANDOFF.md §4.D). */
export function TrustStrip() {
  return (
    <section className="bg-ink text-paper">
      <div className="mx-auto grid max-w-5xl grid-cols-2 gap-6 px-4 py-8 sm:grid-cols-4 sm:px-6">
        {ITEMS.map(({ icon: Icon, title, body }) => (
          <div key={title} className="flex flex-col items-center gap-2 text-center sm:items-start sm:text-left">
            <Icon className="h-6 w-6 text-grit-yellow" />
            <p className="text-[13px] font-extrabold tracking-wide">{title}</p>
            <p className="text-[12px] text-paper/70">{body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
