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
