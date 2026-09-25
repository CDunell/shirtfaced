"""Insert a locally-generated image as a pending design sample.

Usage::

    python scripts/ingest_local_image.py <image_path> <tradition> <batch> \
        <concept_text_file> <prompt_file>

The concept text and prompt are read from files rather than argv, so
punctuation, quotes and apostrophes in generated prose don't have to
survive shell escaping.

Mirrors ``POST /api/design/generations`` exactly -- same thumbnail size,
same asset store, same default status of "pending" -- so a row from a
batch run and one from the HTTP endpoint are indistinguishable. See that
route (``app/routes/design_advisor.py``) if the two ever need to diverge;
until then this stays a plain re-read of it rather than importing it,
because the route also owns the upload size limit and HTTP error shape,
neither of which apply here.
"""

from __future__ import annotations

import io
import sys
import uuid
from pathlib import Path

from PIL import Image

from app.adapters.asset_store import FilesystemAssetStore
from app.config import get_settings
from app.db.generation_sample_models import DesignGenerationSample
from app.db.session import get_session_factory

THUMB_WIDTH = 480


def main() -> None:
    if len(sys.argv) != 6:
        print(__doc__)
        raise SystemExit(1)

    image_path, tradition, batch, concept_file, prompt_file = sys.argv[1:]
    concept_text = Path(concept_file).read_text(encoding="utf-8").strip()
    prompt = Path(prompt_file).read_text(encoding="utf-8").strip()

    settings = get_settings()
    store = FilesystemAssetStore(settings.assets_root_resolved)
    session = get_session_factory()()

    data = Path(image_path).read_bytes()
    full_image = Image.open(io.BytesIO(data)).convert("RGB")
    full_buf = io.BytesIO()
    full_image.save(full_buf, format="PNG")

    w, h = full_image.size
    thumb = full_image.resize((THUMB_WIDTH, round(h * (THUMB_WIDTH / w))), Image.Resampling.LANCZOS)
    thumb_buf = io.BytesIO()
    thumb.save(thumb_buf, format="JPEG", quality=78, optimize=True)

    sample_id = uuid.uuid4()
    full_key = f"design_generations/{batch}/{sample_id}_full.png"
    thumb_key = f"design_generations/{batch}/{sample_id}_thumb.jpg"
    store.save(full_key, full_buf.getvalue(), "image/png")
    store.save(thumb_key, thumb_buf.getvalue(), "image/jpeg")

    row = DesignGenerationSample(
        id=sample_id,
        tradition=tradition,
        concept_text=concept_text,
        prompt=prompt,
        image_relative_path=full_key,
        thumb_relative_path=thumb_key,
        status="pending",
        batch=batch,
        model="chatgpt-session",
    )
    session.add(row)
    session.commit()
    print(f"inserted {sample_id}")


if __name__ == "__main__":
    main()
