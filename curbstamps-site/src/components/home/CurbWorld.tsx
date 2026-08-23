"use client";

import { useRef } from "react";

const I = "#1c1a17";
const C = "#fffaf0";
const P = "#f1e9d8";

const line = { fill: "none", stroke: I, strokeWidth: 5, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
const fine = { fill: "none", stroke: I, strokeWidth: 3, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };

function WorldArt() {
  return (
    <svg viewBox="0 0 5200 520" className="h-[420px] w-[5200px] max-w-none sm:h-[500px]" aria-label="A long illustrated curb with street objects, drains, weeds and rubbish">
      <rect width="5200" height="520" fill={C} />
      <path d="M0 325H5200V440H0Z" fill={P} />
      <path d="M0 440H5200V520H0Z" fill={C} />
      <path d="M0 325H5200M0 440H5200M0 472H5200" {...line} />

      {/* Background facades and boundary walls */}
      <path d="M0 325V126h430v199M430 325V181h380v144M810 325V94h520v231M1330 325V164h390v161M1720 325V110h560v215M2280 325V189h370v136M2650 325V83h610v242M3260 325V155h440v170M3700 325V104h590v221M4290 325V176h390v149M4680 325V112h520v213" {...fine} />
      <path d="M0 126h430M810 94h520M1720 110h560M2650 83h610M3700 104h590M4680 112h520" {...fine} />
      <path d="M87 325V181h117v144m45 0V181h117v144M873 325V145h157v180m64 0V145h165v180M1791 325V165h183v160m70 0V165h170v160M2730 325V136h198v189m70 0V136h188v189M3782 325V159h188v166m74 0V159h176v166M4760 325V169h162v156m68 0V169h155v156" {...fine} />
      <path d="M108 200h76m87 0h74M901 171h101m120 0h106M1822 194h119m136 0h105M2767 168h124m142 0h119M3817 191h116m142 0h112M4789 201h103m125 0h98" {...fine} />

      {/* Clouds and distant birds */}
      <g className="world-cloud"><path d="M142 79c26-35 65-30 83 0 30-22 73-1 75 34H126c-12-14-5-27 16-34Z" fill={C} stroke={I} strokeWidth="4" /><path d="M521 117c17-22 43-19 55 0 20-14 48 0 50 22H510c-8-9-3-18 11-22Z" fill={C} stroke={I} strokeWidth="4" /></g>
      <g className="world-cloud world-cloud-late"><path d="M2370 76c27-34 65-29 84 0 30-21 72 0 74 34h-173c-12-13-5-26 15-34Z" fill={C} stroke={I} strokeWidth="4" /><path d="M4485 88c22-28 54-23 69 0 24-18 59-1 61 27h-142c-10-11-4-21 12-27Z" fill={C} stroke={I} strokeWidth="4" /></g>
      <path d="M1115 67q18-18 36 0m20 0q18-18 36 0M3390 73q16-16 32 0m18 0q16-16 32 0" {...fine} />

      {/* Segment 1: broken curb, hydrant and weeds */}
      <path d="M0 440l82-23 76 18 91-31 76 31 92-16 89 21 83-28 87 28" {...line} />
      <path d="M58 439l28-64 31 26 36-84 39 53 42-37m-108 70-17-49m69 14 12-42" {...line} />
      <g className="world-hydrant" transform="translate(402 235)"><path d="M53 89v102M19 95h68M28 95V55h50v40M37 55V28h32v27M10 108h20m56 0h20M29 191h49" fill={C} stroke={I} strokeWidth="5" /><circle cx="9" cy="108" r="9" fill={C} stroke={I} strokeWidth="5" /><circle cx="107" cy="108" r="9" fill={C} stroke={I} strokeWidth="5" /></g>
      <g className="world-weeds"><path d="M560 437c2-42-10-78-37-108m39 108c7-54 28-91 64-112m-61 112c33-42 68-64 105-66m-101 66c47-24 88-24 124-1" {...line} /><path d="M523 329c29 1 43 16 42 43-28 0-42-14-42-43Zm103-4c0 29-15 43-42 42 1-28 15-41 42-42Zm44 46c23-18 45-18 65 1-21 19-43 18-65-1Z" fill={C} stroke={I} strokeWidth="4" /></g>

      {/* Segment 2: fence, puddle and lost shoe */}
      <path d="M720 325V142m0 36h580m0-36v183M720 178l580 147M720 242l320-64m-320 128 580-128m-408 147 408-83m-205 83 205-42" {...fine} />
      <path d="M751 325v-33m108 33v-33m108 33v-33m108 33v-33m108 33v-33" {...fine} />
      <g className="world-puddle"><path d="M762 431c46-58 134-65 195-27 63-38 156-25 215 29-83 25-320 26-410-2Z" fill={C} stroke={I} strokeWidth="5" /><path d="M823 420c56-25 103-22 145 3m68-3c34-15 64-14 91 1" {...fine} /></g>
      <g className="world-rubbish"><path d="M1195 430c52-18 92-60 139-79l121 42c12 5 16 21 5 30-59 35-163 37-265 7Z" fill={C} stroke={I} strokeWidth="5" /><path d="M1240 408c40 10 79 7 116-12m-70-22 15-29m53 50 42 14" {...fine} /></g>

      {/* Segment 3: bus stop, posters, bin and litter */}
      <path d="M1536 325V134h314v191m-314-160h314m-268 38h119v84h-119Zm151 0h72v84h-72Z" {...line} />
      <path d="M1570 217l115 57m-109-3 106-54m75 6h47m-47 22h38" {...fine} />
      <g className="world-sign" transform="translate(1875 120)"><path d="M55 64v205M13 64h84V10H13Z" fill={C} stroke={I} strokeWidth="5" /><text x="55" y="34" textAnchor="middle" fill={I} fontSize="14" fontWeight="900">THE CURB</text><text x="55" y="51" textAnchor="middle" fill={I} fontSize="10" fontWeight="800">KEEP GOING →</text></g>
      <g transform="translate(2072 257)"><path d="M15 65 31 8h91l15 57m-112 0h102l-9 111H34Z" fill={C} stroke={I} strokeWidth="5" /><path d="M53 32h48m-61 61h77m-72 29h68" {...fine} /><circle cx="50" cy="187" r="13" fill={C} stroke={I} strokeWidth="5" /><circle cx="105" cy="187" r="13" fill={C} stroke={I} strokeWidth="5" /></g>
      <g className="world-paper"><path d="M2240 414l54-29 33 47-58 20Z" fill={C} stroke={I} strokeWidth="4" /><path d="m2258 411 41 18m-28-30 10 41" {...fine} /></g>

      {/* Segment 4: storm drain, trolley and cracked gutter */}
      <path d="M2310 440l76-18 68 15 78-28 89 31 84-19 73 17 88-24 81 26" {...line} />
      <g transform="translate(2380 333)"><path d="M0 107V18h410v89" fill={I} /><path d="M35 37v52m47-52v52m47-52v52m47-52v52m47-52v52m47-52v52m47-52v52m47-52v52" stroke={C} strokeWidth="9" strokeLinecap="round" /><path d="M-13 14h436" {...line} /></g>
      <g className="world-cart" transform="translate(2850 235)"><path d="M21 43h44l25 144h164l36-111H76m21 33h180m-170 39h158M33 43 19 10H0" fill={C} stroke={I} strokeWidth="5" /><circle cx="114" cy="210" r="17" fill={C} stroke={I} strokeWidth="5" /><circle cx="238" cy="210" r="17" fill={C} stroke={I} strokeWidth="5" /></g>
      <path d="M3090 439l31-72 38 40 44-91 37 59 46-53m-109 72-14-53" {...line} />

      {/* Segment 5: roller door, crates and cardboard shelter */}
      <path d="M3296 325V128h446v197m-402 0V163h356v162m-356-131h356m-356 34h356m-356 34h356m-356 34h356" {...line} />
      <g transform="translate(3330 365)"><path d="M0 70V0h104v70M0 0l52 35L104 0M52 35v35" fill={C} stroke={I} strokeWidth="5" /><path d="M121 70V17h86v53m-86-53 43 27 43-27m-43 27v26" fill={C} stroke={I} strokeWidth="5" /></g>
      <g className="world-rubbish" transform="translate(3570 315)"><path d="M0 120V24h169v96M0 24l82 39 87-39M82 63v57M0 24 34 0l83 27 52-3" fill={C} stroke={I} strokeWidth="5" /><path d="M36 0v56m82-29v47" {...fine} /></g>
      <path d="M3760 440l64-25 76 22 65-32 91 35" {...line} />

      {/* Segment 6: tree roots, bollards, wheel and bottle */}
      <g className="world-tree"><path d="M3990 326c3-84-9-165-36-244m39 244c27-89 36-178 27-267m-29 157c-55-28-95-69-120-123m124 76c47-31 85-76 115-135m-119 183c66-12 125-41 178-88" {...line} /><path d="M3880 440c59-34 104-72 133-114 21 48 70 87 145 114m-214-8 74-46 81 47" {...line} /></g>
      <path d="M4203 440v-92h38v92m51 0v-92h38v92m-109-92v-18h18v18m71 0v-18h18v18" fill={C} stroke={I} strokeWidth="5" />
      <circle cx="4430" cy="383" r="72" fill={C} stroke={I} strokeWidth="7" /><circle cx="4430" cy="383" r="42" fill={P} stroke={I} strokeWidth="5" />
      <g className="world-rubbish" transform="translate(4530 355) rotate(14)"><path d="M0 79 17 0h48l18 79Z" fill={C} stroke={I} strokeWidth="5" /><path d="M14 25h54m-59 28h66" {...fine} /></g>

      {/* Segment 7: utility box, chain fence, skateboard and final puddle */}
      <path d="M4658 325V149h312v176m-312-141h312m-312 0 312 141m-312-70 134-71m-70 141 248-130m-99 130 99-51" {...fine} />
      <g transform="translate(4740 250)"><path d="M0 190V0h178v190" fill={C} stroke={I} strokeWidth="5" /><path d="M24 43h130M24 78h130M24 113h130M24 148h130" {...fine} /><circle cx="145" cy="163" r="8" fill={I} /></g>
      <g className="world-board" transform="translate(4940 397)"><path d="M0 20c35 22 138 22 173 0-16 35-157 35-173 0Z" fill={C} stroke={I} strokeWidth="5" /><circle cx="38" cy="55" r="10" fill={C} stroke={I} strokeWidth="5" /><circle cx="137" cy="55" r="10" fill={C} stroke={I} strokeWidth="5" /></g>
      <g className="world-puddle"><path d="M5070 435c23-34 69-39 102-17 20-17 54-14 76 12-43 14-131 17-178 5Z" fill={C} stroke={I} strokeWidth="5" /></g>

      {/* Small details across the road */}
      <path d="M610 486h120m512 5h165m490-7h110m558 8h147m522-6h119m476 7h156m470-8h123" stroke={I} strokeWidth="4" strokeLinecap="round" strokeDasharray="24 24" />
      <path d="M1458 438l19-16 24 15 31-13m709 14 21-15 26 14m1352 1 23-15 27 14m964 2 18-15 23 13" {...fine} />
    </svg>
  );
}

export function CurbWorld() {
  const scroller = useRef<HTMLDivElement>(null);

  function move(direction: number) {
    scroller.current?.scrollBy({ left: direction * Math.min(window.innerWidth * 0.82, 760), behavior: "smooth" });
  }

  return (
    <div className="relative mt-5 overflow-hidden border-y-2 border-ink bg-cream sm:rounded-[22px] sm:border-2">
      <div className="pointer-events-none absolute left-3 top-3 z-20 rounded-full border-2 border-ink bg-cream px-4 py-2 text-[10px] font-black uppercase tracking-[0.08em] shadow-[3px_3px_0_#1c1a17]">Scroll → there&apos;s more</div>
      <div className="absolute right-3 top-3 z-20 hidden gap-2 sm:flex"><button type="button" onClick={() => move(-1)} aria-label="Explore left" className="press grid h-11 w-11 place-items-center rounded-full border-2 border-ink bg-cream text-xl font-black">←</button><button type="button" onClick={() => move(1)} aria-label="Explore right" className="press grid h-11 w-11 place-items-center rounded-full border-2 border-ink bg-cream text-xl font-black">→</button></div>
      <div ref={scroller} className="no-scrollbar overflow-x-auto overscroll-x-contain cursor-grab active:cursor-grabbing" aria-label="Explore the illustrated Curb world">
        <WorldArt />
      </div>
    </div>
  );
}
