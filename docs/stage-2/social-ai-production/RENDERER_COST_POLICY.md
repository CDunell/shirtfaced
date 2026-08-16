# SHIRTFACED — Renderer Cost Policy

**Status:** ACTIVE guardrail

The renderer may spend heavily during a bounded experiment when the spend answers a specific production question. It must not carry experimental retry behaviour into routine production.

## Rules

1. Every billable generation belongs to a recorded attempt.
2. Every retry has a classified reason.
3. No video generation begins from an unapproved seed frame.
4. Development budgets may be raised deliberately; production budgets are ratcheted down from measured acceptance data.
5. Default production model selection is based on **cost per accepted output**, not cost per call.
6. Premium models require evidence of materially better acceptance on the relevant failure class.
7. Subscription decisions use replacement evidence from real Shirtfaced workloads, not feature-list equivalence.

## Required economics report

For every five-scene benchmark run record:

- image calls and accepted seeds
- video calls and accepted clips
- first-pass acceptance rate
- retry count by failure class
- provider/model used
- API cost per scene
- API cost per accepted final clip
- manual minutes per accepted clip
- projected monthly cost at 10, 25, 50 and 100 clips

The sustainable production profile is the lowest-cost configuration that continues to clear the owner acceptance gate at the required quality level.
