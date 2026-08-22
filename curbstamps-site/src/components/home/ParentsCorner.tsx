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
      <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 sm:py-14">
        <p className="mb-1 text-[11px] font-black uppercase tracking-[0.16em] text-ink/55">The important stuff</p>
        <h2 className="display text-[10vw] uppercase leading-none sm:text-[32px]">parents corner</h2>

        <div className="mt-5 grid grid-cols-2 gap-2.5 sm:grid-cols-3">
          {CARDS.map((card) => (
            <Link key={card.title} href={card.href} className="press flex min-h-[130px] flex-col items-center justify-center gap-2 rounded-[16px] border border-ink/10 bg-cream p-3 text-center">
              <card.icon className="h-7 w-7 text-ink/75" />
              <span className="text-[11px] font-black uppercase">{card.title}</span>
              <span className="max-w-[14ch] text-[10px] font-bold leading-snug text-ink/60">{card.body}</span>
            </Link>
          ))}
        </div>

        <div className="mt-4 rounded-[16px] border border-ink/10 bg-cream p-4">
          <p className="display text-[20px] uppercase">questions?</p>
          <p className="mt-1 text-[12px] font-bold text-ink/60">We&apos;re here to help.</p>
          <Link href="/contact" className="press mt-3 inline-flex items-center gap-2 rounded-md bg-ink px-4 py-3 text-[11px] font-black uppercase text-paper">
            <IconMail className="h-4 w-4" /> Send us a message
          </Link>
        </div>
      </div>
    </section>
  );
}
