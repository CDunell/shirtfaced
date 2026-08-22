import Link from "next/link";
import { IconHeart, IconRuler, IconShield, IconSmile, IconMail, IconTruck } from "@/components/Icons";

const CARDS = [
  { title: "SOFT & COMFY", body: "Gentle fabrics for happy kids.", icon: IconHeart, href: "/garment-care" },
  { title: "EASY CARE", body: "Wash, wear, repeat.", icon: IconSmile, href: "/garment-care" },
  { title: "BUILT TO LAST", body: "Made strong for play.", icon: IconShield, href: "/garment-care" },
  { title: "SAFE STUFF", body: "No nasties. Just good.", icon: IconShield, href: "/faq" },
  { title: "SIZES 2–10", body: "Room to move. Room to grow.", icon: IconRuler, href: "/size-guide" },
  { title: "FAST SHIPPING", body: "Packed with care. Sent quick.", icon: IconTruck, href: "/shipping" },
];

export function ParentsCorner() {
  return (
    <section className="bg-grit-lilac/35">
      <div className="mx-auto max-w-5xl px-4 py-9 sm:px-6 sm:py-14">
        <p className="mb-1 text-[10px] font-black uppercase tracking-[0.16em] text-ink/50">The important stuff (boring, but good).</p>
        <h2 className="display text-[10.5vw] uppercase leading-none sm:text-[38px]">parents corner</h2>

        <div className="mt-5 grid grid-cols-3 gap-2 sm:gap-3">
          {CARDS.map((card) => (
            <Link key={card.title} href={card.href} className="press flex min-h-[126px] flex-col items-center justify-center gap-2 rounded-[12px] border border-ink/10 bg-cream p-2.5 text-center sm:min-h-[150px] sm:p-4">
              <card.icon className="h-8 w-8 text-ink sm:h-10 sm:w-10" />
              <span className="text-[9px] font-black uppercase leading-tight sm:text-[11px]">{card.title}</span>
              <span className="max-w-[15ch] text-[8px] font-bold leading-snug text-ink/60 sm:text-[10px]">{card.body}</span>
            </Link>
          ))}
        </div>

        <div className="mt-4 grid grid-cols-[1fr_auto] items-center gap-4 rounded-[14px] border border-ink/15 bg-cream p-4 sm:p-5">
          <div>
            <p className="display text-[20px] uppercase">questions?</p>
            <p className="mt-1 text-[11px] font-bold text-ink/60">We&apos;re here to help.</p>
          </div>
          <Link href="/contact" className="press inline-flex items-center gap-2 rounded-md bg-ink px-3 py-3 text-[9px] font-black uppercase text-paper sm:px-4 sm:text-[11px]">
            <IconMail className="h-4 w-4" /> Send us a message
          </Link>
        </div>
      </div>
    </section>
  );
}
