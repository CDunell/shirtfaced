/**
 * Base Web theming.
 *
 * Studio and admin are one product, so they use one brand sheet: the values in
 * tokens.ts, ported from admin. Base's own palettes are not used -- stock Base Web
 * is what made Studio look like a different application.
 *
 * Only the tokens Base exposes can be set here. The page background, the display
 * faces and the focus ring live in index.css, which is the same split admin has
 * between its Tailwind theme and its globals.
 */

import { createDarkTheme, createLightTheme, DarkTheme, LightTheme, type Theme } from "baseui";

import {
  CORAL,
  FONT_SANS,
  GREY,
  GREY_DARK,
  INK,
  INK_LINE,
  INK_SOFT,
  LIME,
  PAPER,
  PAPER_2,
  RADIUS_BTN,
  RADIUS_CARD,
  RADIUS_INPUT,
} from "./tokens";

export type ThemeName = "light" | "dark";

/** Radii are the same in both themes: they are brand, not mode. */
const borders = {
  buttonBorderRadius: RADIUS_BTN,
  inputBorderRadius: RADIUS_INPUT,
  surfaceBorderRadius: RADIUS_CARD,
  popoverBorderRadius: RADIUS_CARD,
  tagBorderRadius: RADIUS_BTN,
  // Card takes its corners from the generic surface step, not from
  // surfaceBorderRadius -- that one only rounds a card's image. Everything on
  // this step is a surface, so the brand radius belongs on it.
  radius400: RADIUS_CARD,
};

/**
 * Every type scale, wearing the brand face.
 *
 * This version of createLightTheme takes overrides only -- there is no primitives
 * argument to carry a font family -- and each of Base's ~20 typography entries
 * names its own. Rewriting them from the theme being extended sets the face once
 * and cannot miss a scale that Base adds later.
 */
function brandType(typography: Theme["typography"]): Theme["typography"] {
  return Object.fromEntries(
    Object.entries(typography).map(([name, value]) => [
      name,
      value && typeof value === "object" && "fontFamily" in value
        ? { ...value, fontFamily: FONT_SANS }
        : value,
    ]),
  ) as Theme["typography"];
}

/** Admin is light only, so this is the one that has to match it exactly. */
const light = createLightTheme({
  borders,
  typography: brandType(LightTheme.typography),
  colors: {
    backgroundPrimary: PAPER,
    backgroundSecondary: PAPER_2,
    backgroundTertiary: PAPER_2,
    backgroundInversePrimary: INK,
    contentPrimary: INK,
    contentSecondary: GREY_DARK,
    contentTertiary: GREY,
    contentInversePrimary: PAPER,
    borderOpaque: PAPER_2,
    borderSelected: INK,
    // Admin's primary action is a solid ink pill with paper text.
    buttonPrimaryFill: INK,
    buttonPrimaryText: PAPER,
    buttonPrimaryHover: INK_SOFT,
    buttonPrimaryActive: INK_LINE,
    buttonSecondaryFill: PAPER_2,
    buttonSecondaryText: INK,
    buttonTertiaryText: INK,
    buttonTertiaryHover: PAPER_2,
    negative: CORAL,
    accent: LIME,
  },
});

/** No admin equivalent to copy. Built from the same tokens, inverted. */
const dark = createDarkTheme({
  borders,
  typography: brandType(DarkTheme.typography),
  colors: {
    backgroundPrimary: INK,
    backgroundSecondary: INK_SOFT,
    backgroundTertiary: INK_LINE,
    contentPrimary: PAPER,
    contentSecondary: PAPER_2,
    contentInversePrimary: INK,
    borderOpaque: INK_LINE,
    borderSelected: PAPER,
    buttonPrimaryFill: PAPER,
    buttonPrimaryText: INK,
    buttonPrimaryHover: PAPER_2,
    buttonPrimaryActive: PAPER_2,
    buttonTertiaryText: PAPER,
    buttonTertiaryHover: INK_SOFT,
    negative: CORAL,
    accent: LIME,
  },
});

export const THEMES: Record<ThemeName, Theme> = { light, dark };

export const THEME_STORAGE_KEY = "shirtfaced-studio.theme";

/**
 * Storage access is wrapped because a browser with site data blocked throws on
 * access rather than returning null. A theme preference is not worth a crash.
 */
function readStoredTheme(): ThemeName | null {
  try {
    const stored = window.localStorage.getItem(THEME_STORAGE_KEY);
    return stored === "light" || stored === "dark" ? stored : null;
  } catch {
    return null;
  }
}

export function storeThemeName(name: ThemeName): void {
  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, name);
  } catch {
    // Preference simply does not persist.
  }
}

/**
 * The stored preference, falling back to the operating system setting.
 *
 * Admin has no dark mode, so a light default keeps the two matching for anyone
 * who has expressed no preference.
 */
export function initialThemeName(): ThemeName {
  return (
    readStoredTheme() ??
    (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")
  );
}
