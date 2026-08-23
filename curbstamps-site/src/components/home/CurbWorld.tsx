"use client";

import { useCallback, useEffect, useRef } from "react";

const PANELS = Array.from({ length: 10 }, (_, index) =>
  `/curbstamps/world/panels/${String(index + 1).padStart(2, "0")}.webp?v=20260823b`,
);
const LOOP_PANEL_NUMBERS = [10, ...Array.from({ length: 10 }, (_, index) => index + 1), 1];

type Motion = "bob" | "peek" | "scuttle" | "wobble" | "breathe";

type CreaturePlacement = {
  name: string;
  left: number;
  top: number;
  width: number;
  motion: Motion;
  delay: number;
  flip?: boolean;
  rotate?: number;
};

const CREATURES: Record<number, CreaturePlacement[]> = {
  1: [
    { name: "plod", left: 25, top: 59, width: 15, motion: "breathe", delay: 0.2 },
    { name: "pip", left: 73, top: 68, width: 12, motion: "scuttle", delay: 1.1, flip: true },
  ],
  2: [
    { name: "twig", left: 19, top: 51, width: 13, motion: "wobble", delay: 0.7, rotate: -3 },
    { name: "nib", left: 68, top: 63, width: 10, motion: "peek", delay: 1.8 },
  ],
  3: [
    { name: "crumb", left: 31, top: 68, width: 12, motion: "bob", delay: 1.3 },
    { name: "yip", left: 79, top: 57, width: 13, motion: "wobble", delay: 0.4, flip: true },
  ],
  4: [
    { name: "grit", left: 23, top: 61, width: 14, motion: "scuttle", delay: 2.1 },
    { name: "lod", left: 66, top: 70, width: 11, motion: "breathe", delay: 0.9 },
  ],
  5: [
    { name: "grub", left: 35, top: 67, width: 14, motion: "peek", delay: 1.5, flip: true },
    { name: "snu", left: 82, top: 54, width: 10, motion: "bob", delay: 0.1 },
  ],
  6: [
    { name: "murk", left: 20, top: 69, width: 12, motion: "breathe", delay: 2.4 },
    { name: "flit", left: 70, top: 47, width: 11, motion: "bob", delay: 1.2, rotate: 4 },
  ],
  7: [
    { name: "squib", left: 30, top: 62, width: 13, motion: "wobble", delay: 0.5 },
    { name: "tum", left: 76, top: 67, width: 15, motion: "peek", delay: 2 },
  ],
  8: [
    { name: "blip", left: 18, top: 55, width: 11, motion: "bob", delay: 1.7, flip: true },
    { name: "slag", left: 65, top: 70, width: 13, motion: "scuttle", delay: 0.3 },
  ],
  9: [
    { name: "bub", left: 28, top: 69, width: 11, motion: "breathe", delay: 0.8 },
    { name: "pex", left: 80, top: 58, width: 13, motion: "wobble", delay: 2.2, flip: true },
  ],
  10: [
    { name: "claw", left: 22, top: 63, width: 15, motion: "peek", delay: 1.4 },
    { name: "zot", left: 72, top: 66, width: 14, motion: "scuttle", delay: 0.6, flip: true },
  ],
};

function WorldPanel({ panel, loopIndex }: { panel: number; loopIndex: number }) {
  const src = PANELS[panel - 1];

  return (
    <div className="relative h-[420px] w-[1041.25px] shrink-0 overflow-hidden sm:h-[500px] sm:w-[1239.58px]">
      <img
        src={src}
        width={1428}
        height={576}
        alt={loopIndex === 1 ? "A very long illustrated curb filled with cracks, drains, weeds, discarded street objects and hidden Curb creatures" : ""}
        aria-hidden={loopIndex === 1 ? undefined : true}
        draggable={false}
        className="absolute inset-0 h-full w-full select-none"
      />

      <div className="pointer-events-none absolute inset-0" aria-hidden={loopIndex === 1 ? undefined : true}>
        {CREATURES[panel].map((creature) => (
          <div
            key={creature.name}
            className="curb-world-creature absolute"
            style={{
              left: `${creature.left}%`,
              top: `${creature.top}%`,
              width: `${creature.width}%`,
              "--creature-delay": `${creature.delay}s`,
              "--creature-rotation": `${creature.rotate ?? 0}deg`,
            } as React.CSSProperties}
          >
            <img
              src={`/creatures/${creature.name}-icon.png`}
              alt={loopIndex === 1 ? creature.name : ""}
              className={`curb-world-sprite curb-motion-${creature.motion} h-auto w-full ${creature.flip ? "-scale-x-100" : ""}`}
              draggable={false}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

export function CurbWorld() {
  const scroller = useRef<HTMLDivElement>(null);
  const worldWidth = useRef(0);
  const panelWidth = useRef(0);
  const correcting = useRef(false);

  const centreWorld = useCallback((panel: HTMLDivElement) => {
    const track = scroller.current;
    if (!track) return;
    panelWidth.current = panel.getBoundingClientRect().width;
    worldWidth.current = panelWidth.current * PANELS.length;
    track.scrollLeft = panelWidth.current;
  }, []);

  const keepLooping = useCallback(() => {
    const track = scroller.current;
    const width = worldWidth.current;
    const panel = panelWidth.current;
    if (!track || !width || !panel || correcting.current) return;

    if (track.scrollLeft < panel * 0.5) {
      correcting.current = true;
      track.scrollLeft += width;
      correcting.current = false;
    } else if (track.scrollLeft > panel + width - track.clientWidth * 0.5) {
      correcting.current = true;
      track.scrollLeft -= width;
      correcting.current = false;
    }
  }, []);

  useEffect(() => {
    const firstMainPanel = scroller.current?.querySelectorAll<HTMLDivElement>("[data-world-panel]")[1];
    if (firstMainPanel) centreWorld(firstMainPanel);
  }, [centreWorld]);

  function move(direction: number) {
    scroller.current?.scrollBy({
      left: direction * Math.min(window.innerWidth * 0.82, 760),
      behavior: "smooth",
    });
  }

  return (
    <div className="relative mt-5 overflow-hidden border-y-2 border-ink bg-cream sm:rounded-[22px] sm:border-2">
      <div className="pointer-events-none absolute left-3 top-3 z-20 rounded-full border-2 border-ink bg-white px-4 py-2 text-[10px] font-black uppercase tracking-[0.08em] shadow-[3px_3px_0_#1c1a17]">
        Scroll → find all 20
      </div>

      <div className="absolute right-3 top-3 z-20 hidden gap-2 sm:flex">
        <button type="button" onClick={() => move(-1)} aria-label="Explore left" className="press grid h-11 w-11 place-items-center rounded-full border-2 border-ink bg-white text-xl font-black">←</button>
        <button type="button" onClick={() => move(1)} aria-label="Explore right" className="press grid h-11 w-11 place-items-center rounded-full border-2 border-ink bg-white text-xl font-black">→</button>
      </div>

      <div
        ref={scroller}
        onScroll={keepLooping}
        className="no-scrollbar cursor-grab overflow-x-auto overscroll-x-none active:cursor-grabbing"
        aria-label="Explore the illustrated Curb world and find 20 animated creatures"
      >
        <div className="flex w-max">
          {LOOP_PANEL_NUMBERS.map((panel, index) => (
            <div key={`${panel}-${index}`} data-world-panel>
              <WorldPanel panel={panel} loopIndex={index} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
