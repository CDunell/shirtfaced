"use client";

import { useCallback, useEffect, useRef } from "react";

const PANELS = Array.from({ length: 10 }, (_, index) =>
  `/curbstamps/world/panels/${String(index + 1).padStart(2, "0")}.webp?v=20260823b`,
);
const LOOP_PANELS = [PANELS[9], ...PANELS, PANELS[0]];

type CreaturePlacement = {
  name: string;
  panel: number;
  left: number;
  top: number;
  width: number;
  height: number;
  motion: "left" | "right" | "up" | "down";
  delay: number;
  duration: number;
};

const CREATURES: CreaturePlacement[] = [
  { name: "bub", panel: 1, left: 66.8, top: 47.5, width: 6.5, height: 6.5, motion: "down", delay: -2.1, duration: 8.4 },
  { name: "grub", panel: 2, left: 51.2, top: 72.8, width: 14, height: 9.5, motion: "left", delay: -4.7, duration: 9.1 },
  { name: "zot", panel: 2, left: 90.5, top: 72.2, width: 6.5, height: 8.5, motion: "up", delay: -1.3, duration: 7.9 },
  { name: "crumb", panel: 3, left: 57.5, top: 73.2, width: 13, height: 9.5, motion: "right", delay: -3.2, duration: 8.7 },
  { name: "grit", panel: 3, left: 80.8, top: 35.8, width: 7.5, height: 7.5, motion: "down", delay: -6.4, duration: 10.2 },
  { name: "lod", panel: 4, left: 81.8, top: 56, width: 13, height: 9, motion: "left", delay: -5.1, duration: 9.6 },
  { name: "flit", panel: 4, left: 39.8, top: 46, width: 5.5, height: 8, motion: "right", delay: -1.8, duration: 8.2 },
  { name: "blip", panel: 5, left: 2.2, top: 73.5, width: 12.5, height: 9, motion: "right", delay: -2.8, duration: 9.3 },
  { name: "murk", panel: 5, left: 68.2, top: 74, width: 11.5, height: 8.5, motion: "left", delay: -7.1, duration: 10.6 },
  { name: "nib", panel: 6, left: 79, top: 72.4, width: 6.5, height: 8.5, motion: "up", delay: -3.9, duration: 8.8 },
  { name: "pex", panel: 6, left: 9.5, top: 66.5, width: 11, height: 8, motion: "down", delay: -6.2, duration: 10.1 },
  { name: "plod", panel: 7, left: 4.8, top: 42.8, width: 13.5, height: 9, motion: "right", delay: -1.1, duration: 8.5 },
  { name: "slag", panel: 7, left: 19.5, top: 42.8, width: 13, height: 9, motion: "left", delay: -5.5, duration: 9.8 },
  { name: "snu", panel: 8, left: 50.5, top: 32.5, width: 15, height: 11, motion: "down", delay: -3.4, duration: 9.4 },
  { name: "squib", panel: 8, left: 57.5, top: 72.5, width: 12.5, height: 9, motion: "left", delay: -7.4, duration: 10.8 },
  { name: "tum", panel: 9, left: 3.2, top: 31.5, width: 13.5, height: 10, motion: "right", delay: -4.2, duration: 9.7 },
  { name: "twig", panel: 9, left: 19.2, top: 72.8, width: 8.5, height: 8.5, motion: "up", delay: -1.6, duration: 8.1 },
  { name: "yip", panel: 10, left: 3.8, top: 73, width: 12.5, height: 9, motion: "right", delay: -6.8, duration: 10.4 },
  { name: "claw", panel: 10, left: 63, top: 71.8, width: 14.5, height: 10, motion: "left", delay: -2.5, duration: 9 },
];

