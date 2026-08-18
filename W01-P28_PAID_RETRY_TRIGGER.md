# W01-P28 guarded paid coverage retry

Trigger exactly one paid scene-coverage generation after deployment, using the approved W01-P28 master plus these approved identity references:

- `damo:contact_sheet`
- `emma:contact_sheet`
- `brock:contact_sheet`

The workflow must verify the deployed `338b0d5` prompt hardening and provider-error containment before making the single billable call.
