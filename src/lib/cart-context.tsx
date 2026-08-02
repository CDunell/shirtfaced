"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { products } from "./products";

export type CartLine = {
  slug: string;
  name: string;
  price: number;
  size: string;
  colour: string;
  art: string;
  /** Garment body + ink so the cart thumbnail renders without a lookup */
  body: string;
  ink: string;
  quantity: number;
};

type CartContextValue = {
  lines: CartLine[];
  addLine: (line: Omit<CartLine, "quantity">, quantity?: number) => void;
  removeLine: (slug: string, size: string, colour: string) => void;
  setQuantity: (
    slug: string,
    size: string,
    colour: string,
    quantity: number
  ) => void;
  itemCount: number;
  subtotal: number;
  /** Bumps on every add — drives the cart badge pop */
  addTick: number;
  hydrated: boolean;
};

const CartContext = createContext<CartContextValue | null>(null);
const STORAGE_KEY = "shirtfaced-cart";

const sameLine = (l: CartLine, slug: string, size: string, colour: string) =>
  l.slug === slug && l.size === size && l.colour === colour;

/**
 * Repair carts written by an older version of this app.
 *
 * CartLine gained `colour`, `art`, `body` and `ink` after the first release.
 * A cart saved before that has none of them, and the cart page then crashed on
 * `garment.name.replace(...)` — which also trapped the user, because the crash
 * stopped them removing the offending item.
 *
 * Anything repairable is backfilled from the catalogue; anything referencing a
 * product that no longer exists is dropped rather than rendered half-broken.
 */
function migrate(stored: unknown[]): CartLine[] {
  const out: CartLine[] = [];

  for (const raw of stored) {
    if (!raw || typeof raw !== "object") continue;
    const l = raw as Partial<CartLine>;
    if (typeof l.slug !== "string" || typeof l.size !== "string") continue;

    const product = products.find((p) => p.slug === l.slug);
    if (!product) continue; // discontinued or renamed — drop it

    const colour =
      product.colours.find((c) => c.name === l.colour) ?? product.colours[0];

    const quantity =
      typeof l.quantity === "number" && l.quantity > 0
        ? Math.floor(l.quantity)
        : 1;

    out.push({
      slug: product.slug,
      name: product.name,
      price: product.price,
      size: l.size,
      colour: colour.name,
      art: product.art,
      body: colour.body,
      ink: colour.ink,
      quantity,
    });
  }

  return out;
}

export function CartProvider({ children }: { children: ReactNode }) {
  const [lines, setLines] = useState<CartLine[]>([]);
  const [hydrated, setHydrated] = useState(false);
  const [addTick, setAddTick] = useState(0);

  useEffect(() => {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (raw) {
      try {
        const parsed = JSON.parse(raw);
        // eslint-disable-next-line react-hooks/set-state-in-effect -- one-time hydration from localStorage
        if (Array.isArray(parsed)) setLines(migrate(parsed));
      } catch {
        // malformed cart data — start clean rather than crash the app
      }
    }
    setHydrated(true);
  }, []);

  useEffect(() => {
    // Guarded on `hydrated` so the initial empty state never overwrites a
    // stored cart before the load effect has run.
    if (hydrated) {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(lines));
    }
  }, [lines, hydrated]);

  const addLine = useCallback<CartContextValue["addLine"]>(
    (line, quantity = 1) => {
      setLines((prev) => {
        const existing = prev.find((l) =>
          sameLine(l, line.slug, line.size, line.colour)
        );
        if (existing) {
          return prev.map((l) =>
            l === existing ? { ...l, quantity: l.quantity + quantity } : l
          );
        }
        return [...prev, { ...line, quantity }];
      });
      setAddTick((t) => t + 1);
    },
    []
  );

  const removeLine = useCallback<CartContextValue["removeLine"]>(
    (slug, size, colour) =>
      setLines((prev) => prev.filter((l) => !sameLine(l, slug, size, colour))),
    []
  );

  const setQuantity = useCallback<CartContextValue["setQuantity"]>(
    (slug, size, colour, quantity) =>
      setLines((prev) =>
        prev
          .map((l) =>
            sameLine(l, slug, size, colour) ? { ...l, quantity } : l
          )
          .filter((l) => l.quantity > 0)
      ),
    []
  );

  const itemCount = useMemo(
    () => lines.reduce((sum, l) => sum + l.quantity, 0),
    [lines]
  );
  const subtotal = useMemo(
    () => lines.reduce((sum, l) => sum + l.quantity * l.price, 0),
    [lines]
  );

  const value = useMemo(
    () => ({
      lines,
      addLine,
      removeLine,
      setQuantity,
      itemCount,
      subtotal,
      addTick,
      hydrated,
    }),
    [lines, addLine, removeLine, setQuantity, itemCount, subtotal, addTick, hydrated]
  );

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart must be used within a CartProvider");
  return ctx;
}
