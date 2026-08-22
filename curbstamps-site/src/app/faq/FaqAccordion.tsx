"use client";

import { useState } from "react";
import Link from "next/link";
import { IconPlus } from "@/components/Icons";

export type FaqItem = {
  question: string;
  answer: string;
  linkHref?: string;
  linkLabel?: string;
};

export function FaqAccordion({ items }: { items: FaqItem[] }) {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <ul className="flex flex-col divide-y-2 divide-ink/8 border-y-2 border-ink/8">
      {items.map((item, i) => {
        const isOpen = open === i;
        return (
          <li key={item.question}>
            <button
              type="button"
              onClick={() => setOpen(isOpen ? null : i)}
              aria-expanded={isOpen}
              className="press flex w-full items-center justify-between gap-4 py-4 text-left"
            >
              <span className="text-[15px] font-extrabold">{item.question}</span>
              <IconPlus className={`h-5 w-5 shrink-0 transition-transform ${isOpen ? "rotate-45" : ""}`} />
            </button>
            {isOpen && (
              <p className="fade-rise pb-4 text-[14px] leading-relaxed text-ink/70">
                {item.answer}{" "}
                {item.linkHref && item.linkLabel && (
                  <Link href={item.linkHref} className="font-bold underline underline-offset-4">
                    {item.linkLabel}
                  </Link>
                )}
              </p>
            )}
          </li>
        );
      })}
    </ul>
  );
}
