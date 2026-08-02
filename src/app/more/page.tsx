import Link from "next/link";
import { IconArrowRight } from "@/components/Icons";

export const metadata = { title: "More — Shirtfaced" };

const LINKS = [
  { href: "/about", label: "About", note: "Who's behind this" },
  { href: "/size-guide", label: "Size guide", note: "Measurements, honestly" },
  { href: "/shipping", label: "Shipping", note: "Where and how fast" },
  { href: "/returns", label: "Returns", note: "No drama" },
  { href: "/contact", label: "Contact", note: "Talk to a human" },
];

export default function MorePage() {
  return (
    <div className="mx-auto max-w-2xl px-4 pt-8 pb-16 sm:px-6">
      <h1 className="display distressed text-[16vw] leading-[0.84] sm:text-[76px]">
        more
      </h1>

      <ul className="mt-8 flex flex-col">
        {LINKS.map((l) => (
          <li key={l.href}>
            <Link
              href={l.href}
              className="press flex items-center justify-between gap-4 border-b border-ink/10 py-5"
            >
              <span>
                <span className="display block text-[22px]">{l.label}</span>
                <span className="mt-0.5 block text-[14px] text-grey-dark">
                  {l.note}
                </span>
              </span>
              <IconArrowRight className="h-5 w-5 shrink-0 text-grey-dark" />
            </Link>
          </li>
        ))}
      </ul>

      <div className="mt-10 rounded-[20px] bg-ink px-6 py-7 text-paper">
        <p className="display text-[22px] leading-tight">
          bad financial decisions since 2026
        </p>
        <p className="mt-2 text-[14px] text-paper/60">
          Designed in Australia. Printed properly. Worn badly.
        </p>
      </div>

      <p className="mt-8 text-[13px] text-grey-dark">
        © {new Date().getFullYear()} Shirtfaced. All rights reserved, most
        regrets retained.
      </p>
    </div>
  );
}
