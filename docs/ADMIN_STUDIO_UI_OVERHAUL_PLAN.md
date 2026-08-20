# Admin/Studio UI Overhaul — Pre-Kickoff Audit + Phased Plan

**Date:** 20 August 2026
**Trigger:** "FIX THE FUCKING UI. This is the 3rd time I have requested the UI match the
store/site and it hasn't been done." Full ask: separate admin.shirtfaced.wtf from
studio.shirtfaced.wtf with a 2-link nav (admin = store backend, studio =
generation/socials/marketing), audit nav + pages for staleness, flesh out admin with
store backend + ordering.

**Method:** live-verified against the running sites (computed styles pulled from
shirtfaced.wtf, admin.shirtfaced.wtf, studio.shirtfaced.wtf directly), not just code
reading. Full page inventory read from both apps' route trees, not from the one flow
that was already open. Nothing below was scoped from memory of a prior session.

---

## 1. Subdomain separation — already true, the nav hierarchy isn't

`admin.shirtfaced.wtf` and `studio.shirtfaced.wtf` are already two separate
deployments (separate Next.js and Vite apps, separate Cloudflare Tunnel routes,
confirmed live). Technical separation is not the gap.

The gap is that each app treats the other as a secondary escape hatch, not a peer:

- **Admin's nav** (`admin/src/components/Nav.tsx`): `Products | Content` as real tabs,
  then `Studio ↗` bolted on as one more link in the same row, opening in a new tab.
- **Studio's nav** (`studio/web/src/App.tsx`): a hamburger menu (used at *every*
  width, not just mobile) with two pipeline groups ("Product", "World"), and a third
  group called **"Elsewhere"** containing `Admin ↗` next to the theme toggle — Admin is
  filed alongside a display preference, not presented as the other half of the same
  tool.

Neither app currently has a real 2-link, symmetric "Admin | Studio" nav. That's what
needs building, not a subdomain split that already exists.

---

## 2. Why "match the site" has failed 3 times — root cause, not symptom

This is the part worth being honest about before starting a 4th attempt at the same
fix.

**Admin** is Next.js + Tailwind and already shares literal class/token names with the
storefront (`bg-ink`, `text-paper`, `wordmark`, the same `press` button-press utility).
Architecturally the closest of the two apps to the storefront.

**Studio** is a Vite/React app built on **Base Web (`baseui`)**, a full component
library with its own styletron-based theming engine. A prior session already found
and named this exact problem — `studio/web/src/theme.ts`'s own comment says *"stock
Base Web is what made Studio look like a different application"* — and responded by
porting the full brand sheet (colours, radii, fonts, from `admin/src/app/globals.css`)
into Base Web's theme object, value for value (`studio/web/src/tokens.ts`). That fix
already shipped. It is still not enough, per this being the 3rd complaint.

**Live-verified drift that token-porting can't fix**, pulled from computed styles on
the running sites just now, not theorised from code:

| Surface | Storefront | Admin | Studio |
|---|---|---|---|
| Header background | solid **ink** (`#0d0d0d`), paper text — the loudest, most identity-bearing bar on the site | **paper**, blends into the page, `border-b` hairline only | **paper**, same as Admin |
| Hero / opening moment | huge uppercase **Anton** display headline on a dark section, reversed-contrast paper pill CTA ("shop the damage") | none — opens straight into a product list | none — opens straight into a "Work" queue |
| Primary CTA | pill button, paper-on-ink or ink-on-paper, `press` micro-interaction | Tailwind pill buttons, same radius tokens | Base Web buttons, themed to the same hex values but a different component's padding/shadow/focus-ring/motion underneath |

**Conclusion:** the two previous fix attempts (this one included, going by the code
comments) worked at the *token* layer — same hex values, same radii, same font
files. That was necessary but not sufficient. The actual gap is **compositional**
(the storefront uses ink-as-background boldly and rarely; admin/studio use it only as
text) and, for Studio specifically, **structural** — Base Web's own component
behaviour (padding rhythm, shadow, focus rings, transition curves) cannot be made
pixel-identical to the storefront's hand-built Tailwind components by overriding a
theme object, because the components themselves are not the same components.

