"""Generate and persist real test renders for a batch of pool concepts.

Usage::

    python scripts/eval_concept_batch.py <concepts.json> <batch-label>

``concepts.json`` is a list of ``{"tradition": ..., "concept_text": ...,
"structural_shape": ...}`` objects -- the same shape written by hand each
session so far and, until now, only ever imported into ``design_concept_pool``
after being tested against scratch files nobody but that session could see.

This is the fix: every concept is rendered through the same ``advise()`` +
``render_generation_prompt()`` path production uses, saved as a real image
via the existing asset store, and written straight into
``design_generation_samples`` -- so the render and its exact prompt outlive
the session, and the next person (or the next Claude) can browse what a batch
actually produced instead of trusting a batch's own writer that it was good.

Every row starts ``status="kept"``. Review the renders (the Gallery page, or
the saved files under ``var/assets/design_generations/<batch>/``) and flip any
real failures with ``mark_generation_dropped.py`` -- this script never decides
that for you.
"""

from __future__ import annotations

import io
import json
import sys
import uuid
from pathlib import Path

from PIL import Image

from app.adapters.asset_store import FilesystemAssetStore
from app.adapters.google_media import GoogleImageClient, GoogleImageRequest
from app.config import get_settings
from app.db.generation_sample_models import DesignGenerationSample
from app.db.session import get_session_factory
from app.services.design_advisor import advise, measurement_rows, render_generation_prompt

THUMB_WIDTH = 480


def main() -> None:
    if len(sys.argv) != 3:
        print(__doc__)
        raise SystemExit(1)

    concepts_path = Path(sys.argv[1])
    batch_label = sys.argv[2]
    concepts = json.loads(concepts_path.read_text())

    settings = get_settings()
    client = GoogleImageClient(
        api_key=settings.gemini_api_key.get_secret_value(),
        model=settings.google_image_model,
    )
    store = FilesystemAssetStore(settings.assets_root_resolved)

    session = get_session_factory()()
    rows = measurement_rows(session)

    ok = 0
    for i, concept in enumerate(concepts):
        tradition = concept["tradition"]
        concept_text = concept["concept_text"]
        direction = advise(phrase="", has_graphic=True, tradition=tradition, rows=rows)
        prompt = render_generation_prompt(direction, concept_text)

        try:
            result = client.generate(
                GoogleImageRequest(prompt=prompt, aspect_ratio="1:1", image_size="1K")
            )
        except Exception as error:  # noqa: BLE001 -- report and continue the batch
            print(f"[{i:02d}] {tradition}: FAILED -> {error}")
            continue

        sample_id = uuid.uuid4()
        full_key = f"design_generations/{batch_label}/{sample_id}_full.png"
        store.save(full_key, result.data, "image/png")

        thumb_img = Image.open(io.BytesIO(result.data)).convert("RGB")
        w, h = thumb_img.size
        thumb_img = thumb_img.resize(
            (THUMB_WIDTH, int(h * (THUMB_WIDTH / w))), Image.LANCZOS
        )
        thumb_buf = io.BytesIO()
        thumb_img.save(thumb_buf, format="JPEG", quality=78, optimize=True)
        thumb_key = f"design_generations/{batch_label}/{sample_id}_thumb.jpg"
        store.save(thumb_key, thumb_buf.getvalue(), "image/jpeg")

        session.add(
            DesignGenerationSample(
                id=sample_id,
                tradition=tradition,
                concept_text=concept_text,
                prompt=prompt,
                image_relative_path=full_key,
                thumb_relative_path=thumb_key,
                status="kept",
                batch=batch_label,
                model=settings.google_image_model,
            )
        )
        session.commit()
        ok += 1
        print(f"[{i:02d}] {tradition}: OK -> {sample_id}")

    print(f"\nDone. {ok}/{len(concepts)} rendered and saved to design_generation_samples.")


if __name__ == "__main__":
    main()
