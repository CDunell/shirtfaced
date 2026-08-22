import Link from "next/link";
import { CREATURES } from "@/lib/creatures";
import { PlaceholderPhoto } from "./PlaceholderPhoto";

const WORDS = [
  { word: "PLAY", body: "All day.", label: "Kid mid-play, laughing", creature: CREATURES[1], tone: "var(--color-grit-yellow)" },
  { word: "EXPLORE", body: "New places.", label: "Kid exploring outdoors", creature: CREATURES[3], tone: "var(--color-grit-blue)" },
  { word: "MAKE", body: "Memories.", label: "Kid drawing or making something", creature: CREATURES[6], tone: "var(--color-grit-pink)" },
  { word: "BE", body: "Your weird self.", label: "Kid just being a kid", creature: CREATURES[9], tone: "var(--color-grit-green)" },
] as const;

export function AdventureGrid() {
  return (
    <section className="bg-paper">
      <div className="mx-auto max-w-5xl px-4 py-9 sm:px-6 sm:py-14">
        <p className="mb-1 text-[10px] font-black uppercase tracking-[0.16em] text-ink/50">They go everywhere with you</p>
        <h2 className="display text-[12vw] uppercase leading-[0.84] sm:text-[48px]">made for<br />adventures.</h2>

        <div className="mt-5 grid grid-cols-4 gap-1.5 sm:gap-3">
          {WORDS.map(({ word, label, tone }) => (
            <PlaceholderPhoto key={word} label={label} tone={tone} className="aspect-[0.72] w-full rounded-[12px] sm:rounded-[14px]" />
          ))}
        </div>

        <div className="mt-0 grid grid-cols-4 overflow-hidden rounded-b-[14px] border border-t-0 border-ink/10">
          {WORDS.map(({ word, body, creature }) => (
            <div key={word} className="flex min-h-[92px] flex-col items-center justify-between border-r border-ink/10 bg-cream p-2 text-center last:border-r-0 sm:min-h-[116px] sm:p-3">
              <div>
                <p className="text-[10px] font-black uppercase sm:text-[12px]">{word}</p>
                <p className="mt-0.5 text-[9px] leading-tight text-ink/60 sm:text-[11px]">{body}</p>
              </div>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={`/creatures/${creature.slug}-icon.png`} alt="" aria-hidden="true" className="h-8 w-full object-contain sm:h-10" />
            </div>
          ))}
        </div>

        <div className="mt-5 grid grid-cols-[1fr_auto] items-center gap-4 rounded-[14px] bg-grit-blue/45 p-4">
          <div>
            <p className="display text-[19px] uppercase">new here?</p>
            <p className="mt-1 text-[11px] font-bold text-ink/65">Start with a favourite.</p>
          </div>
          <Link href="/shop" className="press rounded-md bg-ink px-4 py-3 text-[10px] font-black uppercase text-paper">Shop best sellers</Link>
        </div>
      </div>
    </section>
  );
}
