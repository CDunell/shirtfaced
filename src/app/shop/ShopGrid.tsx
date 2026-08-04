"use client";

import { useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { ProductCard } from "@/components/ProductCard";
import { CATEGORIES, products } from "@/lib/products";
import { IconChevronDown, IconSliders } from "@/components/Icons";

type SortKey = "featured" | "new" | "price-low" | "price-high";

const SORTS: { key: SortKey; label: string }[] = [
  { key: "featured", label: "Featured" },
  { key: "new", label: "Newest" },
  { key: "price-low", label: "Price: low to high" },
  { key: "price-high", label: "Price: high to low" },
];

export function ShopGrid() {
  const params = useSearchParams();
  const [filter, setFilter] = useState<string>(params.get("f") ?? "all");
  const [sort, setSort] = useState<SortKey>("featured");

  const visible = useMemo(() => {
    const list = products.filter((p) => {
      if (filter === "all") return true;
      if (filter === "new") return Boolean(p.isNew);
      return p.category === filter;
    });

    switch (sort) {
      case "new":
        return [...list].sort(
          (a, b) => Number(Boolean(b.isNew)) - Number(Boolean(a.isNew))
        );
      case "price-low":
        return [...list].sort((a, b) => a.price - b.price);
      case "price-high":
        return [...list].sort((a, b) => b.price - a.price);
      default:
        return list;
    }
  }, [filter, sort]);

  return (
    <>
      {/* Filter chips — one thumb, large targets, live count */}
      <div className="sticky top-20 z-30 border-b border-ink/10 bg-paper/95 backdrop-blur">
        <ul className="no-scrollbar mx-auto flex max-w-6xl gap-2 overflow-x-auto px-4 py-3 sm:px-6">
          {CATEGORIES.map((c) => {
            const active = filter === c.key;
            return (
              <li key={c.key}>
                <button
                  type="button"
                  onClick={() => setFilter(c.key)}
                  aria-pressed={active}
                  className={`press h-11 shrink-0 rounded-full border px-4 text-[14px] font-semibold whitespace-nowrap ${
                    active
                      ? "border-ink bg-ink text-paper"
                      : "border-ink/15 bg-transparent text-ink"
                  }`}
                >
                  {c.label}
                </button>
              </li>
            );
          })}
        </ul>
      </div>

      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="flex items-center justify-between py-4">
          <p className="text-[13px] font-semibold tracking-wide text-grey-dark uppercase tabular-nums">
            {visible.length} {visible.length === 1 ? "product" : "products"}
          </p>

          <div className="flex items-center gap-2">
            <label htmlFor="sort" className="sr-only">
              Sort products
            </label>
            <div className="relative">
              <select
                id="sort"
                value={sort}
                onChange={(e) => setSort(e.target.value as SortKey)}
                className="press h-11 appearance-none rounded-full border border-ink/15 pr-9 pl-4 text-[14px] font-semibold"
              >
                {SORTS.map((s) => (
                  <option key={s.key} value={s.key}>
                    {s.label}
                  </option>
                ))}
              </select>
              <IconChevronDown className="pointer-events-none absolute top-1/2 right-3 h-4 w-4 -translate-y-1/2" />
            </div>
            <button
              type="button"
              className="press grid h-11 w-11 place-items-center rounded-full border border-ink/15"
              aria-label="Filters"
            >
              <IconSliders className="h-5 w-5" />
            </button>
          </div>
        </div>

        {visible.length === 0 ? (
          /* Empty states are never dead ends. */
          <div className="fade-rise rounded-[20px] bg-paper-2 px-6 py-14 text-center">
            <h2 className="display text-[26px]">nothing here yet</h2>
            <p className="mx-auto mt-2 max-w-[34ch] text-[15px] text-grey-dark">
              That drop hasn&apos;t landed. The tees below are doing just fine in
              the meantime.
            </p>
            <button
              type="button"
              onClick={() => setFilter("all")}
              className="press mt-6 h-12 rounded-[18px] bg-ink px-6 text-[15px] font-bold text-paper"
            >
              Show everything
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-x-4 gap-y-9 pb-4 sm:grid-cols-3">
            {visible.map((p, i) => (
              <ProductCard key={p.slug} product={p} priority={i < 4} />
            ))}
          </div>
        )}
      </div>
    </>
  );
}
