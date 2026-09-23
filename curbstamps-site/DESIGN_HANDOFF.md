# CURB STAMPS — Website Design Handoff

## 2026-08-24 direction reset — current authority

The eight-module bright picture-book direction below is superseded for the
homepage presentation layer. The owner approved:

**Board 2's structure with board 4's full treatment.** This means black and
cream remain the base, with violet, acid green and tan used in controlled
blocks; the condensed display face, painterly splats, sticker/ticket elements,
distressed paper texture and cut-out editorial treatment are all included.

Authoritative visual references:

- `../assets/curbstamps/boards/board-02-structure.webp`
- `../assets/curbstamps/boards/approved-homepage-direction.webp`

Implementation and measurable acceptance criteria:
`../docs/curbstamps/HOMEPAGE_REBUILD_SPEC.md`.

The commerce, Printify, cart and checkout systems are not part of this visual
reset. The historical direction below remains only as a record and must not be
used to revert the approved homepage.

Status: APPROVED VISUAL DIRECTION
Branch: `claude/curb-stamps-kids-shop-sas8gu`
App: `curbstamps-site/`
Admin: `curbstamps-admin/`

## 1. Production authority

Build the storefront from the approved final storyboard direction from the current ChatGPT session: the bright, simple, creature-first kids shop board with eight modules:

1. PICK YOUR WEIRDO
2. MEET THE CURB CREW
3. FIND YOUR WEIRDO
4. SHOP THE LOOK
5. WEIRDO MATCH
6. WEAR YOUR WEIRDO
7. PARENTS CORNER
8. JOIN THE CURB

Do not regress to the earlier streetwear/editorial concepts. This is a brand for little kids first, with parents as the buyer. Target feel: picture-book clarity + playful ecommerce. Cute, direct, bright, tactile, easy to understand without reading much.

## 2. Creative law

- Creature first, product second, copy third.
- Core age range: roughly 2–10, with strongest visual appeal around 3–8.
- Never make the children look like miniature fashion influencers.
- Avoid ironic streetwear language, grunge, skate-editorial layouts, faux-cool adult slogans, complicated quizzes, dark luxury styling or tiny decorative UI.
- Keep the creature drawings extremely simple, naive, cute and horizontally compact.
- Keep black and cream as the brand anchor; use bright child-friendly colour blocks for energy.
- Use real kids in candid play, movement and natural expressions.
- Parent information must be present and obvious, but visually quieter than the kid-facing world.

## 3. Global design system

Existing token file: `src/app/globals.css`.

### Core colours

- Ink: `#1C1A17`
- Paper: `#FBF6EC`
- Paper 2: `#F1E9D8`
- Cream: `#FFFAF0`
- Yellow: `#FFC93C`
- Blue: `#3EC6E0`
- Pink: `#FF6F9C`
- Green: `#7ED957`
- Orange: `#FF8C42`
- Optional soft lilac: `#C7B8FF`

Use black/cream for shell, nav, footer and primary contrast. Use one bright colour per tile or creature state; avoid rainbow gradients.

### Typography

Use the current rounded display + friendly sans pairing already configured in `globals.css`.

Display rules:
- Rounded, chunky, uppercase or short stacked lines.
- Strong hierarchy.
- 0.9–1.0 line-height for large display copy.
- Mobile hero display: 48–62 px.
- Desktop hero display: 72–104 px.

Body/UI:
- 15–18 px normal body.
- 13–15 px helper text.
- Buttons minimum 16 px, bold.

### Shape language

- Buttons: pill or heavily rounded.
- Cards: 18–24 px radius.
- Product photography: 16–20 px radius unless it sits flush inside a colour block.
- Creature tiles can be square-ish or landscape, never fussy.
- Borders: simple 1–2 px ink or `ink/10`.

### Motion

Motion should feel like toy feedback:
- tap = tiny squash
- hover = wiggle or bounce
- creature = blink, shuffle, nod or wobble
- 180–420 ms only
- no parallax-heavy effects
- obey reduced-motion

## 4. Homepage production storyboard

### A. Header

Desktop:
- Black or cream shell depending section.
- CURB STAMPS wordmark left.
- Nav: SHOP / WEIRDOS / NEW / ABOUT.
- Search/account optional if already implemented; cart always visible.

Mobile:
- Wordmark left.
- Hamburger right.
- Cart visible.
- 56–64 px total height.

No mega-menu on first build.

### B. Hero — PICK YOUR WEIRDO

Black background.

