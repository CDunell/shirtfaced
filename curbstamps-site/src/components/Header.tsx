"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useCart } from "@/lib/cart-context";
import { IconCart } from "./Icons";
import { CurbStampsLogo } from "./CurbStampsLogo";

const NAV = [
  { href: "/shop", label: "Shop" },
  { href: "/#crew", label: "Weirdos" },
  { href: "/shop", label: "New" },
  { href: "/about", label: "About" },
];

export function Header() {
  const { itemCount, addTick, hydrated } = useCart();
  const [pop, setPop] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (addTick === 0) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setPop(true);
    const t = setTimeout(() => setPop(false), 280);
    return () => clearTimeout(t);
  }, [addTick]);

  useEffect(() => {
    if (!open) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [open]);

  return (
    <header className="sticky top-0 z-50 border-b border-ink/10 bg-paper/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-4 sm:px-6">
        <Link href="/" aria-label="Curb Stamps home" className="press flex items-center">
          <CurbStampsLogo className="h-[46px] w-auto" />
        </Link>

        <nav className="hidden items-center gap-6 text-[14px] font-extrabold sm:flex">
          {NAV.map((item) => (
            <Link key={item.href + item.label} href={item.href} className="press">
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            aria-controls="mobile-nav-drawer"
            aria-label={open ? "Close menu" : "Open menu"}
            className="press relative z-[60] flex h-11 w-11 items-center justify-center rounded-full sm:hidden"
          >
            <span className="relative block h-5 w-6" aria-hidden="true">
              <span className={`absolute left-0 top-1 h-0.5 w-6 bg-ink transition-transform ${open ? "translate-y-[6px] rotate-45" : ""}`} />
              <span className={`absolute left-0 top-[9px] h-0.5 w-6 bg-ink transition-opacity ${open ? "opacity-0" : ""}`} />
              <span className={`absolute left-0 top-[15px] h-0.5 w-6 bg-ink transition-transform ${open ? "-translate-y-[6px] -rotate-45" : ""}`} />
            </span>
          </button>

          <Link
            href="/cart"
            aria-label={`Cart, ${itemCount} item${itemCount === 1 ? "" : "s"}`}
            className="press relative z-[60] flex h-11 w-11 items-center justify-center rounded-full"
          >
            <IconCart className="h-5 w-5" />
            {hydrated && itemCount > 0 && (
              <span className={`absolute right-0 top-0 flex h-5 min-w-5 items-center justify-center rounded-full bg-grit-pink px-1 text-[11px] font-extrabold text-ink ${pop ? "badge-pop" : ""}`}>
                {itemCount}
              </span>
            )}
          </Link>
        </div>
      </div>

      <div
        aria-hidden="true"
        onClick={() => setOpen(false)}
        className={`fixed inset-x-0 bottom-0 top-16 z-40 bg-ink/45 transition-opacity duration-200 sm:hidden ${open ? "pointer-events-auto opacity-100" : "pointer-events-none opacity-0"}`}
      />

      <aside
        id="mobile-nav-drawer"
        aria-hidden={!open}
        className={`fixed bottom-0 right-0 top-16 z-50 w-[82vw] max-w-[340px] border-l border-ink/10 bg-paper shadow-2xl transition-transform duration-200 ease-out sm:hidden ${open ? "translate-x-0" : "translate-x-full"}`}
      >
        <nav className="flex h-full flex-col px-5 py-6">
          <p className="mb-5 text-[11px] font-black uppercase tracking-[0.16em] text-ink/45">Curb Stamps</p>
          <div className="flex flex-col border-t border-ink/10">
            {NAV.map((item) => (
              <Link
                key={item.href + item.label}
                href={item.href}
                onClick={() => setOpen(false)}
                className="press border-b border-ink/10 py-5 text-[22px] font-black uppercase leading-none"
              >
                {item.label}
              </Link>
            ))}
          </div>
          <div className="mt-auto pt-8 text-[11px] font-bold text-ink/50">Little weirdos. Little clothes.</div>
        </nav>
      </aside>
    </header>
  );
}
