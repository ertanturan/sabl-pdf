import sys
from pathlib import Path

from sabl_pdf.services.release_notes import (
    installed_release_notes,
    load_release_notes,
    release_notes_directory,
)


ROOT = Path(__file__).resolve().parents[1]


def test_loads_only_installed_version_release_notes(tmp_path: Path) -> None:
    (tmp_path / "v1.0.0.md").write_text("# v1.0.0\nFirst release", encoding="utf-8")
    (tmp_path / "v2.0.0.md").write_text("# v2.0.0\nSecond release", encoding="utf-8")

    notes = load_release_notes("1.0.0", tmp_path)

    assert notes == "# v1.0.0\nFirst release"


def test_missing_release_notes_returns_none(tmp_path: Path) -> None:
    (tmp_path / "v2.0.0.md").write_text("# v2.0.0\nSecond release", encoding="utf-8")

    notes = load_release_notes("1.0.0", tmp_path)

    assert notes is None


def test_source_release_notes_directory() -> None:
    directory = release_notes_directory()

    assert directory == ROOT / "docs/changelog/releases"


def test_frozen_release_notes_directory(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

    directory = release_notes_directory()

    assert directory == tmp_path / "release_notes"


def test_current_release_notes_are_available_in_source() -> None:
    notes = installed_release_notes()

    assert notes is not None
    assert "## New features" in notes
    assert "## Bugfixes" in notes


def test_installer_bundles_release_notes_for_offline_use() -> None:
    build_script = (ROOT / "scripts/build.ps1").read_text(encoding="utf-8")

    assert "--add-data 'docs/changelog/releases:release_notes'" in build_script