This is the one decision in this plan I'm not making unilaterally — see the question
below.

---

## 3. Full page inventory — audited from the route tree, not the flow I already knew

Per the standing rule from the Orveris rewrite (don't scope from the one page/flow
that's easy to trace): here is every route in both apps, read from the directory
tree directly.

**Admin** (`admin/src/app/`, 16 routes):
- `/login`
- `/products`, `/products/new`, `/products/[id]` — product + colourway + stock CRUD
- `/content` (landing grid of 11 cards) → `/content/about`, `/shipping`, `/returns`,
  `/contact`, `/size-guide`, `/product`, `/account`, `/more`, `/garment-care`, `/faq`
- Confirmed live, nothing beyond this: **no orders, no customers, no discounts, no
  inventory alerts, no analytics.** `admin/README.md`'s own stated v1 scope agrees:
  "Order/customer records are not built — the storefront still has no
  checkout/payment integration to generate real orders from."

**Studio** (`studio/web/src/App.tsx`, 13 destinations across 2 declared pipelines):
- **Product pipeline:** Prompt, Gallery, Work, Evidence, Research, Designs (this one
  already absorbed former Compose and Score screens — Phase 5 of an earlier
  restructure)
- **World pipeline:** Dashboard, Prompts, Cast, Locations, Scenes, Social, Email
- Studio's nav has already been through at least two internal audits (a "14 August
  audit" and a "Phase 2a/Phase 5" restructure, both referenced in code comments) — so
  nav *information architecture* work is partway done already. The open ask now is
  chrome/visual parity plus re-grouping to your stated frame (generation / socials /
  marketing), not a from-scratch IA pass.

---

## 4. Staleness audit — resolved, 20 August 2026

Checked every one of the 13 Studio destinations and all 16 Admin routes against git
history (last-touch date per file), live GitHub Actions run history, and a grep for
dead references. Correcting my own first-pass guess below rather than repeating it as
fact — the evidence contradicts it.

**Result: nothing in either app shows real signs of staleness.** Every Studio bench
component was touched between 5–20 August 2026 (two weeks); the oldest-touched
(`WorldPage`, `ServiceStatus`, `ReviewPanel`, `DecisionPanel`, `CanonProposals`, all
5 Aug) are stable dashboard/review pieces that simply haven't needed edits since, not
abandoned code. Every Admin route is either live production tooling (confirmed by
browsing the running site — real products, real content rows) or unchanged because
it's a simple, working form.

Specifically, correcting the three things I flagged as questions before checking:

- **`VintageEvidenceBench` / `VintageResearchBench` — actively developed, not a pivot
  leftover.** I was wrong to flag this as possibly stale without checking. Evidence:
  10 vintage-specific commits in the last two weeks (`fix(vintage): ...`,
  `feat(vintage): ...`), 5 dedicated GitHub Actions workflows
  (`backfill-vintage-ebay-images.yml`, `check-vintage-image-cache.yml`,
  `collect-vintage-ebay-next100.yml`, `collect-vintage-ebay-sold.yml`,
  `commit-vintage-agent-batches.yml`), and real recent run history on the Oracle box.
  This is a live eBay-sourced evidence pipeline, per its own current state consistent
  with `[[shirtfaced-vintage-chain-stops-at-planned]]` (open at PLANNED stage, not
  dead). **Keep, no change.**
- **`EmailBench` — real, working tooling (templates, DNS plan, test-send, marketing
  consent), not a leftover.** Not stale — just filed under Studio's "World" pipeline
  today. Fits naturally under your "marketing" framing. **Keep, regroup in Phase 4.**
- **Print/compositing leftovers — none found.** Grepped the whole `studio/web/src`
  tree for any reference to the old manual 4-corner placement flow the App.tsx
  comment says was removed 15 August. Nothing left pointing at it. **Nothing to clean
  up.**

**Correction, 20 August 2026:** the git-recency method above is worthless on a
project that's one week old — everything will trivially show as "recently touched"
regardless of whether it's actually live or already abandoned in your head, which is
exactly what happened with the print/placement flow days earlier. Recency isn't a
staleness signal here; only you know what's already been mentally dropped. Asked
directly instead: **confirmed none of the 13 Studio destinations or 16 Admin routes
are considered stale or superseded.** Pruning is deferred to after the Phase 0/1
refit rather than attempted now — noted, not forgotten.

**Phase 2 status: closed.** Full destination list carries forward unpruned into
Phase 0 and Phase 4.

---

## 5. "Admin needs ordering" — the real dependency

No checkout/payment integration exists anywhere in the stack — the storefront cart
collects contact/address/shipping and totals but has **no card fields by design**
(confirmed in `src/app/checkout/page.tsx` and the root README's own "Next steps").
So "orders" in Admin can't mean "manage real customer orders" yet — there's nothing
generating them.

This plan treats Admin's order/customer data model and UI as buildable **now**, so
it's ready the moment checkout ships rather than becoming a second scramble later —
but real order rows won't exist until that's wired. Flagging this dependency up front
rather than letting it surface mid-build.

---

# THE PHASED PLAN

## Phase 0 progress — 20 August 2026

**Foundation shipped and verified, not just written:**
- `studio/web`: Tailwind v4 installed and wired (`@tailwindcss/vite`), `index.css` now
  carries the full brand-sheet `@theme` block ported value-for-value from
  `admin/src/app/globals.css` (previously these values sat as bare CSS custom
  properties, not real Tailwind tokens) plus a class-based `dark` variant so the
  existing light/dark toggle keeps working under Tailwind instead of Base Web's theme
  object.
- `studio/web/src/components/ui.tsx` — new shared primitive library: Button, Input,
  Textarea, Select, Checkbox, FormControl, Card, Notification, Tag, ProgressBar,
  Spinner, Table, and the Typography scale (Heading/Label/Paragraph/Mono at
  Small/XSmall), all Tailwind, matching Admin's existing `ui.tsx` patterns and
  extending them to cover what Studio's benches actually use (confirmed by grepping
  every `baseui` import across all 25 component files first — this is that full set,
  not a guess).
- `chrome.tsx` rebuilt off Tailwind — every exported signature (`PageTitle`,
  `SectionTitle`, `StatusChip`, `CopyButton`, `PasteButton`, `Disclosure`) unchanged,
  so the 15 files that import from it don't need to change until their own turn.
- `App.tsx` shell (header, hamburger nav, pipeline grouping) rebuilt off Tailwind.
- **Verified live**, not just typechecked: ran the dev server, confirmed via computed
  styles that the header/wordmark/background render with real Tailwind classes: 144
  existing tests pass, `tsc --noEmit` is clean, production build succeeds.
- **Caught and fixed one real bug in verification**: the dark-theme toggle updated
  state and `localStorage` correctly but never touched `<html class="dark">`, so the
  new Tailwind chrome silently ignored the toggle it always used to render — this
  slipped through typecheck and the build clean, only the live click-and-inspect
  check caught it. Added `useSyncDarkClass` to `ui.tsx` and wired it into `App.tsx`;
  re-verified both directions of the toggle work.
- At this point in the session Base Web was still installed and required — 23 of 25
  component files still imported it directly. See below: by the end of the same
  session, all 26 were converted and the dependency removed entirely.

## Phase 0 — DONE, 20 August 2026 (same night)

All 26 remaining component files converted (parallel background agents, each briefed
with the exact conversion spec and pointed at `ServiceStatus.tsx`/`chrome.tsx` as
real worked examples, not prose alone). Zero files in `studio/web/src` import from
`"baseui"` or call `useStyletron` any more.

**Bugs the migration itself surfaced, fixed as they came up rather than shipped:**
- `ui.tsx` was missing three real capabilities baseui had: `Button.isLoading`
  (spinner + disabled during a request), `Input`/`Textarea` `error` (red border),
  `Checkbox` `disabled`. Added centrally so every in-flight agent inherited the fix
  automatically instead of each hand-rolling a workaround.
- Three test files broke for real reasons, not just needing a migration touch-up:
  `CastBench.test.tsx` (a native `<select>`'s `<option>` text is always in the DOM,
  unlike Base Web's portal-rendered dropdown, so a `getByText` query started
  matching two elements), `PromptWorkbench.test.tsx` and
  `VintageResearchBench.test.tsx` (both used a click-to-open/click-option
  interaction pattern that only ever worked around Base Web's own Select — rewritten
  to `userEvent.selectOptions`, which also exposed a real async-loading race in
  `PromptWorkbench` that the old workaround had been silently masking).
- One process incident worth recording: running many parallel agents against one
  shared (non-isolated) working tree let one agent's own `git stash`/pull sequence
  transiently disturb others' in-progress edits, and separately pulled in unrelated
  content (`CLAUDE.md`, `docs/AGENCY_ARM.md`) plus a stale, unrelated stash conflict
  in two backend Python files from the concurrently-pushing cloud session mentioned
  in `[[shirtfaced-parallel-claude-sessions]]`. Diagnosed and resolved cleanly (the
  conflict was old, superseded WIP — resolved to the current, self-consistent code
  and left the original stash entry untouched and recoverable). Nothing was lost, but
  the next multi-agent pass touching this repo should use worktree isolation per
  agent rather than a shared tree.
- Final cleanup done same session: `baseui`/`styletron-*` dropped from
  `package.json` (129 packages removed), `tokens.ts` deleted, `theme.ts`/`main.tsx`/
  `test/render.tsx` stripped to plain localStorage + rendering with no provider
  tree. React 18 pin deliberately left in place — no longer load-bearing now that
  Base Web's `defaultProps` reliance (ADR-011) is gone, but bumping to 19 is its own
  separately-verified change, not bundled into this cleanup.

**Verified, not just typechecked:** `tsc --noEmit` clean, full suite (144 tests)
passing across multiple consecutive runs, production build succeeds. Bundle size
854KB → 457KB (components converted) → 305KB (dependency removed) — a 64% drop,
concrete proof Base Web is genuinely gone, not just unused-but-still-shipped.

**Exit test — met:** every primitive Studio renders through now comes from the same
Tailwind component layer Admin uses, not a themed instance of a different library.

---

## Phase 0 — original plan text (kept for record; see "DONE" above for what shipped)

- Rebuild Studio's ~25 `components/*.tsx` off Base Web onto hand-built Tailwind
  components matching Admin's actual patterns (`admin/src/components/ui.tsx` and
  friends) — same radius/shadow/motion values, not just same theme tokens feeding a
  different library.
