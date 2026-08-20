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

/**
 * Replaces the old top-header Nav (see docs/ADMIN_STUDIO_UI_OVERHAUL_PLAN.md
 * Phase 1). Admin and Studio now sit as a symmetric, always-visible pair
 * pinned at the sidebar's bottom, not a link bolted onto a tab row.
 */
export function Sidebar({
  adminEmail,
  studioUrl,
}: {
  adminEmail: string | null;
  studioUrl: string;
}) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  // Close the mobile drawer on navigation (covers back/forward, not just link taps).
  useEffect(() => setOpen(false), [pathname]);

  const isActive = (href: string) => pathname.startsWith(href);

  const body = (
    <>
      <Link href="/products" className="wordmark block px-4 pt-6 pb-3 text-[22px]">
        shirtfaced <span className="text-ink/40">/ admin</span>
      </Link>

      <nav className="flex flex-1 flex-col gap-1 px-3 py-2 text-[13px] font-semibold tracking-wide uppercase">
        {LINKS.map((l) => (
          <Link
            key={l.href}
            href={l.href}
            aria-current={isActive(l.href) ? "page" : undefined}
            className={`press rounded-[14px] px-3 py-2.5 ${
              isActive(l.href) ? "bg-ink text-paper" : "hover:bg-paper-2"
            }`}
          >
            {l.label}
          </Link>
        ))}
      </nav>

      {adminEmail && (
        <form action={logoutAction} className="px-3 pt-2">
          <button
            type="submit"
            className="press flex h-11 w-full items-center justify-center rounded-[14px] border border-ink/15 text-[13px] font-semibold tracking-wide text-ink/70 uppercase hover:bg-paper-2"
          >
            Log out
          </button>
        </form>
      )}

      {/* Pinned bottom: Admin | Studio, symmetric peers -- Studio's own sidebar
          mirrors this exact pair the other way round. */}
      <div className="mt-2 border-t border-ink/10 p-3">
        <div className="flex gap-1 rounded-[14px] bg-paper-2 p-1">
          <span className="flex-1 rounded-[10px] bg-ink px-3 py-2 text-center text-[12px] font-bold tracking-wide text-paper uppercase">
            Admin
          </span>
          <a
            href={studioUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="press flex-1 rounded-[10px] px-3 py-2 text-center text-[12px] font-bold tracking-wide text-ink/60 uppercase hover:bg-paper"
          >
            Studio
          </a>
        </div>
      </div>
    </>
  );

  return (
    <>
      {/* Mobile top bar -- the sidebar collapses into a drawer below sm */}
      <div className="sticky top-0 z-40 flex h-16 items-center justify-between border-b border-ink/10 bg-paper/95 px-4 backdrop-blur sm:hidden">
        <Link href="/products" className="wordmark text-[22px]">
          shirtfaced <span className="text-ink/40">/ admin</span>
        </Link>
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          aria-label={open ? "Close menu" : "Open menu"}
          aria-expanded={open}
          aria-controls="admin-sidebar-drawer"
          className="press -mr-2 grid h-11 w-11 place-items-center rounded-[14px]"
        >
          {open ? <IconClose className="h-6 w-6" /> : <IconMenu className="h-6 w-6" />}
        </button>
      </div>

      {open && (
        <div
          className="fixed inset-0 z-50 flex bg-ink/40 sm:hidden"
          onClick={() => setOpen(false)}
        >
          <aside
            id="admin-sidebar-drawer"
            className="fade-rise flex h-full w-72 flex-col bg-paper"
            onClick={(e) => e.stopPropagation()}
          >
            {body}
          </aside>
        </div>
      )}

      {/* Desktop sidebar */}
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r border-ink/10 sm:flex">
        {body}
      </aside>
    </>
  );
}
