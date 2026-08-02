"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCart } from "@/lib/cart-context";
import { IconBag, IconBolt, IconDots, IconSmiley, IconUser } from "./Icons";

const TABS = [
  { href: "/", label: "Home", Icon: IconSmiley },
  { href: "/shop", label: "Shop", Icon: IconBag },
  { href: "/shop?f=new", label: "New", Icon: IconBolt },
  { href: "/account", label: "Account", Icon: IconUser },
  { href: "/more", label: "More", Icon: IconDots },
];

export function BottomNav() {
  const pathname = usePathname();
  const { itemCount, hydrated } = useCart();

  return (
    <nav
      aria-label="Primary"
      className="fixed inset-x-0 bottom-0 z-40 border-t border-ink-line bg-ink pb-[env(safe-area-inset-bottom)] text-paper"
    >
      <ul className="mx-auto flex max-w-5xl items-stretch justify-between px-2">
        {TABS.map(({ href, label, Icon }) => {
          const base = href.split("?")[0];
          const active =
            base === "/" ? pathname === "/" : pathname.startsWith(base);
          return (
            <li key={label} className="flex-1">
              <Link
                href={href}
                aria-current={active ? "page" : undefined}
                className={`press relative flex h-[68px] min-w-[48px] flex-col items-center justify-center gap-1 rounded-[14px] ${
                  active ? "text-lime" : "text-paper/55"
                }`}
              >
                <span className="relative">
                  <Icon className="h-[26px] w-[26px]" />
                  {label === "Shop" && hydrated && itemCount > 0 && (
                    <span className="absolute -top-1.5 -right-2.5 grid h-[17px] min-w-[17px] place-items-center rounded-full bg-lime px-1 text-[10px] font-bold text-ink tabular-nums">
                      {itemCount}
                    </span>
                  )}
                </span>
                <span className="text-[11px] font-semibold tracking-wide uppercase">
                  {label}
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
