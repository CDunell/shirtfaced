"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useCart } from "@/lib/cart-context";
import { products } from "@/lib/products";
import { ProductMedia } from "./ProductMedia";
import { IconBag, IconClose, IconMenu, IconSearch } from "./Icons";

const SHOP = [
  { href: "/shop", label: "shop all" },
  { href: "/shop?f=new", label: "new drops" },
  { href: "/shop?f=tees", label: "tees" },
  { href: "/shop?f=tanks", label: "tanks" },
  { href: "/shop?f=hoodies", label: "hoodies" },
  { href: "/shop?f=hats", label: "hats" },
  { href: "/shop?f=accessories", label: "accessories" },
];

const COLLECTIONS = [
  { href: "/shop", label: "after dark" },
  { href: "/shop", label: "send it" },
  { href: "/shop", label: "warm nights" },
  { href: "/shop", label: "street" },
];

/* No bottom nav any more, so these live in the menu only. */
const HELP = [
  { href: "/account", label: "account" },
  { href: "/about", label: "about" },
  { href: "/shipping", label: "shipping" },
  { href: "/returns", label: "returns" },
  { href: "/size-guide", label: "size guide" },
  { href: "/contact", label: "contact" },
  { href: "/more", label: "more" },
];

function MegaColumn({
  heading,
  items,
  onNavigate,
}: {
  heading: string;
  items: { href: string; label: string }[];
  onNavigate: () => void;
}) {
  return (
    <div>
      <h3 className="text-[12px] font-semibold tracking-wider text-paper/40 uppercase">
        {heading}
      </h3>
      <ul className="mt-4 flex flex-col gap-2.5">
        {items.map((i) => (
          <li key={i.label}>
            <Link
              href={i.href}
              onClick={onNavigate}
              className="text-[17px] text-paper/85 transition-colors duration-150 hover:text-lime"
            >
              {i.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function Header() {
  const { itemCount, addTick, hydrated } = useCart();
  const [open, setOpen] = useState(false); // mobile full-page menu
  const [mega, setMega] = useState(false); // desktop mega panel
  const [pop, setPop] = useState(false);
  const first = useRef(true);
  const megaWrap = useRef<HTMLDivElement>(null);

  const featured = products.find((p) => p.colours[0].images) ?? products[0];

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
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      setOpen(false);
      setMega(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // Close the mega panel when focus leaves it entirely — keyboard users need
  // an exit that isn't "move the mouse away".
  const onBlurCapture = (e: React.FocusEvent) => {
    if (!megaWrap.current?.contains(e.relatedTarget as Node)) setMega(false);
  };

  const closeAll = () => {
    setOpen(false);
    setMega(false);
  };

  return (
    <>
      <header className="sticky top-0 z-40 bg-ink text-paper">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
          {/* Mobile: hamburger. Desktop: inline nav instead. */}
          <button
            type="button"
            onClick={() => setOpen(true)}
            aria-label="Open menu"
            aria-expanded={open}
            className="press -ml-2 grid h-12 w-12 place-items-center rounded-[14px] md:hidden"
          >
            <IconMenu className="h-6 w-6" />
          </button>

          <Link
            href="/"
            className="press flex items-center md:order-first"
            aria-label="Shirtfaced — home"
          >
            {/* eslint-disable-next-line @next/next/no-img-element -- static export */}
            <img
              src="/logo-v2.png"
              alt="Shirtfaced"
              width={703}
              height={120}
              className="h-[26px] w-auto sm:h-[30px]"
            />
          </Link>

          {/* Desktop nav */}
          <nav
            ref={megaWrap}
            onBlurCapture={onBlurCapture}
            onMouseLeave={() => setMega(false)}
            className="hidden md:flex md:flex-1 md:items-center md:gap-7"
          >
            <button
              type="button"
              onMouseEnter={() => setMega(true)}
              onFocus={() => setMega(true)}
              onClick={() => setMega((m) => !m)}
              aria-expanded={mega}
              aria-controls="mega"
              className={`press h-16 text-[15px] font-semibold tracking-wide uppercase transition-colors ${
                mega ? "text-lime" : "hover:text-lime"
              }`}
            >
              Shop
            </button>
            <Link
              href="/shop?f=new"
              onMouseEnter={() => setMega(false)}
              className="press text-[15px] font-semibold tracking-wide uppercase hover:text-lime"
            >
              New drops
            </Link>
            <Link
              href="/about"
              onMouseEnter={() => setMega(false)}
              className="press text-[15px] font-semibold tracking-wide uppercase hover:text-lime"
            >
              About
            </Link>

            {/* Mega panel — anchored to the header, full bleed */}
            {mega && (
              <div
                id="mega"
                className="fade-rise absolute inset-x-0 top-16 border-t border-ink-line bg-ink"
              >
                <div className="mx-auto grid max-w-6xl grid-cols-[repeat(3,minmax(0,1fr))_320px] gap-10 px-6 py-10">
                  <MegaColumn heading="Shop" items={SHOP} onNavigate={closeAll} />
                  <MegaColumn
                    heading="Collections"
                    items={COLLECTIONS}
                    onNavigate={closeAll}
                  />
                  <MegaColumn heading="Help" items={HELP} onNavigate={closeAll} />

                  <Link
                    href={`/products/${featured.slug}`}
                    onClick={closeAll}
                    className="press group"
                  >
                    <div className="relative aspect-[4/5] overflow-hidden rounded-[20px] bg-paper-2">
                      <ProductMedia
                        product={featured}
                        garment={featured.colours[0]}
                        sizes="320px"
                        className="transition-transform duration-[240ms] group-hover:scale-[1.03]"
                      />
                      <span className="absolute top-3 left-3 rounded-[10px] bg-lime px-2.5 py-1 text-[11px] font-bold tracking-wide text-ink uppercase">
                        Featured
                      </span>
                    </div>
                    <p className="display mt-3 text-[17px]">{featured.name}</p>
                    <p className="text-[14px] text-paper/50">{featured.blurb}</p>
                  </Link>
                </div>
              </div>
            )}
          </nav>

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

      {/* Mobile full-page menu. Desktop uses the mega panel above — a
         full-bleed black page for seven links wastes a 1440px screen. */}
      {open && (
        <div
          className="fixed inset-0 z-50 flex flex-col overflow-y-auto bg-ink text-paper md:hidden"
          role="dialog"
          aria-modal="true"
          aria-label="Menu"
        >
          <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col px-4 pt-5 pb-10 sm:px-6">
            <div className="mb-8 flex items-center justify-between">
              {/* eslint-disable-next-line @next/next/no-img-element -- static export */}
              <img
                src="/logo-v2.png"
                alt="Shirtfaced"
                width={703}
                height={120}
                className="h-[26px] w-auto"
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
              {SHOP.map((m) => (
                <li key={m.label}>
                  <Link
                    href={m.href}
                    onClick={closeAll}
                    className="press block rounded-[14px] py-2.5 text-[30px] leading-tight font-medium"
                  >
                    {m.label}
                  </Link>
                </li>
              ))}
              <li>
                <Link
                  href="/shop"
                  onClick={closeAll}
                  className="press block rounded-[14px] py-2.5 text-[30px] leading-tight font-medium text-pink"
                >
                  sale
                </Link>
              </li>
            </ul>

            <div className="mt-auto border-t border-ink-line pt-8">
              <ul className="flex flex-wrap gap-x-7 gap-y-3 text-[15px] text-paper/55">
                {HELP.map((h) => (
                  <li key={h.href}>
                    <Link href={h.href} onClick={closeAll}>
                      {h.label}
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
