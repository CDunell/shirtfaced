import type { Metadata } from "next";
import { PlayOnTheCurb } from "@/components/play/PlayOnTheCurb";

export const metadata: Metadata = {
  title: "Play on the Curb | Curb Stamps",
  description: "Make a creature picture, hear the weirdos and try today's tiny mission.",
};

export default function PlayPage() {
  return (
    <main>
      <header className="bg-paper px-4 py-10 sm:px-6 sm:py-14">
        <div className="mx-auto max-w-5xl">
          <p className="mb-2 text-[11px] font-black uppercase tracking-[0.15em] text-ink/55">Welcome to the Curb</p>
          <h1 className="display text-[17vw] uppercase sm:text-[92px]">come play!</h1>
          <p className="mt-3 max-w-xl text-[17px] font-bold sm:text-[20px]">Make pictures, press noisy creatures and do one very small, very important thing.</p>
        </div>
      </header>
      <PlayOnTheCurb />
    </main>
  );
}
