"use client";

import Link from "next/link";
import { CATEGORY_LABEL, type Category } from "@/lib/products";

const TABS: { key: Category | "all"; label: string }[] = [
  { key: "all", label: "All" },
  { key: "tee", label: CATEGORY_LABEL.tee },
  { key: "hoodie", label: CATEGORY_LABEL.hoodie },
  { key: "cap", label: CATEGORY_LABEL.cap },
];

export function ShopFilters({ active }: { active: Category | "all" }) {
  return (
    <div className="no-scrollbar mt-6 flex gap-2 overflow-x-auto">
      {TABS.map((tab) => {
        const isActive = tab.key === active;
        const href = tab.key === "all" ? "/shop" : `/shop?category=${tab.key}`;
        return (
          <Link
            key={tab.key}
            href={href}
            aria-current={isActive ? "page" : undefined}
            className={`press shrink-0 rounded-full px-4 py-2 text-[14px] font-bold ${
              isActive ? "bg-ink text-paper" : "bg-paper-2 text-ink/70"
            }`}
          >
            {tab.label}
          </Link>
        );
      })}
    </div>
  );
}
