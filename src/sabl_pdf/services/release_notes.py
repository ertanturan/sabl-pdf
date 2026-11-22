from pathlib import Path
import sys

from sabl_pdf import __version__


def release_notes_directory() -> Path:
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root is not None:
        return Path(bundle_root) / "release_notes"
    return Path(__file__).resolve().parents[3] / "docs/changelog/releases"


def load_release_notes(version: str, directory: Path) -> str | None:
    try:
        return (directory / f"v{version}.md").read_text(encoding="utf-8")
    except FileNotFoundError:
        return None


def installed_release_notes() -> str | None:
    return load_release_notes(__version__, release_notes_directory())
