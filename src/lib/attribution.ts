/**
 * First-party UTM / click-id capture — ported from mymixups' own
 * attribution.ts. Stored in localStorage and sent along with the order at
 * checkout (see checkout/page.tsx), so admin can eventually answer "which
 * channel actually drove this sale" instead of relying on each ad
 * platform's own (increasingly cookie-blocked) attribution.
 *
 * First touch is kept forever once set. Last touch is overwritten only when
 * the current page load actually carries a new identifying param — a plain
 * internal navigation with no utm_ or click-id params leaves last touch alone.
 */

const STORAGE_KEY = "sf-attribution";

const UTM_KEYS = [
  "utm_source",
  "utm_medium",
  "utm_campaign",
  "utm_content",
  "utm_term",
] as const;

const CLICK_ID_KEYS = [
  "fbclid",
  "ttclid",
  "gclid",
  "gbraid",
  "wbraid",
  "epik",
  "msclkid",
] as const;

// A landing URL can carry a platform's own click id with no utm_source of
// its own (most ad platforms don't add one automatically) — this is what
// that visit is really from.
const CLICK_ID_SOURCE: Record<(typeof CLICK_ID_KEYS)[number], string> = {
  fbclid: "facebook",
  ttclid: "tiktok",
  gclid: "google",
  gbraid: "google",
  wbraid: "google",
  epik: "pinterest",
  msclkid: "bing",
};

export type Touch = {
  at: string;
  landingPath: string;
  referrer: string;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_content?: string;
  utm_term?: string;
  fbclid?: string;
  ttclid?: string;
  gclid?: string;
  gbraid?: string;
  wbraid?: string;
  epik?: string;
  msclkid?: string;
};

export type Attribution = {
  version: 1;
  first: Touch;
  last: Touch;
};

function buildTouch(path: string, search: string, referrer: string): Touch | null {
  const params = new URLSearchParams(search);
  const touch: Touch = { at: new Date().toISOString(), landingPath: path, referrer };
  let hasIdentifyingParam = false;

  for (const key of UTM_KEYS) {
    const value = params.get(key);
    if (value) {
      touch[key] = value;
      hasIdentifyingParam = true;
    }
  }
  for (const key of CLICK_ID_KEYS) {
    const value = params.get(key);
    if (value) {
      touch[key] = value;
      hasIdentifyingParam = true;
      if (!touch.utm_source) touch.utm_source = CLICK_ID_SOURCE[key];
    }
  }

  return hasIdentifyingParam ? touch : null;
}

function readStored(): Attribution | null {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Attribution) : null;
  } catch {
    return null;
  }
}

function writeStored(attribution: Attribution) {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(attribution));
  } catch {
    // localStorage unavailable (private mode, etc.) — attribution just isn't
    // captured for this visitor, not worth failing the page over
  }
}

/** Call on every route change (path or query string) — see
 * components/AttributionCapture.tsx. No-op unless the current load actually
 * carries a new utm_ or click-id param. */
export function captureAttribution(path: string, search: string) {
  if (typeof window === "undefined") return;
  const touch = buildTouch(path, search, document.referrer);
  if (!touch) return;

  const existing = readStored();
  writeStored({
    version: 1,
    first: existing?.first ?? touch,
    last: touch,
  });
}

/** Read at checkout time to send along with the real order. Null for a
 * visitor with no tracked touch yet (direct traffic, or localStorage
 * unavailable) — checkout still works, the order just carries no channel. */
export function getAttribution(): Attribution | null {
  if (typeof window === "undefined") return null;
  return readStored();
}
