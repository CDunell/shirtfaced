# Curb Stamps — Homepage Rebuild Spec

Written 2026-08-24. For an implementer picking this up cold.

This is a **presentation-layer rebuild**. The commerce scaffolding underneath
(Printify catalog, product pages, cart, checkout, creature data) is real,
tested and working — see `docs/curbstamps/HANDOVER_2026-08-24.md`. Do not
touch it. What is wrong is the homepage's layout, density and visual
direction.

---

## 0. Read before you start

| Document | Why |
|---|---|
| `curbstamps-site/DESIGN_HANDOFF.md` | The current governing design doc — **and it conflicts with this spec, see §2** |
| `docs/curbstamps/HANDOVER_2026-08-24.md` | Real state of catalog, POD, payments, known-broken items |
| `docs/curbstamps/CURB_STAMPS_SPEC.md` | Product/brand spec |
| `CLAUDE.md` (repo root) | Standing rules. Especially: *look at it before saying it works* |

---

## 1. Approved references in the repo

**Resolved 2026-08-24.** The two references that now govern the build are:

- `assets/curbstamps/boards/board-02-structure.webp` — structure and illustrated curb world.
- `assets/curbstamps/boards/approved-homepage-direction.webp` — owner-approved full treatment.

The latter is the explicit owner decision and supersedes the earlier four-board
ambiguity described below.

The approved direction lives in **four design board images** that currently
exist **only as chat attachments**. They are not in the repository, not in
`assets/`, and not referenced by any document. Nothing here can be verified
against them until that is fixed.

Board set as observed:

| Board | Title | Character |
|---|---|---|
| 1 | 8-module mobile storyboard | Bright kids palette (pink/yellow/blue/green), picture-book, creature-first. This is what the current site was built from. |
| 2 | **WELCOME TO THE CURB** | Playful world. Full-bleed curb scene hero, dense commerce directly under it. Muted — black, cream, one sage block. |
| 3 | CREATURE INDEX | Archive/collectible. Dark, numbered creature cards. |
| 4 | **CURB CLUB** | Colour, attitude, 90s kids streetwear energy. Violet + acid green + tan, paint splats, stickers, distressed paper. |

**First task: commit boards 1–4 to `assets/curbstamps/boards/` and reference
them by path from this spec and from `DESIGN_HANDOFF.md`.** Until then every
colour value in §4 is an eyeball estimate and must be treated as unverified.

---

## 2. Direction — and the conflict you must resolve

**Owner decision, 2026-08-24: board 2's design with board 4's full treatment.**
Boards 2 and 4 are the owner's favourites. Board 1 is superseded.

**This directly contradicts the document that currently governs the site.**
`DESIGN_HANDOFF.md` §1 says *"Do not regress to the earlier
streetwear/editorial concepts"* and §2 forbids *"grunge, skate-editorial
layouts... dark luxury styling"*. Boards 2 and 4 are those earlier concepts.

Do not quietly build against this spec while that document says the opposite —
the next person to open the repo will revert you. **Update
`DESIGN_HANDOFF.md` to record the new direction and the date, or get explicit
sign-off to supersede it.** Direction is the owner's; the documentation just
has to catch up.

The earlier distinction is resolved:

> Use the palette **and** the full treatment: paint splats, sticker badges,
> distressed paper texture, cut-out photography and a condensed streetwear
> display face. Owner response: **"second all the way"**.

---

## 3. Measured baseline — what is actually wrong

All figures measured against the live build on 2026-08-24, Chrome, at
1440×900 and 390×844. Reproduce with Playwright before and after; these are
your regression targets.

### 3.1 There is no desktop layout

| Measurement | Value |
|---|---|
| `sm:` classes across `curbstamps-site/src` | **182** |
| `md:` / `lg:` / `xl:` / `2xl:` classes | **0** |
| Content column at 1440px viewport | 1024px (`max-w-5xl`) |
| Dead horizontal margin at 1440px | **416px — 29% of the viewport** |
| Page height, desktop 1440px | 6599px |
| Page height, mobile 390px | 6608px |

Tailwind's `sm:` breakpoint is 640px. **The layout at 1440px is identical to
the layout at 640px.** Desktop and mobile page heights matching within 9px is
the proof: the desktop build gains nothing from its extra width.

