/**
 * Hero tagline rotation.
 *
 * Grammar is fixed: <beat one>, <beat two>, shirtfaced. The third beat is
 * always the brand's own name, so every line signs itself — see
 * docs/foundations/BRAND_VOICE.md §3. Only the two beats rotate; "shirtfaced"
 * never changes.
 *
 * Six pairs rather than random line-over-random-image, so each pair can be
 * tuned against a shot that suits its register.
 */
export type Tagline = {
  /** First beat. Renders in bone white. */
  beatOne: string;
  /** Second beat. Renders in bone white. */
  beatTwo: string;
  image: string;
  /**
   * Font sizes in cqw (percent of the hero's width), one per beat.
   *
   * Anton ships a single weight, so beat length alone decides how wide a
   * string renders: "Six mates" is 9 characters and "Two carloads" is 12, and
   * at one size the short beat strands whitespace while the long one
   * overflows. Each value below is measured against the fixed third line so
   * every beat fills the same width — see scripts/tune-taglines.mjs.
   */
  sizeOne: number;
  sizeTwo: number;
  /** Focal point for the paired photo. */
  position: string;
};

export const TAGLINES: Tagline[] = [
  {
    beatOne: "Good mates",
    beatTwo: "great times",
    image: "/products/good-times-1.webp",
    sizeOne: 16.6,
    sizeTwo: 16.4,
    position: "50% 30%",
  },
  {
    beatOne: "Long lunch",
    beatTwo: "no dinner",
    image: "/products/permanent.webp",
    sizeOne: 17.4,
    sizeTwo: 20.0,
    position: "50% 40%",
  },
  {
    beatOne: "Two carloads",
    beatTwo: "one esky",
    image: "/products/hero-street.webp",
    sizeOne: 13.9,
    sizeTwo: 22.2,
    position: "50% 38%",
  },
  {
    beatOne: "Grand final",
    beatTwo: "either way",
    image: "/products/cold-beer-1.webp",
    sizeOne: 16.6,
    sizeTwo: 18.1,
    position: "50% 32%",
  },
  {
    beatOne: "Wrong pub",
    beatTwo: "right crowd",
    image: "/products/midnight-service.webp",
    sizeOne: 17.8,
    sizeTwo: 15.6,
    position: "50% 42%",
  },
  {
    beatOne: "Six mates",
    beatTwo: "one tent",
    image: "/products/roll-the-dice-1.webp",
    sizeOne: 19.7,
    sizeTwo: 22.8,
    position: "50% 30%",
  },
];

/** Fixed third beat. Renders in acid lime — the payoff, not the setup. */
export const LINE_THREE = "shirtfaced";

/**
 * Anchor size for the fixed line, in cqw. Every rotating beat above is
 * measured against the width this produces. "shirtfaced" is 10 characters,
 * the same length class as the old fixed lines this replaces, so this
 * reuses their calibrated size rather than guessing from zero — still worth
 * confirming with scripts/tune-taglines.mjs against a real render.
 */
export const LINE_THREE_SIZE = 17.9;
