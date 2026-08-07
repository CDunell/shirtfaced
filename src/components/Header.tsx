"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useCart } from "@/lib/cart-context";
import {
  IconArrowRight,
  IconBag,
  IconClose,
  IconMenu,
  IconMinus,
  IconPlus,
  IconSearch,
} from "./Icons";

/* Groups collapse behind a +/- like the reference. Direct links have no
   `items` and render as a plain row. */
type Group = {
  label: string;
  href?: string;
  accent?: boolean;
  items?: { href: string; label: string }[];
};

const NAV: Group[] = [
  { label: "New drops", href: "/shop?f=new" },
  {
    label: "Shop by category",
    items: [
      { href: "/shop?f=tees", label: "Tees" },
      { href: "/shop?f=tanks", label: "Tanks" },
      { href: "/shop?f=hoodies", label: "Hoodies" },
      { href: "/shop?f=hats", label: "Hats" },
      { href: "/shop?f=accessories", label: "Accessories" },
    ],
  },
  {
    label: "Collections",
    items: [
      { href: "/shop", label: "After dark" },
      { href: "/shop", label: "Send it" },
      { href: "/shop", label: "Warm nights" },
      { href: "/shop", label: "Street" },
    ],
  },
  { label: "More", href: "/more" },
  { label: "About", href: "/about" },
  { label: "Sale", href: "/shop", accent: true },
];

export function Header() {
  const { itemCount, addTick, hydrated } = useCart();
  const [open, setOpen] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [pop, setPop] = useState(false);
  const first = useRef(true);

  // Badge pops on add — communicates, doesn't decorate.
  useEffect(() => {
    if (first.current) {
      first.current = false;
      return;
    }
    setPop(true);
    const t = setTimeout(() => setPop(false), 260);
    return () => clearTimeout(t);
  }, [addTick]);

  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const close = () => setOpen(false);

  return (
    <>
      <header className="sticky top-0 z-40 bg-ink text-paper">
        <div className="mx-auto flex h-20 max-w-6xl items-center justify-between px-4 sm:px-6">
          <button
            type="button"
            onClick={() => setOpen(true)}
            aria-label="Open menu"
            aria-expanded={open}
            className="press -ml-2 grid h-12 w-12 place-items-center rounded-[14px]"
          >
            <IconMenu className="h-6 w-6" />
          </button>

          <Link
            href="/"
            className="press flex items-center"
            aria-label="shirtfaced — home"
          >
            {/* eslint-disable-next-line @next/next/no-img-element -- static export */}
            <img
              src="/logo-lockup.png"
              alt="shirtfaced"
              width={531}
              height={140}
              className="h-[38px] w-auto translate-y-[5px] sm:h-[46px] sm:translate-y-[6px]"
            />
          </Link>

          <div className="flex items-center">
            <Link
              href="/search"
              aria-label="Search"
              className="press grid h-12 w-12 place-items-center rounded-[14px]"
            >
              <IconSearch className="h-6 w-6" />
            </Link>
            <Link
              href="/cart"
              aria-label={`Cart, ${itemCount} item${itemCount === 1 ? "" : "s"}`}
              className="press relative -mr-2 grid h-12 w-12 place-items-center rounded-[14px]"
            >
              <IconBag className="h-6 w-6" />
              {hydrated && itemCount > 0 && (
                <span
                  className={`absolute top-1.5 right-1 grid h-[19px] min-w-[19px] place-items-center rounded-full bg-lime px-1 text-[11px] font-bold text-ink tabular-nums ${
                    pop ? "badge-pop" : ""
                  }`}
                >
                  {itemCount}
                </span>
              )}
            </Link>
          </div>
        </div>
      </header>

      {/* Left slide-in panel at every width. On mobile it takes the full
         screen; from sm it caps at 400px with the page dimmed behind. */}
      {open && (
        <div className="fixed inset-0 z-50" role="dialog" aria-modal="true" aria-label="Menu">
          <button
            aria-label="Close menu"
            onClick={close}
            className="fade-in absolute inset-0 bg-ink/60 backdrop-blur-[2px]"
          />

          <div className="slide-left absolute inset-y-0 left-0 flex w-full max-w-[400px] flex-col bg-ink text-paper">
            <div className="flex h-20 shrink-0 items-center justify-between px-4 sm:px-6">
              {/* eslint-disable-next-line @next/next/no-img-element -- static export */}
              <img
                src="/logo-lockup.png"
                alt="shirtfaced"
                width={531}
                height={140}
                className="h-[36px] w-auto translate-y-[5px]"
              />
              <button
                type="button"
                onClick={close}
                aria-label="Close menu"
                className="press -mr-2 grid h-12 w-12 place-items-center rounded-[14px]"
              >
                <IconClose className="h-6 w-6" />
              </button>
            </div>

            <nav className="flex-1 overflow-y-auto px-4 pt-3 sm:px-6">
              <ul className="flex flex-col">
                {NAV.map((g) => {
                  const isOpen = expanded === g.label;

                  if (!g.items) {
                    return (
                      <li key={g.label}>
                        <Link
                          href={g.href!}
                          onClick={close}
                          className={`press flex h-14 items-center text-[19px] font-medium ${
                            g.accent ? "text-pink" : ""
                          }`}
                        >
                          {g.label}
                        </Link>
                      </li>
                    );
                  }

                  return (
                    <li key={g.label}>
                      <button
                        type="button"
                        onClick={() => setExpanded(isOpen ? null : g.label)}
                        aria-expanded={isOpen}
                        className="press flex h-14 w-full items-center justify-between text-left text-[19px] font-medium"
                      >
                        {g.label}
                        {isOpen ? (
                          <IconMinus className="h-5 w-5 text-paper/60" />
                        ) : (
                          <IconPlus className="h-5 w-5 text-paper/60" />
                        )}
                      </button>

                      {isOpen && (
                        <ul className="fade-rise mb-2 flex flex-col border-l border-ink-line pl-4">
                          {g.items.map((i) => (
                            <li key={i.label}>
                              <Link
                                href={i.href}
                                onClick={close}
                                className="press flex h-11 items-center text-[16px] text-paper/70"
                              >
                                {i.label}
                              </Link>
                            </li>
                          ))}
                        </ul>
                      )}
                    </li>
                  );
                })}
              </ul>

              <div className="mt-6 flex flex-col gap-3 border-t border-ink-line pt-6 text-[15px] text-paper/55">
                <Link href="/account" onClick={close}>
                  Account
                </Link>
                <Link href="/search" onClick={close}>
                  Search
                </Link>
                <span className="text-paper/35">AUD $</span>
                {/* Staff-facing, not a customer feature — kept last and quiet. */}
                <a href="https://admin.shirtfaced.wtf" className="text-paper/35">
                  Admin
                </a>
              </div>
            </nav>

            <div className="shrink-0 px-4 pt-4 pb-[calc(20px+env(safe-area-inset-bottom))] sm:px-6">
              <Link
                href="/shop"
                onClick={close}
                className="press flex h-14 items-center justify-center gap-2.5 rounded-[18px] bg-paper text-[16px] font-bold text-ink"
              >
                Shop all
                <IconArrowRight className="h-5 w-5" />
              </Link>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
