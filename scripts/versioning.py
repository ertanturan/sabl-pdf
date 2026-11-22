from __future__ import annotations

import argparse
from pathlib import Path
import re
import tomllib


ROOT = Path(__file__).resolve().parents[1]
VERSION_PATTERN = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
VERSION_FILES = (
    (Path("pyproject.toml"), re.compile(r'(?m)^version = "(?P<version>[^"]+)"$')),
    (Path("src/sabl_pdf/__init__.py"), re.compile(r'(?m)^__version__ = "(?P<version>[^"]+)"$')),
    (Path("installer/SABL-PDF.iss"), re.compile(r'(?m)^#define AppVersion "(?P<version>[^"]+)"$')),
)


def extract_version(content: str, pattern: re.Pattern[str], path: Path) -> str:
    matches = list(pattern.finditer(content))
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one version declaration in {path}")
    version = matches[0].group("version")
    if VERSION_PATTERN.fullmatch(version) is None:
        raise ValueError(f"Invalid version in {path}: {version}")
    return version


def load_version_files(root: Path) -> tuple[str, dict[Path, str]]:
    contents = {path: (root / path).read_text(encoding="utf-8") for path, _ in VERSION_FILES}
    versions = [extract_version(contents[path], pattern, path) for path, pattern in VERSION_FILES]
    if len(set(versions)) != 1:
        raise ValueError("Project, application and installer versions must match")
    project = tomllib.loads(contents[Path("pyproject.toml")])
    if project["project"]["version"] != versions[0]:
        raise ValueError("Project metadata version does not match the version declaration")
    return versions[0], contents


def next_version(version: str, part: str) -> str:
    if VERSION_PATTERN.fullmatch(version) is None:
        raise ValueError(f"Invalid version: {version}")
    major, secondary, minor = map(int, version.split("."))
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "secondary":
        return f"{major}.{secondary + 1}.0"
    if part == "minor":
        return f"{major}.{secondary}.{minor + 1}"
    raise ValueError(f"Unknown version component: {part}")


def write_version_files(root: Path, previous: str, current: str, contents: dict[Path, str]) -> None:
    for path, pattern in VERSION_FILES:
        updated = pattern.sub(lambda match: match.group().replace(f'"{previous}"', f'"{current}"'), contents[path], count=1)
        (root / path).write_text(updated, encoding="utf-8")


def bump_version(root: Path, part: str = "minor") -> str:
    previous, contents = load_version_files(root)
    current = next_version(previous, part)
    write_version_files(root, previous, current, contents)
    return current


def check_version(root: Path, expected_tag: str | None = None) -> str:
    version, _ = load_version_files(root)
    if expected_tag is not None and expected_tag != f"v{version}":
        raise ValueError(f"Release tag {expected_tag} does not match version v{version}")
    return version


def main(args: list[str] | None = None, root: Path = ROOT) -> int:
    parser = argparse.ArgumentParser(description="Manage the SABL PDF build version")
    commands = parser.add_subparsers(dest="action", required=True)
    bump = commands.add_parser("bump")
    bump.add_argument("--part", choices=("minor", "secondary", "major"), default="minor")
    check = commands.add_parser("check")
    check.add_argument("--expected-tag")
    options = parser.parse_args(args)
    try:
        version = bump_version(root, options.part) if options.action == "bump" else check_version(root, options.expected_tag)
    except (ValueError, OSError, KeyError, tomllib.TOMLDecodeError) as error:
        parser.error(str(error))
    print(version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
