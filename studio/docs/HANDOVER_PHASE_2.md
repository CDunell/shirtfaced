# Handover — Phase 2, for whoever writes the world documents

## Who this is for

The GPT (or person) authoring and editing `WORLD.md`, `CONTINUITY.md` and
`SHOTLIST.md` for World 01.

Until now those documents were read by humans. As of Phase 2 the application parses
them, imports them into PostgreSQL, selects the next shot from them and builds the
production prompt from them. **What you write now changes what gets generated.**

This document states exactly what the code reads, what it ignores, and where a
careless edit will silently change behaviour.

Nothing here asks you to write differently for a machine. The documents stay
human-readable prose. There are simply a handful of load-bearing structures.

---

## 1. What the application now does with the documents

```
WORLD.md ─────────┐
CONTINUITY.md ────┼──> validate ──> import to PostgreSQL ──> select next shot
SHOTLIST.md ──────┘                                             │
                                                                v
                                    canon excerpts + rotation + shot ──> production prompt
```

Run after any edit:

```bash
python -m app.cli validate-world world-01   # checks the files, changes nothing
python -m app.cli import-world world-01     # loads them into the database
```

`validate-world` reports **every** problem at once with line numbers and exits
non-zero. Use it as your feedback loop; it costs nothing and calls no model.

---

## 2. `WORLD.md`

### Required headings

Validation fails without these. Matching ignores case; everything else about your
prose is free.

`# Purpose` · `# Emotional Tone` · `# Lighting` · `# Colour Palette` ·
`# Photography Language` · `# Locations` · `# People` · `# Wardrobe` ·
`# Composition` · `# Success Test`

The title heading must **begin with** `SHIRTFACED`. The current
`# SHIRTFACED --- WORLD 01` satisfies this.

Additional headings are allowed and preserved. The loader never rewrites the file.

### The part that matters most: only some sections reach the model

A section not on this list is **never sent to the planning model**. A rule written
anywhere else is a rule the generator does not have.

Currently sent, in this order:

| Section | Sent |
|---|---|
| Purpose | ✅ |
| Emotional Tone | ✅ |
| Lighting | ✅ |
| Colour Palette | ✅ |
| Photography Language | ✅ |
| Locations | ✅ |
| People | ✅ |
| Wardrobe | ✅ |
| Composition | ✅ |
| Environmental Branding | ✅ |
| Reference Standard — The Photo We'd Post Anyway | ✅ |
| Global Production Rule — No Visible Branding | ✅ |
| Product Rotation & Vehicle Canon | ✅ |
| Prompt Construction Protocol | ✅ |
| Success Test | ✅ |
| Operating System (roles, review tests, production loop) | ❌ |
| Continuity Ledger (describes the ledger itself) | ❌ |

The two omitted sections direct humans and the review step, not the photograph. The
Continuity Director's review tests will be wired into the review model in Phase 4;
they are deliberately not part of the planning prompt.

**If you add a new section containing an image rule, tell the developer.** It needs
adding to `PLANNING_CANON_HEADINGS` in `app/services/prompt_planner.py` or it will be
invisible. There is a test that fails if a listed heading disappears from the
document, but nothing can detect a rule you invented in an unlisted section.

Subsections are included. `# Product Rotation & Vehicle Canon` has no body of its own —
all its content is under `## Product Rotation` and `## Vehicle Canon` — and the whole
subtree is sent.

Each section is truncated at 2,000 characters. The total currently sent is about
8,300 characters. If a section grows past that limit it will be cut mid-document, so
keep individual sections tight and put detail in subsections of the same heading
rather than in one long block.

---

## 3. `CONTINUITY.md`

### Required headings

`# Status Key` · `# Hero Product Rotation` · `# Camera Position Rotation` ·
`# Approved Reference Frames` · `# Rejected Drift` · `# Current Canon Notes` ·
`# Next Prompt Brief`

### What is actually parsed

