# Renderer Validation Rollout Phases

## Phase 1 — deployed planning harness

Read-only benchmark endpoints, cost guardrails, Google adapters installed, Google billing disabled by default.

## Phase 2 — live seed experiment

Add Gemini key, enable Google media deliberately, run Nano seed generation for the five benchmark scenes, persist attempts and measured cost, stop for owner seed approval.

## Phase 3 — live Veo experiment

Generate first-frame I2V only from approved seeds, persist video attempts and cost, stop for owner performance approval.

## Phase 4 — measured retry policy

Enable classified retries only. Remove blind retries. Measure first-pass acceptance and cost per accepted output.

## Phase 5 — production policy

Select default image/video models by acceptance-adjusted cost. Ratchet candidate counts and budgets down from development settings.

## Phase 6 — subscription decisions

Use benchmark evidence to cancel/downgrade redundant subscriptions rather than relying on feature-list overlap.
