from pathlib import Path
import tomllib

from sabl_pdf import __version__


def test_version_is_defined() -> None:
    project_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    project = tomllib.loads(project_path.read_text(encoding="utf-8"))

    version = __version__

    assert version == project["project"]["version"]
