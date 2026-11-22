from pathlib import Path
import shutil
import subprocess

import pytest

from release import format_notes, generate_history, latest_tag, prepare_release, validate_notes, verify_history


NOTES = """# Unreleased

## New features
- None.

## Bugfixes
- None.

## Performance improvements
- None.

## Documentation
- Add instructions for creating a release.
"""


def git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments], cwd=root, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


@pytest.fixture
def release_root(tmp_path: Path) -> Path:
    (tmp_path / "src/sabl_pdf").mkdir(parents=True)
    (tmp_path / "installer").mkdir()
    (tmp_path / "docs/changelog").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "sabl-pdf"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    (tmp_path / "src/sabl_pdf/__init__.py").write_text(
        '__version__ = "0.1.0"\n', encoding="utf-8"
    )
    (tmp_path / "installer/SABL-PDF.iss").write_text(
        '#define AppVersion "0.1.0"\n', encoding="utf-8"
    )
    (tmp_path / "docs/changelog/current.md").write_text(NOTES, encoding="utf-8")
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "CI test")
    git(tmp_path, "config", "user.email", "ci@example.invalid")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "initial")
    return tmp_path


@pytest.mark.parametrize(
    ("part", "expected"),
    [("minor", "0.1.1"), ("secondary", "0.2.0"), ("major", "1.0.0")],
)
def test_manual_release_bumps_selected_component(
    release_root: Path, part: str, expected: str
) -> None:
    notes_path = release_root / "docs/changelog/releases" / f"v{expected}.md"

    version = prepare_release(release_root, part, "2026-11-22")

    assert version == expected
    assert notes_path.is_file()
    assert f"# v{expected} (2026-11-22)" in notes_path.read_text(encoding="utf-8")
    assert f'version = "{expected}"' in (release_root / "pyproject.toml").read_text(
        encoding="utf-8"
    )


def test_release_notes_contain_only_selected_version(release_root: Path) -> None:
    version = prepare_release(release_root, "minor", "2026-11-22")

    snapshot = (release_root / "docs/changelog/releases" / f"v{version}.md").read_text(
        encoding="utf-8"
    )

    assert snapshot.count("## ") == 4
    assert "## Documentation" in snapshot
    assert "## New features" in snapshot
    assert "## Bugfixes" in snapshot
    assert "## Performance improvements" in snapshot
    assert "# Unreleased" not in snapshot


def test_released_notes_match_generated_history(release_root: Path) -> None:
    prepare_release(release_root, "minor", "2026-11-22")
    git(release_root, "add", ".")
    git(release_root, "commit", "-qm", "release")
    git(release_root, "tag", "v0.1.1")

    history = generate_history(release_root)
    verify_history(release_root)

    assert "# v0.1.1 (2026-11-22)" in history


def test_published_changelog_cannot_be_edited(release_root: Path) -> None:
    prepare_release(release_root, "minor", "2026-11-22")
    git(release_root, "add", ".")
    git(release_root, "commit", "-qm", "release")
    git(release_root, "tag", "v0.1.1")
    path = release_root / "docs/changelog/releases/v0.1.1.md"
    path.write_text("# altered\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Published changelog cannot change"):
        verify_history(release_root)


def test_new_release_preserves_published_notes(release_root: Path) -> None:
    prepare_release(release_root, "minor", "2026-11-22")
    git(release_root, "add", ".")
    git(release_root, "commit", "-qm", "release")
    git(release_root, "tag", "v0.1.1")
    snapshot = release_root / "docs/changelog/releases/v0.1.1.md"
    original = snapshot.read_bytes()
    (release_root / "docs/changelog/current.md").write_text(NOTES, encoding="utf-8")

    new_version = prepare_release(release_root, "minor", "2026-11-23")

    assert new_version == "0.1.2"
    assert snapshot.read_bytes() == original


