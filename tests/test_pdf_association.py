from pathlib import Path
from unittest.mock import Mock, call

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_installer_refreshes_pdf_associations() -> None:
    installer = (ROOT / "installer" / "SABL-PDF.iss").read_text(encoding="utf-8")

    assert "ChangesAssociations=yes" in installer
    assert 'Subkey: "Software\\Classes\\.pdf\\OpenWithProgids"' in installer
    assert 'ValueName: "SABL.PDF"' in installer
    assert 'Subkey: "Software\\Classes\\Applications\\Simple PDF.exe\\SupportedTypes"' in installer
    assert 'ValueName: ".pdf"' in installer


def test_installer_registers_a_per_user_default_app_without_forcing_it() -> None:
    installer = (ROOT / "installer" / "SABL-PDF.iss").read_text(encoding="utf-8")

    assert 'Root: HKCU; Subkey: "Software\\RegisteredApplications"' in installer
    assert 'ValueName: "Simple PDF"' in installer
    assert 'Subkey: "Software\\SABL PDF\\Capabilities\\FileAssociations"' in installer
    assert "UserChoice" not in installer


def test_windows_settings_link_targets_registered_app(monkeypatch) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QUrl
    from sabl_pdf.ui import default_apps

    launcher = Mock(return_value=True)
    monkeypatch.setattr(default_apps.sys, "platform", "win32")

    result = default_apps.open_default_apps_settings(launcher)

    assert result is True
    launcher.assert_called_once_with(
        QUrl("ms-settings:defaultapps?registeredAppUser=Simple%20PDF")
    )


def test_windows_settings_link_falls_back_to_general_page(monkeypatch) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QUrl
    from sabl_pdf.ui import default_apps

    launcher = Mock(side_effect=[False, True])
    monkeypatch.setattr(default_apps.sys, "platform", "win32")

    result = default_apps.open_default_apps_settings(launcher)

    assert result is True
    assert launcher.call_args_list == [
        call(QUrl("ms-settings:defaultapps?registeredAppUser=Simple%20PDF")),
        call(QUrl("ms-settings:defaultapps")),
    ]


def test_settings_link_does_not_launch_outside_windows(monkeypatch) -> None:
    pytest.importorskip("PySide6")
    from sabl_pdf.ui import default_apps

    launcher = Mock()
    monkeypatch.setattr(default_apps.sys, "platform", "linux")

    result = default_apps.open_default_apps_settings(launcher)

    assert result is False
    launcher.assert_not_called()


def test_welcome_screen_default_button_opens_windows_settings(monkeypatch) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QPushButton
    from sabl_pdf.ui import window as window_module

    application = QApplication.instance() or QApplication([])
    launch = Mock(return_value=True)
    monkeypatch.setattr(window_module, "open_default_apps_settings", launch)
    window = window_module.MainWindow()
    button = window.welcome.findChild(QPushButton, "welcome_default_pdf")

    button.click()

    assert application is not None
    assert button.text() == "Set as default PDF app"
    launch.assert_called_once_with()
    window.close()


def test_file_menu_default_action_is_available_with_document(sample_pdf, monkeypatch) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication
    from sabl_pdf.ui import window as window_module

    application = QApplication.instance() or QApplication([])
    launch = Mock(return_value=True)
    monkeypatch.setattr(window_module, "open_default_apps_settings", launch)
    window = window_module.MainWindow()
    window.open_path(sample_pdf)

    window.default_pdf_action.trigger()

    assert application is not None
    assert window.default_pdf_action.isEnabled()
    launch.assert_called_once_with()
    window.close()


def test_failed_windows_settings_launch_shows_guidance(monkeypatch) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QMessageBox
    from sabl_pdf.ui import window as window_module

    application = QApplication.instance() or QApplication([])
    launch = Mock(return_value=False)
    warning = Mock()
    monkeypatch.setattr(window_module, "open_default_apps_settings", launch)
    monkeypatch.setattr(QMessageBox, "warning", warning)
    window = window_module.MainWindow()

    window.default_pdf_action.trigger()

    assert application is not None
    launch.assert_called_once_with()
    assert "Could not open Windows Default apps" in warning.call_args.args[2]
    assert "Simple PDF" in warning.call_args.args[2]
    window.close()
