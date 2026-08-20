"use client";

import { useState } from "react";
import Link from "next/link";
import { IconChevronDown } from "@/components/Icons";

export function FaqAccordion({
  items,
}: {
  items: {
    question: string;
    answer: string;
    linkHref?: string | null;
    linkLabel?: string | null;
  }[];
}) {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <ul className="flex flex-col">
      {items.map((item, i) => {
        const open = openIndex === i;
        return (
          <li key={item.question} className="border-b border-ink/10">
            <button
              type="button"
              onClick={() => setOpenIndex(open ? null : i)}
              aria-expanded={open}
              className="press flex w-full items-center justify-between gap-4 py-5 text-left"
            >
              <span className="display text-[18px] leading-tight">
                {item.question}
              </span>
              <IconChevronDown
                className={`h-4 w-4 shrink-0 text-grey-dark transition-transform ${
                  open ? "rotate-180" : ""
                }`}
              />
            </button>
            {open && (
              <p className="pb-5 pr-8 text-[15px] leading-relaxed text-ink/70">
                {item.answer}
                {item.linkHref && item.linkLabel && (
                  <>
                    {" "}
                    <Link
                      href={item.linkHref}
                      className="font-semibold text-ink underline underline-offset-2"
                    >
                      {item.linkLabel}
                    </Link>
                  </>
                )}
              </p>
            )}
          </li>
        );
      })}
    </ul>
  );
}
