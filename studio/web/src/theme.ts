/**
 * Theme preference persistence.
 *
 * Used to also build Base Web's light/dark theme objects here; now that every
 * component is Tailwind, dark mode is just a `dark` class on <html> (see
 * useSyncDarkClass in components/ui.tsx) driven by the same preference this
 * file tracks.
 */

export type ThemeName = "light" | "dark";

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
