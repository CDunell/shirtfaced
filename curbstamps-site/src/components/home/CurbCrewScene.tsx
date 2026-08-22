import Link from "next/link";
import { CREATURES } from "@/lib/creatures";

function Scene() {
  return (
    <svg viewBox="0 0 800 220" className="w-full" aria-hidden="true">
      <rect width="800" height="220" fill="#fffaf0" />
      <path d="M0 183 H800" stroke="#1c1a17" strokeWidth="2" strokeLinecap="round" />
      <path d="M40 182 V148 H160 V182 M40 148 H160 M82 148 V182 M82 148 L40 182 M82 148 L160 182" fill="none" stroke="#1c1a17" strokeWidth="2" />
      <path d="M615 182 V118" stroke="#1c1a17" strokeWidth="2" strokeLinecap="round" />
      <rect x="570" y="82" width="92" height="38" rx="4" fill="#fffaf0" stroke="#1c1a17" strokeWidth="2" />
      <text x="616" y="104" textAnchor="middle" fontFamily="sans-serif" fontWeight="800" fontSize="13" fill="#1c1a17">WEIRDOS</text>
      <text x="616" y="116" textAnchor="middle" fontFamily="sans-serif" fontWeight="800" fontSize="10" fill="#1c1a17">LIVE HERE</text>
      <path d="M280 56 q18 -18 36 0 q15 -11 27 1 q15 -7 24 8 q-7 11 -20 11 h-50 q-14 0 -17 -11 Z" fill="#fffaf0" stroke="#1c1a17" strokeWidth="2" />
      <path d="M706 182 q8 -18 0 -35 M706 166 q-15 -5 -13 -18 M706 154 q15 -4 13 -17" fill="none" stroke="#1c1a17" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export function CurbCrewScene() {
  const featured = CREATURES.slice(0, 4);
  const cardAccents = ["#ffb2c7", "#ffd65a", "#addff0", "#c8ef63"];

  return (
    <section id="crew" className="bg-paper">
      <div className="mx-auto max-w-5xl px-4 py-9 sm:px-6 sm:py-12">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="mb-1 text-[10px] font-black uppercase tracking-[0.16em] text-ink/50">Scroll to explore</p>
            <h2 className="display text-[12.5vw] uppercase leading-[0.84] sm:text-[48px]">meet the<br />curb crew!</h2>
          </div>
          <span className="mt-2 text-[34px] leading-none">☁</span>
        </div>

        <div className="mt-4 overflow-hidden border-y border-ink/15 bg-cream sm:rounded-[18px] sm:border-2 sm:border-ink">
          <Scene />
          <div className="flex items-center justify-center gap-2 border-t border-ink/10 py-2 text-[10px] font-black uppercase tracking-[0.08em]">Tap a weirdo to see their world <span>↓</span></div>
        </div>

        <div className="mt-0 grid grid-cols-4 overflow-hidden border-b border-ink/15 sm:mt-4 sm:gap-3 sm:border-0">
          {featured.map((c, i) => (
            <Link
              key={c.slug}
              href={`/products/${c.slug}-tee`}
              className="press flex min-h-[118px] flex-col items-center justify-between border-r border-ink/10 p-2 text-center last:border-r-0 sm:min-h-[150px] sm:rounded-[16px] sm:border-2 sm:border-ink sm:p-3"
              style={{ background: cardAccents[i] }}
            >
              <span className="display self-start text-[13px] uppercase sm:text-[17px]">{c.name}</span>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={`/creatures/${c.slug}-icon.png`} alt={`${c.name} creature`} className="h-14 w-full object-contain sm:h-20" />
              <span className="flex h-6 w-6 items-center justify-center rounded-full border border-ink text-[13px] font-black sm:h-7 sm:w-7">→</span>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