- Build the shared surfaces the live comparison found missing everywhere: an
  ink-header/ink-panel option, a bold hero/section-opener pattern, the storefront's
  specific pill-button treatment and `press` micro-interaction.
- **Exit test:** admin and studio headers, primary buttons, and page-opening treatment
  are visually indistinguishable from the storefront's own, side by side — not just
  matching design tokens on paper.

## Phase 1 — DONE, 20 August 2026 (same night)

Both apps moved off their top-header nav onto a shared sidebar shape — built twice
(Admin's `Sidebar.tsx` in Next.js, Studio's `Sidebar.tsx` in Vite/React, no shared
component library between the two codebases) but to one deliberately mirrored
pattern: a persistent left sidebar on desktop, `Admin`/`Studio` pinned as a
symmetric peer pair at the bottom (whichever app you're in shown active, the other
linking out), collapsing to a top bar + slide-out drawer below the `sm` breakpoint.

- **Admin:** `Products`/`Content` are the sidebar's main items — Phase 2 resolved
  clean so nothing needed pruning first. Old `Nav.tsx` deleted.
- **Studio:** all 13 destinations across the Product/World pipelines render in the
  sidebar unconditionally on desktop — no click needed, unlike the hamburger it
  replaced. Theme toggle moved to its own slot above the pinned Admin/Studio pair.
  Pipeline grouping unchanged — that regroup is Phase 4's job, not this one's.
