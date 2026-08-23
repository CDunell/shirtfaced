"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { CREATURES, creatureMaster } from "@/lib/creatures";

const ink = "#1c1a17";
const cream = "#fffaf0";
const concrete = "#f1e9d8";

function Habitat({ index }: { index: number }) {
  const kind = index % 10;
  const common = { fill: "none", stroke: ink, strokeWidth: 3, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };

  return (
    <svg viewBox="0 0 260 330" preserveAspectRatio="none" className="absolute inset-0 h-full w-full" aria-hidden="true">
      <rect width="260" height="330" fill={cream} />
      <path d="M0 211H260V330H0Z" fill={concrete} />
      <path d="M0 211H260M0 275H260" {...common} />
      <path d={index % 2 ? "M12 275l18-8 25 7 33-10 34 8 42-9 38 10 47-8" : "M7 275l26-10 30 9 36-12 39 11 28-7 41 8 44-11"} {...common} />

      {kind === 0 && <g className="curb-detail"><path d="M62 275l35-30 28 13 31-49 27 25 23-19" {...common} /><path d="M104 249l11-29m31 5 18-38" {...common} /></g>}
      {kind === 1 && <g className="curb-rubbish"><path d="M37 257c34-14 52-43 81-51l79 26c8 3 11 13 4 19-37 23-104 24-164 6Z" fill={cream} stroke={ink} strokeWidth="3" /><path d="M65 241c25 6 49 4 73-7m-45-11 9-19m35 29 25 9" {...common} /></g>}
      {kind === 2 && <g className="curb-rubbish"><path d="M51 250 79 191l72 31-27 54Z" fill={cream} stroke={ink} strokeWidth="3" /><path d="m68 213 72 31M83 199l70 31M63 239l72 31" {...common} /><circle cx="173" cy="253" r="6" fill={ink} /><circle cx="194" cy="263" r="4" fill={ink} /></g>}
      {kind === 3 && <g className="curb-puddle"><path d="M28 267c20-33 67-43 97-23 24-22 73-12 99 21-38 19-157 20-196 2Z" fill={cream} stroke={ink} strokeWidth="3" /><path d="M58 262c25-15 49-14 72-1m25-1c17-8 31-7 43 1" {...common} /></g>}
      {kind === 4 && <g className="curb-weeds"><path d="M39 274c8-32 1-59-17-80m20 80c2-41 20-73 47-94m-44 94c22-31 50-47 83-48m-80 48c39-19 74-19 105 1" {...common} /><path d="M20 194c22 1 31 12 30 31-20 0-30-11-30-31Zm69-14c-1 22-12 32-31 31 1-20 11-30 31-31Zm39 46c17-14 32-13 46 0-15 13-31 13-46 0Z" fill={cream} stroke={ink} strokeWidth="3" /></g>}
      {kind === 5 && <g className="curb-rubbish"><path d="M35 274v-91h143v91m-143-91 70 36 73-36m-73 36v55M35 183l29-29 68 32 46-3" fill={cream} stroke={ink} strokeWidth="3" /><path d="M67 156v52m66-22-1 41" {...common} /></g>}
      {kind === 6 && <g className="curb-drain"><path d="M25 274v-61h205v61" fill={ink} /><path d="M45 226v35m27-35v35m27-35v35m27-35v35m27-35v35m27-35v35m27-35v35" stroke={cream} strokeWidth="5" strokeLinecap="round" /><path d="M18 211h219" {...common} /></g>}
      {kind === 7 && <g className="curb-rubbish"><path d="M83 272 62 191l55-15 21 81Z" fill={cream} stroke={ink} strokeWidth="3" /><path d="M71 204l56-15m-48 46 55-15" {...common} /><path d="M155 272c-1-40 15-64 48-70 17 31 9 54-23 70Z" fill={cream} stroke={ink} strokeWidth="3" /></g>}
      {kind === 8 && <g className="curb-rubbish"><path d="M31 257h166l29-39H70Z" fill={cream} stroke={ink} strokeWidth="3" /><circle cx="79" cy="267" r="11" fill={cream} stroke={ink} strokeWidth="3" /><circle cx="184" cy="267" r="11" fill={cream} stroke={ink} strokeWidth="3" /><path d="M63 218 47 190m14 9 35-10" {...common} /></g>}
      {kind === 9 && <g className="curb-weeds"><path d="M45 274v-90m0 29c-29-5-42-23-38-53 29 5 42 23 38 53Zm2 18c34-3 53-21 55-53-34 3-53 21-55 53Z" fill={cream} stroke={ink} strokeWidth="3" /><path d="M140 274v-48h76v48m-70-48 10-33h48l7 33m-47 0v48m22-48v48" {...common} /></g>}

      <path d="M0 75c23-26 47-21 60-3 26-14 49 2 49 20H1c-9-5-9-12-1-17Z" fill={cream} stroke={ink} strokeWidth="3" className="curb-cloud" />
      {index % 6 === 0 && <path d="M218 58v108m-25-78h50m-40 0v-24h30v24" {...common} />}
    </svg>
  );
}

