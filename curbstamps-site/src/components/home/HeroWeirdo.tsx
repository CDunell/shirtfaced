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
      <div className="mx-auto max-w-5xl px-4 pb-6 pt-7 sm:px-6 sm:pb-10 sm:pt-12">
        <div className="grid grid-cols-[1.05fr_.95fr] items-center gap-2 sm:grid-cols-2 sm:gap-8">
          <div className="relative z-10">
            <p className="mb-2 text-[9px] font-black uppercase tracking-[0.17em] text-paper/60 sm:text-[11px]">Tap a weirdo. Pick a favourite.</p>
            <h1 className="display text-[13.5vw] uppercase leading-[0.82] sm:text-[70px]">
              pick your<br />weirdo!
            </h1>
            <Link
              href={`/products/${active.slug}-tee`}
              className="press mt-4 inline-flex min-h-10 items-center rounded-full px-4 py-2.5 text-[11px] font-black uppercase text-ink sm:mt-5 sm:min-h-12 sm:px-5 sm:py-3 sm:text-[13px]"
              style={{ background: accent.hex }}
            >
              Find your favourite
            </Link>
          </div>

          <div className="relative flex min-h-[180px] items-center justify-center sm:min-h-[300px]">
            <span className="absolute right-1 top-3 h-8 w-1 rotate-12 rounded-full bg-grit-green sm:right-8 sm:top-4" />
            <span className="absolute right-7 top-0 h-6 w-1 rotate-45 rounded-full bg-grit-green sm:right-14" />
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              key={active.slug}
              src={`/creatures/${active.slug}-icon.png`}
              alt={`${active.name} creature`}
              className="fade-rise max-h-[145px] w-full max-w-[190px] object-contain brightness-0 invert sm:max-h-[220px] sm:max-w-[310px]"
            />
          </div>
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
                <img src={`/creatures/${c.slug}-icon.png`} alt="" aria-hidden="true" className="h-7 w-11 object-contain opacity-90" />
                <span className="text-[9px] font-black uppercase">{c.name}</span>
              </button>
            );
          })}
        </div>
      </div>
    </section>
  );
}
