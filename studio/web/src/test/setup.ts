import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach, beforeEach } from "vitest";

afterEach(() => {
  cleanup();
});

// jsdom doesn't implement matchMedia. DesignGalleryBench's useIsDesktop reads
// it on mount, so anything that can render Gallery needs this even if the
// test itself never touches viewport width. Defaults to "not matched" (the
// mobile/narrow branch) -- deterministic, and every existing assertion was
// already written against that page size.
beforeEach(() => {
  window.matchMedia = function matchMedia(query: string): MediaQueryList {
    return {
      matches: false,
      media: query,
      onchange: null,
      addListener: () => undefined,
      removeListener: () => undefined,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      dispatchEvent: () => false,
    } as MediaQueryList;
  };
});
