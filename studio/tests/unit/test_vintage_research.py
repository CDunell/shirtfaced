from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services import vintage_research as vr


REQUIRED = (
    "pure black artwork on a pure white background, no grey, no gradient, "
    "maximum contrast, flat graphic design, print on demand ready"
)


def _concepts(extra: int = 0) -> dict[str, object]:
    return {
        "concepts": [
            {
                "concept_number": number,
                "title": f"Concept {number}",
                "idea": f"Original idea {number}",
                "prompt": ("Detailed original prompt " * (8 + extra)) + REQUIRED,
            }
            for number in range(1, 11)
        ]
    }


def test_select_images_uses_actual_cached_bytes_and_persists_hash(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    evidence = tmp_path / "123456"
    evidence.mkdir()
    payload = b"\x89PNG\r\n\x1a\nactual-evidence-bytes"
    (evidence / "front.png").write_bytes(payload)
    (evidence / "record.json").write_text(
        json.dumps(
            {
                "listing_id": "123456",
                "brand": "Example",
                "title": "Vintage skate tee",
                "era_claim": "1990s",
                "tradition": "skate",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(vr, "DEFAULT_ROOT", tmp_path)

    listings, images = vr.select_images(
        filters={"tradition": "skate"},
        listing_ids=["123456"],
        image_urls=None,
        image_limit=16,
    )

    assert [item["listing_id"] for item in listings] == ["123456"]
    assert len(images) == 1
    assert images[0]["path"].read_bytes() == payload
    assert images[0]["image_url"] == "/vintage-evidence/image/123456/front.png"
    assert images[0]["sha256"]

    content = vr._image_content(images)
    assert content[0]["type"] == "input_image"
    assert content[0]["image_url"].startswith("data:image/png;base64,")


def test_pass_prompts_are_the_authoritative_two_pass_process() -> None:
    assert "generate 10 design ideas and prompts" in vr.PASS_1_PROMPT
    assert REQUIRED in vr.PASS_1_PROMPT
    assert "Make these 10 t-shirt design prompts more detailed" in vr.PASS_2_PROMPT
    assert "same 10 concepts" in vr.PASS_2_PROMPT


def test_pass2_must_keep_same_ten_concepts_and_expand_prompts() -> None:
    first = _concepts()
    second = _concepts(extra=8)
    vr._validate_pass2(first, second)

    changed = _concepts(extra=8)
    changed["concepts"][4]["title"] = "Different concept"
    with pytest.raises(vr.VintageResearchError, match="changed the title"):
        vr._validate_pass2(first, changed)


def test_pass2_rejects_cosmetic_expansion() -> None:
    first = _concepts()
    second = _concepts()
    with pytest.raises(vr.VintageResearchError, match="did not substantially expand"):
        vr._validate_pass2(first, second)
