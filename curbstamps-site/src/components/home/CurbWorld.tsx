"use client";

import { useCallback, useEffect, useRef } from "react";

const PANEL_COUNT = 10;
const PANEL_WIDTH = 951;
const PANEL_HEIGHT = 576;
const PANELS = Array.from({ length: PANEL_COUNT }, (_, index) =>
  `/curbstamps/world/panels/${String(index + 1).padStart(2, "0")}.webp?v=20260824a`,
);
const LOOP_PANELS = [PANELS[PANEL_COUNT - 1], ...PANELS, PANELS[0]];

export function CurbWorld() {
  const scroller = useRef<HTMLDivElement>(null);
  const worldWidth = useRef(0);
  const panelWidth = useRef(0);
  const correcting = useRef(false);

  const centreWorld = useCallback((image: HTMLImageElement) => {
    const track = scroller.current;
    if (!track) return;
    panelWidth.current = image.getBoundingClientRect().width;
    worldWidth.current = panelWidth.current * PANEL_COUNT;
    const mobileRevealOffset = window.innerWidth < 640 ? panelWidth.current * 0.42 : 0;
    track.scrollLeft = panelWidth.current + mobileRevealOffset;
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
    const image = scroller.current?.querySelectorAll<HTMLImageElement>("[data-world-panel]")[1];
    if (image?.complete) centreWorld(image);
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
        Scroll → explore the curb
      </div>

      <div className="absolute right-3 top-3 z-20 hidden gap-2 sm:flex">
        <button type="button" onClick={() => move(-1)} aria-label="Explore left" className="press grid h-11 w-11 place-items-center rounded-full border-2 border-ink bg-white text-xl font-black">←</button>
        <button type="button" onClick={() => move(1)} aria-label="Explore right" className="press grid h-11 w-11 place-items-center rounded-full border-2 border-ink bg-white text-xl font-black">→</button>
      </div>

      <div
        ref={scroller}
        onScroll={keepLooping}
        className="no-scrollbar cursor-grab overflow-x-auto overscroll-x-none active:cursor-grabbing"
        aria-label="Explore the illustrated Curb world"
      >
        <div className="flex w-max">
          {LOOP_PANELS.map((src, index) => (
            <div key={`${src}-${index}`} className="relative h-[420px] aspect-[951/576] shrink-0 sm:h-[500px]">
              <img
                data-world-panel
                src={src}
                width={PANEL_WIDTH}
                height={PANEL_HEIGHT}
                alt={index === 1 ? "A long hand-drawn curb with weeds, drains, a cardboard shelter, skateboard and discarded street objects" : ""}
                aria-hidden={index === 1 ? undefined : true}
                draggable={false}
                onLoad={index === 1 ? (event) => centreWorld(event.currentTarget) : undefined}
                className="absolute inset-0 h-full w-full select-none"
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
