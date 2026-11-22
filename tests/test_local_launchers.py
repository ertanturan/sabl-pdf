from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_windows_launchers_target_existing_scripts() -> None:
    for name in ("run", "test", "build"):
        command = (ROOT / f"{name}.cmd").read_text(encoding="utf-8")

        assert f"scripts\\{name}.ps1" in command
        assert "powershell.exe -NoProfile -ExecutionPolicy Bypass -File" in command
        assert (ROOT / "scripts" / f"{name}.ps1").is_file()


def test_tests_use_offscreen_qt_and_restore_previous_setting() -> None:
    script = (ROOT / "scripts" / "test.ps1").read_text(encoding="utf-8")

    assert "$env:QT_QPA_PLATFORM = 'offscreen'" in script
    assert "SetEnvironmentVariable('QT_QPA_PLATFORM', $previousPlatform, 'Process')" in script


def test_build_uses_test_script() -> None:
    script = (ROOT / "scripts" / "build.ps1").read_text(encoding="utf-8")

    assert "(Join-Path $PSScriptRoot 'test.ps1')" in script


def test_pyright_runs_after_existing_checks() -> None:
    import tomllib

    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    script = (ROOT / "scripts" / "test.ps1").read_text(encoding="utf-8")

    assert any(
        dependency.startswith("pyright")
        for dependency in project["project"]["optional-dependencies"]["dev"]
    )
    assert project["tool"]["pyright"]["include"] == ["src"]
    assert project["tool"]["pyright"]["typeCheckingMode"] == "basic"

    ci_steps = [
        "python -m pip install -e '.[dev]'",
        "python -m pytest -q",
        "python -m compileall -q src",
        "python -m ruff check .",
        "python -m pyright",
    ]
    local_steps = [
        "Invoke-Check -Arguments @('-m', 'pytest', '-q')",
        "Invoke-Check -Arguments @('-m', 'compileall', '-q', 'src')",
        "Invoke-Check -Arguments @('-m', 'ruff', 'check', '.')",
        "Invoke-Check -Arguments @('-m', 'pyright')",
    ]

    assert all(step in workflow for step in ci_steps)
    assert all(step in script for step in local_steps)
    assert [workflow.index(step) for step in ci_steps] == sorted(workflow.index(step) for step in ci_steps)
    assert [script.index(step) for step in local_steps] == sorted(script.index(step) for step in local_steps)
