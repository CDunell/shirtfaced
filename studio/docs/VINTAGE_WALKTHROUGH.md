# Vintage: the whole path, end to end

Written 2026-08-14 because the pieces work and the joins are invisible. This
traces one design from a collector to an approved version, naming the file and
the route at every step, and saying plainly where the chain stops.

Read the last section first if you only read one. **The chain does not run by
itself, and the place it stops is not where it looks like it stops.**

---

## 1. Where the evidence physically is

Two collectors write into one root on the Oracle box.

| Tree | Holds | Written by |
|---|---|---|
| `vintage-ebay-images/` | ~607 sold eBay listings | the four agent workers |
| `vintage-archive-images/` | 3,032 pieces from 22 non-eBay sources | `adapt_archive_to_evidence.py` |
| `vintage-evidence-merged/` | symlinks to both, plus `manifest.json` | assembled by hand |

All under `/home/ubuntu/shirtfaced-research/`. The service reads whichever one
`VINTAGE_EVIDENCE_ROOT` names, set in `/home/ubuntu/shirtfaced-studio/.env`.
It currently names the merged root. Changing that one line changes what the
whole system can see, and nothing else needs restarting but the service.

One record per listing: a numeric directory holding `record.json` and its
images. The directory name **must be all digits** — `evidence_records()` skips
anything else, which is why archive pieces get synthetic 15-digit ids based at
9e14, above eBay's twelve-digit ones so the two can never collide.

## 2. Collectors

None need credentials except the first.

| Script | Source | Needs |
|---|---|---|
| `worker_scripts/vintage-agent.mjs` | eBay sold listings | eBay app keyset |
| `scripts/collect_design_corpus.py` | Shopify storefronts, 11 vintage resellers | nothing |
| `scripts/collect_wp_archives.py` | WordPress design archives | nothing |
| `scripts/collect_wayback_corpus.py` | dead brands' own archived sites | nothing |
| `scripts/collect_archive_corpus.py` | eBay Browse | eBay app keyset |
| `scripts/adapt_archive_to_evidence.py` | converts the above into the service's record shape | nothing |
| `scripts/index_archive.py` | reads titles, indexes by decade | nothing |

`corpus_tiers.py` is a read-time filter, not a delete: 34 brands are excluded
for structural reasons (marketplaces, retailers who sell other labels' goods,
licensed reproduction). Every miner should apply it.

## 3. Evidence → the screen

```
GET /api/vintage-evidence      vintage_evidence.py    records + manifest counts
GET /vintage-evidence/image/{listing_id}/{filename}   the bytes
```

`VintageEvidenceBench` reads both. Filtering happens in the browser so each
option can state its own count before you pick it.

Counts come from the walk, not from `manifest.json` — that file is written by
whichever collector ran last and went stale the moment a second source appeared
under one root.

## 4. Research: two passes

```
POST /api/vintage-research/runs      vintage_api.py → execute_research()
```

Pass one sends the selected **image bytes** plus `PASS_1_PROMPT` and gets ten
concepts. Pass two deepens the same ten. Both are persisted with provenance to
`research-runs/<uuid>.json`.

Slow by nature: real images to a vision model, twice.

Selection is breadth-first — the first image of every listing before the second
of any — capped at 16 by default, 24 maximum.

## 5. Review

```
POST /api/vintage-research/runs/{run_id}/concepts/{n}    status / prompt / note
```

Approve, reject, or edit the prompt. This only writes to the run's JSON file.
Nothing else happens, and nothing else is meant to.

## 6. Send to the design pipeline

```
POST /api/vintage-design/runs/{run_id}/concepts/{n}/pipeline
```

**Use this endpoint.** It refuses an unapproved concept, resolves the design
concept, refuses an empty prompt, then calls `create_attempt(...)`.

Do **not** route this through `vintage_research`'s `mark_pipeline`, which only
stamps `concept["pipeline"]` on the JSON. A wrapper doing exactly that shipped
on 2026-08-13 and made the button appear to work while creating nothing.

## 7. Where the chain stops

`create_attempt` opens a `DesignAttempt` in state **`PLANNED`**. Its own
docstring is the honest summary:

> *"Open one execution of a concept. The row exists before any work does."*

**No image is generated.** Nothing polls the attempt. Nothing queues it. The
method is named `IMAGE_GENERATION`, which reads like a promise the code does
not make — it records how the artwork is *intended* to be produced, not that
anything will produce it.

To move an attempt forward, artwork has to be **uploaded**:

```
POST /api/concepts/attempts/{attempt_id}/assets      multipart file upload
POST /api/concepts/attempts/{attempt_id}/submit
POST /api/concepts/attempts/{attempt_id}/decision
POST /api/concepts/attempts/{attempt_id}/approve-design
```

So the real loop today is:

```
research prompt  →  you generate the image elsewhere (Kittl, ChatGPT)
                 →  you upload it to the attempt
                 →  submit, decide, approve
                 →  Print places it on a garment
```

That manual hop is the whole answer to "none of this is connected". Everything
either side of it is wired; the middle is a person with a browser and two tabs.

## 8. The other break: references never reach the generator

`vintage_design.py` records the evidence on the attempt:

```python
reference_inputs={
    "evidence_listing_ids": [...],
    "evidence_images": [...],
}
```

That is **provenance only**. The evidence images are read once, by the research
model, to write words. The words then go to an image generator alone.

This is why output comes back as competent generic skate art rather than
1991: a text-only model renders its own average idea of "airbrush gradient
modelling in two colours".

The machinery to fix it already exists and is in production for photography:

```
image_generation.py:53        reference_images: tuple[ReferenceImage, ...]
generation_orchestrator.py:229  reference_images=tuple(references)
api.py:546                    reference_store=FilesystemReferenceImageStore(...)
```

The vintage path is the one that does not use it. Wiring a `ReferenceImageStore`
at the evidence root into the generation call is a wiring job against a proven
adapter, not a new capability.

## 9. What is genuinely missing, shortest list

1. **Nothing executes an attempt** — and it should stay that way. The owner
   holds paid subscriptions to OpenAI, Gemini and Anthropic; an API key bills
   separately from all three, so wiring generation would charge twice for
   something already owned. The manual hop is the cheap path, not a defect.
   What it needs is to be *deliberate*: copy the prompt, generate in the
   subscription UI, upload the result. Rename the state so it stops reading as
   automatic, and consider local generation for volume.
2. **Reference images do not reach generation** (§8).
3. **The prompts sent are generic.** `PASS_1_PROMPT` asks for "the retro skate,
   surf and streetwear niche" at large. `docs/ARCHIVE_PROMPT_LIBRARY.md` holds
   per-era cells with three filled axes each; nothing feeds them to the service.

Fix those three and the loop closes without any new subsystem.
