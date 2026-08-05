# Runway image-to-video worker

This worker turns one local still image into one downloaded MP4 through the Runway developer API.

## One-time setup

1. Create a Runway developer account.
2. Add API credits.
3. Create an API key.
4. Put the key in your local environment:

```bash
export RUNWAYML_API_SECRET="key_your_real_key"
```

Do not commit the real key.

## Generate a clip

```bash
npm run video:generate -- \
  --image ./assets/source.png \
  --prompt "Natural subtle body movement. Slow handheld camera drift. Preserve faces, clothing, lighting and composition." \
  --output ./output/source-video.mp4 \
  --model gen4.5 \
  --ratio 720:1280 \
  --duration 5
```

The command:

1. reads the local image
2. converts it to an accepted data URI
3. creates a Runway image-to-video task
4. polls until completion
5. downloads the temporary output URL immediately
6. saves the MP4 locally

## Supported input

- PNG
- JPEG
- WebP
- maximum 5MB for this implementation

## Useful options

- `--model gen4.5`
- `--ratio 720:1280`
- `--duration 2` through `10`
- `--seed 0` through `4294967295`
- `--output ./chosen/path.mp4`

## Current boundary

This command generates one candidate clip per invocation. Human review remains outside the worker, by design.