`DESIGN_HANDOFF.md` §8 requires `--page-max: 1180px`. That token **does not
exist** in `globals.css`.

### 3.2 Type never scales

| Element | Live desktop | `DESIGN_HANDOFF.md` §3 requires |
|---|---|---|
| Hero display | 64–68px, fixed at `sm:` | **72–104px** |
| Section headings | 38–58px, fixed at `sm:` | Strong hierarchy |

Mobile uses `vw` units and is roughly correct. Every desktop size is a fixed
`sm:` value that never grows again.

### 3.3 Commerce is absent from a quarter of the page

Eleven links to a product or the shop across 6599px:

| Scroll | Section | Shop links |
|---|---|---|
| 79–614 | PICK YOUR WEIRDO | 1 |
| 614–965 | NEW DROP | 1 |
| 964–1106 | Trust strip | 0 |
| **1106–1855** | **MEET THE CURB CREW** | **0** |
| **1855–2211** | **MAKE SOME WEIRDO NOISE** | **0** |
| **2211–2830** | **WHICH ONE IS BLIP?** | **0 until you win the game** |
| 2830–3718 | GOOD DAYS START HERE | 7 ← the only real commerce block |
| **3718–4196** | **WHAT'S YOUR THING?** | **0 until you pick a tile** |
| 4196–4978 | MADE FOR ADVENTURES | 1 |
| 4977–5575 | PARENTS CORNER | 0 |
| 5575–6281 | JOIN THE CURB | 0 |

Two distinct problems:

- **A 1724px dead zone** (26% of the page, three consecutive sections) with no
  path to any product. First substantial commerce block is at 2830px.
- **CTAs that exist but are hidden behind interaction.** `FindWeirdo` reveals
  `SHOP BLIP` only after a correct guess; `WeirdoMatch` reveals three product
  links only after a tile is picked. Neither renders any commercial
  affordance in its default state. Boards 1, 2 and 4 all show a visible CTA
  in the resting state.

### 3.4 Play occupies a third of the homepage

| Component | Height | Shop links at rest |
|---|---|---|
| `CurbCrewScene` / `CurbWorld` | 749px | 0 |
| `PlayInvitation` | 357px | 0 |
| `FindWeirdo` | 618px | 0 |
| `WeirdoMatch` | 477px | 0 |
| **Total** | **2201px — 33% of the page** | |

Board 1 had one game plus one preference picker that ended in product.
**Boards 2 and 4 contain no games at all.**

---

## 4. Target design

### 4.1 Palette — board 4

**Unverified estimates, eyeballed from the board image. Sample the real values
once the boards are committed (§1).**

| Token | Estimate | Role |
|---|---|---|
| `--color-ink` | `#1c1a17` | Unchanged. Shell, type, borders |
| `--color-paper` | `#fbf6ec` | Unchanged. Page ground |
| `--color-cream` | `#fffaf0` | Unchanged. Cards on paper |
| `--color-violet` | `~#8b6fe8` | **Primary accent.** One loud block per viewport |
| `--color-club` | `~#b8c62e` | Acid green. CTAs, the CURB CLUB band |
| `--color-tan` | `~#c9b58d` | Tertiary blocks, sticker/ticket elements |
| `--color-sage` | `~#6b7264` | Board 2's ADOPT A WEIRDO strip |

Board 4's discipline is **one loud block per viewport**, not a rainbow. In the
board, only the HOODIES block is violet; NEW DROP and TEES are cream and
ACCESSORIES is tan, which is what makes the violet land.

**Do not delete the six `--color-grit-*` values.** `src/lib/creatures.ts`
binds them to real garment colourways wired through to Printify. They stay as
per-creature accents. What changes is that they stop colouring the *shell*.

Known bug to fix while you are in there: `WeirdoMatch.tsx:29` derives each
tile's colour from `uiAccentFor(o.matches[0])` — the first matched creature's
accent — instead of assigning six distinct colours. LOVE OUTSIDE, LOVE
SLEEPING and LOVE FAST all render the same cyan.

### 4.2 Typography

Current display face is Baloo (rounded, friendly) — correct for board 1.
Board 4's condensed streetwear-leaning display treatment is approved. This is
a site-wide display-face change, while the friendly sans remains for body copy.

Sizes, regardless of face:

