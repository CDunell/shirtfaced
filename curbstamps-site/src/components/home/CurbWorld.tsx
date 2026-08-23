"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";
import { CREATURES, creatureMaster, UI_ACCENTS } from "@/lib/creatures";

function House({ index }: { index: number }) {
  const kind = index % 5;
  if (kind === 0) return <div className="curb-house absolute bottom-[72px] left-5 h-[108px] w-[128px] border-[3px] border-ink bg-cream"><div className="absolute -left-[9px] -top-[40px] h-[70px] w-[140px] rotate-[-4deg] border-[3px] border-ink bg-grit-pink [clip-path:polygon(50%_0,100%_62%,92%_100%,8%_100%,0_62%)]" /><div className="curb-door absolute bottom-0 left-11 h-[58px] w-10 origin-left border-x-[3px] border-t-[3px] border-ink bg-grit-yellow" /><div className="absolute bottom-8 left-3 h-7 w-7 border-2 border-ink bg-grit-blue" /></div>;
  if (kind === 1) return <div className="curb-house absolute bottom-[72px] left-5 h-[96px] w-[138px] rounded-t-[52px] border-[3px] border-ink bg-grit-lilac"><div className="curb-door absolute bottom-0 left-12 h-[55px] w-11 origin-left rounded-t-full border-x-[3px] border-t-[3px] border-ink bg-cream" /><div className="absolute left-4 top-9 h-7 w-7 rounded-full border-2 border-ink bg-grit-yellow" /><div className="absolute right-4 top-9 h-7 w-7 rounded-full border-2 border-ink bg-grit-yellow" /></div>;
  if (kind === 2) return <div className="curb-house absolute bottom-[72px] left-6 h-[116px] w-[124px] border-[3px] border-ink bg-grit-blue"><div className="absolute -left-2 -top-5 h-6 w-[140px] border-[3px] border-ink bg-cream" /><div className="curb-door absolute bottom-0 right-5 h-[62px] w-11 origin-left border-x-[3px] border-t-[3px] border-ink bg-grit-green" /><div className="absolute left-4 top-8 grid h-10 w-10 grid-cols-2 border-2 border-ink bg-cream"><i className="border-b border-r border-ink" /><i className="border-b border-ink" /><i className="border-r border-ink" /><i /></div><div className="absolute -top-14 right-5 h-9 w-6 border-[3px] border-ink bg-grit-orange"><span className="curb-smoke absolute -top-7 left-[-7px] h-5 w-8 rounded-full border-2 border-ink bg-cream" /></div></div>;
  if (kind === 3) return <div className="curb-house absolute bottom-[72px] left-5 h-[105px] w-[137px] rotate-[1deg] border-[3px] border-ink bg-grit-green"><div className="absolute -left-3 -top-8 h-9 w-[157px] -rotate-[3deg] border-[3px] border-ink bg-grit-yellow" /><div className="curb-door absolute bottom-0 left-4 h-[59px] w-11 origin-left border-x-[3px] border-t-[3px] border-ink bg-grit-pink" /><div className="absolute right-5 top-7 h-9 w-12 border-2 border-ink bg-cream"><span className="absolute left-1/2 top-0 h-full border-l border-ink" /><span className="absolute left-0 top-1/2 w-full border-t border-ink" /></div></div>;
  return <div className="curb-house absolute bottom-[72px] left-5 h-[92px] w-[143px] border-[3px] border-ink bg-grit-orange"><div className="absolute -left-1 -top-12 h-14 w-[151px] rounded-t-full border-[3px] border-ink bg-cream" /><div className="curb-door absolute bottom-0 left-[52px] h-[54px] w-10 origin-left rounded-t-full border-x-[3px] border-t-[3px] border-ink bg-grit-lilac" /><div className="absolute left-4 top-7 h-7 w-7 rounded-full border-2 border-ink bg-grit-blue" /><div className="absolute right-4 top-7 h-7 w-7 rounded-full border-2 border-ink bg-grit-blue" /></div>;
}

