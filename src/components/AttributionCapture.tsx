"use client";

import { useEffect } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import { captureAttribution } from "@/lib/attribution";

/** Renders nothing — just watches route changes and hands them to
 * captureAttribution (see src/lib/attribution.ts). Needs useSearchParams,
 * so it's wrapped in Suspense from layout.tsx, same as checkout/success. */
export function AttributionCapture() {
  const pathname = usePathname();
  const search = useSearchParams().toString();

  useEffect(() => {
    captureAttribution(pathname, search);
  }, [pathname, search]);

  return null;
}
