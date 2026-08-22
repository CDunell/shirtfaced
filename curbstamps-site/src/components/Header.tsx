"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useCart } from "@/lib/cart-context";
import { IconCart } from "./Icons";

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
    // Bumps a CSS animation class on every add — genuinely reacting to an
    // external event (addTick from cart-context), not state this component
    // could derive during render.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setPop(true);
    const t = setTimeout(() => setPop(false), 280);
    return () => clearTimeout(t);
  }, [addTick]);

  return (
    <header className="sticky top-0 z-50 border-b border-ink/10 bg-paper/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-4 sm:px-6">
        <Link href="/" className="display leading-[0.8] text-[19px] uppercase tracking-[-0.04em]">
          curb<br />stamps
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
            aria-label="Open menu"
            className="press flex h-11 w-11 items-center justify-center rounded-full sm:hidden"
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
            className="press relative flex h-11 w-11 items-center justify-center rounded-full"
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

      {open && (
        <nav className="border-t border-ink/10 bg-paper px-4 py-3 sm:hidden">
          <div className="grid grid-cols-2 gap-2">
            {NAV.map((item) => (
              <Link
                key={item.href + item.label}
                href={item.href}
                onClick={() => setOpen(false)}
                className="press rounded-2xl bg-paper-2 px-4 py-4 text-[15px] font-extrabold"
              >
                {item.label}
              </Link>
            ))}
          </div>
        </nav>
      )}
    </header>
  );
}
