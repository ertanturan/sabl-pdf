import tomllib
import os
from pathlib import Path
from unittest.mock import Mock

import pytest


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]


def test_qt_application_uses_simple_pdf_name(monkeypatch) -> None:
    pytest.importorskip("PySide6")
    from sabl_pdf import main as main_module

    application = Mock()
    application.exec.return_value = 0
    window = Mock()
    monkeypatch.setattr(main_module, "QApplication", Mock(return_value=application))
    monkeypatch.setattr(main_module, "MainWindow", Mock(return_value=window))
    monkeypatch.setattr(main_module.sys, "argv", ["simple-pdf"])

    result = main_module.main()

    assert result == 0
    application.setApplicationName.assert_called_once_with("Simple PDF")
    window.show.assert_called_once_with()


def test_welcome_screen_uses_simple_pdf_title() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication
    from sabl_pdf.ui.window import MainWindow

    application = QApplication.instance() or QApplication([])
    window = MainWindow()
    heading = window.welcome.layout().itemAt(0).widget()

    assert application is not None
    assert window.windowTitle() == "Simple PDF"
    assert heading.text() == "Simple PDF"
    window.close()


def test_document_window_uses_simple_pdf_title(sample_pdf: Path) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication
    from sabl_pdf.ui.window import MainWindow

    application = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.open_path(sample_pdf)

    assert application is not None
    assert window.windowTitle() == "Simple PDF | sample.pdf"
    window.close()


def test_build_uses_simple_pdf_executable_name() -> None:
    build = (ROOT / "scripts/build.ps1").read_text(encoding="utf-8")

    assert "--name 'Simple PDF'" in build
    assert "'dist/Simple PDF/tessdata'" in build


def test_installer_uses_simple_pdf_public_name() -> None:
    installer = (ROOT / "installer/SABL-PDF.iss").read_text(encoding="utf-8")

    assert '#define AppName "Simple PDF"' in installer
    assert 'UninstallDisplayName=Simple PDF' in installer
    assert "OutputBaseFilename=Simple-PDF-Setup-" in installer
    assert 'ValueData: "Simple PDF Document"' in installer


def test_installer_removes_old_public_registration_on_upgrade() -> None:
    installer = (ROOT / "installer/SABL-PDF.iss").read_text(encoding="utf-8")

    assert 'ValueName: "SABL PDF"; Flags: deletevalue' in installer
    assert 'Subkey: "Software\\Classes\\Applications\\SABL PDF.exe"; Flags: deletekey' in installer
    assert 'Name: "{app}\\SABL PDF.exe"' in installer
    assert 'ValueName: "SABL.PDF"' in installer


def test_release_workflow_smoke_tests_simple_pdf_name() -> None:
    workflow = (ROOT / ".github/workflows/installer.yml").read_text(encoding="utf-8")

    assert '$filename = "Simple-PDF-Setup-$env:TAG-x64.exe"' in workflow
    assert "'Simple PDF.exe'" in workflow
    assert '--title "Simple PDF $env:TAG"' in workflow


def test_console_command_offers_simple_pdf_with_legacy_alias() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    scripts = project["project"]["scripts"]

    assert scripts["simple-pdf"] == "sabl_pdf.main:main"
    assert scripts["sabl-pdf"] == "sabl_pdf.main:main"
