"use client";

import type { CSSProperties } from "react";
import { useCallback, useEffect, useRef } from "react";
import styles from "./CurbWorld.module.css";

const PANEL_COUNT = 10;
const PANEL_WIDTH = 951;
const PANEL_HEIGHT = 576;
const PANELS = Array.from({ length: PANEL_COUNT }, (_, index) =>
  `/curbstamps/world/panels/${String(index + 1).padStart(2, "0")}.webp?v=20260824a`,
);
const LOOP_PANEL_IDS = [PANEL_COUNT - 1, ...Array.from({ length: PANEL_COUNT }, (_, index) => index), 0];

const CREATURE_ROOT = "/curbstamps/world/creatures";

type Motion = "peek" | "creep" | "scuttle" | "duck" | "nose" | "edge" | "sneak" | "settle";

type Placement = {
  name: string;
  x: number;
  y: number;
  width: number;
  motion: Motion;
  delay: number;
  maskClip: string;
};

const PANEL_SCENES: Placement[][] = [
  [
    { name: "blip", x: 8.5, y: 69.5, width: 14, motion: "peek", delay: -1.2, maskClip: "polygon(4% 77.5%, 28% 77.5%, 28% 100%, 4% 100%)" },
  ],
  [],
  [],
  [],
  [],
  [],
  [],
  [],
  [],
  [],
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
    worldWidth.current = panelWidth.current * PANEL_COUNT;
    const mobileRevealOffset = window.innerWidth < 640 ? panelWidth.current * 0.24 : 0;
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
    <div className={`${styles.frame} curb-world-frame relative mt-6 overflow-hidden bg-cream md:mt-8 lg:mt-10`}>
      <div className="curb-world-badge pointer-events-none absolute left-3 top-3 z-20 bg-club px-3 py-1.5 text-[9px] font-black uppercase tracking-[0.08em] shadow-[3px_3px_0_#1c1a17] md:left-4 md:top-4 md:px-4 md:py-2 md:text-[11px]">
        Scroll → explore the curb
      </div>

      <div className="absolute right-4 top-4 z-20 hidden gap-2 md:flex">
        <button type="button" onClick={() => move(-1)} aria-label="Explore left" className="press grid h-11 w-11 place-items-center border-2 border-ink bg-white text-xl font-black shadow-[3px_3px_0_#1c1a17]">←</button>
        <button type="button" onClick={() => move(1)} aria-label="Explore right" className="press grid h-11 w-11 place-items-center border-2 border-ink bg-white text-xl font-black shadow-[3px_3px_0_#1c1a17]">→</button>
      </div>

      <div
        ref={scroller}
        onScroll={keepLooping}
        className="no-scrollbar cursor-grab overflow-x-auto overscroll-x-none active:cursor-grabbing"
        aria-label="Explore the illustrated Curb world"
      >
        <div className="flex w-max">
          {LOOP_PANEL_IDS.map((panelId, index) => {
            const src = PANELS[panelId];
            const placements = PANEL_SCENES[panelId];

            return (
              <div key={`${panelId}-${index}`} className={styles.panel}>
                <div className={styles.scene}>
                  <img
                    data-world-panel
                    src={src}
                    width={PANEL_WIDTH}
                    height={PANEL_HEIGHT}
                    alt={index === 1 ? "A long hand-drawn curb with weeds, drains, a cardboard shelter, skateboard and discarded street objects" : ""}
                    aria-hidden={index === 1 ? undefined : true}
                    draggable={false}
                    onLoad={index === 1 ? (event) => centreWorld(event.currentTarget) : undefined}
                    className={styles.panelArt}
                  />

                  {placements.map((placement) => {
                    const creatureStyle = {
                      left: `${placement.x}%`,
                      top: `${placement.y}%`,
                      "--creature-width": `${placement.width}%`,
                      animationDelay: `${placement.delay}s`,
                    } as CSSProperties;

                    return (
                      <div key={placement.name}>
                        <svg
                          viewBox="0 0 1200 500"
                          aria-hidden="true"
                          className={`${styles.creature} ${styles[placement.motion]}`}
                          style={creatureStyle}
                        >
                          {placement.name === "blip" && (
                            <path
                              d="M 820.74 289.74 Q 917.69 291.05 931.44 289.08 Q 945.20 287.12 955.68 282.53 Q 966.16 277.95 968.78 270.74 Q 971.40 263.54 970.74 258.30 Q 970.09 253.06 964.19 245.20 Q 958.30 237.34 934.72 218.34 Q 911.14 199.34 892.14 178.38 Q 873.14 157.42 860.70 146.94 Q 848.25 136.46 830.57 125.33 Q 812.88 114.19 790.61 103.71 Q 768.34 93.23 739.52 84.72 Q 710.70 76.20 690.39 72.93 Q 670.09 69.65 650.44 68.34 Q 630.79 67.03 598.03 68.34 Q 565.28 69.65 544.98 72.93 Q 524.67 76.20 493.89 85.37 Q 463.10 94.54 432.31 110.26 Q 401.53 125.98 394.98 127.29 Q 388.43 128.60 343.89 127.29 Q 319.00 129.91 309.83 133.19 Q 300.66 136.46 287.55 137.77 Q 284.93 143.01 276.42 148.25 Q 267.90 153.49 259.39 162.66 Q 250.87 171.83 244.32 183.62 Q 237.77 195.41 233.84 207.21 Q 229.91 219.00 229.26 234.72 Q 228.60 250.44 229.91 254.37 Q 231.22 258.30 235.81 260.92 Q 240.39 263.54 250.87 264.85 L 309.83 262.23 Q 500 278 820.74 289.74 Z"
                              fill="#fff"
                            />
                          )}
                          <image
                            href={`${CREATURE_ROOT}/${placement.name}.svg`}
                            width="1200"
                            height="500"
                          />
                        </svg>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