Left:
- `PICK YOUR WEIRDO!`
- small CTA: `FIND YOUR FAVOURITE`

Right:
- one oversized cream line creature, approx 42–48% of hero width desktop.
- hero creature must look friendly and simple, not anatomically accurate.

Under hero:
- horizontally scrollable creature strip.
- each item = line creature + short name.
- selected creature tile receives a bright colour block.
- tapping a creature changes hero creature, accent and product link.

Desktop hero: about 560–680 px tall including chooser.
Mobile: stack text, creature, chooser.

### C. NEW DROP

Directly after creature chooser.

Mixed 4-column / 2-column responsive strip:
- one candid child image
- one cream tee flat/product image
- one black hoodie flat/product image
- one second candid child image

Add a small coloured title block: `NEW DROP!` / `Just landed.` / `SHOP NEW`.

Photography should feel natural and active: laughing, running, sitting outdoors, climbing, drawing, mucking around. No studio-fashion posing.

### D. Trust strip

Black strip, cream iconography and copy.

Four concise items:
- SOFT STUFF — Feels good.
- MADE TO PLAY — Built tough.
- EASY PEASY — Easy returns.
- HAPPY MUMS — We get you.

Do not over-explain.

### E. MEET THE CURB CREW

Cream/paper section.

Large illustrated scene spanning width: a curb, cardboard box, simple sign, tiny plant/cloud details and 4–6 creatures. It should look like a children’s book spread, not a detailed environment.

Headline: `MEET THE CURB CREW!`

Below:
- four big coloured creature cards.
- each card has one creature, its name, and arrow/button.
- cards use pink / yellow / blue / green as separate blocks.

### F. FIND YOUR WEIRDO mini-game

Black outer section.

Headline: `CAN YOU FIND [CREATURE]?`

Main content:
- simple cream line-art playground or park illustration on paper background.
- hide multiple creatures inside it.
- tap/click targets should be generous and keyboard accessible.
- successful find gives a friendly state: `FOUND ONE!` and direct CTA to that creature’s products.

Keep this optional/lazy loaded on low-power devices.

### G. SHOP THE LOOK

Paper/cream with bright top accent.

Large candid child photo with simple doodle accents (sun, rainbow, tiny creature).
Headline: `GOOD DAYS START HERE.`
Subline: clothes for little weirdos who do big things.

Category chips/cards beneath:
- TEES
- HOODIES
- SHORTS
- HATS
- ACCESSORIES

Large simple icons. Touch targets minimum 48 px.

### H. WEIRDO MATCH

Black background.

This is not an adult personality quiz. It is a six-button child-friendly picker.

Headline: `WHAT'S YOUR THING?`

Six large colour tiles:
- LOVE ANIMALS
- LOVE OUTSIDE
- LOVE SILLY
- LOVE SLEEPING
- LOVE FAST
- LOVE SNACKS

Each tile has one obvious icon/doodle. After selecting, show 3 creature suggestions, not a long questionnaire.

### I. WEAR YOUR WEIRDO

Paper section.

Headline: `MADE FOR ADVENTURES.`

4 candid child photos in a row/grid, each paired with a tiny creature and one word:
- PLAY
- EXPLORE
- MAKE
- BE

Keep children diverse in appearance and activity. Avoid overly styled editorial fashion poses.

### J. PARENTS CORNER

Soft paper or pale lilac block.

Headline: `PARENTS CORNER`

Six simple information cards:
- SOFT & COMFY
- EASY CARE
- BUILT TO LAST
- SAFE STUFF
- SIZES 2–10
- FAST SHIPPING

Use simple line icons. Each card can link to full information pages.

Include a small `QUESTIONS? SEND US A MESSAGE` contact block.

### K. JOIN THE CURB

Black background.

Headline: `JOIN THE CURB!`
Subline: first to see new drops and special stuff.

Email field + bright green/yellow submit button.
No manipulative scarcity language.

Below:
- Instagram/TikTok links if enabled.
- row of all current creatures marching across the footer.
- closing line: `MORE WEIRDOS COMING SOON...`

## 5. Responsive rules

Breakpoints can stay Tailwind defaults.

Mobile-first requirements:
- No horizontal text clipping.
- Horizontal creature picker may scroll.
- All tap targets >= 44 px; use 48–56 px where practical.
- Product/category cards one or two columns.
- Hide nonessential decorative doodles under ~420 px.
- Keep one dominant CTA per viewport.
- Do not force desktop compositions into tiny stacked replicas; simplify.

## 6. Image and illustration asset manifest

