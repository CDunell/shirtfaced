import Link from "next/link";

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
    <footer className="mt-16 border-t-2 border-ink/8 bg-paper-2/60">
      <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
        <p className="display text-[20px]">
          curb <span className="text-grit-pink">stamps</span>
        </p>
        <p className="mt-2 max-w-[46ch] text-[14px] text-grey-dark">
          Little creatures on little clothes. Toddler to teen, screen-printed properly,
          made to be handed down.
        </p>
        <nav className="mt-6 flex flex-wrap gap-x-5 gap-y-2 text-[13px] font-bold text-ink/70">
          {LINKS.map((l) => (
            <Link key={l.href} href={l.href} className="press hover:text-ink">
              {l.label}
            </Link>
          ))}
        </nav>
        <p className="mt-8 text-[12px] text-grey">
          © {new Date().getFullYear()} Curb Stamps. Made in Australia.
        </p>
      </div>
    </footer>
  );
}
