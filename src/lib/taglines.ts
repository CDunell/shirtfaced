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
    image: "/products/eight-ball.webp",
    sizeOne: 15.8,
    sizeTwo: 15.6,
    position: "50% 25%",
  },
  {
    beatOne: "Long lunch",
    beatTwo: "no dinner",
    image: "/products/permanent.webp",
    sizeOne: 16.6,
    sizeTwo: 19.3,
    position: "50% 40%",
  },
  {
    beatOne: "Two carloads",
    beatTwo: "one esky",
    image: "/products/built-different.webp",
    sizeOne: 13.2,
    sizeTwo: 21.5,
    position: "50% 35%",
  },
  {
    beatOne: "Grand final",
    beatTwo: "either way",
    image: "/products/love-fast-die-last.webp",
    sizeOne: 15.8,
    sizeTwo: 17.3,
    position: "50% 40%",
  },
  {
    beatOne: "Wrong pub",
    beatTwo: "right crowd",
    image: "/products/midnight-service.webp",
    sizeOne: 17.1,
    sizeTwo: 14.9,
    position: "50% 42%",
  },
  {
    beatOne: "Six mates",
    beatTwo: "one tent",
    image: "/products/take-your-chances.webp",
    sizeOne: 18.9,
    sizeTwo: 22.1,
    position: "50% 35%",
  },
  {
    beatOne: "Nan's 80th",
    beatTwo: "told to behave",
    image: "/products/midnight-service.webp",
    sizeOne: 17.2,
    sizeTwo: 12.6,
    position: "50% 35%",
  },
  {
    beatOne: "Cousin's boat",
    beatTwo: "nobody can drive it",
    image: "/products/not-yours.webp",
    sizeOne: 13.7,
    sizeTwo: 9.5,
    position: "50% 40%",
  },
  {
    beatOne: "Everyone said early",
    beatTwo: "no one meant it",
    image: "/products/permanent.webp",
    sizeOne: 9.3,
    sizeTwo: 11.8,
    position: "50% 45%",
  },
  {
    beatOne: "Ferry there",
    beatTwo: "taxi home",
    image: "/products/roll-the-dice-1.webp",
    sizeOne: 15.9,
    sizeTwo: 18.6,
    position: "50% 35%",
  },
  {
    beatOne: "Best mate's wedding",
    beatTwo: "worst speech",
    image: "/products/send-it-1.webp",
    sizeOne: 8.9,
    sizeTwo: 13.4,
    position: "50% 40%",
  },
  {
    beatOne: "Shoes in hand",
    beatTwo: "kilometre to go",
    image: "/products/send-it-2.webp",
    sizeOne: 13.4,
    sizeTwo: 11.6,
    position: "50% 45%",
  },
  {
    beatOne: "Sunrise",
    beatTwo: "servo pie",
    image: "/products/spin-cycle.webp",
    sizeOne: 24.5,
    sizeTwo: 20.2,
    position: "50% 35%",
  },
  {
    beatOne: "Bali day three",
    beatTwo: "passport's fine",
    image: "/products/take-your-chances.webp",
    sizeOne: 13,
    sizeTwo: 12,
    position: "50% 40%",
  },
  {
    beatOne: "Christmas",
    beatTwo: "with the outlaws",
    image: "/products/built-different.webp",
    sizeOne: 17.4,
    sizeTwo: 10.5,
    position: "50% 45%",
  },
  {
    beatOne: "Meant to be there",
    beatTwo: "for one",
    image: "/products/cold-beer-1.webp",
    sizeOne: 10.2,
    sizeTwo: 24.6,
    position: "50% 35%",
  },
  {
    beatOne: "Someone's turning 30",
    beatTwo: "again",
    image: "/products/eight-ball.webp",
    sizeOne: 8.5,
    sizeTwo: 33.8,
    position: "50% 40%",
  },
  {
    beatOne: "Melbourne Cup",
    beatTwo: "it's a Tuesday",
    image: "/products/good-times-1.webp",
    sizeOne: 12.2,
    sizeTwo: 13.7,
    position: "50% 45%",
  },
  {
    beatOne: "Backyard",
    beatTwo: "borrowed chairs",
    image: "/products/hero-good-times.webp",
    sizeOne: 19.4,
    sizeTwo: 10.7,
    position: "50% 35%",
  },
  {
    beatOne: "Camping",
    beatTwo: "technically",
    image: "/products/hero-street.webp",
    sizeOne: 21.7,
    sizeTwo: 15.8,
    position: "50% 40%",
  },
  {
    beatOne: "Fishing trip",
    beatTwo: "no fish",
    image: "/products/love-fast-die-last.webp",
    sizeOne: 16,
    sizeTwo: 26.3,
    position: "50% 45%",
  },
  {
    beatOne: "Bucks in a bus",
    beatTwo: "driver's seen worse",
    image: "/products/midnight-service.webp",
    sizeOne: 13,
    sizeTwo: 9.2,
    position: "50% 35%",
  },
  {
    beatOne: "Twenty year reunion",
    beatTwo: "same jokes",
    image: "/products/not-yours.webp",
    sizeOne: 9,
    sizeTwo: 15.9,
    position: "50% 40%",
  },
  {
    beatOne: "Golf day",
    beatTwo: "front nine only",
    image: "/products/permanent.webp",
    sizeOne: 21.7,
    sizeTwo: 12,
    position: "50% 45%",
  },
  {
    beatOne: "Missed the last train",
    beatTwo: "walked it",
    image: "/products/roll-the-dice-1.webp",
    sizeOne: 8.5,
    sizeTwo: 19.3,
    position: "50% 35%",
  },
  {
    beatOne: "Uncle's on the karaoke",
    beatTwo: "send help",
    image: "/products/send-it-1.webp",
    sizeOne: 8,
    sizeTwo: 19,
    position: "50% 40%",
  },
  {
    beatOne: "Barefoot by nine",
    beatTwo: "home by four",
    image: "/products/send-it-2.webp",
    sizeOne: 11.1,
    sizeTwo: 13.7,
    position: "50% 45%",
  },
  {
    beatOne: "Whole street's here",
    beatTwo: "nobody invited them",
    image: "/products/spin-cycle.webp",
    sizeOne: 9.2,
    sizeTwo: 9.1,
    position: "50% 35%",
  },
  {
    beatOne: "Nobody's got a charger",
    beatTwo: "nobody cares",
    image: "/products/take-your-chances.webp",
    sizeOne: 7.8,
    sizeTwo: 13.6,
    position: "50% 40%",
  },
  {
    beatOne: "Group chat",
    beatTwo: "still going",
    image: "/products/built-different.webp",
    sizeOne: 16.5,
    sizeTwo: 17.2,
    position: "50% 45%",
  },
  {
    beatOne: "Sunday session",
    beatTwo: "Monday problem",
    image: "/products/cold-beer-1.webp",
    sizeOne: 12.1,
    sizeTwo: 10.8,
    position: "50% 35%",
  },
  {
    beatOne: "One more",
    beatTwo: "famous last words",
    image: "/products/eight-ball.webp",
    sizeOne: 19.6,
    sizeTwo: 9.3,
    position: "50% 40%",
  },
  {
    beatOne: "Servo run",
    beatTwo: "never came back",
    image: "/products/good-times-1.webp",
    sizeOne: 18.5,
    sizeTwo: 10.9,
    position: "50% 45%",
  },
  {
    beatOne: "Two-up",
    beatTwo: "still going",
    image: "/products/hero-good-times.webp",
    sizeOne: 25.8,
    sizeTwo: 17.2,
    position: "50% 35%",
  },
  {
    beatOne: "Boxing Day",
    beatTwo: "third innings",
    image: "/products/hero-street.webp",
    sizeOne: 17.2,
    sizeTwo: 14.1,
    position: "50% 40%",
  },
  {
    beatOne: "Beach at noon",
    beatTwo: "pub by two",
    image: "/products/love-fast-die-last.webp",
    sizeOne: 13,
    sizeTwo: 16.7,
    position: "50% 45%",
  },
  {
    beatOne: "Sausage sizzle",
    beatTwo: "everyone stayed",
    image: "/products/midnight-service.webp",
    sizeOne: 12.7,
    sizeTwo: 11.3,
    position: "50% 35%",
  },
  {
    beatOne: "Someone brought a guitar",
    beatTwo: "it's over",
    image: "/products/not-yours.webp",
    sizeOne: 7,
    sizeTwo: 21.8,
    position: "50% 40%",
  },
  {
    beatOne: "Long weekend",
    beatTwo: "longer Monday",
    image: "/products/permanent.webp",
    sizeOne: 13.4,
    sizeTwo: 12,
    position: "50% 45%",
  },
  {
    beatOne: "Pub raffle",
    beatTwo: "won the meat tray",
    image: "/products/roll-the-dice-1.webp",
    sizeOne: 17.4,
    sizeTwo: 9.8,
    position: "50% 35%",
  },
  {
    beatOne: "Rained the whole time",
    beatTwo: "stayed anyway",
    image: "/products/send-it-1.webp",
    sizeOne: 8.3,
    sizeTwo: 12.4,
    position: "50% 40%",
  },
  {
    beatOne: "Trailer full of chairs",
    beatTwo: "nobody sat down",
    image: "/products/send-it-2.webp",
    sizeOne: 8.4,
    sizeTwo: 10.7,
    position: "50% 45%",
  },
  {
    beatOne: "Nobody booked anything",
    beatTwo: "worked out",
    image: "/products/spin-cycle.webp",
    sizeOne: 7.6,
    sizeTwo: 15.9,
    position: "50% 35%",
  },
  {
    beatOne: "Last one standing",
    beatTwo: "first one asleep",
    image: "/products/take-your-chances.webp",
    sizeOne: 10.3,
    sizeTwo: 11.4,
    position: "50% 40%",
  },
  {
    beatOne: "Cousin's engagement",
    beatTwo: "met the family",
    image: "/products/built-different.webp",
    sizeOne: 8.8,
    sizeTwo: 12.3,
    position: "50% 45%",
  },
  {
    beatOne: "Bowls club",
    beatTwo: "accidentally",
    image: "/products/cold-beer-1.webp",
    sizeOne: 16,
    sizeTwo: 14.3,
    position: "50% 35%",
  },
  {
    beatOne: "Ute in the paddock",
    beatTwo: "stereo on",
    image: "/products/eight-ball.webp",
    sizeOne: 10,
    sizeTwo: 19.1,
    position: "50% 40%",
  },
  {
    beatOne: "Cricket on",
    beatTwo: "nobody watching",
    image: "/products/good-times-1.webp",
    sizeOne: 17.8,
    sizeTwo: 10.7,
    position: "50% 45%",
  },
  {
    beatOne: "Meant to work tomorrow",
    beatTwo: "didn't",
    image: "/products/hero-good-times.webp",
    sizeOne: 7,
    sizeTwo: 31.8,
    position: "50% 35%",
  },
  {
    beatOne: "Four hour drive",
    beatTwo: "three hour stop",
    image: "/products/hero-street.webp",
    sizeOne: 11.7,
    sizeTwo: 11.5,
    position: "50% 40%",
  },
  {
    beatOne: "Bought a round",
    beatTwo: "lost the tab",
    image: "/products/love-fast-die-last.webp",
    sizeOne: 11.9,
    sizeTwo: 15.2,
    position: "50% 45%",
  },
  {
    beatOne: "Nan won the raffle",
    beatTwo: "again",
    image: "/products/midnight-service.webp",
    sizeOne: 9.5,
    sizeTwo: 33.8,
    position: "50% 35%",
  },
  {
    beatOne: "Dropped in for one",
    beatTwo: "stayed for six",
    image: "/products/not-yours.webp",
    sizeOne: 9.8,
    sizeTwo: 13,
    position: "50% 40%",
  },
  {
    beatOne: "Wrong turn",
    beatTwo: "better pub",
    image: "/products/permanent.webp",
    sizeOne: 15.6,
    sizeTwo: 17.4,
    position: "50% 45%",
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