| Structure | Read as | Effect |
|---|---|---|
| `## Next Rotation Priority` bullet list | Preferred next hero products | Sent to the planner as guidance |
| `## Next Camera Priority` bullet list | Preferred next camera positions | Sent to the planner as guidance |
| `### ...` subsections under `# Rejected Drift` | Each heading + body | Sent to the planner as "drift to avoid" (first 3, 600 characters each) |
| `# Current Canon Notes` bullet list | Standing notes | Sent to the planner in full |

Bullets may use `-`, `*`, `+` or `1.`, and `**bold**` markers are stripped.

### What is validated but not yet consumed

Be aware of this so you do not expect an effect that does not exist yet:

- **`# Hero Product Rotation` and `# Camera Position Rotation` tables.** What has
  actually been used is derived from approved shots in the database, not from these
  tables. They remain the human-readable audit record. Editing them changes nothing
  about selection.
- **`# Approved Reference Frames`.** Not yet sent. Reference images arrive in a later
  phase.
- **`# Status Key`.** Required to exist; not parsed.
- **`# Next Prompt Brief`.** Required to exist; **not currently used**. The planner
  builds its own brief from the selected shot plus rotation state. Treat this section
  as a human note to yourself, not an instruction to the system. If you want it to
  drive generation, that is a change to request, not something to assume.

---

## 4. `SHOTLIST.md`

This is the file with the most machine-visible structure. It is the production
backlog and it drives selection directly.

### Table format

Two styles are accepted:

- Pandoc simple tables (what World 01 currently uses — space-aligned columns under a
  row of dashes);
- pipe tables (`| ID | Scene | ... |`).

Rows in a simple table are read by splitting on runs of **two or more spaces**, with
the dashed rule's column positions as a fallback. This means **you do not have to
preserve the original column alignment** when you edit a cell. Renaming a scene to
something shorter or longer is safe. Keep at least two spaces between cells.

### Required columns

`ID` · `Scene` · `Hero Product` · `Camera` · `Status`

Optional and understood: `Priority`. Optional and currently ignored: `Time`,
`Location`, `Notes`.

### Status markers

| Marker | Meaning |
|---|---|
| `⬜` | planned |
| `🟡` | in progress |
| `✅` | approved |
| `❌` | rejected |

The words `planned`, `in progress`, `approved`, `rejected` and `abandoned` are also
accepted, so the file stays usable in a plain terminal.

### What will fail validation

- a duplicate `ID` (reported with both line numbers);
- a row with no `ID` or no `Scene`;
- an unrecognised status marker;
- a non-numeric `Priority`.

### How selection uses these columns

The next shot is the first eligible planned shot ordered by:

1. `Priority` ascending — omitted means 100, so an explicit lower number jumps the queue;
2. row order in the file;
3. creation time.

A shot is skipped when it is disabled, blocked, already generating, or not planned.

Then rotation applies: a shot that repeats the **hero product** of the most recently
approved shot is set aside, and then likewise for **camera** — unless doing so would
leave nothing, in which case the rule stands down and says so.

Product rotation is applied before camera rotation. Where the two disagree, product wins.

---

## 5. Three things that will catch you out

### Rotation compares hero product and camera as exact strings

`Cap` and `Black cap` are different products as far as rotation is concerned. So are
`Rear seat` and `From the rear seat`. Inconsistent vocabulary in the `Hero Product`
and `Camera` columns quietly breaks rotation — the system will think a product has not
been used recently when it has.

**Keep to a fixed vocabulary in those two columns.** Currently in use:

- Hero Product: `T-shirt`, `Hoodie`, `Cap`, `Tote bag`, `Mixed`, `Hoodie waist`, `Back surface`
- Camera: `Across street`, `Across forecourt`, `Across road`, `Across car park`,
  `Opposite footpath`, `Nearby table`, `Dining room`, `Front gate`, `Beside parked car`,
  `Rear seat`, `Inside lift`, `Inside lounge`, `Inside servo`, `Hallway`,
  `Balcony doorway`, `Behind queue`, `Dune path`, `Carpark`, `Window seat`

Descriptive elaboration belongs in the prompt, not in these cells. The planner is
allowed to expand `Tote bag` into `Plain black tote bag`; it is rejected if it
substitutes a different product entirely.

### The database wins on decided shots