- `App.test.tsx` needed a real rewrite, not a patch: every test was built around
  "everything lives behind the hamburger, at every width," which stopped being true
  the moment the sidebar started rendering its nav unconditionally on desktop.
  `getByRole("banner")` also stopped matching anything once neither the mobile bar
  nor the desktop `<aside>` carried that role. Replaced with a `sidebar()` helper
  scoped to the actual element.
- Two real lint issues surfaced and fixed: an unnecessary effect-based
  close-on-navigate in Studio's sidebar (plain `useState`, not a router pathname —
  no back/forward to catch, so `setState-in-effect` was correctly flagging dead
  weight) and two test callbacks left `async` with nothing left to await.
- The exact same `useEffect(() => setOpen(false), [pathname])` pattern in Admin's
  new sidebar also trips `setState-in-effect` — checked against the original
  `Nav.tsx` before any of this session's changes and confirmed it was already
  there, unchanged. Left alone, consistent with Phase 0's rule: fix what you
  introduce, don't scope-creep into unrelated pre-existing debt.

**Verified live in both breakpoints, both apps:** desktop sidebar is a real 240px
sticky flex column (not just styled to look like one) with every destination
visible with zero interaction; mobile collapses to the top bar and the drawer opens
correctly. `tsc --noEmit` clean, eslint clean, full suites passing (Admin: 9 tests;
Studio: 144 tests across 3 consecutive runs), both production builds succeed.

