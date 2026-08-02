"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { ProductCard } from "@/components/ProductCard";
import { products } from "@/lib/products";
import { IconClose, IconSearch } from "@/components/Icons";

const POPULAR = ["send it", "cold beer", "8 ball", "black", "no regrets"];
const RECENT_KEY = "shirtfaced-recent-searches";

/** Cheap edit-distance so a one-letter slip still finds the product. */
function close(a: string, b: string) {
  if (Math.abs(a.length - b.length) > 1) return false;
  let i = 0,
    j = 0,
    diff = 0;
  while (i < a.length && j < b.length) {
    if (a[i] === b[j]) {
      i++;
      j++;
      continue;
    }
    if (++diff > 1) return false;
    if (a.length > b.length) i++;
    else if (a.length < b.length) j++;
    else {
      i++;
      j++;
    }
  }
  return diff + (a.length - i) + (b.length - j) <= 1;
}

function score(q: string, p: (typeof products)[number]) {
  const hay = [p.name, p.blurb, p.description, ...p.colours.map((c) => c.name)]
    .join(" ")
    .toLowerCase();
  const terms = q.toLowerCase().split(/\s+/).filter(Boolean);
  let s = 0;
  for (const t of terms) {
    if (p.name.toLowerCase().includes(t)) s += 10;
    else if (hay.includes(t)) s += 4;
    else if (hay.split(/\W+/).some((w) => w.length > 3 && close(w, t))) s += 2;
    else return 0; // every term must match somehow
  }
  return s;
}

export function SearchClient() {
  const [q, setQ] = useState("");
  const [recent, setRecent] = useState<string[]>([]);
  const input = useRef<HTMLInputElement>(null);

  useEffect(() => {
    input.current?.focus();
    try {
      const raw = localStorage.getItem(RECENT_KEY);
      // eslint-disable-next-line react-hooks/set-state-in-effect -- one-time hydration
      if (raw) setRecent(JSON.parse(raw).slice(0, 6));
    } catch {
      // ignore malformed history
    }
  }, []);

  const remember = (term: string) => {
    const t = term.trim();
    if (t.length < 2) return;
    const next = [t, ...recent.filter((r) => r !== t)].slice(0, 6);
    setRecent(next);
    try {
      localStorage.setItem(RECENT_KEY, JSON.stringify(next));
    } catch {
      // storage unavailable — search still works, history just won't persist
    }
  };

  const results = useMemo(() => {
    if (q.trim().length < 2) return null;
    return products
      .map((p) => ({ p, s: score(q, p) }))
      .filter((r) => r.s > 0)
      .sort((a, b) => b.s - a.s)
      .map((r) => r.p);
  }, [q]);

  return (
    <div className="mx-auto max-w-5xl px-4 pt-6 pb-16 sm:px-6">
      <div className="flex items-center gap-2 rounded-[18px] border border-ink/15 px-4">
        <IconSearch className="h-5 w-5 shrink-0 text-grey-dark" />
        <label htmlFor="q" className="sr-only">
          Search products
        </label>
        <input
          id="q"
          ref={input}
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onBlur={() => remember(q)}
          type="search"
          enterKeyHint="search"
          placeholder="Search tees…"
          className="h-14 min-w-0 flex-1 bg-transparent text-[16px] outline-none placeholder:text-grey"
        />
        {q && (
          <button
            type="button"
            onClick={() => {
              setQ("");
              input.current?.focus();
            }}
            aria-label="Clear search"
            className="press -mr-2 grid h-11 w-11 shrink-0 place-items-center rounded-full"
          >
            <IconClose className="h-5 w-5" />
          </button>
        )}
      </div>

      {results === null ? (
        <div className="mt-8 flex flex-col gap-8">
          {recent.length > 0 && (
            <section>
              <h2 className="text-[13px] font-semibold tracking-wide text-grey-dark uppercase">
                Recent
              </h2>
              <ul className="mt-3 flex flex-wrap gap-2">
                {recent.map((r) => (
                  <li key={r}>
                    <button
                      type="button"
                      onClick={() => setQ(r)}
                      className="press h-11 rounded-full border border-ink/15 px-4 text-[14px] font-medium"
                    >
                      {r}
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          )}

          <section>
            <h2 className="text-[13px] font-semibold tracking-wide text-grey-dark uppercase">
              Popular
            </h2>
            <ul className="mt-3 flex flex-wrap gap-2">
              {POPULAR.map((t) => (
                <li key={t}>
                  <button
                    type="button"
                    onClick={() => setQ(t)}
                    className="press h-11 rounded-full border border-ink/15 px-4 text-[14px] font-medium"
                  >
                    {t}
                  </button>
                </li>
              ))}
            </ul>
          </section>

          <section>
            <h2 className="display mb-4 text-[24px]">everything</h2>
            <div className="grid grid-cols-2 gap-x-4 gap-y-9 sm:grid-cols-3">
              {products.slice(0, 6).map((p) => (
                <ProductCard key={p.slug} product={p} />
              ))}
            </div>
          </section>
        </div>
      ) : results.length === 0 ? (
        /* Never a dead end. */
        <div className="mt-10">
          <h2 className="display text-[26px]">nothing matched</h2>
          <p className="mt-2 max-w-[38ch] text-[15px] text-grey-dark">
            No results for &ldquo;{q}&rdquo;. Either we don&apos;t make it yet or
            the spelling has gone sideways. These are doing well:
          </p>
          <div className="mt-7 grid grid-cols-2 gap-x-4 gap-y-9 sm:grid-cols-3">
            {products.slice(0, 4).map((p) => (
              <ProductCard key={p.slug} product={p} />
            ))}
          </div>
        </div>
      ) : (
        <div className="mt-6">
          <p className="text-[13px] font-semibold tracking-wide text-grey-dark uppercase tabular-nums">
            {results.length} {results.length === 1 ? "result" : "results"}
          </p>
          <div className="mt-4 grid grid-cols-2 gap-x-4 gap-y-9 sm:grid-cols-3">
            {results.map((p) => (
              <ProductCard key={p.slug} product={p} />
            ))}
          </div>
        </div>
      )}

      <p className="mt-12 text-center text-[14px] text-grey-dark">
        Can&apos;t find it?{" "}
        <Link href="/shop" className="font-semibold underline underline-offset-4">
          Browse everything
        </Link>
      </p>
    </div>
  );
}
