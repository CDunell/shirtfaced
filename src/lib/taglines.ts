/**
 * Hero tagline rotation.
 *
 * Structure is fixed: GOOD TIMES. / <rotating> / ZERO REGRETS. Only the middle
 * line moves. "Bad decisions" is the most-used phrase in the Australian
 * humour-apparel category, so the brand deliberately refuses to settle on one
 * answer — the rotation is the attitude.
 *
 * Fixed pairs rather than random line-over-random-image, so each line can be
 * tuned against a shot that suits its register.
 */
export type Tagline = {
  /** Middle line. Renders in acid lime; lines 1 and 3 are bone white. */
  line: string;
  image: string;
  /**
   * Font size in cqw (percent of the hero's width).
   *
   * Anton ships a single weight, so the middle line CANNOT use a fixed
   * font-size: "FUCK YES." is 9 characters and "DUBIOUS CHOICES." is 16, and at
   * one size the short line strands whitespace while the long one overflows.
   * Each value below is measured so every line fills the same width — see
   * scripts/tune-taglines.mjs.
   */
  size: number;
  /** Focal point for the paired photo. */
  position: string;
};

export const TAGLINES: Tagline[] = [
  {
    line: "BAD INFLUENCES",
    image: "/products/good-times-1.webp",
    size: 15.6,
    position: "50% 30%",
  },
  {
    line: "COMPLETE CHAOS",
    image: "/products/permanent.webp",
    size: 14.5,
    position: "50% 40%",
  },
  {
    line: "FUCK YES",
    image: "/products/hero-street.webp",
    size: 27.5,
    position: "50% 38%",
  },
  {
    line: "NO PLAN",
    image: "/products/cold-beer-1.webp",
    size: 30.2,
    position: "50% 32%",
  },
  {
    line: "WENT SIDEWAYS",
    image: "/products/midnight-service.webp",
    size: 15.7,
    position: "50% 42%",
  },
  {
    line: "DUBIOUS CHOICES",
    image: "/products/roll-the-dice-1.webp",
    size: 14.7,
    position: "50% 30%",
  },
];

export const LINE_ONE = "GOOD TIMES.";
export const LINE_THREE = "ZERO REGRETS.";

/** One shared size for the two fixed lines, so they keep their natural
 *  ragged widths. The rotating line is measured against the wider of them. */
export const LINE_ONE_SIZE = 17.9;
export const LINE_THREE_SIZE = 17.9;
