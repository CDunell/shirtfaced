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
                      filter: placement.name === "blip"
                        ? "invert(78%) sepia(89%) saturate(403%) hue-rotate(46deg) brightness(94%) contrast(87%)"
                        : undefined,
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