export function CurbWorld() {
  const scroller = useRef<HTMLDivElement>(null);
  const worldWidth = useRef(0);
  const panelWidth = useRef(0);
  const correcting = useRef(false);

  const centreWorld = useCallback((image: HTMLImageElement) => {
    const track = scroller.current;
    if (!track) return;
    panelWidth.current = image.getBoundingClientRect().width;
    worldWidth.current = panelWidth.current * PANELS.length;
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
          {LOOP_PANELS.map((src, index) => {
            const isPanelOne = index === 1 || index === LOOP_PANELS.length - 1;
            const panelNumber = index === 0 ? 10 : index === LOOP_PANELS.length - 1 ? 1 : index;
            const creatures = CREATURES.filter((creature) => creature.panel === panelNumber);

            return (
              <div key={`${src}-${index}`} className="relative h-[420px] aspect-[1428/576] shrink-0 sm:h-[500px]">
                <img
                  data-world-panel
                  src={src}
                  width={1428}
                  height={576}
                  alt={index === 1 ? "A very long illustrated curb filled with cracks, drains, weeds and discarded street objects" : ""}
                  aria-hidden={index === 1 ? undefined : true}
                  draggable={false}
                  onLoad={index === 1 ? (event) => centreWorld(event.currentTarget) : undefined}
                  className="absolute inset-0 h-full w-full select-none"
                />

                {isPanelOne && (
                  <div className="pip-drain absolute overflow-hidden" aria-hidden="true">
                    <img
                      src="/curbstamps/world/creatures/pip.svg?v=20260823c"
                      alt=""
                      draggable={false}
                      className="pip-drain-creature absolute h-full w-auto max-w-none select-none"
                    />
                  </div>
                )}

                {creatures.map((creature) => (
                  <div
                    key={`${creature.name}-${index}`}
                    className="curb-hideout absolute overflow-hidden"
                    style={{
                      left: `${creature.left}%`,
                      top: `${creature.top}%`,
                      width: `${creature.width}%`,
                      height: `${creature.height}%`,
                    }}
                    aria-hidden="true"
                  >
                    <img
                      src={`/curbstamps/world/creatures/${creature.name}.svg?v=20260823c`}
                      alt=""
                      draggable={false}
                      className={`curb-creature curb-creature-${creature.motion} h-full w-full object-contain select-none`}
                      style={{
                        animationDelay: `${creature.delay}s`,
                        animationDuration: `${creature.duration}s`,
                      }}
                    />
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      </div>

      <style jsx>{`
        .pip-drain {
          left: 57.65%;
          top: calc(72.6% + 5px);
          width: 14.45%;
          height: 9.4%;
        }

        .pip-drain-creature {
          left: 0;
          top: 0;
          animation: pip-peek 7.5s cubic-bezier(0.45, 0, 0.55, 1) infinite;
          will-change: transform;
        }

        .curb-creature {
          animation-timing-function: cubic-bezier(0.45, 0, 0.55, 1);
          animation-iteration-count: infinite;
          will-change: transform;
        }

        .curb-creature-left { animation-name: peek-left; }
        .curb-creature-right { animation-name: peek-right; }
        .curb-creature-up { animation-name: peek-up; }
        .curb-creature-down { animation-name: peek-down; }

        @keyframes pip-peek {
          0%, 18% { transform: translateX(112%); }
          38%, 62% { transform: translateX(8%); }
          82%, 100% { transform: translateX(112%); }
        }

        @keyframes peek-left {
          0%, 20% { transform: translateX(112%); }
          40%, 62% { transform: translateX(3%); }
          82%, 100% { transform: translateX(112%); }
        }

        @keyframes peek-right {
          0%, 20% { transform: translateX(-112%) scaleX(-1); }
          40%, 62% { transform: translateX(-3%) scaleX(-1); }
          82%, 100% { transform: translateX(-112%) scaleX(-1); }
        }

        @keyframes peek-up {
          0%, 20% { transform: translateY(112%); }
          40%, 62% { transform: translateY(4%); }
          82%, 100% { transform: translateY(112%); }
        }

        @keyframes peek-down {
          0%, 20% { transform: translateY(-112%); }
          40%, 62% { transform: translateY(-4%); }
          82%, 100% { transform: translateY(-112%); }
        }

        @media (prefers-reduced-motion: reduce) {
          .pip-drain-creature {
            animation: none;
            transform: translateX(8%);
          }

          .curb-creature {
            animation: none;
            transform: none;
          }
        }
      `}</style>
    </div>
  );
}
