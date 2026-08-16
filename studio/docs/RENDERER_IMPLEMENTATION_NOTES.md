# Renderer implementation notes

- The Google adapters are installed but no billable endpoint is exposed in Phase 1.
- `GOOGLE_MEDIA_ENABLED` defaults false.
- `GEMINI_API_KEY` has no default and must never be logged.
- The five-scene benchmark is the gate to live rendering.
- Production economics are evaluated as cost per accepted output, not cost per API call.
