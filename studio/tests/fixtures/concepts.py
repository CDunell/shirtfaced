"""Builders for concept-library fixtures.

A valid document is the smallest thing that satisfies the entry grammar, so a
test that breaks one is unambiguous about what it broke. The retirement forms
and the decoy mirror the real library exactly: the parser's whole job is
telling those apart.
"""
# ruff: noqa: E501  -- entries are one line by contract, exactly as the real library writes them.

from __future__ import annotations

# Every retirement form the real library uses, plus the trap. Entry 4 contains
# the word "retired" in prose and must stay live -- the real library's entry 54
# ("three retired blokes") is the reason substring matching is forbidden.
VALID_LIBRARY = """\
# shirtfaced — Garment Concept Library

Status: Working concept archive

## Hard guardrails

- No souvenir Australiana.

## Round 01

1. **ABSOLUTE WEAPON** — Museum-quality portrait treatment of a pedestal fan. ABSOLUTE WEAPON. No explanation.
2. **RETIRED — SEND IT (technical treatment)** — The trajectory version is retired.
3. **THE DROP BEAR** — Retired. Too directly Australiana.
4. **SENIOR MANAGEMENT** — Portrait of three retired blokes judging everyone. Clean institutional layout.

## Round 02 — garment-led

5. **BIN NIGHT** — Retire as currently framed if it reads suburban-Australiana. The western treatment can return.
6. **HOT GIRL ADMIN** — Crop. Clean tiny front type HOT GIRL ADMIN. Back neck `shirtfaced`.
7. **THE LOT** — Crop/tee/crew/hoodie. One word, enormous: THE LOT.
8. **shirtfaced** — Tee pair. The word, twice, disagreeing about the font.

## Selection rule

Work the queue in order.
"""


def entry(number: int, title: str, body: str) -> str:
    """One well-formed entry line."""
    return f"{number}. **{title}** — {body}"


def library(*entries: str, heading: str = "## Round 01") -> str:
    """The smallest valid document around the given entry lines."""
    lines = "\n".join(entries)
    return f"# Fixture Library\n\n{heading}\n\n{lines}\n"
