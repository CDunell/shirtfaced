import { Suspense } from "react";
import { ShopGrid } from "./ShopGrid";

export const metadata = {
  title: "Shop — Shirtfaced",
  description: "Every tee. Good times. Bad decisions. Zero regrets.",
};

function GridSkeleton() {
  // Skeletons, never spinners — the layout is known, so hold its shape.
  return (
    <div className="mx-auto max-w-5xl px-4 pt-4 sm:px-6">
      <div className="grid grid-cols-2 gap-x-4 gap-y-9 sm:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i}>
            <div className="skeleton aspect-[4/5] rounded-[20px]" />
            <div className="skeleton mt-3 h-4 w-3/4 rounded" />
            <div className="skeleton mt-2 h-4 w-1/3 rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}

export default function ShopPage() {
  return (
    <>
      <div className="mx-auto max-w-5xl px-4 pt-8 pb-1 sm:px-6">
        <h1 className="display distressed text-[17vw] leading-[0.84] sm:text-[86px]">
          shop
        </h1>
        <p className="mt-3 text-[15px] font-semibold tracking-wide uppercase">
          Good times. Bad decisions.{" "}
          <span className="text-ink/45">Zero regrets.</span>
        </p>
      </div>

      <Suspense fallback={<GridSkeleton />}>
        <ShopGrid />
      </Suspense>
    </>
  );
}