def test_release_rejects_stale_master_version(release_root: Path) -> None:
    git(release_root, "tag", "v0.1.1")

    with pytest.raises(ValueError, match="Merge the preceding release"):
        prepare_release(release_root, "minor", "2026-11-22")


def test_release_rejects_empty_changelog(release_root: Path) -> None:
    empty = NOTES.replace("- Add instructions for creating a release.", "- None.")
    (release_root / "docs/changelog/current.md").write_text(empty, encoding="utf-8")

    with pytest.raises(ValueError, match="actual changelog entry"):
        prepare_release(release_root, "minor", "2026-11-22")


def test_release_rejects_overlong_bullet() -> None:
    long_note = "- " + ("a" * 99)
    notes = NOTES.replace("- Add instructions for creating a release.", long_note)

    with pytest.raises(ValueError, match="at most 100 characters"):
        validate_notes(notes)


def test_release_rejects_invalid_category_order() -> None:
    reordered = NOTES.replace("## Bugfixes", "## Corrections")

    with pytest.raises(ValueError, match="required order"):
        validate_notes(reordered)


def test_release_rejects_extra_category() -> None:
    extra = NOTES + "\n## Other\n- None.\n"

    with pytest.raises(ValueError, match="exactly four"):
        validate_notes(extra)


def test_release_tag_selection_is_numeric(release_root: Path) -> None:
    git(release_root, "tag", "v0.1.9")
    git(release_root, "tag", "v0.1.10")

    tag = latest_tag(release_root)

    assert tag == "v0.1.10"


def test_release_draft_is_reset_after_freezing(release_root: Path) -> None:
    prepare_release(release_root, "minor", "2026-11-22")

    draft = (release_root / "docs/changelog/current.md").read_text(encoding="utf-8")

    assert draft.startswith("# Unreleased")
    assert draft.count("- None.") == 4


def test_release_formats_version_and_date() -> None:
    version = "0.1.10"

    notes = format_notes(version, NOTES, "2026-11-22")

    assert notes.startswith("# v0.1.10 (2026-11-22)")


def test_published_changelog_cannot_be_deleted(release_root: Path) -> None:
    prepare_release(release_root, "minor", "2026-11-22")
    git(release_root, "add", ".")
    git(release_root, "commit", "-qm", "release")
    git(release_root, "tag", "v0.1.1")
    (release_root / "docs/changelog/releases/v0.1.1.md").unlink()

    with pytest.raises(ValueError, match="Published changelog cannot change"):
        verify_history(release_root)


def test_cumulative_history_cannot_be_rewritten(release_root: Path) -> None:
    prepare_release(release_root, "minor", "2026-11-22")
    git(release_root, "add", ".")
    git(release_root, "commit", "-qm", "release")
    git(release_root, "tag", "v0.1.1")
    (release_root / "CHANGELOG.md").write_text("# rewritten\n", encoding="utf-8")

    with pytest.raises(ValueError, match="CHANGELOG.md"):
        verify_history(release_root)


def test_release_rejects_unpublished_snapshot(release_root: Path) -> None:
    notes = release_root / "docs/changelog/releases/v0.1.1.md"
    notes.parent.mkdir(parents=True)
    notes.write_text(format_notes("0.1.1", NOTES, "2026-11-22"), encoding="utf-8")
    (release_root / "CHANGELOG.md").write_text(
        generate_history(release_root), encoding="utf-8"
    )

    with pytest.raises(ValueError, match="no published tag"):
        verify_history(release_root)


def test_entire_published_history_directory_cannot_be_deleted(release_root: Path) -> None:
    prepare_release(release_root, "minor", "2026-11-22")
    git(release_root, "add", ".")
    git(release_root, "commit", "-qm", "release")
    git(release_root, "tag", "v0.1.1")
    shutil.rmtree(release_root / "docs/changelog/releases")

    with pytest.raises(ValueError, match="Published changelog cannot change"):
        verify_history(release_root)
