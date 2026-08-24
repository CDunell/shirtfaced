"use client";

import Link from "next/link";
import { useState } from "react";
import { CREATURES, creatureMaster, uiAccentFor } from "@/lib/creatures";

const START = [0, 18, 31];
function nextRound(previous: number[]) {
  const first = (previous[0] + 7) % CREATURES.length;
  return [first, (first + 11) % CREATURES.length, (first + 23) % CREATURES.length];
}

export function FindWeirdo() {
  const [round, setRound] = useState(START);
  const [picked, setPicked] = useState<number | null>(null);
  const target = CREATURES[round[0]];
  const won = picked === round[0];
  function playAgain() { setRound(nextRound(round)); setPicked(null); }
  return (
    <section className="bg-ink px-4 py-10 text-paper sm:px-6 sm:py-14">
      <div className="mx-auto max-w-5xl">
        <div className="text-center">
          <p className="mb-2 text-[11px] font-black uppercase tracking-[0.18em] text-paper/60">Weirdo match</p>
          <h2 className="display text-[12vw] uppercase leading-[0.88] sm:text-[54px]">which one is<br /><span className="text-grit-green">{target.name}?</span></h2>
          <p className="mt-3 text-[13px] font-bold text-paper/70">Tap the right creature.</p>
        </div>
        <div className="mt-7 grid grid-cols-3 gap-2 sm:mx-auto sm:max-w-2xl sm:gap-4">
          {round.map((index) => {
            const creature = CREATURES[index], selected = picked === index, correct = index === round[0];
            return <button key={creature.slug} type="button" onClick={() => setPicked(index)} disabled={won} aria-label={`Choose ${creature.name}`} className={`press flex min-h-[150px] flex-col items-center justify-between rounded-[22px] border-2 p-3 text-ink transition sm:min-h-[190px] sm:p-5 ${selected && correct ? "border-grit-green bg-grit-green" : selected ? "border-[#ff6f9c] bg-[#ff6f9c]" : "border-paper bg-paper"}`}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={creatureMaster(creature.slug)} alt="" className="h-24 w-full object-contain brightness-0 sm:h-32" />
              <span className="display text-[18px] uppercase leading-none sm:text-[22px]">{picked === null ? "?" : creature.name}</span>
            </button>;
          })}
        </div>
        <div aria-live="polite" className="mt-6 min-h-[68px] text-center">
          {picked !== null && !won && <p className="display text-[22px] uppercase text-[#ff9cbc]">nope — try again!</p>}
          {won && <div className="badge-pop flex flex-wrap justify-center gap-3">
            <button type="button" onClick={playAgain} className="press min-h-12 rounded-md bg-grit-green px-5 py-3 text-[12px] font-black uppercase text-ink">Next weirdo</button>
            <Link href={`/products/tee?design=${target.slug}`} className="press min-h-12 rounded-md border-2 border-paper px-5 py-3 text-[12px] font-black uppercase text-paper">Shop {target.name}</Link>
          </div>}
        </div>
        <div className="mt-5 flex items-center justify-center gap-2 text-[10px] font-black uppercase tracking-[0.12em] text-paper/55">
          <span className="h-2.5 w-2.5 rounded-full" style={{ background: uiAccentFor(target.slug).hex }} />{CREATURES.length} weirdos in the crew
        </div>
      </div>
    </section>
  );
}
