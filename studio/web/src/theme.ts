/**
 * Base Web theming.
 *
 * Base's light and dark themes are used as supplied. Studio-specific tokens go here
 * rather than being hard-coded into components, so the visual language stays in one
 * place as the interface grows.
 */

import { DarkTheme, LightTheme, type Theme } from "baseui";

export type ThemeName = "light" | "dark";

export const THEMES: Record<ThemeName, Theme> = {
  light: LightTheme,
  dark: DarkTheme,
};

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

/** The stored preference, falling back to the operating system setting. */
export function initialThemeName(): ThemeName {
  return (
    readStoredTheme() ??
    (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")
  );
}
