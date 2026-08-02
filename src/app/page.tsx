import Link from "next/link";
import { ProductCard } from "@/components/ProductCard";
import { products } from "@/lib/products";
import {
  IconArrowRight,
  IconLock,
  IconSmiley,
  IconTruck,
} from "@/components/Icons";

const TRUST = [
  { Icon: IconSmiley, top: "designed in aus", bottom: "zero apologies" },
  { Icon: IconTruck, top: "bad decisions", bottom: "ship fast" },
  { Icon: IconLock, top: "secure checkout", bottom: "no judgement" },
  { Icon: IconSmiley, top: "no regrets", bottom: "returns policy" },
];

const COLLECTIONS = [
  { label: "beach bums", tint: "#297bff" },
  { label: "road trip", tint: "#ff6a00" },
  { label: "camp legends", tint: "#c6ff33" },
  { label: "party animals", tint: "#ff3c8e" },
  { label: "skate rats", tint: "#f2f0ed" },
];

export default function Home() {
  const drops = products.filter((p) => p.isNew);

  return (
    <>
      {/* ---------------- Hero ----------------
          Art-directed: the wide banner carries its own typography and only
          works at desktop widths, so mobile gets the product shot with live
          text over it instead. <picture> means exactly one image downloads. */}
      <section className="relative bg-ink text-paper">
        <div className="relative sm:mx-6 sm:mb-6">
          <picture>
            <source
              media="(min-width: 640px)"
              srcSet="/products/hero-good-times.webp"
            />
            {/* eslint-disable-next-line @next/next/no-img-element -- art
                direction needs <source media>, which next/image can't express */}
            <img
              src="/products/hero-street.webp"
              alt="Model in the Good Times Bad Decisions tee on a Sydney back street"
              width={1800}
              height={900}
              fetchPriority="high"
              className="aspect-[3/4] w-full object-cover object-[50%_38%] sm:aspect-[2/1] sm:rounded-[20px]"
            />
          </picture>

          {/* Scrim + live type on mobile only — the desktop banner carries its
              own typography, so overlaying there would double it up. */}
          <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-ink via-ink/80 to-transparent px-4 pt-24 pb-6 sm:hidden">
            <h1 className="display distressed text-[13.5vw] leading-[0.86]">
              good times.
              <br />
              <span className="text-lime">bad decisions.</span>
              <br />
              zero regrets.
            </h1>
            <Link
              href="/shop"
              className="press mt-5 inline-flex h-14 items-center gap-3 rounded-[18px] bg-lime pr-5 pl-6 text-[17px] font-bold text-ink"
            >
              shop the damage
              <IconArrowRight className="h-5 w-5" />
            </Link>
          </div>

          <Link
            href="/shop"
            className="absolute inset-0 hidden sm:block"
            aria-label="Good Times Bad Decisions — new drop, shop now"
          />
        </div>
      </section>

      {/* ---------------- Trust bar ---------------- */}
      <section className="bg-ink text-paper">
        <ul className="mx-auto grid max-w-5xl grid-cols-4 gap-2 px-4 pb-8 sm:px-6">
          {TRUST.map(({ Icon, top, bottom }) => (
            <li key={top} className="flex flex-col items-center gap-2 text-center">
              <Icon className="h-7 w-7 text-lime" strokeWidth={1.8} />
              <span className="text-[11px] leading-tight text-paper/70">
                {top}
                <br />
                {bottom}
              </span>
            </li>
          ))}
        </ul>
      </section>

      {/* ---------------- New drops ---------------- */}
      <section className="mx-auto max-w-5xl px-4 pt-10 sm:px-6">
        <div className="mb-5 flex items-end justify-between">
          <h2 className="display distressed text-[34px]">new drops</h2>
          <Link
            href="/shop?f=new"
            className="press flex items-center gap-1.5 pb-1 text-[15px] font-semibold"
          >
            see all
            <IconArrowRight className="h-4 w-4" />
          </Link>
        </div>

        <div className="grid grid-cols-2 gap-x-4 gap-y-8 sm:grid-cols-3">
          {drops.map((p, i) => (
            <ProductCard key={p.slug} product={p} priority={i < 2} />
          ))}
        </div>
      </section>

      {/* ---------------- Promo ---------------- */}
      <section className="mx-auto mt-12 max-w-5xl px-4 sm:px-6">
        <div className="relative overflow-hidden rounded-[20px] bg-pink px-6 py-9">
          <h2 className="display distressed max-w-[9ch] text-[34px] leading-[0.92] text-ink sm:text-[46px]">
            dress like you&apos;ve got better plans.
          </h2>
          <Link
            href="/shop"
            className="press mt-6 inline-flex h-12 items-center gap-2.5 rounded-[18px] bg-ink pr-4 pl-5 text-[15px] font-bold text-paper"
          >
            shop now
            <IconArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      {/* ---------------- Collections ---------------- */}
      <section className="mt-12">
        <h2 className="display distressed mx-auto mb-5 max-w-5xl px-4 text-[34px] sm:px-6">
          collections
        </h2>
        <ul className="no-scrollbar flex snap-x snap-mandatory gap-4 overflow-x-auto px-4 pb-2 sm:px-6">
          {COLLECTIONS.map((c) => (
            <li key={c.label} className="snap-start">
              <Link
                href="/shop"
                className="press flex w-[92px] flex-col items-center gap-2.5"
              >
                <span
                  className="grid h-[84px] w-[84px] place-items-center rounded-full border-2 border-ink/10"
                  style={{ background: c.tint }}
                >
                  <IconSmiley className="h-9 w-9 text-ink" strokeWidth={1.8} />
                </span>
                <span className="text-center text-[13px] leading-tight font-medium">
                  {c.label}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      {/* ---------------- Newsletter ---------------- */}
      <section className="mx-auto mt-12 max-w-5xl px-4 sm:px-6">
        <div className="rounded-[20px] bg-lime px-6 py-8">
          <h2 className="display distressed max-w-[13ch] text-[30px] leading-[0.95] text-ink">
            we promise fewer emails than your ex.
          </h2>
          <form className="mt-6 flex gap-2" action="/shop">
            <label htmlFor="email" className="sr-only">
              Email address
            </label>
            <input
              id="email"
              type="email"
              inputMode="email"
              autoComplete="email"
              placeholder="your@email.com"
              className="h-14 min-w-0 flex-1 rounded-[16px] bg-paper px-4 text-[16px] placeholder:text-grey"
            />
            <button
              type="submit"
              aria-label="Subscribe"
              className="press grid h-14 w-14 shrink-0 place-items-center rounded-[16px] bg-ink text-paper"
            >
              <IconArrowRight className="h-5 w-5" />
            </button>
          </form>
          <p className="mt-3 text-[13px] text-ink/65">
            new drops, dumb jokes, the occasional life update.
          </p>
        </div>
      </section>

      {/* ---------------- Brand line ---------------- */}
      <section className="mt-12 overflow-hidden bg-ink py-5">
        <div className="marquee-track flex w-max">
          {[0, 1].map((dup) => (
            <span key={dup} className="flex shrink-0" aria-hidden={dup === 1}>
              {Array.from({ length: 4 }).map((_, i) => (
                <span
                  key={i}
                  className="display px-5 text-[26px] whitespace-nowrap text-paper"
                >
                  good times. <span className="text-lime">bad decisions.</span>{" "}
                  zero regrets.
                </span>
              ))}
            </span>
          ))}
        </div>
      </section>
    </>
  );
}
