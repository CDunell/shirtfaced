"use client";

import { useEffect, useState } from "react";
import { useCart } from "@/lib/cart-context";
import { money } from "@/lib/money";
import type { Product, SizeKey } from "@/lib/products";
import { sizeGuide, productPage } from "@/lib/content-data.generated";
import { ProductMedia, mediaCount } from "./ProductMedia";
import {
  IconArrowRight,
  IconCheck,
  IconClose,
  IconHeart,
  IconSmiley,
  IconTruck,
} from "./Icons";

/** Photography first, then a fast path to size + add. No tabs, no clutter. */
export function BuyPanel({ product }: { product: Product }) {
  const { addLine } = useCart();
  const [colourIdx, setColourIdx] = useState(0);
  const [size, setSize] = useState<SizeKey | null>(null);
  const [frame, setFrame] = useState(0);
  const [sheet, setSheet] = useState(false);
  const [fav, setFav] = useState(false);
  const [added, setAdded] = useState(false);

  const garment = product.colours[colourIdx];
  const frames = mediaCount(garment);

  // Switching colourway switches the gallery — reset to its first shot.
  useEffect(() => setFrame(0), [colourIdx]);

  useEffect(() => {
    document.body.style.overflow = sheet ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [sheet]);

  const commit = (chosen: SizeKey) => {
    addLine({
      slug: product.slug,
      name: product.name,
      price: product.price,
      size: chosen,
      colour: garment.name,
      art: product.art,
      body: garment.body,
      ink: garment.ink,
    });
    setSheet(false);
    setAdded(true);
    setTimeout(() => setAdded(false), 1800);
  };

  const onAdd = () => (size ? commit(size) : setSheet(true));

  return (
    <>
      {/* Mobile keeps the full-bleed gallery with the details below. From md up
         that becomes two columns — an unconstrained 4:5 image on a 1920px
         screen is ~2400px tall and pushes every detail below the fold. */}
      <div className="mx-auto md:grid md:max-w-6xl md:grid-cols-2 md:items-start md:gap-10 md:px-6 md:pt-2 lg:gap-14">
      {/* -------- Gallery -------- */}
      <div className="relative md:overflow-hidden md:rounded-[20px]">
        <div
          className="no-scrollbar flex snap-x snap-mandatory overflow-x-auto"
          onScroll={(e) => {
            const el = e.currentTarget;
            setFrame(Math.round(el.scrollLeft / el.clientWidth));
          }}
        >
          {Array.from({ length: frames }).map((_, i) => (
            <div
              key={i}
              className="relative aspect-[4/5] w-full shrink-0 snap-center bg-paper-2"
            >
              <ProductMedia
                product={product}
                garment={garment}
                index={i}
                priority={i === 0}
                sizes="(max-width: 640px) 100vw, 560px"
              />
            </div>
          ))}
        </div>

        {product.isNew && (
          <span className="pointer-events-none absolute top-4 left-4 rounded-[10px] bg-lime px-2.5 py-1 text-[11px] font-bold tracking-wide text-ink uppercase">
            New
          </span>
        )}

        <button
          type="button"
          onClick={() => setFav((f) => !f)}
          aria-label={fav ? "Remove from favourites" : "Save to favourites"}
          aria-pressed={fav}
          className="press absolute top-2.5 right-2.5 grid h-12 w-12 place-items-center rounded-full text-white drop-shadow-[0_1px_3px_rgba(0,0,0,0.5)]"
        >
          <IconHeart
            className={`h-6 w-6 ${fav ? "scale-110 text-coral" : ""}`}
            filled={fav}
          />
        </button>

        {frames > 1 && (
          <div
            className="pointer-events-none absolute bottom-3 left-1/2 flex -translate-x-1/2 gap-1.5"
            aria-hidden
          >
            {Array.from({ length: frames }).map((_, i) => (
              <span
                key={i}
                className={`h-1.5 rounded-full transition-all duration-200 ${
                  i === frame ? "w-4 bg-lime" : "w-1.5 bg-white/60"
                }`}
              />
            ))}
          </div>
        )}
      </div>

      {/* -------- Details -------- */}
      <div className="mx-auto max-w-2xl px-4 pt-6 sm:px-6 md:mx-0 md:px-0 md:pt-0">
        <h1 className="display text-[34px] leading-[0.92]">
          {product.name}
        </h1>

        <div className="mt-2 flex items-center gap-3">
          <p className="text-[20px] font-semibold tabular-nums">
            {money(product.price)}
          </p>
          <span className="text-[13px] text-grey-dark">
            or 4 × {money(product.price / 4)} interest free
          </span>
        </div>


        <p className="mt-4 text-[15px] leading-relaxed text-ink/75">
          {product.description}
        </p>

        {/* Colour */}
        <div className="mt-7">
          <p className="text-[13px] font-semibold tracking-wide uppercase">
            Colour:{" "}
            <span className="text-grey-dark normal-case">{garment.name}</span>
          </p>
          <div className="mt-3 flex gap-3">
            {product.colours.map((c, i) => (
              <button
                key={c.name}
                type="button"
                onClick={() => setColourIdx(i)}
                aria-label={c.name}
                aria-pressed={i === colourIdx}
                className={`press grid h-12 w-12 place-items-center rounded-full border-2 ${
                  i === colourIdx ? "border-ink" : "border-ink/15"
                }`}
              >
                <span
                  className="h-8 w-8 rounded-full border border-black/10"
                  style={{ background: c.swatch }}
                />
              </button>
            ))}
          </div>
        </div>

        {/* Size */}
        <div className="mt-6">
          <div className="flex items-baseline justify-between">
            <p className="text-[13px] font-semibold tracking-wide uppercase">
              Size{size ? <span className="text-grey-dark">: {size}</span> : ""}
            </p>
            <button
              type="button"
              onClick={() => setSheet(true)}
              className="press text-[13px] font-semibold underline underline-offset-4"
            >
              Size guide
            </button>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {product.sizes.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setSize(s)}
                aria-pressed={s === size}
                className={`press h-12 min-w-[56px] rounded-[16px] border px-4 text-[15px] font-semibold ${
                  s === size
                    ? "border-ink bg-lime text-ink"
                    : "border-ink/15 text-ink"
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* Features */}
        <ul className="mt-8 grid grid-cols-2 gap-y-4 border-t border-ink/10 pt-6">
          {[IconSmiley, IconSmiley, IconTruck, IconArrowRight].map((Icon, i) => {
            const { a, b } = productPage.features[i];
            return (
              <li key={a} className="flex items-start gap-2.5">
                <Icon className="mt-0.5 h-5 w-5 shrink-0" strokeWidth={1.8} />
                <span className="text-[13px] leading-tight">
                  {a}
                  <br />
                  <span className="text-grey-dark">{b}</span>
                </span>
              </li>
            );
          })}
        </ul>

        {/* Desktop buys from here; the fixed bar is mobile-only. */}
        <button
          type="button"
          onClick={onAdd}
          className={`press mt-8 hidden h-14 w-full max-w-[340px] rounded-[18px] text-[16px] font-bold md:block ${
            added ? "bg-ink text-lime" : "bg-lime text-ink"
          }`}
        >
          {added ? "Added" : `Add to cart · ${money(product.price)}`}
        </button>
      </div>
      </div>

      {/* -------- Sticky purchase bar: mobile only -------- */}
      <div className="fixed inset-x-0 bottom-0 z-30 border-t border-ink/10 bg-paper/95 px-4 pt-3 pb-[calc(12px+env(safe-area-inset-bottom))] backdrop-blur sm:px-6 md:hidden">
        <div className="mx-auto flex max-w-2xl gap-2">
          <button
            type="button"
            onClick={onAdd}
            className={`press h-14 flex-1 rounded-[18px] text-[16px] font-bold ${
              added ? "bg-ink text-lime" : "bg-lime text-ink"
            }`}
          >
            {added ? (
              <span className="inline-flex items-center gap-2">
                <IconCheck className="h-5 w-5" /> Added
              </span>
            ) : (
              `Add to cart · ${money(product.price)}`
            )}
          </button>
        </div>
      </div>

      {/* -------- Size sheet -------- */}
      {sheet && (
        <div className="fixed inset-0 z-50" role="dialog" aria-modal="true">
          <button
            aria-label="Close size selector"
            onClick={() => setSheet(false)}
            className="absolute inset-0 bg-ink/60"
          />
          <div className="sheet-up absolute inset-x-0 bottom-0 max-h-[85vh] overflow-y-auto rounded-t-[28px] bg-paper px-4 pt-5 pb-[calc(24px+env(safe-area-inset-bottom))] sm:px-6">
            <div className="mb-4 flex items-start justify-between">
              <div>
                <h2 className="display text-[24px]">Select size</h2>
                <p className="text-[14px] text-grey-dark">{product.name}</p>
              </div>
              <button
                type="button"
                onClick={() => setSheet(false)}
                aria-label="Close"
                className="press -mr-2 grid h-12 w-12 place-items-center rounded-[14px]"
              >
                <IconClose className="h-6 w-6" />
              </button>
            </div>

            <ul className="flex flex-col gap-2">
              {product.sizes.map((s) => {
                const active = s === size;
                return (
                  <li key={s}>
                    <button
                      type="button"
                      onClick={() => {
                        setSize(s);
                        commit(s);
                      }}
                      className={`press flex h-[68px] w-full items-center justify-between rounded-[16px] border px-4 text-left ${
                        active ? "border-lime bg-lime/10" : "border-ink/12"
                      }`}
                    >
                      <span className="display text-[22px] w-12">{s}</span>
                      <span className="flex-1 text-[13px] tracking-wide text-grey-dark uppercase">
                        Chest {sizeGuide.chart[s].chest} · Length{" "}
                        {sizeGuide.chart[s].length}
                      </span>
                      {active && (
                        <span className="grid h-7 w-7 place-items-center rounded-full bg-lime">
                          <IconCheck className="h-4 w-4 text-ink" />
                        </span>
                      )}
                    </button>
                  </li>
                );
              })}
            </ul>

            <p className="mt-4 flex items-center gap-2 text-[13px] text-grey-dark">
              <IconSmiley className="h-4 w-4" strokeWidth={1.8} />
              Those are the real measurements — get it right the first time.
              We don&apos;t do wrong-size returns.
            </p>
          </div>
        </div>
      )}
    </>
  );
}
