"""The design-data report, which makes "the advisor is uninformed" visible.

The consumers of the mined corpus refuse honestly when their artefacts are
absent -- and did so invisibly for months. The report exists so the state of
the data is a printed fact rather than an archaeology finding, so the one
thing worth pinning is that it states absence plainly and never needs a
database to say so.
"""

from __future__ import annotations

from app.cli import EXIT_OK, _design_data


def test_the_report_names_every_absent_artefact(capsys, monkeypatch, tmp_path) -> None:
    import app.config

    monkeypatch.setattr(app.config, "PROJECT_ROOT", tmp_path)

    assert _design_data(refresh=False) == EXIT_OK

    out = capsys.readouterr().out
    for artefact in (
        "design_patterns.json",
        "design_structure.json",
        "design_templates.json",
        "joined.json",
    ):
        assert artefact in out
    assert "ABSENT" in out
    assert "design-data --refresh" in out, "an absent artefact must state its remedy"


def test_a_present_artefact_reports_its_size_and_age(capsys, monkeypatch, tmp_path) -> None:
    import app.config

    monkeypatch.setattr(app.config, "PROJECT_ROOT", tmp_path)
    corpus = tmp_path / "var" / "design_corpus"
    corpus.mkdir(parents=True)
    (corpus / "joined.json").write_text('[{"a": 1}, {"b": 2}]', encoding="utf-8")

    assert _design_data(refresh=False) == EXIT_OK

    out = capsys.readouterr().out
    assert "2 entries" in out
