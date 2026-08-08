"""The range and the decision, over HTTP.

Section 9 of DESIGN_ENGINE_ADAPTATION.md names one thread to prove before
anything else, and half of it was already true at the engine level and untrue as
a product: `CompositionEngine` sat on no route, so the approve control that is
supposed to be the training signal did not exist for anyone to press.

These use their own approval store rather than the real one. Writing test
approvals into `var/approvals.json` would train the engine on decisions nobody
made, which is worse than no learning at all -- and it happened once by hand
before these existed.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.routes import range as range_route

BRIEF = {
    "elements": [
        {"kind": "image", "content": "photo", "aspect": 0.8},
        {"kind": "text", "content": "SHIRTFACED"},
    ]
}


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    """A client whose decisions land in a throwaway store."""
    from app.services.composition_engine import CompositionEngine

    store = tmp_path / "approvals.json"

    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(range_route.router)
    # Through dependency_overrides rather than monkeypatching the module
    # attribute. Depends(get_engine) captured the original function at import,
    # so patching the name had no effect and these tests wrote into the real
    # approvals store -- training the engine on decisions nobody made, which is
    # the exact fault the docstring above warns about.
    app.dependency_overrides[range_route.get_engine] = lambda: CompositionEngine(
        range_route.TEMPLATES, store
    )
    return TestClient(app)


def test_a_range_covers_every_garment(client: TestClient) -> None:
    """Mandatory output for every garment is the point, not a nicety."""
    body = client.post("/api/range", json=BRIEF).json()

    assert body["total"] >= 11
    assert body["offered"] == body["total"]


def test_a_garment_that_cannot_take_the_assets_says_so(client: TestClient) -> None:
    """A refusal belongs in the range. A missing row reads as "not applicable"
    when it usually means "not considered"."""
    crowded = {
        "elements": [
            {"kind": "image", "content": "photo"},
            {"kind": "text", "content": "SHIRTFACED"},
            {"kind": "text", "content": "EST 2026"},
            {"kind": "text", "content": "AUSTRALIA"},
        ]
    }
    body = client.post("/api/range", json=crowded).json()

    assert body["total"] == len(body["garments"]), "a garment was dropped rather than refused"
    for garment in body["garments"]:
        assert garment["offered"] or garment["refusal_reason"], garment["garment"]


def test_every_placement_carries_its_evidence(client: TestClient) -> None:
    """A confidence with nothing behind it is a number, not evidence."""
    body = client.post("/api/range", json=BRIEF).json()
    placement = next(g for g in body["garments"] if g["offered"])["placements"][0]
    option = placement["options"][0]

    assert option["corpus_designs"] > 0
    assert option["rationale"]
    assert 0.0 < option["confidence"] <= 1.0


def test_a_decision_moves_the_confidence(client: TestClient) -> None:
    """The kill gate, through the product rather than the library."""
    body = client.post("/api/range", json=BRIEF).json()
    option = next(g for g in body["garments"] if g["offered"])["placements"][0]["options"][0]
    before = option["confidence"]

    for _ in range(3):
        client.post(
            "/api/range/decision",
            json={
                "element_count": 2,
                "template_id": option["template_id"],
                "approved": True,
                "decided_by": "test",
            },
        )

    after_body = client.post("/api/range", json=BRIEF).json()
    after = next(
        o
        for g in after_body["garments"]
        if g["offered"]
        for o in g["placements"][0]["options"]
        if o["template_id"] == option["template_id"]
    )["confidence"]

    assert after > before, "approving through the API did not move the confidence"


def test_a_decision_reports_what_it_changed(client: TestClient) -> None:
    """Returning only the new number asks to be trusted; both can be checked."""
    body = client.post("/api/range", json=BRIEF).json()
    option = next(g for g in body["garments"] if g["offered"])["placements"][0]["options"][0]

    result = client.post(
        "/api/range/decision",
        json={
            "element_count": 2,
            "template_id": option["template_id"],
            "approved": True,
            "decided_by": "test",
        },
    ).json()

    assert result["before"]["decisions"] == 0
    assert result["after"]["decisions"] == 1


def test_a_decision_needs_an_author(client: TestClient) -> None:
    """An approval nobody signed is not an approval."""
    response = client.post(
        "/api/range/decision",
        json={"element_count": 2, "template_id": "2-3", "approved": True, "decided_by": ""},
    )

    assert response.status_code == 422


def test_an_empty_brief_is_refused(client: TestClient) -> None:
    """The engine never invents content, so it has nothing to arrange."""
    assert client.post("/api/range", json={"elements": []}).status_code == 422
