"use client";

import Link from "next/link";
import { useState } from "react";
import { CREATURES } from "@/lib/creatures";

const FIELD = [2, 7, 4, 9, 1, 6, 3, 8, 5, 10, 0, 11, 4, 2, 8, 7, 3, 10, 5, 1, 6, 9, 11, 4];

export function FindWeirdo() {
  const target = CREATURES[0];
  const [found, setFound] = useState(false);

  return (
    <section className="bg-ink text-paper">
      <div className="mx-auto max-w-5xl">
        <div className="px-4 pb-6 pt-9 text-center sm:px-6 sm:pt-12">
          <p className="mb-2 text-[10px] font-black uppercase tracking-[0.18em] text-paper/55">Can you spot them all?</p>
          <h2 className="display text-[13vw] uppercase leading-[0.84] sm:text-[52px]">can you<br />find <span className="text-grit-green">{target.name}?</span></h2>
        </div>

        <div className="relative overflow-hidden border-y border-paper/15 bg-paper px-4 py-5 text-ink">
          <div className="grid grid-cols-6 gap-x-3 gap-y-5">
            {FIELD.map((index, i) => {
              const c = CREATURES[index % CREATURES.length];
              const isTarget = i === 10;
              return (
                <button
                  key={`${c.slug}-${i}`}
                  type="button"
                  disabled={!isTarget}
                  onClick={() => setFound(true)}
                  aria-label={isTarget ? `Found ${target.name}` : undefined}
                  className={`press flex aspect-square items-center justify-center rounded-full disabled:cursor-default ${found && isTarget ? "badge-pop bg-grit-green/70" : ""}`}
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={`/creatures/${c.slug}-icon.png`} alt="" aria-hidden="true" className="h-9 w-full object-contain brightness-0" />
                </button>
              );
            })}
          </div>
          <div className="pointer-events-none absolute inset-x-0 bottom-0 h-8 bg-[linear-gradient(8deg,transparent_0_42%,rgba(28,26,23,.08)_43%_48%,transparent_49%)]" />
        </div>

        <div aria-live="polite" className="grid grid-cols-[1fr_auto] items-center gap-5 px-4 py-7 sm:px-6">
          <div>
            <p className="display text-[24px] uppercase leading-none">{found ? "found one!" : `find ${target.name}!`}</p>
            <p className="mt-1 text-[12px] font-bold text-paper/65">{found ? `That's ${target.name}.` : "Tap the matching weirdo."}</p>
            {found && <Link href={`/products/${target.slug}-tee`} className="press mt-4 inline-flex min-h-11 items-center rounded-md bg-grit-green px-4 py-3 text-[11px] font-black uppercase text-ink">See {target.name}&apos;s stuff</Link>}
          </div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={`/creatures/${target.slug}-icon.png`} alt={`${target.name} creature`} className="h-24 w-32 object-contain brightness-0 invert" />
        </div>
      </div>
    </section>
  );
}
