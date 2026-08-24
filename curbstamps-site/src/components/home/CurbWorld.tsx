"use client";

import type { CSSProperties } from "react";
import { useCallback, useEffect, useRef, useState } from "react";
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

const WHITE_FILL_CREATURES = [
  "bub", "claw", "crumb", "flit", "grit", "grub", "lod", "murk", "nib",
  "pex", "pip", "plod", "slag", "snu", "squib", "tum", "twig", "yip", "zot",
] as const;

function fillEnclosedBodyWhite(name: string): Promise<[string, string]> {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = 1200;
      canvas.height = 500;
      const context = canvas.getContext("2d", { willReadFrequently: true });
      if (!context) {
        reject(new Error("Canvas is unavailable"));
        return;
      }

      context.drawImage(image, 0, 0, canvas.width, canvas.height);
      const frame = context.getImageData(0, 0, canvas.width, canvas.height);
      const pixels = frame.data;
      const count = canvas.width * canvas.height;
      const outside = new Uint8Array(count);
      const queue = new Int32Array(count);
      let head = 0;
      let tail = 0;

      const visit = (index: number) => {
        if (outside[index] || pixels[index * 4 + 3] >= 24) return;
        outside[index] = 1;
        queue[tail++] = index;
      };

      for (let x = 0; x < canvas.width; x += 1) {
        visit(x);
        visit((canvas.height - 1) * canvas.width + x);
      }
      for (let y = 0; y < canvas.height; y += 1) {
        visit(y * canvas.width);
        visit(y * canvas.width + canvas.width - 1);
      }

      while (head < tail) {
        const index = queue[head++];
        const x = index % canvas.width;
        const y = Math.floor(index / canvas.width);
        if (x > 0) visit(index - 1);
        if (x + 1 < canvas.width) visit(index + 1);
        if (y > 0) visit(index - canvas.width);
        if (y + 1 < canvas.height) visit(index + canvas.width);
      }

      for (let index = 0; index < count; index += 1) {
        const alpha = index * 4 + 3;
        if (!outside[index] && pixels[alpha] < 24) {
          pixels[index * 4] = 255;
          pixels[index * 4 + 1] = 255;
          pixels[index * 4 + 2] = 255;
          pixels[alpha] = 255;
        }
      }

      context.putImageData(frame, 0, 0);
      resolve([name, canvas.toDataURL("image/png")]);
    };
    image.onerror = () => reject(new Error(`Unable to load ${name}`));
    image.src = `${CREATURE_ROOT}/${name}.svg`;
  });
}

function useWhiteCreatureSources() {
  const [sources, setSources] = useState<Record<string, string>>({});

  useEffect(() => {
    let cancelled = false;
    Promise.all(WHITE_FILL_CREATURES.map(fillEnclosedBodyWhite))
      .then((entries) => {
        if (!cancelled) setSources(Object.fromEntries(entries));
      })
      .catch(() => {
        if (!cancelled) setSources({});
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return sources;
}

export function CurbWorld() {
  const filledCreatureSources = useWhiteCreatureSources();
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
                            href={
                              placement.name === "blip"
                                ? `${CREATURE_ROOT}/${placement.name}.svg`
                                : filledCreatureSources[placement.name]
                            }
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
