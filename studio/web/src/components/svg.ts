/**
 * Make print-sized SVG artwork fit a preview card.
 *
 * The artwork is emitted at real print size -- width="200mm" -- because that is
 * what a separator and an RIP want, and measuring in millimetres is the point of
 * the engine. A browser honours those units literally, so a 200mm design lays
 * out around 756 pixels wide and overflows a preview card, showing a black
 * corner instead of the artwork.
 *
 * Only the two dimension attributes are dropped. The viewBox stays, so the
 * drawing scales rather than being cropped, and the stored artwork is untouched.
 */
export function fitToCard(svg: string): string {
  return svg.replace(
    /<svg([^>]*)>/,
    (_match, attributes: string) =>
      `<svg${attributes.replace(/ (?:width|height)="[^"]*"/g, "")} style="width:100%;height:auto;max-height:200px">`,
  );
}
