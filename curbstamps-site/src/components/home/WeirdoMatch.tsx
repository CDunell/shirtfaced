"use client";

import { useState } from "react";
import Link from "next/link";
import { creatureMaster, getCreature, uiAccentFor } from "@/lib/creatures";

const OPTIONS = [
  { key: "animals", label: "LOVE ANIMALS", emoji: "🐾", matches: ["grit", "snu", "squib"] },
  { key: "outside", label: "LOVE OUTSIDE", emoji: "🌲", matches: ["twig", "claw", "plod"] },
  { key: "silly", label: "LOVE SILLY", emoji: "☺", matches: ["dreg", "bub", "lod"] },
  { key: "sleeping", label: "LOVE SLEEPING", emoji: "☾", matches: ["bub", "plod", "lod"] },
  { key: "fast", label: "LOVE FAST", emoji: "⚡", matches: ["twig", "claw", "grit"] },
  { key: "snacks", label: "LOVE SNACKS", emoji: "●", matches: ["grub", "blip", "murk"] },
] as const;

export function WeirdoMatch() {
  const [picked, setPicked] = useState<(typeof OPTIONS)[number]["key"] | null>(null);
  const option = OPTIONS.find((o) => o.key === picked);

  return (
    <section className="bg-ink text-paper">
      <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 sm:py-14">
        <p className="mb-1 text-[11px] font-black uppercase tracking-[0.16em] text-paper/55">Pick what you like</p>
        <h2 className="display text-[12vw] uppercase leading-[0.86] sm:text-[44px]">what&apos;s your<br />thing?</h2>

        <div className="mt-6 grid grid-cols-3 gap-2.5 sm:grid-cols-6">
          {OPTIONS.map((o) => {
            const accent = uiAccentFor(o.matches[0]);
            const isActive = picked === o.key;
            return (
              <button
                key={o.key}
                type="button"
                onClick={() => setPicked(o.key)}
                aria-pressed={isActive}
                className="press flex aspect-[0.82] min-h-[110px] flex-col items-center justify-center gap-2 rounded-[14px] border-2 border-paper/20 p-2 text-center text-ink"
                style={{ background: accent.hex, outline: isActive ? "3px solid #fffaf0" : undefined }}
              >
                <span className="text-[26px] leading-none" aria-hidden="true">{o.emoji}</span>
                <span className="text-[10px] font-black leading-tight">{o.label}</span>
              </button>
            );
          })}
        </div>

        <p className="mt-7 text-center text-[14px] font-black uppercase">We&apos;ll find your perfect weirdo!</p>

        {option && (
          <div className="fade-rise mt-5 grid grid-cols-3 gap-2">
            {option.matches.map((slug) => {
              const creature = getCreature(slug);
              if (!creature) return null;
              return (
                <Link key={slug} href={`/products/${slug}-tee`} className="press rounded-[14px] bg-paper p-2 text-center text-ink">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={creatureMaster(slug)} alt={`${creature.name} creature`} className="mx-auto h-16 w-full object-contain brightness-0" />
                  <span className="text-[11px] font-black uppercase">{creature.name}</span>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
