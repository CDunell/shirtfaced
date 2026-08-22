import Link from "next/link";
import { CurbStampsLogoTransparent } from "./CurbStampsLogoTransparent";

const LINKS = [
  { href: "/shop", label: "Shop" },
  { href: "/about", label: "About" },
  { href: "/faq", label: "FAQ" },
  { href: "/shipping", label: "Shipping" },
  { href: "/returns", label: "Returns" },
  { href: "/size-guide", label: "Size guide" },
  { href: "/contact", label: "Contact" },
  { href: "/terms", label: "Terms" },
  { href: "/privacy", label: "Privacy" },
];

export function Footer() {
  return (
    <footer className="border-t border-paper/10 bg-ink text-paper">
      <div className="mx-auto max-w-5xl px-4 pb-10 pt-10 sm:px-6 sm:pb-12">
        <CurbStampsLogoTransparent className="h-[72px] w-auto overflow-visible" />
        <p className="mt-4 max-w-[34ch] text-[13px] font-bold text-paper/70">
          Little weirdos on clothes made for play. Kids roughly 2–10.
        </p>
        <nav className="mt-7 grid grid-cols-2 gap-x-5 gap-y-3 text-[12px] font-extrabold text-paper/75 sm:flex sm:flex-wrap">
          {LINKS.map((l) => (
            <Link key={l.href} href={l.href} className="press hover:text-paper">{l.label}</Link>
          ))}
        </nav>
        <p className="mt-9 pb-1 text-[11px] text-paper/45">© {new Date().getFullYear()} Curb Stamps. Made in Australia.</p>
      </div>
    </footer>
  );
}
