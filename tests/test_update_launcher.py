from pathlib import Path
from unittest.mock import Mock

import pytest

from sabl_pdf.services.update_launcher import launch_verified_installer


def test_launch_uses_detached_windows_installer_script(tmp_path: Path, monkeypatch) -> None:
    installer = tmp_path / "update.exe"
    app = tmp_path / "Simple PDF.exe"
    installer.write_bytes(b"verified")
    app.write_bytes(b"app")
    launch = Mock()
    monkeypatch.setattr("sabl_pdf.services.update_launcher.subprocess.Popen", launch)

    launch_verified_installer(installer, app, 1234, "1.0.4")

    script = tmp_path / "install-update.ps1"
    args = launch.call_args.args[0]
    assert script.is_file()
    assert "Wait-Process" in script.read_text(encoding="utf-8")
    assert "'/SILENT'" in script.read_text(encoding="utf-8")
    assert "'/SUPPRESSMSGBOXES'" not in script.read_text(encoding="utf-8")
    assert "'/NOCLOSEAPPLICATIONS'" in script.read_text(encoding="utf-8")
    assert '/DIR="' in script.read_text(encoding="utf-8")
    assert '/LOG="' in script.read_text(encoding="utf-8")
    assert "Get-ItemProperty" in script.read_text(encoding="utf-8")
    assert "$installed.DisplayVersion -ne $ExpectedVersion" in script.read_text(encoding="utf-8")
    assert "if ($completed)" in script.read_text(encoding="utf-8")
    assert "Start-Process -FilePath $AppPath" in script.read_text(encoding="utf-8")
    assert args[-8:] == ["-Installer", str(installer), "-AppPath", str(app), "-ParentId", "1234", "-ExpectedVersion", "1.0.4"]
    launch.assert_called_once()


def test_launcher_rejects_missing_verified_installer(tmp_path: Path) -> None:
    app = tmp_path / "Simple PDF.exe"
    app.write_bytes(b"app")

    with pytest.raises(FileNotFoundError, match="verified installer"):
        launch_verified_installer(tmp_path / "missing.exe", app, 42, "1.0.4")

    assert not (tmp_path / "install-update.ps1").exists()


def test_launcher_cleans_script_when_powershell_cannot_start(tmp_path: Path, monkeypatch) -> None:
    installer = tmp_path / "update.exe"
    app = tmp_path / "Simple PDF.exe"
    installer.write_bytes(b"verified")
    app.write_bytes(b"app")
    launch = Mock(side_effect=OSError("PowerShell unavailable"))
    monkeypatch.setattr("sabl_pdf.services.update_launcher.subprocess.Popen", launch)

    with pytest.raises(OSError, match="PowerShell unavailable"):
        launch_verified_installer(installer, app, 42, "1.0.4")

    assert not (tmp_path / "install-update.ps1").exists()
    assert installer.exists()


def test_launcher_rejects_invalid_target_version(tmp_path: Path, monkeypatch) -> None:
    installer = tmp_path / "update.exe"
    app = tmp_path / "Simple PDF.exe"
    installer.write_bytes(b"verified")
    app.write_bytes(b"app")
    launch = Mock()
    monkeypatch.setattr("sabl_pdf.services.update_launcher.subprocess.Popen", launch)

    with pytest.raises(ValueError, match="version is invalid"):
        launch_verified_installer(installer, app, 42, "1.0.4-malicious")

    launch.assert_not_called()
    assert not (tmp_path / "install-update.ps1").exists()
