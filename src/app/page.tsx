import Link from "next/link";
import { ProductCard } from "@/components/ProductCard";
import { products } from "@/lib/products";
import {
  LINE_ONE,
  LINE_ONE_SIZE,
  LINE_THREE,
  LINE_THREE_SIZE,
  TAGLINES,
} from "@/lib/taglines";
import { IconArrowRight } from "@/components/Icons";

/* One line, no icons — the old four-column version wrapped to uneven heights
   and repeated its icons. But clean shouldn't mean neutered: each claim still
   has to sound like us. Nothing here jokes about whether checkout is actually
   secure or whether returns actually work; the attitude sits on the brand's
   side of the promise, not the customer's risk. */
const TRUST = ["Designed in Aus", "Zero apologies", "Returns easy as"];

/* Photography carries these, not colour. Accents stay reserved for the things
   that actually need emphasis: primary CTA, active nav, NEW, cart count. */
const COLLECTIONS = [
  { label: "after dark", img: "/products/good-times-1.webp" },
  { label: "send it", img: "/products/send-it-2.webp" },
  { label: "warm nights", img: "/products/cold-beer-1.webp" },
  { label: "street", img: "/products/hero-street.webp" },
];

export default function Home() {
  const drops = products.filter((p) => p.isNew);

  return (
    <>
      {/* ---------------- Hero ----------------
          Full bleed: the photograph runs edge to edge at every width. The type
          sits in the normal page column inside it, so it lines up with
          everything below rather than floating.

          Line and paired photo are chosen before paint by the inline script in
          layout.tsx, which sets data-tag on <html>; CSS then reveals one line
          and paints one background. All six lines are in the DOM but hidden
          with display:none, which keeps them from screen readers too.

          Photography here is placeholder — product shots standing in until
          real hero frames exist. */}
      <section className="relative bg-ink text-paper">
        <div className="hero-img relative aspect-[3/4] w-full bg-ink bg-cover sm:aspect-auto sm:h-[70vh] sm:max-h-[720px] sm:min-h-[460px]">
          <div className="absolute inset-0 bg-gradient-to-t from-ink from-10% via-ink/70 via-45% to-transparent to-90%" />

          <div className="absolute inset-x-0 bottom-0">
            <div className="mx-auto max-w-6xl px-4 pb-7 sm:px-6 sm:pb-12">
              <div className="tagline-box w-full sm:max-w-[46%]">
                <h1 className="display leading-[0.86] whitespace-nowrap">
                  <span className="block" style={{ fontSize: `${LINE_ONE_SIZE}cqw` }}>
                    {LINE_ONE}
                  </span>

                  {/* One of these six is revealed by CSS. */}
                  <span className="block text-lime">
                    {TAGLINES.map((t, i) => (
                      <span
                        key={t.line}
                        className={`tl tl-${i}`}
                        style={{ fontSize: `${t.size}cqw` }}
                      >
                        {t.line}
                      </span>
                    ))}
                  </span>

                  <span className="block" style={{ fontSize: `${LINE_THREE_SIZE}cqw` }}>
                    {LINE_THREE}
                  </span>
                </h1>
              </div>

              <Link
                href="/shop"
                className="press mt-5 inline-flex h-14 items-center gap-3 rounded-[18px] bg-paper pr-5 pl-6 text-[17px] font-bold text-ink"
              >
                shop the damage
                <IconArrowRight className="h-5 w-5" />
              </Link>
            </div>
          </div>

          <Link href="/shop" className="absolute inset-0 -z-10" aria-label="Shop the new drop" />
        </div>
      </section>

      {/* ---------------- Trust bar ---------------- */}
      <section className="bg-ink text-paper">
        <ul className="mx-auto flex max-w-6xl items-center justify-center gap-x-2 px-4 pb-7 text-[11px] tracking-wide text-paper/45 uppercase sm:gap-x-3 sm:text-[12px]">
          {TRUST.map((t, i) => (
            <li key={t} className="flex items-center gap-x-2 sm:gap-x-3">
              {i > 0 && <span aria-hidden>&middot;</span>}
              {t}
            </li>
          ))}
        </ul>
      </section>

      {/* ---------------- New drops ---------------- */}
      <section className="mx-auto max-w-6xl px-4 pt-10 sm:px-6">
        <div className="mb-5 flex items-end justify-between">
          <h2 className="display text-[34px]">new drops</h2>
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
      <section className="mx-auto mt-12 max-w-6xl px-4 sm:px-6">
        <Link
          href="/shop"
          className="press relative block overflow-hidden rounded-[20px]"
        >
          {/* eslint-disable-next-line @next/next/no-img-element -- static export, no loader */}
          <img
            src="/products/send-it-1.webp"
            alt="Model wearing the Send It Club tee in vintage white"
            width={1000}
            height={1250}
            loading="lazy"
            className="aspect-[4/3] w-full object-cover object-[50%_28%] sm:aspect-[21/9]"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-ink via-ink/70 to-ink/10" />
          <div className="absolute inset-0 bg-gradient-to-r from-ink/80 via-transparent to-transparent" />
          <div className="absolute inset-x-0 bottom-0 p-6">
            <h2 className="display max-w-[10ch] text-[32px] leading-[0.92] text-paper sm:text-[44px]">
              dress like you&apos;ve got better plans.
            </h2>
            <span className="mt-4 inline-flex h-12 items-center gap-2.5 rounded-[18px] bg-paper pr-4 pl-5 text-[15px] font-bold text-ink">
              shop now
              <IconArrowRight className="h-4 w-4" />
            </span>
          </div>
        </Link>
      </section>

      {/* ---------------- Collections ---------------- */}
      <section className="mt-12">
        <h2 className="display mx-auto mb-5 max-w-6xl px-4 text-[34px] sm:px-6">
          collections
        </h2>
        <ul className="no-scrollbar mx-auto flex max-w-6xl snap-x snap-mandatory gap-3 overflow-x-auto px-4 pb-2 sm:gap-4 sm:px-6">
          {COLLECTIONS.map((c) => (
            <li key={c.label} className="snap-start shrink-0">
              <Link
                href="/shop"
                className="press relative block h-[188px] w-[142px] overflow-hidden rounded-[20px] sm:h-[300px] sm:w-[228px]"
              >
                {/* eslint-disable-next-line @next/next/no-img-element -- static export, no loader */}
                <img
                  src={c.img}
                  alt=""
                  loading="lazy"
                  className="h-full w-full object-cover"
                />
                <span className="absolute inset-0 bg-gradient-to-t from-ink/85 via-ink/10 to-transparent" />
                <span className="display absolute inset-x-0 bottom-0 p-3 text-[17px] leading-tight text-paper sm:p-4 sm:text-[21px]">
                  {c.label}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      {/* ---------------- Newsletter ---------------- */}
      <section className="mx-auto mt-12 max-w-6xl px-4 sm:px-6">
        <div className="rounded-[20px] bg-ink px-6 py-8 text-paper">
          <h2 className="display max-w-[13ch] text-[30px] leading-[0.95]">
            we promise fewer emails than your ex.
          </h2>
          <form className="mt-6 flex max-w-md gap-2" action="/shop">
            <label htmlFor="email" className="sr-only">
              Email address
            </label>
            <input
              id="email"
              type="email"
              inputMode="email"
              autoComplete="email"
              placeholder="your@email.com"
              className="h-14 min-w-0 flex-1 rounded-[16px] border border-paper/15 bg-transparent px-4 text-[16px] text-paper placeholder:text-paper/40"
            />
            <button
              type="submit"
              aria-label="Subscribe"
              className="press grid h-14 w-14 shrink-0 place-items-center rounded-[16px] bg-paper text-ink"
            >
              <IconArrowRight className="h-5 w-5" />
            </button>
          </form>
          <p className="mt-3 text-[13px] text-paper/50">
            new drops, dumb jokes, the occasional life update.
          </p>
        </div>
      </section>

      {/* ---------------- Brand line ----------------
          Cycles all six rather than repeating one — same build, and it shows
          the whole rotation to anyone who scrolls. */}
      <section className="mt-12 overflow-hidden bg-ink py-5">
        <div className="marquee-track flex w-max">
          {[0, 1].map((dup) => (
            <span key={dup} className="flex shrink-0" aria-hidden={dup === 1}>
              {TAGLINES.map((t) => (
                <span
                  key={t.line}
                  className="display px-5 text-[26px] whitespace-nowrap text-paper"
                >
                  {LINE_ONE} <span className="text-lime">{t.line}</span>{" "}
                  {LINE_THREE}
                </span>
              ))}
            </span>
          ))}
        </div>
      </section>
    </>
  );
}
