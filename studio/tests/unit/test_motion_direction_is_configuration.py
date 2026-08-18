"""Motion direction is scene configuration, not something a script carries.

``run_pub_coverage_veo.py`` held two motion prompts as string literals and
declared ``--shot`` as ``choices=sorted(PROMPTS)``. The only animatable shots in
any world were therefore the two somebody had typed into a script named after
one pub, and a panel called ``damo-incident-in-context`` -- which is what the
Scenes bench now produces and writes into the Veo trigger -- was rejected by
argparse before anything reached the provider.

These pin the separation: the engine takes a scene and a shot, and the words
come from the world.
"""

from __future__ import annotations

import ast

from app.config import PROJECT_ROOT

RUNNER = PROJECT_ROOT / "scripts" / "run_pub_coverage_veo.py"
SHOTS = PROJECT_ROOT / "worlds" / "world-01" / "shots"


def test_the_runner_carries_no_prompts_of_its_own() -> None:
    """No motion prompt literal, and no closed list of shot names."""
    source = RUNNER.read_text(encoding="utf-8")
    tree = ast.parse(source)

    # Module-level string constants only, checked on the tree rather than the
    # text: the docstring quotes the old code on purpose, and a test that greps
    # prose fails on an accurate comment.
    assigned = {
        target.id
        for node in tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    assert "PROMPTS" not in assigned
    # The scene is named by the caller. It used to default to one.
    assert 'parser.add_argument("--scene", required=True)' in source


def test_no_shot_name_is_refused_before_the_world_is_consulted() -> None:
    """argparse must not be the thing that decides what a shot can be called."""
    tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if getattr(node.func, "attr", None) != "add_argument":
            continue
        names = [a.value for a in node.args if isinstance(a, ast.Constant)]
        if "--shot" in names:
            assert not any(k.arg == "choices" for k in node.keywords)


def test_the_scene_holds_its_own_motion_direction() -> None:
    """Beside the coverage prompt, named the same way."""
    scene = SHOTS / "W01-P28.veo-motion.txt"

    assert scene.is_file()
    text = scene.read_text(encoding="utf-8")
    # §14: the prompt describes what changes through time.
    assert "rocking out" in text
    # And the invariants the take must not break.
    assert "stool and pint remain stable" in text
    # The cap that was never canon.
    assert "cap" not in text.lower()


def test_a_second_scene_needs_a_file_not_a_code_change() -> None:
    """The resolver looks for two filenames and nothing else.

    A scene override and a per-shot override, in that order of specificity, in
    any world. Adding W02's first scene means writing one text file.
    """
    source = RUNNER.read_text(encoding="utf-8")

    assert "{scene_key}.veo-motion.txt" in source
    assert "{scene_key}.{shot}.veo-motion.txt" in source
    assert 'worlds.glob("*/shots")' in source
