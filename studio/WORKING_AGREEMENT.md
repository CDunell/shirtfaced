# Working agreement

*Supersedes the original `START_CODEX.md`, which told whoever opened this repository to
have a single agent implement the whole application. That is no longer how the work is
split.*

Agreed 5 August 2026.

## The repository is authoritative

`main` is the source of truth for what exists, what is decided and what is next.

Anything produced elsewhere — a chat, a document pack, an exported archive — is a
**proposal**, not a fact about the system. Proposals go stale within hours. The
Stage 2 pack that arrived on 5 August was already wrong about the branding conflict by
the time it was opened, because the conflict had been resolved in `WORLD.md` an hour
earlier.

So: start creative work from the current repository documents, not from an earlier
export. Do not pass archives back and forth.

## Division of labour

Neither environment is uniquely capable of writing the world documents. The split is
about **role**, not ability.

### Creative direction — wherever the visual thinking happens

- developing what the world should become;
- campaign architecture and image concepts;
- generating and critiquing visual experiments;
- proposing new rules and new shots.

The distinct advantage there is direct image generation and a separate
creative-director perspective. Its output is a proposal.

### This repository — implementation and authority

- editing `WORLD.md`, `CONTINUITY.md` and `SHOTLIST.md` as the authoritative copies;
- placing a rule under a heading the planner actually reads;
- validating, importing, previewing the prompt and running the tests;
- migrations, architecture, planner integration, committing.

Final editing of the canon documents belongs here, because only here can a change be
validated and imported immediately, and only here is it known which headings are
planner-visible.

## The loop

1. Develop the creative direction wherever visual thinking helps.
2. Bring the **decision** here — as text, not an archive.
3. Edit the authoritative document, under a planner-visible heading.
4. `validate-world`, `import-world`, preview the prompt, run the tests, commit.
5. Take generated results back out for critique when that is useful.

Step 3 is the one that silently fails. A rule under a heading that is not in
`PLANNING_CANON_HEADINGS` never reaches the model. That is not hypothetical: the
vehicle canon — the rule whose breach caused a recorded rejection — was invisible to
the planner until 5 August 2026.

## Canon changes need a human decision

Models propose. The owner decides. That applies to a rule suggested in a chat exactly
as it applies to one proposed by the review model.

Where two rules conflict, the conflict is resolved in the document by the owner, not
papered over in code. The branding question was settled that way: the ban is
third-party only, garments stay blank.

## Stage 2 material

The five creative documents in `docs/stage-2/` are a future library. They are inactive
by design. A rule in them becomes real only when it is deliberately promoted into
`WORLD.md` and tested — see `docs/stage-2/README.md`.

## Reading order

Unchanged, and listed in `README.md`. `AGENTS.md` first, then the documents under
`docs/`. `docs/HANDOVER_PHASE_2.md` describes current behaviour for anyone writing the
world documents.
