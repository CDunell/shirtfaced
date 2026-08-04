"""Committing canonical documents to Git.

Every invocation passes arguments as a list. Nothing user-authored or model-authored
is ever interpolated into a shell command, and the shell is never involved.

A failed commit does not undo the files. The specification is explicit: keep the valid
documents, flag the change as uncommitted, and surface the exact error rather than
pretending the change is versioned.
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from app.domain.errors import StudioError

logger = logging.getLogger(__name__)

COMMAND_TIMEOUT_SECONDS = 30


class GitError(StudioError):
    """A Git operation failed."""


@dataclass(frozen=True)
class CommitResult:
    """What was committed."""

    commit: str
    committed_paths: list[str]


@runtime_checkable
class GitStore(Protocol):
    """Versions canonical documents."""

    def commit_paths(self, paths: list[Path], message: str) -> CommitResult: ...


class DisabledGitStore:
    """Used when ``GIT_ENABLED`` is false.

    Refuses rather than silently doing nothing, so a caller cannot report a commit
    that never happened.
    """

    def commit_paths(self, paths: list[Path], message: str) -> CommitResult:
        raise GitError("Git is disabled by configuration (GIT_ENABLED=false).")


class SubprocessGitStore:
    """Runs the local ``git`` binary."""

    def __init__(self, repository_root: Path) -> None:
        self._root = repository_root.resolve()

    def _run(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                ["git", *arguments],
                cwd=self._root,
                capture_output=True,
                text=True,
                check=False,
                timeout=COMMAND_TIMEOUT_SECONDS,
                # Never shell=True: a commit message is user-authored text.
                shell=False,
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise GitError(f"git could not be run: {error}") from error

    def commit_paths(self, paths: list[Path], message: str) -> CommitResult:
        """Stage exactly these paths and make one commit.

        Only the named files are staged, so unrelated working changes are never swept
        into a canon commit.
        """
        if not paths:
            raise GitError("No paths were given to commit.")

        relative: list[str] = []
        for path in paths:
            resolved = path.resolve()
            if self._root not in resolved.parents:
                raise GitError(f"{path} is outside the repository.")
            relative.append(resolved.relative_to(self._root).as_posix())

        staged = self._run("add", "--", *relative)
        if staged.returncode != 0:
            raise GitError(f"git add failed: {staged.stderr.strip()}")

        # Nothing to do is not an error: an idempotent retry lands here.
        status = self._run("diff", "--cached", "--quiet", "--", *relative)
        if status.returncode == 0:
            head = self._run("rev-parse", "HEAD")
            return CommitResult(commit=head.stdout.strip(), committed_paths=relative)

        committed = self._run("commit", "-m", message, "--only", "--", *relative)
        if committed.returncode != 0:
            raise GitError(
                f"git commit failed: {committed.stderr.strip() or committed.stdout.strip()}"
            )

        head = self._run("rev-parse", "HEAD")
        if head.returncode != 0:
            raise GitError(f"git rev-parse failed: {head.stderr.strip()}")

        commit = head.stdout.strip()
        logger.info("Committed %s as %s", ", ".join(relative), commit[:12])
        return CommitResult(commit=commit, committed_paths=relative)


def build_git_store(repository_root: Path, *, enabled: bool) -> GitStore:
    """The Git store for these settings."""
    return SubprocessGitStore(repository_root) if enabled else DisabledGitStore()
