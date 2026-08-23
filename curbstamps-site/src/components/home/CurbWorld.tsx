"use client";

import { useCallback, useRef } from "react";

const WORLD_PARTS = [
  "/curbstamps/world/curb-world-a.webp",
  "/curbstamps/world/curb-world-b.webp",
];

export function CurbWorld() {
  const scroller = useRef<HTMLDivElement>(null);
  const worldWidth = useRef(0);
  const correcting = useRef(false);

  const centreWorld = useCallback((image: HTMLImageElement) => {
    const track = scroller.current;
    if (!track) return;
    worldWidth.current = image.parentElement?.getBoundingClientRect().width ?? 0;
    track.scrollLeft = worldWidth.current;
  }, []);

  const keepLooping = useCallback(() => {
    const track = scroller.current;
    const width = worldWidth.current;
    if (!track || !width || correcting.current) return;

    if (track.scrollLeft < width * 0.5) {
      correcting.current = true;
      track.scrollLeft += width;
      correcting.current = false;
    } else if (track.scrollLeft > width * 1.5) {
      correcting.current = true;
      track.scrollLeft -= width;
      correcting.current = false;
    }
  }, []);

  function move(direction: number) {
    scroller.current?.scrollBy({
      left: direction * Math.min(window.innerWidth * 0.82, 760),
      behavior: "smooth",
    });
  }

  return (
    <div className="relative mt-5 overflow-hidden border-y-2 border-ink bg-cream sm:rounded-[22px] sm:border-2">
      <div className="pointer-events-none absolute left-3 top-3 z-20 rounded-full border-2 border-ink bg-white px-4 py-2 text-[10px] font-black uppercase tracking-[0.08em] shadow-[3px_3px_0_#1c1a17]">
        Scroll → keep exploring
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
          {[0, 1, 2].map((copy) => (
            <div key={copy} className="flex w-max shrink-0" aria-hidden={copy === 1 ? undefined : true}>
              {WORLD_PARTS.map((src, part) => (
                <img
                  key={src}
                  src={src}
                  width={9664}
                  height={768}
                  alt={copy === 1 && part === 0 ? "A very long illustrated curb filled with cracks, drains, weeds and discarded street objects" : ""}
                  draggable={false}
                  onLoad={copy === 1 && part === 1 ? (event) => centreWorld(event.currentTarget) : undefined}
                  className="h-[420px] w-auto max-w-none shrink-0 select-none sm:h-[500px]"
                />
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
