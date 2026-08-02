"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useCart } from "@/lib/cart-context";
import { IconBag, IconClose, IconMenu, IconSearch } from "./Icons";

const MENU = [
  { href: "/shop", label: "shop all" },
  { href: "/shop?f=new", label: "new drops" },
  { href: "/shop?f=tees", label: "tees" },
  { href: "/shop?f=tanks", label: "tanks" },
  { href: "/shop?f=hoodies", label: "hoodies" },
  { href: "/shop?f=hats", label: "hats" },
  { href: "/shop?f=accessories", label: "accessories" },
];

const SECONDARY = [
  { href: "/about", label: "about" },
  { href: "/shipping", label: "shipping" },
  { href: "/returns", label: "returns" },
  { href: "/size-guide", label: "size guide" },
  { href: "/contact", label: "contact" },
];

export function Header() {
  const { itemCount, addTick, hydrated } = useCart();
  const [open, setOpen] = useState(false);
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

  return (
    <>
      <header className="sticky top-0 z-40 bg-ink text-paper">
        <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-4 sm:px-6">
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
            className="press flex items-center gap-1.5"
            aria-label="Shirtfaced — home"
          >
            {/* eslint-disable-next-line @next/next/no-img-element -- static
                export; explicit dimensions keep CLS at zero */}
            <img
              src="/logo-v2.png"
              alt="Shirtfaced"
              width={703}
              height={120}
              className="h-[26px] w-auto sm:h-[32px]"
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

      {/* Drawer */}
      {open && (
        <div className="fixed inset-0 z-50" role="dialog" aria-modal="true">
          <button
            aria-label="Close menu"
            onClick={() => setOpen(false)}
            className="absolute inset-0 bg-ink/70 backdrop-blur-[2px]"
          />
          <nav className="sheet-up absolute inset-x-0 top-0 max-h-[92vh] overflow-y-auto rounded-b-[28px] bg-ink px-6 pt-5 pb-10 text-paper">
            <div className="mb-7 flex items-center justify-between">
              {/* eslint-disable-next-line @next/next/no-img-element -- static export */}
              <img
                src="/logo-v2.png"
                alt="Shirtfaced"
                width={703}
                height={120}
                className="h-[30px] w-auto"
              />
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Close menu"
                className="press -mr-2 grid h-12 w-12 place-items-center rounded-[14px]"
              >
                <IconClose className="h-6 w-6" />
              </button>
            </div>

            <ul className="flex flex-col gap-1">
              {MENU.map((m) => (
                <li key={m.label}>
                  <Link
                    href={m.href}
                    onClick={() => setOpen(false)}
                    className="press block rounded-[14px] py-2.5 text-[28px] leading-tight font-medium"
                  >
                    {m.label}
                  </Link>
                </li>
              ))}
              <li>
                <Link
                  href="/shop"
                  onClick={() => setOpen(false)}
                  className="press block rounded-[14px] py-2.5 text-[28px] leading-tight font-medium text-pink"
                >
                  sale
                </Link>
              </li>
            </ul>

            <div className="mt-7 border-t border-ink-line pt-6">
              <ul className="flex flex-col gap-3 text-[15px] text-paper/60">
                {SECONDARY.map((s) => (
                  <li key={s.href}>
                    <Link href={s.href} onClick={() => setOpen(false)}>
                      {s.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          </nav>
        </div>
      )}
    </>
  );
}
