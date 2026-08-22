"use client";

import { useState } from "react";
import Link from "next/link";
import { CREATURES, uiAccentFor } from "@/lib/creatures";
import { IconArrowRight } from "@/components/Icons";

/**
 * Section B — "PICK YOUR WEIRDO" (DESIGN_HANDOFF.md §4.B). Black hero with
 * one oversized creature; the horizontal chooser strip below swaps which
 * creature is shown, its accent, and where "Find your favourite" points.
 */
export function HeroWeirdo() {
  const [activeSlug, setActiveSlug] = useState(CREATURES[0].slug);
  const active = CREATURES.find((c) => c.slug === activeSlug) ?? CREATURES[0];
  const accent = uiAccentFor(active.slug);

  return (
    <section className="bg-ink text-paper">
      <div className="mx-auto max-w-5xl px-4 pt-10 pb-6 sm:px-6 sm:pt-14">
        <div className="grid items-center gap-6 sm:grid-cols-2 sm:gap-4">
          <div>
            <h1 className="display text-[15vw] leading-[0.9] sm:text-[64px]">
              pick your
              <br />
              weirdo!
            </h1>
            <Link
              href={`/products/${active.slug}-tee`}
              className="press mt-6 inline-flex h-14 items-center gap-2 rounded-full px-6 text-[15px] font-extrabold text-ink"
              style={{ background: accent.hex }}
            >
              Find your favourite
              <IconArrowRight className="h-5 w-5" />
            </Link>
          </div>
          <div className="flex items-center justify-center">
            {/* eslint-disable-next-line @next/next/no-img-element -- static SVG, swaps by state */}
            <img
              key={active.slug}
              src={`/curbstamps/creatures/${active.slug}-light.svg`}
              alt={`${active.name} the ${active.animal}`}
              className="fade-rise w-full max-w-[420px]"
            />
          </div>
        </div>
      </div>

      <div className="no-scrollbar flex gap-3 overflow-x-auto px-4 pb-8 sm:px-6">
        {CREATURES.map((c) => {
          const tileAccent = uiAccentFor(c.slug);
          const isActive = c.slug === activeSlug;
          return (
            <button
              key={c.slug}
              type="button"
              onClick={() => setActiveSlug(c.slug)}
              aria-pressed={isActive}
              aria-label={`Show ${c.name} the ${c.animal}`}
              className="press flex shrink-0 flex-col items-center gap-1.5 rounded-2xl px-3 py-2.5"
              style={{ background: isActive ? tileAccent.hex : "rgba(255,250,240,0.08)" }}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={`/curbstamps/creatures/${c.slug}-light.svg`} alt="" aria-hidden="true" className="h-10 w-14 object-contain" style={isActive ? { filter: "brightness(0)" } : undefined} />
              <span className={`text-[11px] font-extrabold ${isActive ? "text-ink" : "text-paper/80"}`}>
                {c.name}
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