| Breakpoint | Hero display | Section heading |
|---|---|---|
| < 640px | 48–62px (`vw` units are fine) | 32–44px |
| 640–1024px | 56–72px | 34–44px |
| ≥ 1024px | **76–104px** | 40–56px |

### 4.3 Layout system

- Add real `md:` (768), `lg:` (1024), `xl:` (1280) tiers. **A homepage
  component with only `sm:` variants is not finished.**
- Introduce `--page-max: 1180px` in `globals.css` and use it for contained
  inner columns.
- Sections are **full-bleed**; the *content* inside them is contained. Board 2
  and board 4 both run edge to edge. `max-w-5xl` on the section wrapper is the
  bug — do not reproduce it.
- Horizontal padding: 16px mobile, 24px md, 32px lg.
- Section vertical rhythm: 36–64px mobile, 56–96px desktop.

---

## 5. Section-by-section

Target order. Board 2 supplies structure; board 4 supplies colour.

| # | Section | Source | Notes |
|---|---|---|---|
| 1 | **Header** | 4 | Black bar. Board 4 sets the wordmark in a violet block. Nav: SHOP / CREATURES / NEW / ABOUT / CLUB. Cart always visible. Desktop nav must not stay at its 640px scale. |
| 2 | **Hero — WELCOME TO THE CURB** | 2 | Full-bleed. Copy left, curb scene right/across. Headline 76–104px desktop. Two CTAs: `SHOP THE CREATURES` (ink) + `MEET THEM ALL` (club green). Creature line-up standing on a kerb running the full width. |
| 3 | **Creature picker** | 2 | `WHO'S YOUR FAVOURITE?` — horizontal row of ~10 creatures with names. Scrolls on mobile, fits on desktop. Each links to that creature's products. |
| 4 | **NEW ARRIVALS / MOST WANTED** | 2 | Two-up. **This is what fills the 1724px dead zone.** Commerce directly under the hero, not 2830px down. |
| 5 | **ADOPT A WEIRDO** | 2 | Sage strip, creature row, arrow to full range. |
| 6 | **Category blocks** | 4 | Four-up: NEW DROP / TEES / HOODIES / ACCESSORIES. One violet block only. Each carries its own visible SHOP link. |
| 7 | **Trust strip** | 1/2 | Keep. Four items, black, cream icons. Already fine. |
| 8 | **MEET THE CURB CREW** | 2 | See §6 — the current implementation is broken and off-direction. |
| 9 | **MADE FOR ADVENTURES** | 1 | Keep. Fix the icon bug in §6. |
| 10 | **PARENTS CORNER** | 1 | Keep. Visually quieter than the kid-facing world. |
| 11 | **CURB CLUB** | 4 | Acid-green band. Headline, one line of copy, email + `JOIN UP`, creature parade. Replaces the black JOIN THE CURB block. |
| 12 | **Footer** | 2/4 | Black. SIZING / SHIPPING / RETURNS / FAQ / CONTACT, socials, creature parade. |

### Games

Move `PlayInvitation`, `FindWeirdo` and `WeirdoMatch` to the existing `/play`
page, which is already built and already in the nav. Boards 2 and 4 have no
games on the homepage.

If the owner wants one retained on the homepage, keep **exactly one**, place
it after the commerce blocks, and **give it a visible product CTA in its
resting state** — not one that only appears after the game is won.

`PlayInvitation` is the weakest of the three and should go regardless: 357px
of full-width colour whose only function is to advertise another page.

---

## 6. Bugs to fix

1. **`CurbWorld` promises interaction it does not have.** Copy reads *"Stop at
   a weirdo, **tap their hiding spot** and meet the whole range."* The
   component contains exactly two buttons — the left and right scroll arrows —
   and **zero links and zero clickable creatures**. Nothing in that 749px
   scene is tappable. Either make the creatures real links to their products,
   or change the copy. Currently it is the second module a visitor hits.

2. **Resolved 2026-08-24:** the photoreal crew scene was replaced by ten
   seamless light cream-and-black illustrated panels at
   `public/curbstamps/world/panels/01.webp` through `10.webp`.

3. **`WeirdoMatch` tile colour collision** — see §4.1.

4. **`WeirdoMatch` icons are raw emoji** (`🐾 🌲 ☺ ☾ ⚡ ●`). Three render as
   near-invisible glyphs. Board calls for one obvious icon or doodle per tile.

