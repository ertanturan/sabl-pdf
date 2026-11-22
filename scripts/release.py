from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import subprocess

from versioning import bump_version, check_version, next_version


ROOT = Path(__file__).resolve().parents[1]
HEADINGS = (
    "New features",
    "Bugfixes",
    "Performance improvements",
    "Documentation",
)
DRAFT = Path("docs/changelog/current.md")
RELEASES = Path("docs/changelog/releases")
HISTORY = Path("CHANGELOG.md")
TAG_PATTERN = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")


def latest_tag(root: Path) -> str | None:
    result = subprocess.run(
        ["git", "tag", "--list", "v*"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    versions = [match for tag in result.stdout.splitlines() if (match := TAG_PATTERN.fullmatch(tag))]
    if not versions:
        return None
    highest = max(versions, key=lambda match: tuple(map(int, match.groups())))
    return highest.group()


def validate_notes(notes: str) -> str:
    sections = re.split(r"(?m)^## (.+)\s*$", notes)
    if len(sections) != 1 + len(HEADINGS) * 2:
        raise ValueError("Release notes must contain exactly four required sections")
    headings = sections[1::2]
    if headings != list(HEADINGS):
        raise ValueError("Release note sections must use the required order")
    entries = [line.strip() for section in sections[2::2] for line in section.splitlines() if line.strip()]
    if not entries or any(not item.startswith("- ") for item in entries):
        raise ValueError("Release notes require Markdown bullet entries")
    if any(len(item) > 100 for item in entries):
        raise ValueError("Each release-note bullet must be at most 100 characters")
    if all(item == "- None." for item in entries):
        raise ValueError("Add an actual changelog entry before publishing a release")
    return "\n".join(sections[1:]).strip()


def format_notes(version: str, draft: str, today: str) -> str:
    validate_notes(draft)
    start = draft.index("## ")
    return f"# v{version} ({today})\n\n{draft[start:].strip()}\n"


def snapshot_files(root: Path) -> list[Path]:
    return sorted((root / RELEASES).glob("v*.md"), key=lambda path: version_key(path.stem), reverse=True)


def version_key(label: str) -> tuple[int, int, int]:
    match = TAG_PATTERN.fullmatch(label)
    if match is None:
        raise ValueError(f"Unexpected release notes filename: {label}")
    return tuple(map(int, match.groups()))


def generate_history(root: Path) -> str:
    notes = [path.read_text(encoding="utf-8").strip() for path in snapshot_files(root)]
    if not notes:
        return "# Changelog\n\nRelease history has not been published yet.\n"
    return "# Changelog\n\n" + "\n\n".join(notes) + "\n"


def previous_snapshots_unchanged(root: Path) -> None:
    result = subprocess.run(
        ["git", "tag", "--list", "v*"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    tags = {tag for tag in result.stdout.splitlines() if TAG_PATTERN.fullmatch(tag)}
    for path in snapshot_files(root):
        if path.stem not in tags:
            raise ValueError(f"Release snapshot has no published tag: {path.relative_to(root)}")
    for tag in tags:
        path = root / RELEASES / f"{tag}.md"
        original = subprocess.run(
            ["git", "show", f"{tag}:{path.relative_to(root).as_posix()}"],
            cwd=root,
            capture_output=True,
            check=False,
        )
        if original.returncode == 0 and (
            not path.exists() or original.stdout != path.read_bytes()
        ):
            raise ValueError(f"Published changelog cannot change: {path.relative_to(root)}")


def verify_history(root: Path) -> None:
    previous_snapshots_unchanged(root)
    history = root / HISTORY
    if not snapshot_files(root) and not history.exists():
        return
    if not history.exists() or history.read_text(encoding="utf-8") != generate_history(root):
        raise ValueError("CHANGELOG.md must match the unmodified version snapshots")


def prepare_release(root: Path, part: str, today: str | None = None) -> str:
    verify_history(root)
    current = check_version(root)
    latest = latest_tag(root)
    if latest is not None and version_key(latest) > tuple(map(int, current.split("."))):
        raise ValueError("Merge the preceding release's version and changelog PR before releasing again")
    if latest is not None and version_key(latest) != tuple(map(int, current.split("."))):
        raise ValueError("Project version must match the newest release tag before preparing another release")
    updated = next_version(current, part)
    notes_path = root / RELEASES / f"v{updated}.md"
    if notes_path.exists():
        raise ValueError(f"Version v{updated} already has release notes")
    if latest is not None and version_key(f"v{updated}") <= version_key(latest):
        raise ValueError("Release version must increase")
    draft_path = root / DRAFT
    notes = format_notes(updated, draft_path.read_text(encoding="utf-8"), today or datetime.now(timezone.utc).date().isoformat())
    version = bump_version(root, part)
    notes_path.parent.mkdir(parents=True, exist_ok=True)
    notes_path.write_text(notes, encoding="utf-8")
    (root / HISTORY).write_text(generate_history(root), encoding="utf-8")
    draft_path.write_text(
        "# Unreleased\n\n" + "\n\n".join(f"## {name}\n- None." for name in HEADINGS) + "\n",
        encoding="utf-8",
    )
    return version


def main(args: list[str] | None = None, root: Path = ROOT) -> int:
    parser = argparse.ArgumentParser(description="Prepare SABL PDF's manual GitHub release")
    commands = parser.add_subparsers(dest="action", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--part", choices=("minor", "secondary", "major"), default="minor")
    commands.add_parser("verify-history")
    options = parser.parse_args(args)
    try:
        if options.action == "prepare":
            print(prepare_release(root, options.part))
        else:
            verify_history(root)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
