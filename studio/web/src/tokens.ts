/**
 * The SHIRTFACED brand sheet.
 *
 * Ported value-for-value from admin's `@theme` block in admin/src/app/globals.css,
 * which took them from the storefront. Studio adds nothing decorative of its own:
 * same colours, same radii, same type. If a value here stops matching that file,
 * the two interfaces stop looking like one product.
 */

export const INK = "#0d0d0d";
export const INK_SOFT = "#1a1a1a";
export const INK_LINE = "#2a2a2a";
export const PAPER = "#f2f0ed";
export const PAPER_2 = "#e8e5e0";
export const CREAM = "#f7e9d6";
export const LIME = "#c6ff33";
export const CORAL = "#ff4d4d";
export const PINK = "#ff3c8e";
export const BLUE = "#297bff";
export const ORANGE = "#ff6a00";
export const GREY = "#8a8a86";
export const GREY_DARK = "#5c5c58";

export const RADIUS_CARD = "20px";
export const RADIUS_BTN = "18px";
export const RADIUS_INPUT = "16px";

/** Admin loads these through next/font. Studio self-hosts the same families. */
export const FONT_DISPLAY = 'Anton, "Arial Narrow", sans-serif';
export const FONT_SANS = '"Space Grotesk Variable", "Space Grotesk", system-ui, sans-serif';

export const EASE_OUT_NATURAL = "cubic-bezier(0.22, 0.61, 0.36, 1)";
