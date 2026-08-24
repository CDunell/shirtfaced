import Link from "next/link";
import { CurbStampsLogoTransparent } from "./CurbStampsLogoTransparent";
import { CREATURES, creatureMaster } from "@/lib/creatures";

const LINKS = [
  { href: "/size-guide", label: "Sizing" },
  { href: "/shipping", label: "Shipping" },
  { href: "/returns", label: "Returns" },
  { href: "/faq", label: "FAQ" },
  { href: "/contact", label: "Contact" },
  { href: "/about", label: "About" },
  { href: "/terms", label: "Terms" },
  { href: "/privacy", label: "Privacy" },
];

export function Footer() {
  return (
    <footer className="border-t-2 border-paper/15 bg-ink text-paper">
      <div className="mx-auto max-w-[1180px] px-4 pb-8 pt-10 md:px-6 md:pb-10 md:pt-14 lg:px-8 xl:px-0">
        <div className="grid gap-8 md:grid-cols-[1fr_1.4fr] md:items-start lg:gap-16">
          <div>
            <span className="inline-flex border-2 border-ink bg-violet px-3 py-2">
              <CurbStampsLogoTransparent className="h-[64px] w-auto overflow-visible lg:h-[76px]" />
            </span>
            <p className="mt-4 max-w-[30ch] text-[13px] font-bold leading-relaxed text-paper/65">Little weirdos on clothes made for play. Kids roughly 2–10.</p>
          </div>
          <nav className="grid grid-cols-2 border-t border-paper/15 text-[12px] font-extrabold uppercase tracking-[0.04em] md:grid-cols-4">
            {LINKS.map((link) => (
              <Link key={link.href} href={link.href} className="press min-h-12 border-b border-paper/15 py-4 hover:text-club">{link.label}</Link>
            ))}
          </nav>
        </div>

        <div className="mt-10 grid grid-cols-9 items-end gap-1 border-y border-paper/15 py-5 md:grid-cols-[repeat(18,minmax(0,1fr))] md:gap-2">
          {CREATURES.filter((creature) => creature.slug !== "dreg").slice(0, 18).map((creature) => (
            // eslint-disable-next-line @next/next/no-img-element
            <img key={creature.slug} src={creatureMaster(creature.slug)} alt="" aria-hidden="true" className="h-7 w-full object-contain brightness-0 invert opacity-80 md:h-9" />
          ))}
        </div>

        <div className="mt-6 flex flex-wrap items-center justify-between gap-4 text-[10px] font-black uppercase tracking-[0.06em] text-paper/45">
          <p>© {new Date().getFullYear()} Curb Stamps. Made in Australia.</p>
          <p>Instagram · TikTok</p>
        </div>
      </div>
    </footer>
  );
}
