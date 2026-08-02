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
        if (Array.isArray(parsed)) setLines(parsed);
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
