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
      <div className="mx-auto max-w-5xl px-4 pb-5 pt-8 sm:px-6 sm:pt-14">
        <div className="grid items-center gap-4 sm:grid-cols-2 sm:gap-8">
          <div>
            <p className="mb-2 text-[11px] font-black uppercase tracking-[0.16em] text-paper/65">Tap a weirdo. Pick a favourite.</p>
            <h1 className="display text-[16vw] uppercase leading-[0.82] sm:text-[70px]">
              pick your<br />weirdo!
            </h1>
            <Link
              href={`/products/${active.slug}-tee`}
              className="press mt-5 inline-flex min-h-12 items-center rounded-full px-5 py-3 text-[13px] font-black uppercase text-ink"
              style={{ background: accent.hex }}
            >
              Find {active.name}
            </Link>
          </div>

          <div className="flex min-h-[190px] items-center justify-center sm:min-h-[300px]">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              key={active.slug}
              src={`/creatures/${active.slug}-logo.png`}
              alt={`${active.name} creature stamp`}
              className="fade-rise max-h-[230px] w-full max-w-[380px] object-contain brightness-0 invert"
            />
          </div>
        </div>
      </div>

      <div className="border-t border-paper/10 bg-paper py-3 text-ink">
        <div className="no-scrollbar mx-auto flex max-w-5xl gap-2 overflow-x-auto px-3 sm:px-6">
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
                className="press flex w-[66px] shrink-0 flex-col items-center gap-1 rounded-xl px-2 py-2"
                style={{ background: isActive ? tileAccent.hex : "transparent" }}
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={`/creatures/${c.slug}-icon.png`} alt="" aria-hidden="true" className="h-8 w-12 object-contain" />
                <span className="text-[10px] font-black uppercase">{c.name}</span>
              </button>
            );
          })}
        </div>
      </div>
    </section>
  );
}
