"""Reading Illustrator EPS without a Ghostscript on the machine.

Bought vector packs arrive as .eps and .ai, and the converter read neither, so a
pack sat in assets/stock as a file nobody could open. The usual answer is an
external binary, which would mean every machine that ever rebuilds a design
needs one installed -- and this archive's premise is that its outputs can always
be regenerated.

These cover the three things that were wrong before they were right, each of
which produced a file that parsed cleanly and drew the wrong picture.
"""

from __future__ import annotations

from app.archive.eps import read

HEADER = b"%!PS-Adobe-3.0 EPSF-3.0\n%%HiResBoundingBox: 0 0 100 100\n%%EndSetup\n"


def test_a_square_survives_the_journey() -> None:
    art = read(HEADER + b"0 g\n10 10 m\n90 10 L\n90 90 L\n10 90 L\nf\n")

    assert len(art.paths) == 1
    assert art.width == 100 and art.height == 100


def test_postscript_counts_y_upwards_and_svg_counts_it_down() -> None:
    """The flip, which is the difference between artwork and a mirror image.

    A point at y=10 in a 100-tall box sits near the *bottom* in PostScript, so
    it must come out near 90 in SVG.
    """
    art = read(HEADER + b"0 g\n10 10 m\n20 10 L\n20 20 L\nf\n")
    path = art.paths[0][0]

    assert "M 10 90" in path, f"the y-flip did not happen: {path}"


def test_the_prolog_is_not_read_as_artwork() -> None:
    """Illustrator *defines* its operators before using them.

    Parsing from the top of the file reads `/h { closepath } def` as drawing,
    and the first shape comes back as a run of closepaths with no points.
    """
    prolog = b"%!PS-Adobe-3.0 EPSF-3.0\n%%HiResBoundingBox: 0 0 100 100\n"
    prolog += b"/h { closepath } def\n/f { fill } def\n%%EndSetup\n"
    art = read(prolog + b"0 g\n5 5 m\n50 5 L\nf\n")

    assert len(art.paths) == 1, "the operator dictionary was read as a drawing"
    assert art.paths[0][0].startswith("M "), "an empty path was emitted"


def test_a_gradient_shape_is_dropped_rather_than_painted_in_the_default_ink() -> None:
    """The fault that hid six hundred shapes.

    The pack's background is a gradient rectangle the size of the canvas. With
    no gradient support the colour is unknown, and filling it with the default
    black buried everything drawn afterwards.
    """
    art = read(
        HEADER
        + b"0 g\nBb\n0 0 m\n100 0 L\n100 100 L\n0 100 L\nF\n0 BB\n"
        + b"10 10 m\n20 20 L\nf\n"
    )

    assert len(art.paths) == 1, "the gradient rectangle was painted"
    assert "gradients are not converted" in art.skipped


def test_a_compound_path_stays_one_shape() -> None:
    """A ring is an outline and a hole painted together.

    Emitted separately the hole becomes a disc sitting on top of the ring.
    """
    art = read(
        HEADER + b"0 g\n*u\n0 0 m\n100 0 L\n100 100 L\nf\n40 40 m\n60 40 L\n60 60 L\nf\n*U\n"
    )

    assert len(art.paths) == 1, "the subpaths were emitted as separate shapes"
    assert art.paths[0][0].count("M ") == 2, "one of the subpaths was lost"


def test_cmyk_becomes_a_colour() -> None:
    """Packs are printed artwork and arrive in process colours, not RGB."""
    art = read(HEADER + b"0 0 0 1 k\n0 0 m\n10 10 L\nf\n")

    assert art.paths[0][1] == "#000000"


def test_a_file_with_no_bounding_box_is_refused_with_a_reason() -> None:
    """Without one the flip has no reference and the drawing lands off-canvas."""
    art = read(b"%!PS-Adobe-3.0\n0 0 m\n10 10 L\nf\n")

    assert art.paths == []
    assert any("bounding box" in reason for reason in art.skipped)
