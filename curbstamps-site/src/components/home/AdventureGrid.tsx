import { CREATURES } from "@/lib/creatures";
import { PlaceholderPhoto } from "./PlaceholderPhoto";

const WORDS = [
  { word: "PLAY", label: "Kid mid-play, laughing", creature: CREATURES[1], tone: "var(--color-grit-yellow)" },
  { word: "EXPLORE", label: "Kid exploring outdoors", creature: CREATURES[3], tone: "var(--color-grit-blue)" },
  { word: "MAKE", label: "Kid drawing/making something", creature: CREATURES[6], tone: "var(--color-grit-pink)" },
  { word: "BE", label: "Kid just being a kid, natural", creature: CREATURES[9], tone: "var(--color-grit-green)" },
] as const;

/** Section I — "WEAR YOUR WEIRDO" (DESIGN_HANDOFF.md §4.I). */
export function AdventureGrid() {
  return (
    <section className="bg-paper">
      <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
        <h2 className="display text-[11vw] leading-[0.9] sm:text-[38px]">made for adventures.</h2>
        <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
          {WORDS.map(({ word, label, creature, tone }) => (
            <div key={word} className="flex flex-col items-center gap-2">
              <PlaceholderPhoto label={label} tone={tone} className="aspect-[3/4] w-full" />
              <div className="flex items-center gap-1.5">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={`/curbstamps/creatures/${creature.slug}-dark.svg`} alt="" aria-hidden="true" className="h-5 w-7 object-contain" />
                <span className="text-[12px] font-extrabold tracking-wide">{word}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
