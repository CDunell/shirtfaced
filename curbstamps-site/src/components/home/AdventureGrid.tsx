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
      <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 sm:py-14">
        <p className="mb-1 text-[11px] font-black uppercase tracking-[0.16em] text-ink/55">They go everywhere with you</p>
        <h2 className="display text-[12vw] uppercase leading-[0.86] sm:text-[44px]">made for<br />adventures.</h2>

        <div className="mt-5 grid grid-cols-3 gap-2 sm:grid-cols-4 sm:gap-4">
          {WORDS.slice(0, 3).map(({ word, label, tone }) => (
            <PlaceholderPhoto key={word} label={label} tone={tone} className="aspect-[0.78] w-full rounded-[14px]" />
          ))}
        </div>

        <div className="mt-5 divide-y divide-ink/15 border-y border-ink/15">
          {WORDS.map(({ word, body, creature }) => (
            <div key={word} className="flex items-center gap-3 py-3">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={`/creatures/${creature.slug}-icon.png`} alt="" aria-hidden="true" className="h-9 w-12 object-contain" />
              <div>
                <p className="text-[13px] font-black uppercase">{word}</p>
                <p className="text-[12px] text-ink/65">{body}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