function StreetDetail({ index }: { index: number }) {
  if (index % 4 === 0) return <div className="curb-plant absolute bottom-[55px] right-4 h-16 w-10 border-b-[3px] border-ink before:absolute before:bottom-0 before:left-1/2 before:h-14 before:border-l-[3px] before:border-ink after:absolute after:left-1 after:top-3 after:h-6 after:w-8 after:rounded-[50%] after:border-[3px] after:border-ink" />;
  if (index % 4 === 1) return <div className="absolute bottom-[57px] right-3 h-16 w-12 border-[3px] border-ink bg-paper-2 before:absolute before:-left-2 before:-top-3 before:h-4 before:w-16 before:border-[3px] before:border-ink before:bg-grit-pink" />;
  if (index % 4 === 2) return <div className="absolute bottom-[58px] right-3 h-12 w-16 border-[3px] border-ink before:absolute before:-top-5 before:left-4 before:h-6 before:border-l-[3px] before:border-ink after:absolute after:-top-6 after:left-1 after:h-3 after:w-9 after:border-[3px] after:border-ink after:bg-cream" />;
  return <div className="absolute bottom-[58px] right-4 h-14 w-16 border-x-[3px] border-t-[3px] border-ink before:absolute before:left-1/3 before:top-0 before:h-full before:border-l-2 before:border-ink after:absolute after:left-2/3 after:top-0 after:h-full after:border-l-2 after:border-ink" />;
}

export function CurbWorld() {
  const scroller = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const root = scroller.current;
    if (!root) return;
    const plots = Array.from(root.querySelectorAll<HTMLElement>(".curb-plot"));
    const observer = new IntersectionObserver((entries) => entries.forEach((entry) => entry.target.classList.toggle("is-in-view", entry.isIntersecting)), { root, threshold: 0.55 });
    plots.forEach((plot) => observer.observe(plot));
    return () => observer.disconnect();
  }, []);

  function move(direction: number) {
    scroller.current?.scrollBy({ left: direction * Math.min(window.innerWidth * 0.78, 720), behavior: "smooth" });
  }

  return (
    <div className="relative mt-5 overflow-hidden border-y-2 border-ink bg-cream sm:rounded-[22px] sm:border-2">
      <div className="pointer-events-none absolute left-3 top-3 z-30 rounded-full border-2 border-ink bg-cream/95 px-3 py-2 text-[10px] font-black uppercase tracking-[0.08em] shadow-[3px_3px_0_#1c1a17]">Swipe the street →</div>
      <div className="absolute right-3 top-3 z-30 hidden gap-2 sm:flex"><button type="button" onClick={() => move(-1)} aria-label="Explore left" className="press grid h-11 w-11 place-items-center rounded-full border-2 border-ink bg-cream text-xl font-black">←</button><button type="button" onClick={() => move(1)} aria-label="Explore right" className="press grid h-11 w-11 place-items-center rounded-full border-2 border-ink bg-grit-yellow text-xl font-black">→</button></div>
      <div ref={scroller} className="no-scrollbar flex snap-x snap-proximity overflow-x-auto overscroll-x-contain" aria-label="Explore the Curb Crew neighbourhood">
        {CREATURES.map((creature, index) => {
          const accent = UI_ACCENTS[index % UI_ACCENTS.length].hex;
          return (
            <Link key={creature.slug} href={`/shop?creature=${creature.slug}`} className="curb-plot group relative h-[360px] min-w-[228px] snap-center overflow-hidden border-r-2 border-ink bg-cream text-ink sm:h-[410px] sm:min-w-[270px]" aria-label={`Visit ${creature.name}'s home and shop their range`}>
              <div className="absolute inset-x-0 top-0 h-[58%]" style={{ backgroundColor: `${accent}88` }} />
              <div className="curb-cloud absolute right-3 top-12 h-7 w-16 rounded-[50%] border-[3px] border-ink bg-cream before:absolute before:-top-4 before:left-3 before:h-8 before:w-8 before:rounded-full before:border-[3px] before:border-ink before:bg-cream after:absolute after:-top-2 after:right-2 after:h-7 after:w-7 after:rounded-full after:border-[3px] after:border-ink after:bg-cream" />
              <House index={index} /><StreetDetail index={index} />
              <div className="absolute inset-x-0 bottom-0 h-[72px] border-t-[3px] border-ink bg-paper-2 before:absolute before:left-[18%] before:top-8 before:w-10 before:border-t-2 before:border-ink after:absolute after:right-[12%] after:top-4 after:w-12 after:rotate-[-7deg] after:border-t-2 after:border-ink" />
              <div className="curb-creature absolute bottom-[52px] left-[50%] z-10 w-[115px] -translate-x-1/2 rounded-full bg-cream/70 px-2 py-1 sm:w-[138px]">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={creatureMaster(creature.slug)} alt="" className="h-[66px] w-full object-contain brightness-0 sm:h-[78px]" />
              </div>
              <div className="absolute bottom-3 left-3 right-3 z-20 flex items-center justify-between rounded-full border-2 border-ink bg-cream px-4 py-2 shadow-[3px_3px_0_#1c1a17]"><span className="display text-[19px] uppercase">{creature.name}&apos;s place</span><span className="grid h-7 w-7 place-items-center rounded-full bg-ink text-[14px] text-cream">→</span></div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