**Exit test — met:** from either app, the other is one click away at the sidebar's
bottom, presented as a visually equal peer, not "Elsewhere ↗".

## Phase 2 — Nav + page audit, resolved with you

- Every destination named in §3/§4 above gets a keep/merge/retire mark, decided by
  you, before anything is touched.
- Feeds directly into Phase 4's regrouping.

## Phase 3 — Admin store-backend build-out

- Order management UI + data model (built ahead of checkout landing, so it's ready,
  not a scramble)
- Customer records
- Inventory/stock alerts (`colour_stock` exists today as CRUD only — no low-stock
  signal anywhere)
- Discounts/promo codes (none exist)
- **Exit test:** Admin can do everything a store backend needs to do except touch real
  payment data — that one piece stays blocked on checkout shipping.

## Phase 4 — Studio regrouping to "generation / socials / marketing"

- Re-group the 13 destinations under your stated frame instead of the current
  Product/World pipeline split, using Phase 2's keep/merge/retire output.
- **Exit test:** the nav groups match how you described Studio's job in one sentence,
  not the pipeline language currently sitting in the code comments.

---

# Decisions — locked in 20 August 2026

1. **Studio's Base Web problem → rip it out.** Replace Studio's component primitives
   (`studio/web/src/components/*.tsx`, ~25 files) with the same hand-built
   Tailwind-equivalent approach Admin already uses. `baseui`/styletron come out
   entirely — this is the only path that removes the library-behaviour gap a theme
   object can't close. Bigger lift than another token pass, but it's what actually
   fixes the 3-times-failed complaint instead of attempting the same fix a 4th time.

2. **Nav layout → sidebar, Admin/Studio links pinned at the bottom of it.** Both apps
   move from their current top-header nav to a sidebar layout. This is a bigger
   change for Admin than for Studio — Admin's `Nav.tsx` is currently a sticky top
   header with a horizontal link row; it becomes a sidebar with `Products`/`Content`
   (or whatever Phase 2's audit settles on) as the main items and `Admin | Studio` as
   two pinned links at the sidebar's bottom edge. Studio's hamburger-nav goes away
   entirely in favour of the same sidebar shell, sharing the pattern rather than
   inventing its own.

These decisions fold into Phase 0 (component rebuild) and Phase 1 (sidebar shell) —
both phases are now scoped concretely rather than conditionally.
