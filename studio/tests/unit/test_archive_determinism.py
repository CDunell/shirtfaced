"""The archive's load-bearing property: same inputs, same bytes.

Not "looks the same" and not "visually identical". If a reprint two years from
now does not produce the file that was approved, the archive has not done the
one job it exists to do, and the failure is silent until someone compares two
garments.

They also cover what provenance does and does not do: it travels with an
element and it never blocks one. Whether a design may be sold is asked once,
before release.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date

import pytest

from app.archive import authored
from app.archive.render import Palette, RefusedToRender, render
from app.archive.svg import num, rng_for
from app.archive.typeset import MissingGlyph, faces, set_arc, set_line
from app.domain.element import Licence
from app.domain.enums import LicenceStatus

PALETTE = Palette(garment="#101010", inks=("#C6FF00", "#F2F0EA"))
CONTENT = {"primary_text": "SHIRTFACED", "secondary_text": "EST 2026"}


def test_the_same_inputs_render_the_same_bytes() -> None:
    element = authored.element("badge_shield_0001")
    first = render(element, CONTENT, PALETTE, seed=8374)
    second = render(element, CONTENT, PALETTE, seed=8374)
    assert first.svg == second.svg
    assert first.content_hash == second.content_hash


def test_every_authored_element_renders_reproducibly() -> None:
    """Determinism has to hold for all of them, not for the one that was tried."""
    for element in authored.ALL:
        first = render(element, CONTENT, PALETTE, seed=11)
        second = render(element, CONTENT, PALETTE, seed=11)
        assert first.content_hash == second.content_hash, element.id


def test_a_different_seed_changes_a_distressed_render() -> None:
    """The seed must actually reach the geometry, or determinism is vacuous."""
    element = authored.element("badge_shield_0001")
    one = render(element, CONTENT, PALETTE, seed=1, treatment="distressed")
    two = render(element, CONTENT, PALETTE, seed=2, treatment="distressed")
    assert one.content_hash != two.content_hash


def test_a_distressed_render_repeats_for_its_own_seed() -> None:
    element = authored.element("badge_shield_0001")
    one = render(element, CONTENT, PALETTE, seed=99, treatment="distressed")
    two = render(element, CONTENT, PALETTE, seed=99, treatment="distressed")
    assert one.svg == two.svg


def test_different_content_changes_the_output() -> None:
    element = authored.element("type_collegiate_arch_0001")
    one = render(element, CONTENT, PALETTE, seed=5)
    two = render(element, {**CONTENT, "primary_text": "GET SHIRTFACED"}, PALETTE, seed=5)
    assert one.content_hash != two.content_hash


def test_the_output_carries_no_timestamp_or_generator_note() -> None:
    """A stamped date would defeat byte-identity without changing the design."""
    svg = render(authored.element("frame_shield_0001"), CONTENT, PALETTE, seed=3).svg
    assert "<!--" not in svg
    assert "2026" not in svg.split("</svg>")[0].replace(CONTENT["secondary_text"], "")


def test_text_is_outlines_not_a_font_reference() -> None:
    """A <text> element defers layout to whatever opens the file."""
    svg = render(authored.element("type_stack_0001"), CONTENT, PALETTE, seed=3).svg
    assert "<text" not in svg
    assert "font-family" not in svg
    assert "<path" in svg


def test_a_seeded_generator_is_scoped_to_its_purpose() -> None:
    """Two purposes under one seed must not share a stream.

    Otherwise adding a call to one silently changes the other, which is the
    quiet way determinism dies once more than one thing wants variation.
    """
    first = [rng_for(7, "distress").random() for _ in range(4)]
    second = [rng_for(7, "halftone").random() for _ in range(4)]
    assert first != second
    assert first == [rng_for(7, "distress").random() for _ in range(4)]


def test_numbers_are_formatted_one_way() -> None:
    """Negative zero compares equal to zero and does not render identically."""
    assert num(-0.0) == "0"
    assert num(0.0) == "0"
    assert num(1.50000001) == num(1.5)


# --- Provenance travels, and does not block ---------------------------------


def test_an_element_whose_terms_are_unknown_still_renders() -> None:
    """Whether a design may be sold is a release question, asked once, about a
    finished design -- not a question a component can answer."""
    element = replace(authored.element("badge_shield_0001"), licence=Licence())
    result = render(element, CONTENT, PALETTE, seed=1)
    assert result.svg.startswith("<svg")


def test_where_something_came_from_travels_with_it() -> None:
    """Provenance is a record rather than a gate. It is what makes the rights
    question answerable later, when it is actually asked."""
    element = replace(
        authored.element("badge_shield_0001"),
        licence=Licence(
            status=LicenceStatus.UNVERIFIED,
            source="internet-archive",
            source_id="IA-9911",
            source_url="https://example.invalid/IA-9911",
        ),
    )
    assert element.licence.source == "internet-archive"
    assert element.licence.source_id == "IA-9911"
    render(element, CONTENT, PALETTE, seed=1)


def test_non_commercial_terms_are_recorded_not_blocked() -> None:
    """Recorded so the release review sees it. Not blocked, because designing
    with something and selling it are different acts."""
    element = replace(
        authored.element("badge_shield_0001"),
        licence=Licence(
            status=LicenceStatus.VERIFIED,
            terms="CC BY-NC",
            source="somewhere",
            checked_at=date(2026, 8, 8),
            commercial_use=False,
        ),
    )
    assert element.licence.terms == "CC BY-NC"
    assert not element.licence.commercial_use
    assert render(element, CONTENT, PALETTE, seed=1).svg.startswith("<svg")


def test_every_authored_element_declares_a_usable_licence() -> None:
    for element in authored.ALL:
        assert element.licence.usable, element.id


def test_an_excluded_treatment_is_refused() -> None:
    element = authored.element("badge_shield_0001")
    with pytest.raises(RefusedToRender) as raised:
        render(element, CONTENT, PALETTE, seed=1, treatment="photographic")
    assert raised.value.reason == "TREATMENT_EXCLUDED"


def test_too_many_inks_is_refused() -> None:
    element = authored.element("type_stack_0001")
    palette = Palette(inks=("#111111", "#222222", "#333333", "#444444"))
    with pytest.raises(RefusedToRender) as raised:
        render(element, CONTENT, palette, seed=1)
    assert raised.value.reason == "INKS_ABOVE_MAXIMUM"


# --- Content handling -------------------------------------------------------


def test_an_empty_slot_is_reported_rather_than_invented() -> None:
    element = authored.element("badge_shield_0001")
    result = render(element, {"primary_text": "SHIRTFACED"}, PALETTE, seed=1)
    assert any("secondary_text" in warning for warning in result.warnings)


def test_a_character_the_face_cannot_set_is_refused() -> None:
    """Silently dropping a glyph prints the wrong word on a garment."""
    with pytest.raises(MissingGlyph):
        set_line("你好")


def test_setting_text_is_reproducible() -> None:
    assert set_line("SHIRTFACED", cap_height=12).path == set_line("SHIRTFACED", cap_height=12).path
    assert (
        set_arc("SHIRTFACED", radius=40, cap_height=12).path
        == set_arc("SHIRTFACED", radius=40, cap_height=12).path
    )


def test_faces_are_discovered_from_the_type_folder() -> None:
    """Adding a typeface must be dropping in a file, not editing a module.

    The face is close to being the design -- the median streetwear graphic is
    one element and four words -- so a code change per font is friction in
    exactly the wrong place.
    """
    available = faces()

    assert "shirtfaced" in available, "the alias stopped resolving"
    assert "Shirtfaced-Regular" in available, "the file stem is not addressable"


def test_an_unknown_face_names_what_is_available() -> None:
    """A missing font is a setup problem, and the error should say which."""
    with pytest.raises(FileNotFoundError) as caught:
        set_line("SHIRTFACED", face="no-such-face")

    assert "shirtfaced" in str(caught.value), "the error does not list the faces we have"