export function CurbWorld() {
  const scroller = useRef<HTMLDivElement>(null);
  const scrollTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const scrollingRef = useRef(false);
  const pointerStart = useRef({ x: 0, scrollLeft: 0 });
  const dragged = useRef(false);
  const [isScrolling, setIsScrolling] = useState(false);

  useEffect(() => {
    const root = scroller.current;
    if (!root) return;
    const plots = Array.from(root.querySelectorAll<HTMLElement>(".curb-plot"));
    const observer = new IntersectionObserver((entries) => entries.forEach((entry) => entry.target.classList.toggle("is-in-view", entry.isIntersecting)), { root, threshold: 0.45 });
    plots.forEach((plot) => observer.observe(plot));
    return () => observer.disconnect();
  }, []);

  useEffect(() => () => { if (scrollTimer.current) clearTimeout(scrollTimer.current); }, []);

  function handleScroll() {
    scrollingRef.current = true;
    setIsScrolling(true);
    if (scrollTimer.current) clearTimeout(scrollTimer.current);
    scrollTimer.current = setTimeout(() => {
      scrollingRef.current = false;
      setIsScrolling(false);
    }, 180);
  }

  function move(direction: number) {
    handleScroll();
    scroller.current?.scrollBy({ left: direction * Math.min(window.innerWidth * 0.75, 680), behavior: "smooth" });
  }

  return (
    <div className="relative mt-5 overflow-hidden border-y-2 border-ink bg-cream sm:rounded-[22px] sm:border-2">
      <div className="pointer-events-none absolute left-3 top-3 z-30 rounded-full border-2 border-ink bg-cream px-3 py-2 text-[10px] font-black uppercase tracking-[0.08em] shadow-[3px_3px_0_#1c1a17]">Scroll → keep going</div>
      <div className="absolute right-3 top-3 z-30 hidden gap-2 sm:flex"><button type="button" onClick={() => move(-1)} aria-label="Explore left" className="press grid h-11 w-11 place-items-center rounded-full border-2 border-ink bg-cream text-xl font-black">←</button><button type="button" onClick={() => move(1)} aria-label="Explore right" className="press grid h-11 w-11 place-items-center rounded-full border-2 border-ink bg-cream text-xl font-black">→</button></div>
      <div
        ref={scroller}
        onScroll={handleScroll}
        onPointerDown={(event) => { pointerStart.current = { x: event.clientX, scrollLeft: scroller.current?.scrollLeft ?? 0 }; dragged.current = false; }}
        onPointerMove={(event) => { if (Math.abs(event.clientX - pointerStart.current.x) > 7 || Math.abs((scroller.current?.scrollLeft ?? 0) - pointerStart.current.scrollLeft) > 7) dragged.current = true; }}
        className={`no-scrollbar flex overflow-x-auto overscroll-x-contain ${isScrolling ? "cursor-grabbing" : "cursor-grab"}`}
        aria-label="Explore the Curb Crew neighbourhood"
        data-scrolling={isScrolling ? "true" : "false"}
      >
        {CREATURES.map((creature, index) => (
          <Link
            key={creature.slug}
            href={`/shop?creature=${creature.slug}`}
            onClick={(event) => { if (scrollingRef.current || dragged.current) event.preventDefault(); }}
            className="curb-plot group relative h-[350px] min-w-[230px] overflow-hidden bg-cream text-ink sm:h-[400px] sm:min-w-[265px]"
            aria-label={`Visit ${creature.name}'s hiding spot and shop their range`}
            aria-disabled={isScrolling}
          >
            <Habitat index={index} />
            <div className={`curb-creature absolute bottom-[53px] left-1/2 z-10 w-[120px] -translate-x-1/2 sm:w-[142px] ${isScrolling ? "pointer-events-none" : ""}`}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={creatureMaster(creature.slug)} alt="" className="h-[68px] w-full object-contain brightness-0 sm:h-[80px]" />
            </div>
            <div className={`absolute bottom-3 left-4 right-4 z-20 flex items-center justify-between border-2 border-ink bg-cream px-3 py-2 transition-opacity ${isScrolling ? "opacity-0" : "opacity-100"}`}>
              <span className="display text-[16px] uppercase">{creature.name} hides here</span><span className="text-[14px] font-black">TAP →</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
