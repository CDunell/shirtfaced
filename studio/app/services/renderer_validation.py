"""Five-scene Google renderer validation harness.

This module prepares deterministic, auditable scene packages and exposes the manual
gates. Billable rendering is enabled only when a Gemini key is configured; no key
means planning/validation only.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class BenchmarkScene:
    id: str
    title: str
    purpose: str
    hero: str
    exact_instant: str
    required_refs: tuple[str, ...]
    still_gate: tuple[str, ...]
    motion: str


SCENES: tuple[BenchmarkScene, ...] = (
    BenchmarkScene(
        "pub-1105",
        "Pub chorus",
        "crowd + identity + prop + I2V",
        "damo",
        (
            "Damo stands on the pool table with both boots on it, cue horizontal "
            "overhead in both fists, head back, eyes shut, roaring the chorus, facing "
            "away from the stage; stool and full beer remain on the table."
        ),
        ("damo:identity", "damo:body", "brock:identity", "emma:identity"),
        (
            "damo_identity",
            "damo_on_table",
            "cue_overhead",
            "no_invented_identity_marks",
            "stool_and_beer",
            "camera_premise",
        ),
        (
            "Damo keeps the cue overhead and rocks with the chorus; the crowd and "
            "band move independently; a nearby patron lightly bumps the phone, "
            "causing a brief imperfect reframe; native pub audio overloads the phone "
            "mic slightly."
        ),
    ),
    BenchmarkScene(
        "ute-0341",
        "Ute tray",
        "close identity + geometry + wet night",
        "damo",
        (
            "Damo lies in the open tray hugging the wooden pub stool, comfortable, "
            "while the others continue toward the building."
        ),
        ("damo:identity", "damo:body", "brock:identity", "emma:identity"),
        (
            "damo_identity",
            "open_tray_geometry",
            "stool_contact",
            "no_invented_identity_marks",
            "wet_asphalt",
        ),
        (
            "Small breathing and settling movements; the others continue walking; "
            "the ice bag drips; handheld observer movement remains physically plausible."
        ),
    ),
    BenchmarkScene(
        "takeaway-0230",
        "Takeaway kerb",
        "four-person continuity + object counting",
        "ensemble",
        (
            "Four established people sit on the kerb around a pub stool carrying five "
            "food containers; exactly one container is closed."
        ),
        ("damo:identity", "brock:identity", "emma:identity"),
        (
            "cast_identity",
            "four_people",
            "five_containers",
            "one_closed",
            "stool_present",
            "camera_premise",
        ),
        (
            "Natural eating and conversation continue; hands move minimally and "
            "independently; traffic and the takeaway background remain alive."
        ),
    ),
    BenchmarkScene(
        "side-street-2126",
        "Side street",
        "group continuity + moving geography",
        "damo",
        (
            "Damo walks backwards carrying the stool while talking; milk crates are "
            "directly behind him and he has not noticed them."
        ),
        ("damo:identity", "damo:body", "brock:identity", "emma:identity"),
        (
            "damo_identity",
            "stool_present",
            "crates_behind_damo",
            "group_geography",
            "camera_premise",
        ),
        (
            "Damo continues backwards while talking; the group advances naturally; "
            "no one performs for camera; camera remains across the street."
        ),
    ),
    BenchmarkScene(
        "continuity-bridge",
        "Continuity bridge",
        "approved-frame reuse",
        "damo",
        "Begin from an approved in-world frame without resetting identity or wardrobe.",
        ("approved_previous_frame", "canonical_identity_manifest"),
        (
            "identity_continuity",
            "wardrobe_continuity",
            "prop_continuity",
            "camera_premise",
        ),
        (
            "Only the next narrative event changes; preserve successful identity, "
            "wardrobe, environment and capture language."
        ),
    ),
)


def harness_manifest(
    *, google_enabled: bool, image_model: str, video_model: str
) -> dict[str, object]:
    return {
        "version": "1.0",
        "mode": "live" if google_enabled else "planning-only",
        "models": {"image": image_model, "video": video_model},
        "manual_gates": [
            "canon lock for new facts",
            "seed still approval",
            "final video/performance approval",
            "continuity promotion",
        ],
        "automated_stages": [
            "canon/reference resolution",
            "seed prompt package",
            "still QC checklist",
            "motion-only I2V prompt",
            "failure classification",
            "attempt lineage",
            "continuity output package",
        ],
        "scenes": [asdict(scene) for scene in SCENES],
    }


def scene_package(scene_id: str) -> dict[str, object]:
    scene = next((item for item in SCENES if item.id == scene_id), None)
    if scene is None:
        raise KeyError(scene_id)
    return {
        **asdict(scene),
        "authority_order": [
            "scene/world canon",
            "canonical character references",
            "scene appearance state",
            "generator interpretation",
        ],
        "seed_instruction": (
            "Use SHIRTFACED Seed Image Recipe. Preserve locked facts and referenced "
            "identities. Incidental environmental detail is allowed when it remains "
            "background texture."
        ),
        "manual_stop_after_seed": True,
        "video_mode": "first-frame-image-to-video",
        "video_prompt_rule": (
            "Describe only change through time; do not redescribe identity/location/"
            "style already carried by the approved seed."
        ),
    }