Once a shot is `approved`, `rejected` or `abandoned` in the database, re-importing
will **not** change it back, even if you edit the marker in `SHOTLIST.md`. The
database records what actually happened; the import reports the disagreement rather
than silently resolving it.

Planned and in-progress shots do follow the file.

To genuinely reverse a decision, ask for it to be done through the application, not
by editing the Markdown.

### Editing a file changes its hash

Each document's SHA-256 is stored and shown on the world page. That is deliberate:
it identifies exactly which version of the canon a piece of state was built from. Edit
a file and re-import, and the hash changes. Nothing breaks; it is a record.

---

## 6. A canon conflict, now resolved

`# Environmental Branding` and `# Global Production Rule — No Visible Branding` used to
contradict each other, and both are sent to the planning model.

- **Environmental Branding** permits a neon Shirtfaced slogan in a pub, a faded esky
  sticker, a coaster, a window decal — "easter eggs, not advertisements".
- **Global Production Rule** said "No readable branding or commercial logos may appear
  anywhere in the image" and "If any visible branding appears, the image has failed the
  brief."

Read literally, the second forbade the first.

**The owner's decision: the ban is on third-party branding only.** Shirtfaced is the
exception. `WORLD.md` now says so under
`## Shirtfaced Is The Exception`, and the two absolute sentences above are qualified
with "third-party".

Two limits were kept deliberately, because relaxing them would contradict the rejected
drift lesson from the house party:

- Shirtfaced easter eggs are **environmental scenery only** — signage, stickers,
  coasters, decals, posters, street art, hand stamps. They are never the subject.
- **Garments stay blank.** Every t-shirt, hoodie, cap, overshirt, jacket and tote bag
  in frame is still completely blank, and all consumables and packaging still generic.

If either limit is wrong, say so and the section gets amended — this is canon, so it
changes only on your word.

---

## 7. What Phase 2 gives you to check your work

```bash
# Which shot is next, and why — no model call, costs nothing
curl -s localhost:8000/api/worlds/world-01/next-shot

# The full production prompt, without generating an image (DEBUG=true only)
curl -s -X POST localhost:8000/api/worlds/world-01/plan-preview
```

Both are on the world page in the interface: the selected shot, the reasoning, an
expandable list of every shot that was set aside with the reason, and a
**Preview production prompt** button.

Without `OPENAI_API_KEY` and `OPENAI_TEXT_MODEL` set, a deterministic local planner
builds the prompt instead of the real model. It costs nothing, and the interface says
so plainly. That makes it safe to iterate on the documents and watch selection change
without spending anything.

Current state, for reference:

```
selected: W01-011 — Car interior transition
eligible: 10 planned shots
reason:   Lowest priority (100), then sequence (11). Hero product 'Tote bag'
          differs from the previous 'Cap'. Camera 'Rear seat' differs from the
          previous 'Beside parked car'.
set aside: W01-016, W01-020 — repeat the previous hero product 'Cap'
```

---

## 8. Editing checklist

1. Make the edit.
2. `python -m app.cli validate-world world-01` — fix everything it reports.
3. `python -m app.cli import-world world-01`.
4. Check `next-shot` still selects what you expect, and read the reason.
5. If the shot changed unexpectedly, look first at the `Hero Product` and `Camera`
   vocabulary — inconsistent wording there is the usual cause.

---

## 9. What is coming, so you can write ahead of it

- **Phase 3** — image generation. Attempt history replaces the current use of a shot's
  `in progress` status, and rejected attempts become available to the planner.
- **Phase 4** — automated review. This is where `# Operating System` → Continuity
  Director's review tests become load-bearing. The Mood / Australian Authenticity /
  Product Visibility / Vehicle Continuity / Wardrobe Balance / Composition /
  Documentary Credibility / Story headings will map to the review model's structured
  output, so keep those subsection headings stable.
- **Phase 5** — human decisions, where approval starts appending to `CONTINUITY.md`
  automatically. From that point the application writes to the continuity document as
  well as reading it, and the safe-update rule applies: the model proposes an entry,
  application code constructs and validates the final Markdown.
- **Phase 6** — canon proposals, the only route by which `WORLD.md` changes without a
  human editing it directly, and only after explicit approval.
