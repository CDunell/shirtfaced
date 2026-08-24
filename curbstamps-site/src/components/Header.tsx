"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useCart } from "@/lib/cart-context";
import { IconCart } from "./Icons";
import { CurbStampsLogoTransparent } from "./CurbStampsLogoTransparent";

const NAV = [
  { href: "/shop", label: "Shop" },
  { href: "/#crew", label: "Creatures" },
  { href: "/shop", label: "New" },
  { href: "/about", label: "About" },
  { href: "/#club", label: "Club" },
];

export function Header() {
  const { itemCount, addTick, hydrated } = useCart();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = previous; };
  }, [open]);

  return (
    <header className="sticky top-0 z-50 border-b-2 border-paper/15 bg-ink text-paper">
      <div className="mx-auto flex h-[66px] max-w-[1180px] items-center justify-between px-4 md:h-[74px] md:px-6 lg:h-[82px] lg:px-8 xl:px-0">
        <Link href="/" aria-label="Curb Stamps home" className="brand-sticker press flex h-[58px] w-[150px] items-center justify-center md:h-[66px] md:w-[172px] lg:h-[74px] lg:w-[190px]">
          <CurbStampsLogoTransparent className="brand-sticker-logo h-[48px] w-auto md:h-[54px] lg:h-[60px]" />
        </Link>

        <nav className="hidden items-center gap-8 font-display text-[17px] font-extrabold uppercase tracking-[0.045em] lg:flex xl:gap-11 xl:text-[18px]">
          {NAV.map((item) => (
            <Link key={item.href + item.label} href={item.href} className="press border-b-2 border-transparent py-3 text-paper hover:border-club hover:text-club">{item.label}</Link>
          ))}
        </nav>

        <div className="flex items-center gap-1 md:gap-2">
          <button type="button" onClick={() => setOpen((value) => !value)} aria-expanded={open} aria-controls="mobile-nav-drawer" aria-label={open ? "Close menu" : "Open menu"} className="press relative z-[60] flex h-11 w-11 items-center justify-center text-paper lg:hidden">
            <span className="relative block h-5 w-6" aria-hidden="true">
              <span className={`absolute left-0 top-1 h-0.5 w-6 bg-paper transition-transform ${open ? "translate-y-[6px] rotate-45" : ""}`} />
              <span className={`absolute left-0 top-[9px] h-0.5 w-6 bg-paper transition-opacity ${open ? "opacity-0" : ""}`} />
              <span className={`absolute left-0 top-[15px] h-0.5 w-6 bg-paper transition-transform ${open ? "-translate-y-[6px] -rotate-45" : ""}`} />
            </span>
          </button>

          <Link href="/cart" aria-label={`Cart, ${itemCount} item${itemCount === 1 ? "" : "s"}`} className="press relative z-[60] flex h-11 w-11 items-center justify-center text-paper">
            <IconCart className="h-5 w-5 lg:h-6 lg:w-6" />
            {hydrated && itemCount > 0 && (
              <span key={addTick} className={`absolute right-0 top-0 flex h-5 min-w-5 items-center justify-center rounded-full bg-club px-1 text-[11px] font-extrabold text-ink ${addTick > 0 ? "badge-pop" : ""}`}>{itemCount}</span>
            )}
          </Link>
        </div>
      </div>

      <button aria-label="Close menu" onClick={() => setOpen(false)} className={`fixed inset-x-0 bottom-0 top-[66px] z-40 bg-black/70 transition-opacity duration-200 md:top-[74px] lg:hidden ${open ? "pointer-events-auto opacity-100" : "pointer-events-none opacity-0"}`} />

      <aside id="mobile-nav-drawer" aria-hidden={!open} className={`fixed bottom-0 right-0 top-[66px] z-50 w-[84vw] max-w-[360px] border-l-2 border-paper/15 bg-ink text-paper shadow-2xl transition-transform duration-200 ease-out md:top-[74px] lg:hidden ${open ? "translate-x-0" : "translate-x-full"}`}>
        <nav className="flex h-full flex-col px-5 py-7">
          <div className="flex flex-col border-t border-paper/15">
            {NAV.map((item) => (
              <Link key={item.href + item.label} href={item.href} onClick={() => setOpen(false)} className="press border-b border-paper/15 py-4 font-display text-[31px] font-extrabold uppercase leading-none text-paper md:text-[36px]">{item.label}</Link>
            ))}
          </div>
          <div className="mt-auto border-t border-paper/15 pt-5 text-[11px] font-black uppercase tracking-[0.08em] text-paper/50">Welcome to the curb.</div>
        </nav>
      </aside>
    </header>
  );
}
