import Link from "next/link";
import { IconHeart, IconRuler, IconShield, IconSmile, IconMail, IconTruck } from "@/components/Icons";

const CARDS = [
  { title: "SOFT & COMFY", icon: IconHeart, href: "/garment-care" },
  { title: "EASY CARE", icon: IconSmile, href: "/garment-care" },
  { title: "BUILT TO LAST", icon: IconShield, href: "/garment-care" },
  { title: "SAFE STUFF", icon: IconShield, href: "/faq" },
  { title: "SIZES 2–10", icon: IconRuler, href: "/size-guide" },
  { title: "FAST SHIPPING", icon: IconTruck, href: "/shipping" },
];

/** Section J — "PARENTS CORNER" (DESIGN_HANDOFF.md §4.J). Visually quieter
 * than the kid-facing sections above and below it, on purpose. */
export function ParentsCorner() {
  return (
    <section className="bg-grit-lilac/25">
      <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
        <h2 className="display text-[9vw] leading-none sm:text-[26px]">parents corner</h2>
        <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3">
          {CARDS.map((card) => (
            <Link
              key={card.title}
              href={card.href}
              className="press flex flex-col items-center gap-2 rounded-[18px] bg-cream p-4 text-center"
            >
              <card.icon className="h-6 w-6 text-ink/70" />
              <span className="text-[12px] font-extrabold">{card.title}</span>
            </Link>
          ))}
        </div>
        <Link
          href="/contact"
          className="press mt-6 inline-flex items-center gap-2 rounded-full border-2 border-ink/15 px-5 py-3 text-[13px] font-extrabold"
        >
          <IconMail className="h-4 w-4" />
          Questions? Send us a message
        </Link>
      </div>
    </section>
  );
}
