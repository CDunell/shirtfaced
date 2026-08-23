import Link from "next/link";
import { IconShirt, IconHoodie, IconShorts, IconCap, IconBag } from "@/components/Icons";
import { PlaceholderPhoto } from "./PlaceholderPhoto";
import type { HomepagePhoto } from "@/lib/homepage-photos";

const CATEGORIES = [
  { label: "Tees", href: "/shop?category=tee", icon: IconShirt, tone: "#d8ef6d" },
  { label: "Hoodies", href: "/shop?category=hoodie", icon: IconHoodie, tone: "#b9ddf3" },
  { label: "Crewnecks", href: "/shop?category=crewneck", icon: IconShorts, tone: "#f8b3c6" },
  { label: "Bucket Hats", href: "/shop?category=bucket-hat", icon: IconCap, tone: "#ffd45c" },
  { label: "Accessories", href: "/shop", icon: IconBag, tone: "#cabcf3" },
];

export function ShopByCategory({ photo }: { photo?: HomepagePhoto }) {
  return (
    <section className="bg-paper">
      <div className="mx-auto max-w-5xl px-4 py-9 sm:px-6 sm:py-12">
        <div className="grid grid-cols-[.9fr_1.1fr] items-center gap-4 sm:grid-cols-2 sm:gap-6">
          <div>
            <p className="mb-1 text-[11px] font-black uppercase tracking-[0.12em] text-ink/50">Made for play. Loved all day.</p>
            <h2 className="display text-[11vw] uppercase leading-[0.84] sm:text-[48px]">good days<br />start here.</h2>
            <p className="mt-3 max-w-[22ch] text-[13px] font-bold leading-snug text-ink/70 sm:text-[14px]">Clothes for little weirdos who do big things.</p>
            <div className="mt-4 flex flex-col items-start gap-2 sm:flex-row">
              <Link href="/shop?category=tee" className="press inline-flex min-h-11 items-center rounded-md bg-ink px-3 py-2.5 text-[11px] font-black uppercase text-paper sm:px-4 sm:py-3">Shop tees</Link>
              <Link href="/shop?category=hoodie" className="press inline-flex min-h-11 items-center rounded-md bg-ink px-3 py-2.5 text-[11px] font-black uppercase text-paper sm:px-4 sm:py-3">Shop hoodies</Link>
            </div>
          </div>
          {photo ? (
            // eslint-disable-next-line @next/next/no-img-element -- static homepage photo, no next/image benefit
            <img src={photo.src} alt={photo.alt} className="aspect-[0.88] w-full rounded-[16px] object-cover" />
          ) : (
            <PlaceholderPhoto label="Happy kid running outside in Curb Stamps tee" className="aspect-[0.88] w-full rounded-[16px]" tone="var(--color-grit-yellow)" />
          )}
        </div>

        <div className="mt-6 grid grid-cols-5 gap-2 border-t border-ink/10 pt-4">
          {CATEGORIES.map((cat) => (
            <Link key={cat.label} href={cat.href} className="press flex min-w-0 flex-col items-center gap-2 text-center">
              <span className="flex aspect-square w-full items-center justify-center rounded-full" style={{ background: cat.tone }}>
                <cat.icon className="h-5 w-5 sm:h-6 sm:w-6" />
              </span>
              <span className="text-[9px] font-black uppercase leading-tight sm:text-[11px]">{cat.label}</span>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
