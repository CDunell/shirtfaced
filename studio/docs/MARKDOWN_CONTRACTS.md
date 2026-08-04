# Markdown Contracts

Markdown remains readable by humans but must follow parseable contracts.

## WORLD.md

Required headings:

- `# SHIRTFACED` — matched as a prefix, so `# SHIRTFACED --- WORLD 01` satisfies it.
  Every other heading below must match in full, ignoring case.
- `# Purpose`
- `# Emotional Tone`
- `# Lighting`
- `# Colour Palette`
- `# Photography Language`
- `# Locations`
- `# People`
- `# Wardrobe`
- `# Composition`
- `# Success Test`

Additional headings are allowed.

The loader must preserve unknown sections and ordering.

## CONTINUITY.md

Required headings:

- `# Status Key`
- `# Hero Product Rotation`
- `# Camera Position Rotation`
- `# Approved Reference Frames`
- `# Rejected Drift`
- `# Current Canon Notes`
- `# Next Prompt Brief`

Continuity updates should append or update bounded sections rather than regenerate the full document.

## SHOTLIST.md

### Table format

Two styles are accepted, because the file is hand-edited and different tools produce
different output:

- pipe tables, as used in `CONTINUITY.md`;
- Pandoc simple tables, where a row of dashes marks the column widths, as the current
  World 1 shotlist uses.

Simple-table rows are read by splitting on runs of two or more spaces, falling back to
the column positions marked by the dashed rule. Editing a cell therefore does not
have to preserve the original column alignment.

Required table columns:

- `ID`
- `Scene`
- `Hero Product`
- `Camera`
- `Status`

Recommended additional columns:

- `Priority`
- `Time`
- `Location`
- `Notes`

Allowed status markers:

- `⬜` planned
- `🟡` in progress
- `✅` approved
- `❌` rejected

The parser must also accept canonical text values so the file remains usable in plain terminals.

## Safe update rule

Never ask a model to return the entire replacement file.

The model may propose:

- a continuity entry;
- a shot status change;
- a canon rule proposal.

Application code constructs and validates the final Markdown.

## Drift detection

Store hashes of all three documents.

Before applying an update:

1. compare current hash to the hash loaded for the operation;
2. refuse on mismatch;
3. require reload and reconciliation.

This prevents overwriting a manual edit made while a generation was in progress.
