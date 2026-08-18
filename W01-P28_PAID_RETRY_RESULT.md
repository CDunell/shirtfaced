# W01-P28 paid coverage retry result

This file is machine-recorded by `.github/workflows/w01-p28-paid-retry.yml`.

```json
{
  "aspect_ratio": "16:9",
  "attempt_incremented_once": false,
  "attempts_after": 31,
  "attempts_before": 31,
  "http_status": 409,
  "prompt_sha256": "96494543adee8809844a032e8fba239516aa68757a2f8a7de0a829ad01912615",
  "response": {
    "detail": "Nano refused the coverage generation: BadRequestError: Error code: 400 - {'error': {'message': 'Request blocked due to prohibited content guidelines. Please modify your input and retry.', 'code': \"Unable to show the generated image. The image was filtered out because it violated Google's [Generative AI Prohibited Use policy](https://policies.google.com/terms/generative-ai/use-policy). Try rephrasing the prompt. If you think this was an error, [send feedback](https://ai.google.dev/gemini-api/docs/troubleshooting).\"}}"
  },
  "scene": "W01-P28",
  "selections": [
    "damo:contact_sheet",
    "emma:contact_sheet",
    "brock:contact_sheet"
  ],
  "trigger_commit": null
}
```
