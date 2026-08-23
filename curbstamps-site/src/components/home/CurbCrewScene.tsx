import { CurbWorld } from "./CurbWorld";

export function CurbCrewScene() {
  return (
    <section id="crew" className="bg-paper">
      <div className="mx-auto max-w-5xl px-4 py-9 sm:px-6 sm:py-12">
        <p className="mb-2 text-[10px] font-black uppercase tracking-[0.16em] text-ink/50">World study — creatures removed for now</p>
        <h2 className="display whitespace-nowrap text-[7.7vw] uppercase leading-none sm:text-[48px]">meet the curb crew!</h2>
        <p className="mt-3 max-w-2xl text-[14px] font-bold text-ink/70 sm:text-[16px]">One continuous curb. Scroll through it first—we add the crew only after the world is right.</p>
        <CurbWorld />
      </div>
    </section>
  );
}
