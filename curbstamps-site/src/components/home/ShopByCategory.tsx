import Link from "next/link";
import { IconShirt, IconHoodie, IconShorts, IconCap, IconBag } from "@/components/Icons";
import { PlaceholderPhoto } from "./PlaceholderPhoto";

const CATEGORIES = [
  { label: "Tees", href: "/shop?category=tee", icon: IconShirt, tone: "#d8ef6d" },
  { label: "Hoodies", href: "/shop?category=hoodie", icon: IconHoodie, tone: "#b9ddf3" },
  { label: "Shorts", href: "/shop", icon: IconShorts, tone: "#f8b3c6" },
  { label: "Hats", href: "/shop?category=cap", icon: IconCap, tone: "#ffd45c" },
  { label: "Accessories", href: "/shop", icon: IconBag, tone: "#cabcf3" },
];

export function ShopByCategory() {
  return (
    <section className="bg-paper">
      <div className="mx-auto max-w-5xl px-4 py-9 sm:px-6 sm:py-12">
        <div className="grid gap-5 sm:grid-cols-2 sm:items-center">
          <div>
            <p className="mb-1 text-[11px] font-black uppercase tracking-[0.16em] text-ink/55">Made for play. Loved all day.</p>
            <h2 className="display text-[12vw] uppercase leading-[0.86] sm:text-[46px]">good days<br />start here.</h2>
            <p className="mt-3 max-w-[28ch] text-[14px] font-bold text-ink/70">Clothes for little weirdos who do big things.</p>
            <div className="mt-4 flex gap-2">
              <Link href="/shop?category=tee" className="press rounded-md bg-ink px-4 py-3 text-[11px] font-black uppercase text-paper">Shop tees</Link>
              <Link href="/shop?category=hoodie" className="press rounded-md bg-ink px-4 py-3 text-[11px] font-black uppercase text-paper">Shop hoodies</Link>
            </div>
          </div>
          <PlaceholderPhoto label="Happy kid running outside" className="aspect-[0.92] w-full rounded-[18px]" tone="var(--color-grit-yellow)" />
        </div>

        <div className="mt-7 grid grid-cols-5 gap-2">
          {CATEGORIES.map((cat) => (
            <Link key={cat.label} href={cat.href} className="press flex min-w-0 flex-col items-center gap-2 text-center">
              <span className="flex aspect-square w-full items-center justify-center rounded-full border-2 border-ink/10" style={{ background: cat.tone }}>
                <cat.icon className="h-6 w-6" />
              </span>
              <span className="text-[9px] font-black uppercase leading-tight sm:text-[11px]">{cat.label}</span>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
