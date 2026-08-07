"""stage-2/PRODUCT_PHOTOGRAPHY.md must not contradict the vehicle canon.

It listed "rear seat" and "passenger seat" as camera positions, "car interiors" as an
approved environment, and "car seats" as a surface products may rest on — all put the
camera, the product or an implied subject inside the vehicle cabin. The decision on a
second pass: product photography gets no exception at all, not even the outside-
looking-in frame the general enclosed-space rule allows elsewhere in WORLD.md. No
enclosed space of any kind — car, lift, tent, phone box — is ever the setting for a
product frame. Found while promoting this document out of stage-2's reference-only
status; see docs/shirtfaced-audit.md Hot List item 2.
"""

from __future__ import annotations

from app.config import PROJECT_ROOT

PRODUCT_PHOTOGRAPHY_PATH = PROJECT_ROOT / "docs" / "stage-2" / "PRODUCT_PHOTOGRAPHY.md"
WORLD_PATH = PROJECT_ROOT / "worlds" / "world-01" / "WORLD.md"


def _text(path) -> str:  # type: ignore[no-untyped-def]
    return path.read_text(encoding="utf-8").lower()


def test_the_document_exists() -> None:
    assert PRODUCT_PHOTOGRAPHY_PATH.is_file()


def test_camera_and_environment_rules_stay_out_of_enclosed_spaces() -> None:
    text = _text(PRODUCT_PHOTOGRAPHY_PATH)

    banned = (
        "rear seat",
        "passenger seat",
        "car interiors",
        "car seats",
        "dashboards",
        "in ordinary vehicles",
    )
    offenders = [phrase for phrase in banned if phrase in text]

    assert not offenders, (
        f"PRODUCT_PHOTOGRAPHY.md still lists these as camera positions, "
        f"environments or resting surfaces: {offenders}. Each puts something "
        "inside an enclosed space, which product photography gets no exception "
        "for, regardless of which document is speaking."
    )


def test_world_md_carries_the_no_exception_rule() -> None:
    """The promoted heading has to state the stricter product-photography rule.

    WORLD.md's general enclosed-space rule allows a camera outside looking in.
    Product extraction does not get that allowance — it was explicitly decided
    to be stricter, and a heading that only pointed back at the general rule
    would silently reintroduce the exception.
    """
    text = _text(WORLD_PATH)

    assert "product photography extraction" in text
    assert "no enclosed space is ever the setting" in text
