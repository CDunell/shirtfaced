import Link from "next/link";
import { CREATURES } from "@/lib/creatures";
import { productsForCreature } from "@/lib/products";
import { ProductCard } from "@/components/ProductCard";
import { IconArrowRight } from "@/components/Icons";

export default function HomePage() {
  const featured = CREATURES.slice(0, 8).map((c) => productsForCreature(c.slug)[0]);

  return (
    <div>
      <section className="mx-auto max-w-5xl px-4 pt-10 pb-8 sm:px-6 sm:pt-16">
        <h1 className="display text-[14vw] leading-[0.88] sm:text-[80px]">
          little creatures.
          <br />
          <span className="text-grit-pink">little clothes.</span>
        </h1>
        <p className="mt-5 max-w-[46ch] text-[17px] leading-relaxed text-ink/70">
          60 little creatures, one at a time. 12 are out in the world so far — tees,
          hoodies and caps for toddlers through teens, screen-printed thick enough to
          survive the yard and the wash and the next kid it gets handed down to.
        </p>
        <div className="mt-7 flex flex-wrap gap-3">
          <Link
            href="/shop"
            className="press inline-flex h-14 items-center gap-2 rounded-full bg-ink pr-5 pl-6 text-[16px] font-extrabold text-paper"
          >
            Shop the collection
            <IconArrowRight className="h-5 w-5" />
          </Link>
          <Link
            href="/about"
            className="press inline-flex h-14 items-center rounded-full border-2 border-ink/15 px-6 text-[16px] font-extrabold"
          >
            Meet the creatures
          </Link>
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
        <div className="flex items-baseline justify-between">
          <h2 className="display text-[26px]">the crew so far</h2>
          <Link href="/shop" className="press text-[13px] font-bold text-grey-dark">
            See all →
          </Link>
        </div>
        <div className="mt-5 grid grid-cols-2 gap-x-4 gap-y-8 sm:grid-cols-4">
          {featured.map((p) => (
            <ProductCard key={p.slug} product={p} />
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
        <div className="grid gap-4 rounded-card border-2 border-ink/10 bg-paper-2/60 p-6 text-center sm:grid-cols-3 sm:text-left">
          <div>
            <p className="display text-[20px]">2T to teen</p>
            <p className="mt-1 text-[14px] text-grey-dark">One size chart, no guessing.</p>
          </div>
          <div>
            <p className="display text-[20px]">Screen-printed</p>
            <p className="mt-1 text-[14px] text-grey-dark">Thick ink, made to survive a kid.</p>
          </div>
          <div>
            <p className="display text-[20px]">60 creatures coming</p>
            <p className="mt-1 text-[14px] text-grey-dark">12 out now, more every drop.</p>
          </div>
        </div>
      </section>
    </div>
  );
}
