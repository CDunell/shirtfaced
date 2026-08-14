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


def test_select_images_uses_actual_cached_bytes_and_persists_hash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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


def test_manual_prompts_carry_the_contract_the_api_gets_from_its_schema() -> None:
    """A chat window has no structured output, so the prompt has to say the shape.

    The API path passes CONCEPT_SCHEMA and is forced into it. The manual path
    was handed the same prompt with nothing enforcing the result, and a run came
    back as prose that import_run then refused.
    """
    contract = vr.manual_output_contract()

    for field in vr.CONCEPT_SCHEMA["properties"]["concepts"]["items"]["required"]:
        assert field in contract
    assert '{"concepts":' in contract
    assert "1 to 10 in order" in contract
    assert vr.POD_SUFFIX in contract


def test_sources_are_interleaved_so_one_cannot_crowd_out_the_other() -> None:
    """Archive ids sort above every eBay id, so ordering alone hid half the corpus.

    evidence_records sorts by listing_id descending and the archive adapter
    mints ids at 9e14 to avoid colliding with eBay's twelve digits. A sixteen
    image run drew sixteen archive pieces and no sold listings at all.
    """
    rows = [
        {"listing_id": "900000000000003", "marketplace": "archive"},
        {"listing_id": "900000000000002", "marketplace": "archive"},
        {"listing_id": "900000000000001", "marketplace": "archive"},
        {"listing_id": "406847192188", "marketplace": "ebay"},
        {"listing_id": "406847192187", "marketplace": "ebay"},
    ]

    ordered = vr._interleave_sources(rows)

    # Both sources appear inside the first four, rather than one filling them.
    first_four = {row["marketplace"] for row in ordered[:4]}
    assert first_four == {"archive", "ebay"}
    assert len(ordered) == len(rows)


def test_interleaving_leaves_a_single_source_untouched() -> None:
    rows = [{"listing_id": "1", "marketplace": "ebay"}, {"listing_id": "2", "marketplace": "ebay"}]

    assert vr._interleave_sources(rows) == rows
