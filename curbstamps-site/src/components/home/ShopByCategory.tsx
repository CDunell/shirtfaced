import Link from "next/link";
import { IconShirt, IconHoodie, IconShorts, IconCap, IconBag } from "@/components/Icons";
import { PlaceholderPhoto } from "./PlaceholderPhoto";

const CATEGORIES = [
  { label: "Tees", href: "/shop?category=tee", icon: IconShirt, soon: false },
  { label: "Hoodies", href: "/shop?category=hoodie", icon: IconHoodie, soon: false },
  { label: "Shorts", href: "/shop", icon: IconShorts, soon: true },
  { label: "Hats", href: "/shop?category=cap", icon: IconCap, soon: false },
  { label: "Accessories", href: "/shop", icon: IconBag, soon: true },
];

/** Section G — "SHOP THE LOOK" (DESIGN_HANDOFF.md §4.G). Shorts and
 * Accessories aren't real SKUs yet (see curbstamps-site/README.md) — shown
 * as coming soon rather than left out, since the handoff lists all five. */
export function ShopByCategory() {
  return (
    <section className="bg-paper-2/50">
      <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
        <div className="grid gap-6 sm:grid-cols-2 sm:items-center">
          <PlaceholderPhoto label="Candid kid outdoors, doodle accents" className="aspect-[4/3]" tone="var(--color-grit-green)" />
          <div>
            <h2 className="display text-[11vw] leading-[0.92] sm:text-[38px]">good days start here.</h2>
            <p className="mt-2 max-w-[36ch] text-[15px] text-ink/70">
              Clothes for little weirdos who do big things.
            </p>
          </div>
        </div>

        <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-5">
          {CATEGORIES.map((cat) => (
            <Link
              key={cat.label}
              href={cat.href}
              className="press relative flex min-h-[88px] flex-col items-center justify-center gap-2 rounded-[20px] bg-cream text-center"
            >
              <cat.icon className="h-7 w-7" />
              <span className="text-[13px] font-extrabold">{cat.label}</span>
              {cat.soon && (
                <span className="absolute top-2 right-2 rounded-full bg-grit-orange px-2 py-0.5 text-[9px] font-extrabold text-ink">
                  Soon
                </span>
              )}
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
