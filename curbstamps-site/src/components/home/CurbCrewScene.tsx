import { CurbWorld } from "./CurbWorld";

export function CurbCrewScene() {
  return (
    <section id="crew" className="bg-paper">
      <div className="mx-auto max-w-5xl px-4 py-9 sm:px-6 sm:py-12">
        <p className="mb-2 text-[10px] font-black uppercase tracking-[0.16em] text-ink/50">A very long street full of weirdos</p>
        <h2 className="display whitespace-nowrap text-[7.7vw] uppercase leading-none sm:text-[48px]">meet the curb crew!</h2>
        <p className="mt-3 max-w-2xl text-[14px] font-bold text-ink/70 sm:text-[16px]">Every weirdo has a place on the Curb. Swipe past their homes, tap one and meet the whole range.</p>
        <CurbWorld />
      </div>
    </section>
  );
}
