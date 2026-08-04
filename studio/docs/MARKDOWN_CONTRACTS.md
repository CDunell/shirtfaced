# Markdown Contracts

Markdown remains readable by humans but must follow parseable contracts.

## WORLD.md

Required headings:

- `# SHIRTFACED`
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
