import Link from "next/link";
import { CREATURES } from "@/lib/creatures";
import { IconArrowRight } from "@/components/Icons";

/**
 * Section E — "MEET THE CURB CREW" (DESIGN_HANDOFF.md §4.E). The scene is a
 * simple, hand-built line illustration (curb, box, sign, cloud, plant) — not
 * the full illustrated spread the handoff describes under
 * public/curbstamps/scenes/curb-crew.svg. That's real illustration work for
 * a follow-up pass; this gets the section live with the same picture-book
 * feel using basic shapes rather than blocking the whole homepage on it.
 */
function Scene() {
  return (
    <svg viewBox="0 0 800 220" className="w-full" aria-hidden="true">
      <path d="M0 190 H800 V220 H0 Z" fill="var(--color-paper-2)" />
      <path d="M0 178 H800" stroke="#1c1a17" strokeWidth="4" strokeLinecap="round" />
      <path d="M60 178 V150 H160 V178" fill="none" stroke="#1c1a17" strokeWidth="4" strokeLinejoin="round" />
      <path d="M60 150 H160 M95 150 V178 M95 150 L60 178 M95 150 L160 178" stroke="#1c1a17" strokeWidth="3" fill="none" />
      <path d="M620 178 V125" stroke="#1c1a17" strokeWidth="4" strokeLinecap="round" />
      <rect x="588" y="90" width="64" height="36" rx="6" fill="var(--color-grit-yellow)" stroke="#1c1a17" strokeWidth="4" />
      <text x="620" y="113" textAnchor="middle" fontFamily="'Baloo 2', sans-serif" fontWeight="700" fontSize="16" fill="#1c1a17">CURB</text>
      <circle cx="700" cy="55" r="18" fill="none" stroke="#1c1a17" strokeWidth="3" />
      <path d="M300 60 q18 -22 36 0 q14 -14 26 2 q16 -10 24 8 q-6 14 -22 14 h-50 q-16 0 -14 -14 Z" fill="var(--color-cream)" stroke="#1c1a17" strokeWidth="3" />
      <path d="M420 176 q6 -16 0 -30" fill="none" stroke="#1c1a17" strokeWidth="3" strokeLinecap="round" />
      <path d="M420 176 q-14 -6 -10 -20 M420 160 q14 -4 12 -16" fill="none" stroke="#1c1a17" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

export function CurbCrewScene() {
  const featured = CREATURES.slice(0, 4);
  const cardAccents = ["var(--color-grit-pink)", "var(--color-grit-yellow)", "var(--color-grit-blue)", "var(--color-grit-green)"];

  return (
    <section id="crew" className="bg-paper">
      <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
        <h2 className="display text-[11vw] leading-[0.9] sm:text-[42px]">meet the curb crew!</h2>
        <div className="mt-6 overflow-hidden rounded-[24px] border-2 border-ink/10 bg-cream">
          <Scene />
        </div>
        <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
          {featured.map((c, i) => (
            <Link
              key={c.slug}
              href={`/products/${c.slug}-tee`}
              className="press flex flex-col items-center gap-2 rounded-[22px] p-4 text-center"
              style={{ background: cardAccents[i] }}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={`/curbstamps/creatures/${c.slug}-dark.svg`} alt="" aria-hidden="true" className="h-16 w-full object-contain" />
              <span className="display text-[18px]">{c.name}</span>
              <span className="press inline-flex items-center gap-1 text-[12px] font-extrabold" aria-label={`View ${c.name} products`}>
                Shop <IconArrowRight className="h-3.5 w-3.5" />
              </span>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
