"use client";

import type { CSSProperties } from "react";
import { useCallback, useEffect, useRef } from "react";

const PANELS = Array.from({ length: 10 }, (_, index) =>
  `/curbstamps/world/panels/${String(index + 1).padStart(2, "0")}.webp?v=20260823b`,
);
const LOOP_PANEL_NUMBERS = [10, ...Array.from({ length: 10 }, (_, index) => index + 1), 1];

type CreaturePlacement = {
  name: "plod" | "pip";
  left: number;
  top: number;
  width: number;
  scene: "plod-bin" | "pip-drain";
  flip?: boolean;
};

const CREATURES: Record<number, CreaturePlacement[]> = {
  1: [
    { name: "plod", left: 46.8, top: 51.5, width: 15, scene: "plod-bin", flip: true },
    { name: "pip", left: 65.5, top: 76.5, width: 18, scene: "pip-drain" },
  ],
  2: [],
  3: [],
  4: [],
  5: [],
  6: [],
  7: [],
  8: [],
  9: [],
  10: [],
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
            } as CSSProperties}
          >
            <div className={`curb-world-motion curb-scene-${creature.scene} ${creature.flip ? "-scale-x-100" : ""}`}>
              <img
                src={`/curbstamps/world/creatures/${creature.name}.svg?v=20260823c`}
                alt={loopIndex === 1 ? creature.name : ""}
                className="curb-world-filled h-auto w-full"
                draggable={false}
              />
            </div>
          </div>
        ))}
      </div>

      {panel === 1 ? (
        <div className="pointer-events-none absolute inset-0 z-[3]" aria-hidden="true">
          <img
            src={src}
            alt=""
            className="curb-bin-foreground absolute inset-0 h-full w-full"
            draggable={false}
          />
          <img
            src={src}
            alt=""
            className="curb-drain-foreground absolute inset-0 h-full w-full"
            draggable={false}
          />
        </div>
      ) : null}
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
        Two weirdos live here
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
