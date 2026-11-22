from pathlib import Path

import pytest
import tomllib

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("name", ("run", "test", "build"))
def test_windows_launchers_target_existing_scripts(name: str) -> None:
    path = ROOT / f"{name}.cmd"

    command = path.read_text(encoding="utf-8")

    assert f"scripts\\{name}.ps1" in command
    assert "powershell.exe -NoProfile -ExecutionPolicy Bypass -File" in command
    assert (ROOT / "scripts" / f"{name}.ps1").is_file()


def test_tests_use_offscreen_qt_and_restore_previous_setting() -> None:
    script_path = ROOT / "scripts" / "test.ps1"

    script = script_path.read_text(encoding="utf-8")

    assert "$env:QT_QPA_PLATFORM = 'offscreen'" in script
    assert "SetEnvironmentVariable('QT_QPA_PLATFORM', $previousPlatform, 'Process')" in script


def test_build_uses_test_script() -> None:
    script_path = ROOT / "scripts" / "build.ps1"

    script = script_path.read_text(encoding="utf-8")

    assert "(Join-Path $PSScriptRoot 'test.ps1')" in script


def test_pyright_project_configuration() -> None:
    project_path = ROOT / "pyproject.toml"

    project = tomllib.loads(project_path.read_text(encoding="utf-8"))

    assert "pyright>=1.1.400,<2" in project["project"]["optional-dependencies"]["dev"]
    assert project["tool"]["pyright"]["include"] == ["src"]
    assert project["tool"]["pyright"]["typeCheckingMode"] == "basic"


def test_ci_runs_coverage_and_static_checks_in_order() -> None:
    workflow_path = ROOT / ".github" / "workflows" / "ci.yml"
    install = "python -m pip install -e '.[dev]'"
    test = "python -m pytest -q --cov=sabl_pdf --cov-report=term-missing --cov-fail-under=80"
    compile_python = "python -m compileall -q src"
    lint = "python -m ruff check ."
    type_check = "python -m pyright"

    workflow = workflow_path.read_text(encoding="utf-8")

    assert install in workflow
    assert test in workflow
    assert compile_python in workflow
    assert lint in workflow
    assert type_check in workflow
    assert workflow.index(install) < workflow.index(test)
    assert workflow.index(test) < workflow.index(compile_python)
    assert workflow.index(compile_python) < workflow.index(lint)
    assert workflow.index(lint) < workflow.index(type_check)


def test_windows_launcher_runs_coverage_and_static_checks_in_order() -> None:
    script_path = ROOT / "scripts" / "test.ps1"
    test = "Invoke-Check -Arguments @('-m', 'pytest', '-q', '--cov=sabl_pdf', '--cov-report=term-missing', '--cov-fail-under=80')"
    compile_python = "Invoke-Check -Arguments @('-m', 'compileall', '-q', 'src')"
    lint = "Invoke-Check -Arguments @('-m', 'ruff', 'check', '.')"
    type_check = "Invoke-Check -Arguments @('-m', 'pyright')"

    script = script_path.read_text(encoding="utf-8")

    assert test in script
    assert compile_python in script
    assert lint in script
    assert type_check in script
    assert script.index(test) < script.index(compile_python)
    assert script.index(compile_python) < script.index(lint)
    assert script.index(lint) < script.index(type_check)


def test_build_launcher_forwards_version_options() -> None:
    launcher = (ROOT / "build.cmd").read_text(encoding="utf-8")
    script = (ROOT / "scripts" / "build.ps1").read_text(encoding="utf-8")

    assert 'scripts\\build.ps1" %*' in launcher
    assert "[switch]$Major" in script
    assert "[switch]$Secondary" in script
    assert "[switch]$Minor" in script
    assert "[switch]$NoVersionBump" in script
    assert "versioning.py', 'bump'" in script


def test_github_release_bumps_only_when_triggered_manually() -> None:
    workflow = (ROOT / '.github' / 'workflows' / 'installer.yml').read_text(encoding='utf-8')
    build = (ROOT / 'scripts' / 'build.ps1').read_text(encoding='utf-8')

    assert 'workflow_dispatch:' in workflow
    assert '  push:' not in workflow
    assert 'default: minor' in workflow
    assert '          - secondary' in workflow
    assert '          - major' in workflow
    assert 'scripts/release.py prepare --part $env:BUMP_PART' in workflow
    assert "if ($NoVersionBump -or (-not ($Major -or $Secondary -or $Minor)))" in build


def test_tagged_build_does_not_change_release_version() -> None:
    workflow = (ROOT / ".github" / "workflows" / "installer.yml").read_text(encoding="utf-8")
    script = (ROOT / "scripts" / "build.ps1").read_text(encoding="utf-8")

    assert "run: ./scripts/build.ps1 -NoVersionBump" in workflow
    assert "'--expected-tag', $env:GITHUB_REF_NAME" in script