5. **`AdventureGrid` creature/photo mismatch** — already logged as outstanding
   in `HANDOVER_2026-08-24.md`. The icon under each of PLAY/EXPLORE/MAKE/BE is
   a fixed `CREATURES[1]/[3]/[6]/[9]`, unrelated to whichever rotated photo
   landed above it. `HomepagePhoto` needs a `creature` field.

6. **Composited lifestyle photos read as stickers.** Also logged in the
   handover: the 13 homepage photos use flat alpha-overlay compositing with no
   perspective warp or shadow matching. This is a property of the method, not
   a tuning issue. Affects all 13. Out of scope for a layout rebuild, but do
   not design a layout that leans harder on them than the current one does.

---

## 7. Assets required

**This is the part that cannot be coded.** An earlier attempt at this rebuild
hand-rolled board 4's paint splats as SVG blobs and produced grey circles.
Do not repeat that. Layout, breakpoints, type scale, colour and density are
engineering. The following are art, and must be produced as assets before the
board 2/4 look is achievable:

| Asset | For | Notes |
|---|---|---|
| Curb scene, line-art, light | Hero (§5.2) and crew scene (§5.8) | Board 2 style. SVG so line weight stays crisp. Replaces the photoreal webp |
| Paint splats — violet, acid green | Board 4 treatment | Painterly edges. Only if §2's treatment question resolves yes |
| Sticker/badge elements | Board 4 treatment | CURB STAMPS stamp, LOCALS ONLY ticket, smiley, star doodles. Same condition |
| Distressed paper texture | Board 4 hero ground | Same condition |
| Street sign — CURB STAMPS | Hero | Board 2 |
| Creature parade strip | Footer, CURB CLUB band | Can be composed from existing `public/curbstamps/creatures/*.svg` |
| Cut-out product photography | Category blocks, hero | Subject on transparent ground, not the current composited-print photos |

`studio/docs/ASSET_SPECIFICATION.md` is the brief format for this repo.
**Audit `assets/` before requesting anything** — a lot already exists.

---

## 8. Acceptance criteria

Measurable. Run these; do not eyeball them alone.

- [ ] `md:` / `lg:` / `xl:` variants present across homepage components. Zero
      homepage components with only `sm:` variants.
- [ ] At 1440×900, content spans ≥ 1180px. Dead margin ≤ 12% (from 29%).
- [ ] Desktop page height is **materially shorter** than mobile page height.
      Currently 6599 vs 6608 — they must diverge.
- [ ] Hero display ≥ 76px at 1024px and above.
- [ ] **No scroll span greater than 800px without a visible link to a product
      or the shop.** Currently the worst gap is 1724px.
- [ ] A visible shop CTA exists **above 1200px scroll** on desktop, in
      addition to the hero.
- [ ] Every interactive module renders a commercial affordance in its
      **resting** state, before any interaction.
- [ ] `CurbWorld` copy and behaviour agree — creatures are links, or the copy
      changes.
- [ ] Six visually distinct tile colours in `WeirdoMatch`.
- [ ] No unintended document-level horizontal overflow at 320, 390, 768,
      1024, 1440, 1920. `CurbWorld` and the mobile creature picker intentionally
      scroll inside their own bounded containers.
- [ ] Tap targets ≥ 44px throughout.
- [ ] Reduced-motion respected.
- [ ] WCAG AA on body copy and controls — check violet and acid green against
      both ink and paper, both directions.
- [ ] Screenshots at 390, 768, 1440 attached to the handover before claiming
      done.

---

## 9. Traps

Each of these was hit on 2026-08-24 and cost time.

- **Do not hand-code the artwork.** Splats, textures and stickers as CSS or
  inline SVG paths look like grey circles. Get real assets (§7).
- **Do not `max-w-5xl` the section wrapper.** That single class is the root
  cause of the sparse desktop. Full-bleed section, contained content.
- **Do not constrain a 90px headline to a `max-w-[16ch]` column.** It wraps to
  four lines and the CTAs wrap with it.
- **Do not assume `DESIGN_HANDOFF.md` endorses this direction.** It forbids it.
  Update it (§2).
- **Do not treat the §4.1 hexes as canon.** They are eyeballed from an image
  that is not in the repo.
- **Do not delete `--color-grit-*`.** Wired to Printify garment colourways.
- **Look at it before saying it works.** Screenshot every breakpoint.
