"""Composable Veo motion-prompt functions.

The first frame already owns appearance, composition and geography. The prompt
therefore has one job: constrain what may change through time. Keeping those
constraints as small named functions makes the behaviour reusable across scenes
without hard-coding scene-specific text into the runner.
"""

from __future__ import annotations


def temporal_window() -> str:
    """Make the take a slice of an ongoing event, not a generated action arc."""
    return (
        "TEMPORAL WINDOW — The clip begins mid-event and ends mid-event. Treat the supplied "
        "first frame as the centre of an already-running motion state, not the start of an "
        "action. Motion stays bounded around that state for the whole take. There is no "
        "build-up, escalation, payoff, resolution or final pose."
    )


def bounded_subject_motion() -> str:
    """Stop Veo turning lively movement into progressive displacement."""
    return (
        "BOUNDED SUBJECT MOTION — Use short reversible micro-movements around the starting "
        "pose: small weight shifts, light bounce, brief torso movement, head movement and "
        "natural balance corrections. Each movement returns toward the starting pose instead "
        "of accumulating. Do not create monotonic motion such as progressively crouching, "
        "lowering, advancing, turning away, sitting, kneeling or completing a gesture."
    )


def observational_camera() -> str:
    """The camera is another body in the event, not a cinematography instruction."""
    return (
        "CAMERA — Keep the supplied composition. The phone is physically inside the event: "
        "tiny handheld sway, small crowd bumps and imperfect corrective settling only. No "
        "intentional pan, tilt, push, pull, orbit, zoom, reveal, rack-focus move or heroic "
        "reframing. Foreground bodies may briefly occlude parts of the frame."
    )


def world_independence() -> str:
    """Prevent a crowd from synchronising around the named subject."""
    return (
        "WORLD MOTION — Background people continue independent overlapping behaviour on "
        "different rhythms and in different directions. Some may briefly react to a nearby "
        "incident while others keep watching the event source, talking, drinking, singing "
        "with mates or moving through the room. Do not synchronise the crowd or progressively "
        "redirect collective attention toward one person. Maintain approximately the same "
        "crowd density and energy from first frame to last."
    )


def physical_state_invariance() -> str:
    """Prevent Veo from inventing a new material/health state as motion accumulates."""
    return (
        "PHYSICAL STATE — Preserve the physical condition shown in the first frame. Skin, hair "
        "and clothing may move naturally but must not acquire a new state through time. Do not "
        "invent or progressively add sweat, wet or glossy skin, soaked or darkened clothing, "
        "flushing, heat distress, grime, wounds, bruising, tears, blood, spills or other new "
        "material conditions unless the shot direction explicitly requires one already implied "
        "by the first frame."
    )


def first_frame_locks() -> str:
    """Make stable first-frame facts explicit without asking Veo to redraw them."""
    return (
        "FIRST-FRAME LOCKS — Preserve identities, clothing, props, object scale, spatial "
        "relationships, lighting logic and room density established by the supplied frame. "
        "Stable objects remain stable unless the scene direction explicitly says they move. "
        "Do not invent accessories, tattoos, duplicate people, remove people or clean up the "
        "environment."
    )


def finish_state() -> str:
    """A compact last instruction that biases against Veo resolving the scene."""
    return (
        "END CONDITION — The final second must still look like the same ongoing moment seen "
        "in the first second. Nothing has been completed; the editor could cut into or out of "
        "either end without revealing a beginning or an ending."
    )


def build_motion_prompt(scene_direction: str) -> str:
    """Compile generic motion law around scene/shot-specific production direction.

    ``scene_direction`` remains world configuration. These functions only define
    how Veo should interpret motion through time, so a new scene still needs no
    runner code change.
    """
    direction = scene_direction.strip()
    if not direction:
        raise ValueError("scene motion direction is empty")
    return "\n\n".join(
        (
            temporal_window(),
            bounded_subject_motion(),
            observational_camera(),
            world_independence(),
            physical_state_invariance(),
            "SCENE / SHOT DIRECTION — " + direction,
            first_frame_locks(),
            finish_state(),
        )
    )
