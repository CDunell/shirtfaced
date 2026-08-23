"use client";

import { useMemo, useRef, useState } from "react";
import { CREATURES, creatureMaster, UI_ACCENTS } from "@/lib/creatures";

type PlacedStamp = {
  id: number;
  slug: string;
  name: string;
  x: number;
  y: number;
  rotation: number;
  size: number;
};

const PLAY_CREATURES = CREATURES.slice(0, 12);
const SOUND_CREATURES = [
  { slug: "blip", word: "bip!", frequency: 310, type: "sine" as OscillatorType },
  { slug: "plod", word: "plod.", frequency: 120, type: "triangle" as OscillatorType },
  { slug: "bub", word: "bwoop!", frequency: 190, type: "sine" as OscillatorType },
  { slug: "zot", word: "zzip!", frequency: 620, type: "square" as OscillatorType },
  { slug: "fizz", word: "bzzzz!", frequency: 240, type: "sawtooth" as OscillatorType },
  { slug: "nib", word: "nip nip!", frequency: 430, type: "triangle" as OscillatorType },
];

const MISSIONS = [
  "Walk like Plod for ten slow steps.",
  "Find three things shaped like Bub.",
  "Draw Nib wearing enormous shoes.",
  "Invent a snack for Grub.",
  "Make the tiniest sound Mote might make.",
  "Race Zot to the nearest chair.",
  "Build Crumb Hill from three safe things.",
  "Wiggle like Wisp without moving your feet.",
];

function playCreatureSound(frequency: number, type: OscillatorType, double = false) {
  const AudioContextClass = window.AudioContext ?? (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!AudioContextClass) return;

  const context = new AudioContextClass();
  const start = context.currentTime;
  const notes = double ? [0, 0.13] : [0];
  const compressor = context.createDynamicsCompressor();
  compressor.threshold.setValueAtTime(-18, start);
  compressor.knee.setValueAtTime(12, start);
  compressor.ratio.setValueAtTime(4, start);
  compressor.attack.setValueAtTime(0.003, start);
  compressor.release.setValueAtTime(0.18, start);
  compressor.connect(context.destination);

  notes.forEach((offset) => {
    const oscillator = context.createOscillator();
    const gain = context.createGain();
    oscillator.type = type;
    oscillator.frequency.setValueAtTime(frequency, start + offset);
    oscillator.frequency.exponentialRampToValueAtTime(Math.max(70, frequency * 0.72), start + offset + 0.16);
    gain.gain.setValueAtTime(0.0001, start + offset);
    gain.gain.exponentialRampToValueAtTime(0.38, start + offset + 0.015);
    gain.gain.exponentialRampToValueAtTime(0.0001, start + offset + 0.24);
    oscillator.connect(gain);
    gain.connect(compressor);
    oscillator.start(start + offset);
    oscillator.stop(start + offset + 0.25);
  });

  window.setTimeout(() => void context.close(), 500);
}

