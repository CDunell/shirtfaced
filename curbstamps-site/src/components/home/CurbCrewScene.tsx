import Link from "next/link";
import { CREATURES } from "@/lib/creatures";

function Scene() {
  return (
    <svg viewBox="0 0 800 220" className="w-full" aria-hidden="true">
      <rect width="800" height="220" fill="#fffaf0" />
      <path d="M0 182 H800" stroke="#1c1a17" strokeWidth="4" strokeLinecap="round" />
      <path d="M45 182 V145 H155 V182 M45 145 H155 M80 145 V182 M80 145 L45 182 M80 145 L155 182" fill="none" stroke="#1c1a17" strokeWidth="3" />
      <path d="M620 182 V115" stroke="#1c1a17" strokeWidth="4" strokeLinecap="round" />
      <rect x="576" y="78" width="88" height="40" rx="5" fill="#ffc93c" stroke="#1c1a17" strokeWidth="4" />
      <text x="620" y="103" textAnchor="middle" fontFamily="sans-serif" fontWeight="900" fontSize="15" fill="#1c1a17">WEIRDOS LIVE HERE</text>
      <path d="M282 55 q17 -19 35 0 q14 -12 26 1 q16 -8 24 8 q-6 12 -20 12 h-49 q-15 0 -16 -12 Z" fill="#fffaf0" stroke="#1c1a17" strokeWidth="3" />
      <path d="M710 182 q8 -18 0 -36 M710 166 q-15 -5 -13 -18 M710 155 q15 -5 13 -18" fill="none" stroke="#1c1a17" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

export function CurbCrewScene() {
  const featured = CREATURES.slice(0, 4);
  const cardAccents = ["#ff9fba", "#ffd34f", "#9eddf0", "#b7e85b"];

  return (
    <section id="crew" className="bg-paper">
      <div className="mx-auto max-w-5xl px-4 py-9 sm:px-6 sm:py-12">
        <p className="mb-1 text-[11px] font-black uppercase tracking-[0.16em] text-ink/55">Scroll to explore</p>
        <h2 className="display text-[12vw] uppercase leading-[0.86] sm:text-[46px]">meet the<br />curb crew!</h2>

        <div className="mt-5 overflow-hidden rounded-[20px] border-2 border-ink bg-cream">
          <Scene />
        </div>
        <p className="mt-3 text-center text-[12px] font-black uppercase">Tap a weirdo to see their world ↓</p>

        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {featured.map((c, i) => (
            <Link
              key={c.slug}
              href={`/products/${c.slug}-tee`}
              className="press flex min-h-[145px] flex-col items-center justify-between rounded-[18px] border-2 border-ink p-3 text-center"
              style={{ background: cardAccents[i] }}
            >
              <span className="display self-start text-[17px] uppercase">{c.name}</span>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={`/creatures/${c.slug}-icon.png`} alt={`${c.name} creature`} className="h-20 w-full object-contain" />
              <span className="flex h-7 w-7 items-center justify-center rounded-full border-2 border-ink text-[16px] font-black">→</span>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
