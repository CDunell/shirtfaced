"""The attempt record: every provider call, whether or not it returned anything.

§6 of ``NANO_BANANA_CONTACT_SHEET_PIPELINE.md`` asks for prompt, model, exact
inputs, output and lineage on each call. That is one shape, and it does not vary
by provider — a Veo take that came back empty is the same kind of fact as a Nano
sheet that did, and both are worth keeping. Nano's pipeline and the motion
service therefore write through here rather than each growing their own version.

Failures are recorded on purpose. A refusal is a fact about the prompt, and
dropping it means learning the same thing twice at the same price.
"""

from __future__ import annotations

import hashlib
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.visual_models import GenerationCall

PROVIDER = "google"


def record_call(
    session: Session,
    *,
    operation: str,
    model: str,
    scene_key: str | None,
    subject: str | None,
    prompt: str,
    inputs: list[uuid.UUID],
    output_asset_id: uuid.UUID | None,
    succeeded: bool,
    failure: str | None,
    duration_ms: int,
    actor: str,
    provider: str = PROVIDER,
) -> GenerationCall:
    """Write one call to the ledger. The prompt is stored as its hash.

    ``output_asset_id`` is a visual asset, so a video take passes ``None`` and
    names its clip in the take row instead: the ledger records that the call
    happened, and the take records what came back.
    """
    call = GenerationCall(
        provider=provider,
        model=model,
        operation=operation,
        scene_key=scene_key,
        subject=subject,
        prompt_sha256=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        input_asset_ids=[str(one) for one in inputs],
        output_asset_id=output_asset_id,
        succeeded=succeeded,
        failure=failure,
        duration_ms=duration_ms,
        actor=actor,
    )
    session.add(call)
    return call


def calls_for_scene(session: Session, scene_key: str) -> int:
    """How many provider calls this scene has behind it, successful or failed."""
    return int(
        session.execute(
            select(func.count())
            .select_from(GenerationCall)
            .where(GenerationCall.scene_key == scene_key)
        ).scalar()
        or 0
    )
