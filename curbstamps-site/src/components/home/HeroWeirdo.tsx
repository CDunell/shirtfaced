"use client";

import { useState } from "react";
import Link from "next/link";
import { CREATURES, uiAccentFor } from "@/lib/creatures";

export function HeroWeirdo() {
  const [activeSlug, setActiveSlug] = useState(CREATURES[0].slug);
  const active = CREATURES.find((c) => c.slug === activeSlug) ?? CREATURES[0];
  const accent = uiAccentFor(active.slug);

  return (
    <section className="bg-ink text-paper">
      <div className="mx-auto max-w-5xl px-4 pb-4 pt-6 sm:px-6 sm:pb-10 sm:pt-12">
        <p className="mb-4 text-[9px] font-black uppercase tracking-[0.17em] text-paper/60 sm:text-[11px]">
          Tap a weirdo. Pick a favourite.
        </p>

        <div className="relative pb-2 sm:min-h-[330px] sm:pb-0">
          <div className="relative z-10 w-[58%] sm:w-1/2">
            <h1 className="display uppercase leading-[0.84]">
              <span className="block whitespace-nowrap text-[11.4vw] sm:text-[64px]">pick your</span>
              <span className="block whitespace-nowrap text-[12.2vw] sm:text-[68px]">weirdo!</span>
            </h1>

            <Link
              href={`/products/${active.slug}-tee`}
              className="press mt-6 inline-flex min-h-11 items-center rounded-full px-5 py-3 text-[11px] font-black uppercase text-ink sm:mt-7 sm:min-h-12 sm:px-6 sm:text-[13px]"
              style={{ background: accent.hex }}
            >
              Find your favourite
            </Link>
          </div>

          <div className="absolute right-0 top-7 flex h-[190px] w-[48%] items-center justify-center sm:top-0 sm:h-[260px] sm:w-1/2">
            <span className="absolute right-3 top-1 h-9 w-1 rotate-12 rounded-full bg-grit-green sm:right-9 sm:top-5" />
            <span className="absolute right-10 top-0 h-7 w-1 rotate-45 rounded-full bg-grit-green sm:right-16 sm:top-2" />
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              key={active.slug}
              src={`/creatures/${active.slug}-icon.png`}
              alt={`${active.name} creature`}
              className="fade-rise max-h-[155px] w-full max-w-[205px] object-contain brightness-0 invert sm:max-h-[225px] sm:max-w-[320px]"
            />
          </div>

          <div className="h-[205px] sm:hidden" aria-hidden="true" />
        </div>
      </div>

      <div className="border-t border-paper/10 bg-paper py-2.5 text-ink">
        <div className="no-scrollbar mx-auto flex max-w-5xl gap-1.5 overflow-x-auto px-3 sm:px-6">
          {CREATURES.map((c) => {
            const tileAccent = uiAccentFor(c.slug);
            const isActive = c.slug === activeSlug;
            return (
              <button
                key={c.slug}
                type="button"
                onClick={() => setActiveSlug(c.slug)}
                aria-pressed={isActive}
                aria-label={`Show ${c.name}`}
                className="press flex w-[60px] shrink-0 flex-col items-center gap-1 rounded-[12px] px-1.5 py-2"
                style={{ background: isActive ? tileAccent.hex : "transparent" }}
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={`/creatures/${c.slug}-icon.png`}
                  alt=""
                  aria-hidden="true"
                  className="h-7 w-11 object-contain opacity-90 brightness-0"
                />
                <span className="text-[9px] font-black uppercase">{c.name}</span>
              </button>
            );
          })}
        </div>
      </div>
    </section>
  );
}
