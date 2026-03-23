#!/usr/bin/env python3
"""Automatically commit and push repository changes at a fixed interval."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a git command in the repository and return the completed process."""
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=check,
        text=True,
        capture_output=True,
    )


def tracked_changes() -> list[str]:
    """Return the current porcelain status lines."""
    result = run_git("status", "--porcelain", check=True)
    return [line for line in result.stdout.splitlines() if line.strip()]


def next_iteration_number() -> int:
    """Return the next iteration number based on existing commit subjects."""
    result = run_git("log", "--format=%s", check=True)
    highest = 0
    for subject in result.stdout.splitlines():
        match = re.match(r"Iteration (\d+):", subject)
        if match:
            highest = max(highest, int(match.group(1)))
    return highest + 1


def has_test1_commit() -> bool:
    """Return True if a `test1` commit already exists in history."""
    result = run_git("log", "--format=%s", check=True)
    return any(subject.strip() == "test1" for subject in result.stdout.splitlines())


def summarize_changes(status_lines: list[str]) -> str:
    """Generate a short commit description from the changed file paths."""
    paths = []
    for line in status_lines:
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", maxsplit=1)[1]
        paths.append(Path(path).name)

    unique_paths = sorted(dict.fromkeys(paths))
    if not unique_paths:
        return "auto-sync repository changes"
    if len(unique_paths) == 1:
        return f"update {unique_paths[0]}"
    if len(unique_paths) == 2:
        return f"update {unique_paths[0]} and {unique_paths[1]}"
    return (
        f"update {unique_paths[0]}, {unique_paths[1]}, "
        f"and {len(unique_paths) - 2} more files"
    )


def build_commit_message(status_lines: list[str]) -> str:
    """Return the next commit message in the required assignment format."""
    if not has_test1_commit():
        return "test1"
    iteration = next_iteration_number()
    return f"Iteration {iteration}: {summarize_changes(status_lines)}"


def commit_and_push(remote: str, branch: str | None, dry_run: bool) -> bool:
    """Commit and push current changes. Returns True when a commit was made."""
    status_lines = tracked_changes()
    if not status_lines:
        print("No changes detected.")
        return False

    message = build_commit_message(status_lines)
    print(f"Preparing commit: {message}")

    if dry_run:
        for line in status_lines:
            print(f"  {line}")
        return True

    run_git("add", "-A", check=True)
    run_git("commit", "-m", message, check=True)

    push_target = branch or run_git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    run_git("push", remote, push_target, check=True)
    print(f"Pushed {message} to {remote}/{push_target}.")
    return True


def parse_args() -> argparse.Namespace:
    """Parse CLI options for the auto-commit helper."""
    parser = argparse.ArgumentParser(
        description="Commit and push repository changes every N seconds."
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Polling interval in seconds. Defaults to 60.",
    )
    parser.add_argument(
        "--remote",
        default="origin",
        help="Git remote to push to. Defaults to origin.",
    )
    parser.add_argument(
        "--branch",
        default=None,
        help="Branch to push. Defaults to the current branch.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single check instead of looping forever.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the commit message that would be used without committing.",
    )
    return parser.parse_args()


def main() -> int:
    """Run the auto-commit loop."""
    args = parse_args()
    print(
        "Watching for Git changes every "
        f"{args.interval} seconds in {REPO_ROOT}."
    )

    while True:
        try:
            commit_and_push(args.remote, args.branch, args.dry_run)
        except subprocess.CalledProcessError as exc:
            print(exc.stderr.strip() or exc.stdout.strip() or str(exc), file=sys.stderr)
            return exc.returncode or 1

        if args.once:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