export function PlayOnTheCurb() {
  const boardRef = useRef<HTMLDivElement>(null);
  const stampId = useRef(0);
  const [selectedSlug, setSelectedSlug] = useState(PLAY_CREATURES[0].slug);
  const [stamps, setStamps] = useState<PlacedStamp[]>([]);
  const [heard, setHeard] = useState<string | null>(null);
  const [missionShift, setMissionShift] = useState(0);

  const selected = PLAY_CREATURES.find((creature) => creature.slug === selectedSlug) ?? PLAY_CREATURES[0];
  const dailyIndex = useMemo(() => {
    const now = new Date();
    return Math.floor(Date.UTC(now.getFullYear(), now.getMonth(), now.getDate()) / 86_400_000) % MISSIONS.length;
  }, []);
  const mission = MISSIONS[(dailyIndex + missionShift) % MISSIONS.length];

  function placeStamp(event: React.PointerEvent<HTMLDivElement>) {
    if (!boardRef.current || (event.target as HTMLElement).closest("button")) return;
    const bounds = boardRef.current.getBoundingClientRect();
    const x = ((event.clientX - bounds.left) / bounds.width) * 100;
    const y = ((event.clientY - bounds.top) / bounds.height) * 100;
    stampId.current += 1;
    setStamps((current) => [
      ...current,
      {
        id: stampId.current,
        slug: selected.slug,
        name: selected.name,
        x,
        y,
        rotation: ((stampId.current * 17) % 18) - 9,
        size: 62 + ((stampId.current * 13) % 30),
      },
    ]);
  }

  return (
    <div>
      <section className="bg-grit-yellow px-4 py-10 sm:px-6 sm:py-14" aria-labelledby="make-picture-title">
        <div className="mx-auto max-w-5xl">
          <p className="mb-2 text-[11px] font-black uppercase tracking-[0.15em]">Tap. Stamp. Make a mess.</p>
          <h2 id="make-picture-title" className="display max-w-3xl text-[14vw] uppercase sm:text-[72px]">make a picture!</h2>
          <p className="mt-3 max-w-xl text-[16px] font-bold sm:text-[18px]">Pick a weirdo, then tap anywhere on the curb.</p>

          <div className="no-scrollbar -mx-4 mt-6 flex gap-2 overflow-x-auto px-4 pb-2 sm:mx-0 sm:px-0" aria-label="Choose a creature stamp">
            {PLAY_CREATURES.map((creature, index) => {
              const active = creature.slug === selected.slug;
              return (
                <button
                  key={creature.slug}
                  type="button"
                  aria-pressed={active}
                  onClick={() => setSelectedSlug(creature.slug)}
                  className={`press flex min-w-[88px] flex-col items-center rounded-[18px] border-2 border-ink p-2 font-black uppercase ${active ? "translate-y-[-3px] shadow-[0_5px_0_#1c1a17]" : "bg-cream"}`}
                  style={active ? { backgroundColor: UI_ACCENTS[index % UI_ACCENTS.length].hex } : undefined}
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={creatureMaster(creature.slug)} alt="" className="game-creature h-11 w-16 object-contain brightness-0" />
                  <span className="mt-1 text-[12px]">{creature.name}</span>
                </button>
              );
            })}
          </div>

          <div
            ref={boardRef}
            onPointerDown={placeStamp}
            className="relative mt-4 h-[390px] touch-none overflow-hidden rounded-[26px] border-2 border-ink bg-cream sm:h-[500px]"
            role="application"
            aria-label={`Picture board. Tap to place ${selected.name}.`}
          >
            <div className="absolute inset-x-0 bottom-0 h-[32%] bg-grit-blue/35" aria-hidden="true" />
            <div className="absolute inset-x-0 bottom-[32%] border-t-2 border-ink" aria-hidden="true" />
            <div className="pointer-events-none absolute left-[8%] top-[10%] h-14 w-14 rounded-full bg-grit-pink sm:h-20 sm:w-20" aria-hidden="true" />
            {stamps.map((stamp) => (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                key={stamp.id}
                src={creatureMaster(stamp.slug)}
                alt={stamp.name}
                draggable={false}
                className="game-creature pointer-events-none absolute object-contain brightness-0"
                style={{ left: `${stamp.x}%`, top: `${stamp.y}%`, width: stamp.size, transform: `translate(-50%, -50%) rotate(${stamp.rotation}deg)` }}
              />
            ))}
            {stamps.length === 0 && (
              <div className="pointer-events-none absolute inset-0 grid place-items-center px-8 text-center">
                <p className="display max-w-xs text-[30px] uppercase text-ink/35 sm:text-[42px]">tap here to add {selected.name}</p>
              </div>
            )}
          </div>

          <div className="mt-3 flex gap-2">
            <button type="button" onClick={() => setStamps((current) => current.slice(0, -1))} disabled={stamps.length === 0} className="press min-h-12 flex-1 rounded-full border-2 border-ink bg-cream px-4 text-[14px] font-black uppercase disabled:opacity-40">Undo</button>
            <button type="button" onClick={() => setStamps([])} disabled={stamps.length === 0} className="press min-h-12 flex-1 rounded-full border-2 border-ink bg-ink px-4 text-[14px] font-black uppercase text-cream disabled:opacity-40">Clear all</button>
          </div>
        </div>
      </section>

      <section className="bg-ink px-4 py-10 text-cream sm:px-6 sm:py-14" aria-labelledby="noises-title">
        <div className="mx-auto max-w-5xl">
          <p className="mb-2 text-[11px] font-black uppercase tracking-[0.15em] text-cream/60">Sound on. Grown-ups warned.</p>
          <h2 id="noises-title" className="display text-[13vw] uppercase sm:text-[68px]">creature noises!</h2>
          <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3">
            {SOUND_CREATURES.map((sound, index) => {
              const creature = CREATURES.find((item) => item.slug === sound.slug)!;
              const active = heard === sound.slug;
              return (
                <button
                  key={sound.slug}
                  type="button"
                  onClick={() => {
                    setHeard(sound.slug);
                    playCreatureSound(sound.frequency, sound.type, sound.slug === "nib");
                    window.setTimeout(() => setHeard((current) => current === sound.slug ? null : current), 450);
                  }}
                  className={`press min-h-[150px] rounded-[22px] border-2 border-cream p-3 text-ink ${active ? "scale-[0.97]" : ""}`}
                  style={{ backgroundColor: UI_ACCENTS[index].hex }}
                  aria-label={`Hear ${creature.name}: ${sound.word}`}
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={creatureMaster(creature.slug)} alt="" className="game-creature mx-auto h-16 w-full object-contain brightness-0" />
                  <span className="display mt-2 block text-[22px] uppercase">{active ? sound.word : creature.name}</span>
                </button>
              );
            })}
          </div>
        </div>
      </section>

      <section className="bg-grit-lilac px-4 py-10 sm:px-6 sm:py-14" aria-labelledby="mission-title">
        <div className="mx-auto max-w-5xl rounded-[28px] border-2 border-ink bg-cream p-6 shadow-[7px_7px_0_#1c1a17] sm:p-10">
          <p className="text-[11px] font-black uppercase tracking-[0.15em]">Today&apos;s tiny mission</p>
          <h2 id="mission-title" className="display mt-4 max-w-3xl text-[38px] uppercase leading-[0.95] sm:text-[62px]">{mission}</h2>
          <button type="button" onClick={() => setMissionShift((value) => value + 1)} className="press mt-6 min-h-12 rounded-full border-2 border-ink bg-grit-green px-6 text-[14px] font-black uppercase">Give me another</button>
        </div>
      </section>
    </div>
  );
}
