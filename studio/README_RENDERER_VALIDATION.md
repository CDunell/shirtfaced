# Renderer Validation Operator Note

The deployed validation endpoints are read-only and non-billable:

- `GET /api/renderer/validation`
- `GET /api/renderer/validation/{scene_id}`

Google media generation remains disabled until `GOOGLE_MEDIA_ENABLED=true` and `GEMINI_API_KEY` are both present.

The intended operating sequence is:

1. inspect/lock scene canon and references
2. generate candidate seed stills
3. manually approve one seed
4. generate Veo motion from that approved seed
5. manually approve final performance
6. classify failures before any retry
7. record measured cost per accepted output

Use `docs/stage-2/social-ai-production/GOOGLE_RENDERER_VALIDATION_PLAN.md` for the full phased plan and `RENDERER_COST_POLICY.md` for the economic acceptance rules.
