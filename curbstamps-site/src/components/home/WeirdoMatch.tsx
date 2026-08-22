"use client";

import { useState } from "react";
import Link from "next/link";
import { getCreature, uiAccentFor } from "@/lib/creatures";
import { IconHeart, IconShield, IconSmile, IconArrowRight } from "@/components/Icons";

/**
 * Section H — "WEIRDO MATCH" (DESIGN_HANDOFF.md §4.H): a six-button picker,
 * not a quiz. Each option maps to three creatures by personality fit — a
 * judgement call made here, not derived from any tagging data that exists
 * yet (there is no "vibe" field on Creature).
 */
const OPTIONS = [
  { key: "animals", label: "LOVE ANIMALS", icon: IconSmile, matches: ["grit", "snu", "squib"] },
  { key: "outside", label: "LOVE OUTSIDE", icon: IconShield, matches: ["twig", "claw", "plod"] },
  { key: "silly", label: "LOVE SILLY", icon: IconHeart, matches: ["dreg", "bub", "lod"] },
  { key: "sleeping", label: "LOVE SLEEPING", icon: IconSmile, matches: ["bub", "plod", "lod"] },
  { key: "fast", label: "LOVE FAST", icon: IconShield, matches: ["twig", "claw", "grit"] },
  { key: "snacks", label: "LOVE SNACKS", icon: IconHeart, matches: ["grub", "blip", "murk"] },
] as const;

export function WeirdoMatch() {
  const [picked, setPicked] = useState<(typeof OPTIONS)[number]["key"] | null>(null);
  const option = OPTIONS.find((o) => o.key === picked);

  return (
    <section className="bg-ink text-paper">
      <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
        <h2 className="display text-[11vw] leading-[0.9] sm:text-[38px]">what&apos;s your thing?</h2>

        <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3">
          {OPTIONS.map((o) => {
            const accent = uiAccentFor(o.matches[0]);
            const isActive = picked === o.key;
            return (
              <button
                key={o.key}
                type="button"
                onClick={() => setPicked(o.key)}
                aria-pressed={isActive}
                className="press flex min-h-[92px] flex-col items-center justify-center gap-2 rounded-[20px] text-center text-ink"
                style={{ background: accent.hex, outline: isActive ? "3px solid var(--color-paper)" : undefined }}
              >
                <o.icon className="h-6 w-6" />
                <span className="text-[13px] font-extrabold">{o.label}</span>
              </button>
            );
          })}
        </div>

        {option && (
          <div className="fade-rise mt-8 rounded-[22px] bg-paper/10 p-5">
            <p className="text-[13px] font-bold text-paper/70">Good pick. Try these:</p>
            <div className="mt-4 grid grid-cols-3 gap-3">
              {option.matches.map((slug) => {
                const creature = getCreature(slug);
                if (!creature) return null;
                return (
                  <Link
                    key={slug}
                    href={`/products/${slug}-tee`}
                    className="press flex flex-col items-center gap-2 rounded-[16px] bg-paper p-3 text-ink"
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={`/curbstamps/creatures/${slug}-dark.svg`} alt="" aria-hidden="true" className="h-10 w-full object-contain" />
                    <span className="flex items-center gap-1 text-[12px] font-extrabold">
                      {creature.name} <IconArrowRight className="h-3 w-3" />
                    </span>
                  </Link>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
