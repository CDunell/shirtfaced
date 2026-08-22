import Link from "next/link";
import { CurbStampsLogo } from "./CurbStampsLogo";

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
    <footer className="border-t border-ink/10 bg-paper-2/60">
      <div className="mx-auto max-w-5xl px-4 py-9 sm:px-6">
        <CurbStampsLogo className="h-[86px] w-auto" />
        <p className="mt-3 max-w-[34ch] text-[13px] font-bold text-grey-dark">
          Little weirdos on clothes made for play. Kids roughly 2–10.
        </p>
        <nav className="mt-6 grid grid-cols-2 gap-x-5 gap-y-3 text-[12px] font-extrabold text-ink/70 sm:flex sm:flex-wrap">
          {LINKS.map((l) => (
            <Link key={l.href} href={l.href} className="press hover:text-ink">{l.label}</Link>
          ))}
        </nav>
        <p className="mt-8 text-[11px] text-grey">© {new Date().getFullYear()} Curb Stamps. Made in Australia.</p>
      </div>
    </footer>
  );
}
