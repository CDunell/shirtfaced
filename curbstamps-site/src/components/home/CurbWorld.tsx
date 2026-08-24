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
    { name: "blip", x: 13, y: 56, width: 18, motion: "peek", delay: -1.2, maskClip: "polygon(8% 69%, 34% 69%, 34% 100%, 8% 100%)" },
    { name: "bub", x: 63, y: 60, width: 17, motion: "nose", delay: -3.1, maskClip: "polygon(58% 72%, 84% 72%, 84% 100%, 58% 100%)" },
  ],
  [
    { name: "claw", x: 18, y: 57, width: 18, motion: "edge", delay: -2.4, maskClip: "polygon(12% 70%, 39% 70%, 39% 100%, 12% 100%)" },
    { name: "crumb", x: 69, y: 54, width: 16, motion: "duck", delay: -0.8, maskClip: "polygon(64% 68%, 89% 68%, 89% 100%, 64% 100%)" },
  ],
  [
    { name: "flit", x: 9, y: 61, width: 15, motion: "scuttle", delay: -4.2, maskClip: "polygon(5% 73%, 28% 73%, 28% 100%, 5% 100%)" },
    { name: "grit", x: 56, y: 55, width: 19, motion: "creep", delay: -1.7, maskClip: "polygon(50% 69%, 80% 69%, 80% 100%, 50% 100%)" },
  ],
  [
    { name: "grub", x: 21, y: 54, width: 19, motion: "settle", delay: -3.6, maskClip: "polygon(15% 69%, 43% 69%, 43% 100%, 15% 100%)" },
    { name: "lod", x: 73, y: 58, width: 13, motion: "peek", delay: -0.5, maskClip: "polygon(69% 71%, 90% 71%, 90% 100%, 69% 100%)" },
  ],
  [
    { name: "murk", x: 12, y: 57, width: 17, motion: "sneak", delay: -2.8, maskClip: "polygon(7% 70%, 33% 70%, 33% 100%, 7% 100%)" },
    { name: "nib", x: 60, y: 59, width: 17, motion: "duck", delay: -4.5, maskClip: "polygon(55% 72%, 81% 72%, 81% 100%, 55% 100%)" },
  ],
  [
    { name: "pex", x: 17, y: 55, width: 17, motion: "nose", delay: -1.5, maskClip: "polygon(11% 69%, 38% 69%, 38% 100%, 11% 100%)" },
    { name: "pip", x: 70, y: 56, width: 15, motion: "edge", delay: -3.9, maskClip: "polygon(65% 70%, 89% 70%, 89% 100%, 65% 100%)" },
  ],
  [
    { name: "plod", x: 8, y: 54, width: 20, motion: "creep", delay: -0.9, maskClip: "polygon(3% 69%, 32% 69%, 32% 100%, 3% 100%)" },
    { name: "slag", x: 58, y: 60, width: 17, motion: "scuttle", delay: -2.6, maskClip: "polygon(53% 72%, 79% 72%, 79% 100%, 53% 100%)" },
  ],
  [
    { name: "snu", x: 19, y: 58, width: 16, motion: "peek", delay: -4.8, maskClip: "polygon(14% 71%, 39% 71%, 39% 100%, 14% 100%)" },
    { name: "squib", x: 68, y: 54, width: 18, motion: "settle", delay: -1.9, maskClip: "polygon(62% 69%, 91% 69%, 91% 100%, 62% 100%)" },
  ],
  [
    { name: "tum", x: 10, y: 59, width: 18, motion: "duck", delay: -3.4, maskClip: "polygon(5% 72%, 32% 72%, 32% 100%, 5% 100%)" },
    { name: "twig", x: 57, y: 53, width: 20, motion: "sneak", delay: -0.3, maskClip: "polygon(51% 68%, 82% 68%, 82% 100%, 51% 100%)" },
  ],
  [
    { name: "yip", x: 18, y: 55, width: 18, motion: "edge", delay: -2.1, maskClip: "polygon(12% 69%, 40% 69%, 40% 100%, 12% 100%)" },
    { name: "zot", x: 69, y: 58, width: 18, motion: "peek", delay: -4.1, maskClip: "polygon(63% 71%, 92% 71%, 92% 100%, 63% 100%)" },
  ],
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
                        <img
                          src={`${CREATURE_ROOT}/${placement.name}.svg`}
                          alt=""
                          aria-hidden="true"
                          draggable={false}
                          className={`${styles.creature} ${styles[placement.motion]}`}
                          style={creatureStyle}
                        />
                        <img
                          src={src}
                          alt=""
                          aria-hidden="true"
                          draggable={false}
                          className={styles.foregroundMask}
                          style={{ clipPath: placement.maskClip }}
                        />
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
