"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useCart } from "@/lib/cart-context";
import { IconCart } from "./Icons";

export function Header() {
  const { itemCount, addTick, hydrated } = useCart();
  const [pop, setPop] = useState(false);

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
    <header className="sticky top-0 z-40 border-b-2 border-ink/8 bg-paper/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-4 sm:px-6">
        <Link href="/" className="display text-[22px] tracking-tight">
          curb <span className="text-grit-pink">stamps</span>
        </Link>
        <nav className="hidden items-center gap-6 text-[14px] font-bold sm:flex">
          <Link href="/shop" className="press">
            Shop
          </Link>
          <Link href="/about" className="press">
            About
          </Link>
          <Link href="/faq" className="press">
            FAQ
          </Link>
        </nav>
        <Link
          href="/cart"
          aria-label={`Cart, ${itemCount} item${itemCount === 1 ? "" : "s"}`}
          className="press relative flex h-11 w-11 items-center justify-center rounded-full bg-ink text-paper"
        >
          <IconCart className="h-5 w-5" />
          {hydrated && itemCount > 0 && (
            <span
              className={`absolute -top-1 -right-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-grit-pink px-1 text-[11px] font-extrabold text-ink ${
                pop ? "badge-pop" : ""
              }`}
            >
              {itemCount}
            </span>
          )}
        </Link>
      </div>
    </header>
  );
}
