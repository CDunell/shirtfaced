# shirtfaced — AI Campaign Story Engine

**Status:** ACTIVE contract  
**Scope:** Campaign kickoff through approved story version  
**Depends on:** ADR-016, ADR-017, `POSTGRES_DATA_MODEL.md`

---

## 1. Purpose

The story engine turns a persisted campaign premise into a versioned narrative that can be decomposed into scenes and shots without inventing story facts during generation.

The unit of authorship is the **campaign story**, not the social post.

The ten-post social cycle is cut from, reframed from, or authored around one coherent campaign world. Posts may stand alone in-feed, but their source story must remain internally consistent.

---

## 2. Campaign kickoff input

Story development starts only after a campaign row exists.

Required kickoff input:

- campaign ID
- world ID
- premise
- objective
- campaign type
- cycle dates / sequence
- intended platforms
- target post mix
- presentation-language target mix
- approved garments/designs in scope
- immutable brand/canon constraints
- source creative brief

Optional inputs:

- required recurring character(s)
- required location(s)
- launch/drop event
- required phrase or graphic only when already approved
- directing-language preferences
- prior campaign callbacks

The story engine must distinguish **requirements** from **ideas**. Suggestions are not silently promoted into locked continuity.

---

## 3. Story version contract

Every story proposal creates a `story_version` belonging to one campaign.

Required fields / concepts:

- version number
- logline
- synopsis
- setup
- commitment
- escalation
- complication
- peak
- aftermath
- ending / callback
- central comic, emotional or tension mechanism
- character roles
- location plan
- garment integration plan
- directing-language plan
- candidate social roles
- structured beats
- source prompt/template version
- model/settings provenance where AI-assisted
- human edits
- review state

A story version is not mutable after approval. Changes create the next version.

Only one story version may be the campaign's active approved version at a time.

---

## 4. Mandatory narrative shape

A campaign story must contain at least these phases:

1. **Setup** — establish ordinary state, people and place.
2. **Commitment** — a choice or event starts the story moving.
3. **Escalation** — consequences accumulate.
4. **Complication** — the expected path is disrupted.
5. **Peak** — strongest comic, emotional, visual or dramatic beat.
6. **Aftermath** — consequences, callback, quiet release or unresolved residue.

The phases do not require conventional dialogue or a feature-film plot. A campaign can be observational, absurd, documentary or near-plotless, but it still needs a change in state over time.

---

## 5. Story quality gates before scene breakdown

A story is not ready for scene planning unless all applicable gates are answerable:

- **world fit** — could this happen in the shirtfaced world without a logo explaining it?
- **story change** — something changes from beginning to end.
- **character motive** — actions are understandable even when stupid.
- **garment naturalism** — products belong to people, not mannequins inserted into plot.
- **Australian grounding** — place/behaviour/details are credible where the campaign claims Australian context.
- **originality** — directing grammar may borrow technique; story facts, dialogue and composition are original.
- **social extractability** — the larger event contains multiple useful editorial moments without being ten disconnected sketches.
- **AI producibility** — continuity burden is achievable with the available generation workflow.
- **ending value** — the story has an ending/callback/aftermath worth publishing, not merely a stop.

A failed gate returns the story to development rather than being delegated to shot generation.

---

## 6. Character role planning

Story versions reference campaign characters by stable ID once characters exist.

Before character rows exist, a draft may carry proposed role handles, but approval requires resolution to persisted characters.

Role examples:

- instigator
- reluctant mate
- missing person / object of search
- witness
- driver
- worker / outsider
- observer
- chaos amplifier

Role is narrative function, not identity. Character identity lives in the character/appearance contract.

---

## 7. Garment integration

The story version declares garment use before scene planning.

For each garment/design in scope, identify:

- wearer / character
- story reason it is present
- whether it needs hero-readable coverage somewhere
- whether front, rear or other placement matters
- whether it changes layer state during the story
- whether it may be obscured in most shots

No rule requires every garment to be readable in every scene. Repeated catalogue posing is a story failure.

---

## 8. Directing-language plan

The story version may assign one or more directing grammars to story phases or candidate post roles.

The grammar is stored as structured production intent, for example:

- presentation class: polished / documentary / rough / weird
- camera behaviour
- pacing
- performance style
- lighting register
- sound register
- edit register
- reference tradition / director technique notes

Director/style references are shorthand for production technique, not instructions to reproduce an identifiable protected scene, character, dialogue or exact composition.

---

## 9. Beat structure

Structured story JSON should contain ordered beats with stable IDs.

Each beat should support:

- beat ID
- phase
- description
- participating character IDs / proposed handles
- location intent
- state entering beat
- action
- state leaving beat
- garment relevance
- key prop relevance
- dialogue/audio relevance
- candidate scene boundary
- candidate social role(s)

Beat IDs survive scene revisions where the underlying event remains the same, allowing traceability from story to scene to shot.

---

## 10. Approval and revision

Story review records:

- approver / origin
- approved/rejected/revision-requested
- structured failure/revision codes where practical
- evidence / notes
- timestamp

A rejected version remains stored.

A new version records its parent story-version ID and reason for revision.

Story approval is a production gate. Scene generation cannot promote an unapproved story version into production silently.

---

## 11. Required outputs for scene planning

An approved story version must provide enough information to derive:

- ordered scene candidates
- character participation
- appearance/wardrobe state
- location use
- time progression
- prop progression
- continuity changes
- hero garment moments
- likely still-photo opportunities
- likely motion/video sequences
- campaign post-role candidates

If scene planning has to invent a major story event not present in the approved story version, the story version is incomplete and must be revised.
