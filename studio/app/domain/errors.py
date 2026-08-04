"""Domain errors.

Validation failures carry every problem found, not just the first. The workflow spends
money on the very next step, so an operator needs the whole list in one go rather than
discovering faults one run at a time.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class StudioError(Exception):
    """Base class for expected, reportable failures."""


class UnsafePathError(StudioError):
    """A path escaped the directory it was required to stay inside."""


class WorldNotFoundError(StudioError):
    """The requested world does not exist on disk or in the database."""


@dataclass(frozen=True)
class ValidationProblem:
    """One specific fault in a canonical document."""

    document: str
    message: str
    line: int | None = None

    def __str__(self) -> str:
        location = f"{self.document}:{self.line}" if self.line else self.document
        return f"{location}: {self.message}"


@dataclass
class WorldValidationError(StudioError):
    """One or more canonical documents failed validation."""

    problems: list[ValidationProblem] = field(default_factory=list)

    def __str__(self) -> str:
        if not self.problems:
            return "The world documents failed validation."
        lines = "\n".join(f"  - {problem}" for problem in self.problems)
        count = len(self.problems)
        noun = "problem" if count == 1 else "problems"
        return f"The world documents failed validation ({count} {noun}):\n{lines}"
