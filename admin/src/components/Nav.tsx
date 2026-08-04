"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { logoutAction } from "@/app/actions";
import { IconClose, IconMenu } from "./Icons";

const LINKS = [
  { href: "/products", label: "Products" },
  { href: "/content", label: "Content" },
];

export function Nav({
  adminEmail,
  studioUrl,
}: {
  adminEmail: string | null;
  studioUrl: string;
}) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  // Close the panel on navigation (covers back/forward, not just link taps).
  useEffect(() => setOpen(false), [pathname]);

  const isActive = (href: string) => pathname.startsWith(href);

  return (
    <header className="sticky top-0 z-40 border-b border-ink/10 bg-paper/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-4 sm:px-6">
        <Link href="/products" className="wordmark text-[22px]">
          shirtfaced <span className="text-ink/40">/ admin</span>
        </Link>

        {/* Desktop nav — sm and up */}
        <nav className="hidden items-center gap-1 text-[13px] font-semibold tracking-wide uppercase sm:flex">
          {LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              aria-current={isActive(l.href) ? "page" : undefined}
              className={`press rounded-[14px] px-3 py-2 ${
                isActive(l.href) ? "bg-ink text-paper" : "hover:bg-paper-2"
              }`}
            >
              {l.label}
            </Link>
          ))}
          <a
            href={studioUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="press rounded-[14px] px-3 py-2 hover:bg-paper-2"
          >
            Studio ↗
          </a>

          {adminEmail && (
            <form action={logoutAction} className="ml-2">
              <button
                type="submit"
                className="press rounded-[14px] border border-ink/15 px-3 py-2 text-ink/70 hover:bg-paper-2"
              >
                Log out
              </button>
            </form>
          )}
        </nav>

        {/* Mobile toggle — below sm */}
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          aria-label={open ? "Close menu" : "Open menu"}
          aria-expanded={open}
          aria-controls="admin-mobile-nav"
          className="press -mr-2 grid h-11 w-11 place-items-center rounded-[14px] sm:hidden"
        >
          {open ? <IconClose className="h-6 w-6" /> : <IconMenu className="h-6 w-6" />}
        </button>
      </div>

      {/* Mobile panel */}
      {open && (
        <nav
          id="admin-mobile-nav"
          className="fade-rise border-t border-ink/10 px-4 pb-4 sm:hidden"
        >
          <ul className="flex flex-col gap-1 pt-3 text-[15px] font-semibold tracking-wide uppercase">
            {LINKS.map((l) => (
              <li key={l.href}>
                <Link
                  href={l.href}
                  aria-current={isActive(l.href) ? "page" : undefined}
                  className={`press flex h-12 items-center rounded-[14px] px-3 ${
                    isActive(l.href) ? "bg-ink text-paper" : "hover:bg-paper-2"
                  }`}
                >
                  {l.label}
                </Link>
              </li>
            ))}
            <li>
              <a
                href={studioUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="press flex h-12 items-center rounded-[14px] px-3 hover:bg-paper-2"
              >
                Studio ↗
              </a>
            </li>
          </ul>

          {adminEmail && (
            <form action={logoutAction} className="mt-3 border-t border-ink/10 pt-3">
              <button
                type="submit"
                className="press flex h-12 w-full items-center justify-center rounded-[14px] border border-ink/15 text-[13px] font-semibold tracking-wide text-ink/70 uppercase"
              >
                Log out
              </button>
            </form>
          )}
        </nav>
      )}
    </header>
  );
}
