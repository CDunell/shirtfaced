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

/* The bottom nav is gone, so the drawer is the only route to these. */
const SECONDARY = [
  { href: "/account", label: "account" },
  { href: "/about", label: "about" },
  { href: "/shipping", label: "shipping" },
  { href: "/returns", label: "returns" },
  { href: "/size-guide", label: "size guide" },
  { href: "/contact", label: "contact" },
  { href: "/more", label: "more" },
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

      {/* Full-page menu — same treatment at every width. A drawer that only
         partly covers a 1440px screen strands the links in a narrow column
         with a field of empty black beside them. */}
      {open && (
        <div
          className="fixed inset-0 z-50 flex flex-col overflow-y-auto bg-ink text-paper"
          role="dialog"
          aria-modal="true"
          aria-label="Menu"
        >
          <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col px-4 pt-5 pb-10 sm:px-6">
            <div className="mb-8 flex items-center justify-between md:mb-14">
              {/* eslint-disable-next-line @next/next/no-img-element -- static export */}
              <img
                src="/logo-v2.png"
                alt="Shirtfaced"
                width={703}
                height={120}
                className="h-[26px] w-auto sm:h-[32px]"
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
                    className="press block rounded-[14px] py-2.5 text-[30px] leading-tight font-medium md:py-3 md:text-[44px]"
                  >
                    {m.label}
                  </Link>
                </li>
              ))}
              <li>
                <Link
                  href="/shop"
                  onClick={() => setOpen(false)}
                  className="press block rounded-[14px] py-2.5 text-[30px] leading-tight font-medium text-pink md:py-3 md:text-[44px]"
                >
                  sale
                </Link>
              </li>
            </ul>

            {/* Pushed to the foot of the viewport so the menu fills the page
               rather than trailing off. */}
            <div className="mt-auto border-t border-ink-line pt-8">
              <ul className="flex flex-wrap gap-x-7 gap-y-3 text-[15px] text-paper/55">
                {SECONDARY.map((sec) => (
                  <li key={sec.href}>
                    <Link href={sec.href} onClick={() => setOpen(false)}>
                      {sec.label}
                    </Link>
                  </li>
                ))}
              </ul>
              <p className="mt-6 text-[13px] text-paper/35">
                Good times. Bad decisions. Zero regrets.
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
