# OpenAI Integration

## Official interfaces

Use the official OpenAI Python SDK.

Use the Responses API for:

- prompt planning;
- structured continuity review;
- image-capable review.

Use an OpenAI image generation interface supported by the current SDK for image creation.

Do not hard-code a model name in domain logic.

## Environment

```env
OPENAI_API_KEY=
OPENAI_TEXT_MODEL=
OPENAI_REVIEW_MODEL=
OPENAI_IMAGE_MODEL=
OPENAI_IMAGE_SIZE=1536x1024
OPENAI_IMAGE_QUALITY=high
OPENAI_TIMEOUT_SECONDS=180
```

Provide sensible documented defaults in configuration, but require explicit model configuration when ambiguity could cause unexpected cost.

## Planning request

Send only the relevant canon, not every historic record.

Include:

- stable world rules;
- selected shot;
- last three approved continuity entries;
- last three relevant rejected drifts;
- current rotation state;
- required output schema.

Use structured output.

## Image generation

Persist:

- final prompt;
- model;
- requested size;
- quality;
- output format;
- request ID where returned;
- exact image bytes;
- image hash.

Do not store only a temporary provider URL.

## Image review

Review the locally stored image.

Include the intended prompt and the smallest relevant canon subset.

The review model must assess the actual image, not merely the prompt.

Use structured output and validate all fields.

## Retries

Use bounded retries for transient failures only.

Recommended:

- maximum three attempts;
- exponential backoff with jitter;
- no automatic retry for authentication, permission or validation failures;
- no automatic regeneration when only review failed.

## Timeouts

Use explicit connect and read timeouts.

Image calls may take longer than text calls.

## Cost control

- Generate one image per user action by default.
- Never create automatic variations.
- Show the model and quality before generation.
- Capture usage where provided.
- Estimate cost separately when exact cost is unavailable.
- Support a configurable daily or monthly soft budget warning.
- Do not claim an estimate is the final invoice.

## Data handling

- Store API keys only in environment variables or an OS secret manager.
- Do not log Authorization headers.
- Avoid logging full image base64 payloads.
- Log provider request IDs for support.
- Keep model input payload logging disabled by default.
- Allow an explicit debug mode with clear warnings.

## Current official references

- OpenAI API developer quickstart:
  https://platform.openai.com/docs/quickstart/make-your-first-api-request
- OpenAI image generation guide:
  https://platform.openai.com/docs/guides/image-generation
- OpenAI structured outputs guide:
  https://platform.openai.com/docs/guides/structured-outputs
- OpenAI Responses API reference:
  https://platform.openai.com/docs/api-reference/responses
