from pathlib import Path

import pytest

from versioning import bump_version, check_version, main, next_version


@pytest.fixture
def version_root(tmp_path: Path) -> Path:
    (tmp_path / "src/sabl_pdf").mkdir(parents=True)
    (tmp_path / "installer").mkdir()
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "sabl-pdf"\nversion = "0.1.9"\n', encoding="utf-8")
    (tmp_path / "src/sabl_pdf/__init__.py").write_text('__version__ = "0.1.9"\n', encoding="utf-8")
    (tmp_path / "installer/SABL-PDF.iss").write_text('#define AppVersion "0.1.9"\n', encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize(
    ("part", "expected"),
    [("minor", "0.1.10"), ("secondary", "0.2.0"), ("major", "1.0.0")],
)
def test_next_version(part: str, expected: str) -> None:
    current = "0.1.9"

    new_version = next_version(current, part)

    assert new_version == expected


def test_default_bump_updates_all_version_sources(version_root: Path) -> None:
    project = version_root / "pyproject.toml"
    package = version_root / "src/sabl_pdf/__init__.py"
    installer = version_root / "installer/SABL-PDF.iss"

    version = bump_version(version_root)

    assert version == "0.1.10"
    assert 'version = "0.1.10"' in project.read_text(encoding="utf-8")
    assert '__version__ = "0.1.10"' in package.read_text(encoding="utf-8")
    assert '#define AppVersion "0.1.10"' in installer.read_text(encoding="utf-8")


def test_consecutive_build_bumps_increment_once_each(version_root: Path) -> None:
    first = bump_version(version_root)

    second = bump_version(version_root)

    assert first == "0.1.10"
    assert second == "0.1.11"


def test_check_does_not_change_version(version_root: Path) -> None:
    old_contents = (version_root / "pyproject.toml").read_bytes()

    checked_version = check_version(version_root, "v0.1.9")

    assert checked_version == "0.1.9"
    assert (version_root / "pyproject.toml").read_bytes() == old_contents


def test_check_rejects_mismatched_tag(version_root: Path) -> None:
    with pytest.raises(ValueError, match="does not match"):
        check_version(version_root, "v0.1.8")


def test_bump_rejects_inconsistent_sources_without_writing(version_root: Path) -> None:
    installer = version_root / "installer/SABL-PDF.iss"
    project = version_root / "pyproject.toml"
    installer.write_text('#define AppVersion "0.1.8"\n', encoding="utf-8")
    original = project.read_bytes()

    with pytest.raises(ValueError, match="must match"):
        bump_version(version_root)

    assert project.read_bytes() == original
    assert installer.read_text(encoding="utf-8") == '#define AppVersion "0.1.8"\n'


def test_bump_rejects_invalid_version_without_writing(version_root: Path) -> None:
    project = version_root / "pyproject.toml"
    project.write_text('[project]\nname = "sabl-pdf"\nversion = "0.01.9"\n', encoding="utf-8")
    original = project.read_bytes()

    with pytest.raises(ValueError, match="Invalid version"):
        bump_version(version_root)

    assert project.read_bytes() == original


def test_bump_rejects_unknown_component(version_root: Path) -> None:
    with pytest.raises(ValueError, match="Unknown version component"):
        bump_version(version_root, "release")


def test_cli_supports_secondary_flag(version_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    result = main(["bump", "--part", "secondary"], root=version_root)
    output = capsys.readouterr()

    assert result == 0
    assert output.out.strip() == "0.2.0"
    assert check_version(version_root) == "0.2.0"


def test_cli_rejects_invalid_release_tag(version_root: Path) -> None:
    with pytest.raises(SystemExit) as failure:
        main(["check", "--expected-tag", "v0.1.10"], root=version_root)

    assert failure.value.code == 2
