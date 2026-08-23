export default function WorldLabPage() {
  return (
    <main className="min-h-screen bg-paper px-4 py-8 text-ink">
      <div className="mx-auto max-w-6xl">
        <p className="text-xs font-black uppercase tracking-[0.18em]">World animation study 01</p>
        <h1 className="display mt-3 text-4xl sm:text-6xl">Pip lives in the pipe.</h1>
        <p className="mt-4 max-w-2xl text-base font-bold text-grey-dark">
          One creature, one hiding place, one complete interaction. The homepage remains untouched.
        </p>

        <div className="pip-lab-frame mt-8" aria-label="Pip emerging from a stormwater pipe">
          <div className="pip-lab-world">
            <img
              src="/curbstamps/world/panels/01.webp?v=20260823b"
              alt="A weathered Australian curb with drains, weeds, rubbish and stormwater pipes"
              className="absolute inset-0 h-full w-full"
              draggable={false}
            />

            <div className="pip-lab-creature" aria-hidden="true">
              <div className="pip-lab-rig">
                <img
                  src="/curbstamps/world/creatures/pip.svg?v=20260823c"
                  alt=""
                  className="h-auto w-full"
                  draggable={false}
                />
                <span className="pip-lab-eyelid" />
              </div>
            </div>

            <img
              src="/curbstamps/world/panels/01.webp?v=20260823b"
              alt=""
              className="pip-lab-curb-mask absolute inset-0 h-full w-full"
              draggable={false}
              aria-hidden="true"
            />
            <img
              src="/curbstamps/world/panels/01.webp?v=20260823b"
              alt=""
              className="pip-lab-pipe-mask absolute inset-0 h-full w-full"
              draggable={false}
              aria-hidden="true"
            />
          </div>
        </div>

        <p className="mt-5 text-sm font-black uppercase tracking-[0.1em]">
          Watch the full loop: hidden → emerges → looks → retreats
        </p>
      </div>
    </main>
  );
}