Create/use these asset groups under `curbstamps-site/public/curbstamps/`:

### Brand
- `logo/curb-stamps-wordmark-dark.svg`
- `logo/curb-stamps-wordmark-light.svg`

### Creatures
For every released creature:
- `creatures/{slug}-dark.svg` — ink line on transparent
- `creatures/{slug}-light.svg` — cream line on transparent
- optional `creatures/{slug}-accent.svg`

Source art rule: preserve the approved one-colour continuous-line style; no added anatomy, textures or shading.

### Homepage illustrated scenes
- `scenes/curb-crew.svg`
- `scenes/find-your-weirdo.svg`
- `scenes/footer-parade.svg`

Scenes should be SVG so line weights remain crisp.

### Photography
Minimum launch set:
- `photos/home-hero-kid-01.webp`
- `photos/home-newdrop-kid-01.webp`
- `photos/home-newdrop-kid-02.webp`
- `photos/adventure-play.webp`
- `photos/adventure-explore.webp`
- `photos/adventure-make.webp`
- `photos/adventure-be.webp`

Image direction:
- genuine children roughly 3–9
- outdoor/natural/playful
- Australian suburban/coastal/park feel where possible
- daylight, warm but not orange-filtered
- no identifiable real brand logos
- garments clearly visible without becoming catalog poses

### Product imagery
For each sellable SKU:
- front flat/product image
- back if printed
- one worn image where possible
- transparent or clean neutral background preferred

## 7. Component map

Recommended components:

- `SiteHeader`
- `MobileNav`
- `HeroWeirdo`
- `CreaturePicker`
- `CreatureTile`
- `NewDropStrip`
- `TrustStrip`
- `CurbCrewScene`
- `FindYourWeirdo`
- `CategoryButton`
- `WeirdoMatch`
- `AdventureGrid`
- `ParentsCorner`
- `NewsletterJoin`
- `CreatureFooterParade`

Keep creature/product data in existing `src/lib` data sources; do not hard-code duplicate catalog data into homepage components.

## 8. CSS implementation notes

Keep existing global tokens. Add component classes/utilities only when repeated; Tailwind is already installed.

Required layout values:
- `--page-max: 1180px`
- desktop horizontal padding: 32 px
- mobile horizontal padding: 16 px
- section vertical rhythm: 56–96 px desktop, 36–64 px mobile
- card gap: 12–20 px

Hero black should be true visual anchor; do not make the entire site black.

Bright accents should be flat solid fills only. No gradients required.

Line-art creature stroke should visually land around 3–5 px at typical card sizes and scale responsively in SVG.

## 9. Accessibility

- WCAG AA minimum for body copy and controls.
- Decorative creature SVGs: `aria-hidden=true`.
- Interactive creature cards require accessible labels, e.g. `View NUB products`.
- Do not encode meaning only by colour.
- Respect reduced motion.
- Mini-game must be keyboard operable and have a non-game fallback link.
- Images of products need product-specific alt text; lifestyle imagery can use short contextual alt or empty alt if purely decorative.

## 10. Admin requirements

`curbstamps-admin/` should be able to manage:
- homepage featured creature
- creature order in picker
- selected creature accent colour
- new drop products
- homepage lifestyle images
- enabled/disabled mini-game
- parent feature copy
- newsletter destination/config

Do not build a page-builder. Keep admin as structured fields for this fixed design system.

## 11. Copy tone

Use very short, playful, literal copy.

Good:
- PICK YOUR WEIRDO!
- MEET THE CURB CREW!
- CAN YOU FIND SLAG?
- GOOD DAYS START HERE.
- WHAT'S YOUR THING?
- MADE FOR ADVENTURES.
- JOIN THE CURB!

Avoid:
- fashion jargon
- ironic adult copy
- aggressive streetwear language
- over-written brand lore

## 12. Build order

1. Rebuild homepage shell + hero + creature picker.
2. Add new-drop strip and trust strip.
3. Add crew scene and creature cards.
4. Add shop-by-category section.
5. Add Weirdo Match.
6. Add adventure photography section.
7. Add Parents Corner.
8. Add Join/footer parade.
9. Add Find Your Weirdo mini-game last.
10. Connect admin fields after visual homepage is approved.

## 13. Acceptance test

The first five seconds of the homepage must communicate:

- this is for little kids
- the creatures are the stars
- the clothes are fun and wearable
- a parent can immediately find the shop/cart

If the page reads as a streetwear editorial, collectible trading platform, complicated game, or adult design exercise, it is wrong.
