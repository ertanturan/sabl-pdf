import os
from unittest.mock import Mock

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

NEW_RELEASE = b'{"tag_name":"v9.0.0","body":"## New features\\n- Faster pages.","draft":false,"prerelease":false}'
CURRENT_RELEASE = b'{"tag_name":"v1.0.0","body":"## New features\\n- Existing features.","draft":false,"prerelease":false}'


def test_update_actions_are_accessible_without_a_pdf(tmp_path) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication

    from sabl_pdf.ui.window import MainWindow

    application = QApplication.instance() or QApplication([])
    settings = QSettings(str(tmp_path / "menu.ini"), QSettings.Format.IniFormat)
    window = MainWindow(settings=settings)

    assert application is not None
    assert window.workspace.currentWidget() is window.welcome
    assert window.check_updates_action.isEnabled()
    assert window.auto_updates_action.isChecked()
    assert window.whats_new_action.isEnabled()
    assert window.update_notice.isHidden()
    window.close()


def test_manual_update_check_uses_public_github_even_when_auto_checks_are_off(tmp_path) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication

    from sabl_pdf.ui.window import MainWindow

    application = QApplication.instance() or QApplication([])
    settings = QSettings(str(tmp_path / "manual.ini"), QSettings.Format.IniFormat)
    settings.setValue("updates/automatic", False)
    window = MainWindow(settings=settings)
    reply = Mock()
    network = Mock()
    network.get.return_value = reply
    window._update_manager = network

    window.check_for_updates()

    request = network.get.call_args.args[0]
    assert application is not None
    assert request.url().toString() == "https://api.github.com/repos/ertanturan/sabl-pdf/releases/latest"
    assert window._pending_update_reply is reply
    assert not window.check_updates_action.isEnabled()
    reply.finished.connect.assert_called_once()
    window.close()


def test_auto_check_starts_when_never_checked(tmp_path) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication

    from sabl_pdf.ui.window import MainWindow

    application = QApplication.instance() or QApplication([])
    settings = QSettings(str(tmp_path / "first-check.ini"), QSettings.Format.IniFormat)
    window = MainWindow(settings=settings)
    network = Mock()
    network.get.return_value = Mock()
    window._update_manager = network

    window.check_for_updates_automatically()

    assert application is not None
    network.get.assert_called_once()
    assert not window.check_updates_action.isEnabled()
    window.close()


def test_recent_successful_check_does_not_repeat_on_startup(tmp_path) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication
    from time import time

    from sabl_pdf.ui.window import MainWindow

    application = QApplication.instance() or QApplication([])
    settings = QSettings(str(tmp_path / "recent.ini"), QSettings.Format.IniFormat)
    settings.setValue("updates/last_successful_check", time())
    window = MainWindow(settings=settings)
    network = Mock()
    window._update_manager = network

    window.check_for_updates_automatically()

    assert application is not None
    network.get.assert_not_called()
    assert window.check_updates_action.isEnabled()
    window.close()


def test_disabling_auto_checks_does_not_hide_manual_actions(tmp_path) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication

    from sabl_pdf.ui.window import MainWindow

    application = QApplication.instance() or QApplication([])
    settings = QSettings(str(tmp_path / "disabled.ini"), QSettings.Format.IniFormat)
    window = MainWindow(settings=settings)
    network = Mock()
    window._update_manager = network

    window.auto_updates_action.setChecked(False)
    window.check_for_updates_automatically()

    assert application is not None
    assert settings.value("updates/automatic", type=bool) is False
    network.get.assert_not_called()
    assert window.check_updates_action.isEnabled()
    assert window.whats_new_action.isEnabled()
    window.close()


def test_successful_auto_check_shows_persistent_update_indicator(tmp_path) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QSettings
    from PySide6.QtNetwork import QNetworkReply
    from PySide6.QtWidgets import QApplication

    from sabl_pdf.ui.window import MainWindow

    application = QApplication.instance() or QApplication([])
    settings = QSettings(str(tmp_path / "newer.ini"), QSettings.Format.IniFormat)
    window = MainWindow(settings=settings)
    window.show()
    reply = Mock()
    reply.error.return_value = QNetworkReply.NetworkError.NoError
    reply.readAll.return_value = NEW_RELEASE
    window._pending_update_reply = reply
    window.check_updates_action.setEnabled(False)

    window._finish_update_check(reply)

    assert application is not None
    assert window._available_update.version == "9.0.0"
    assert window.update_notice.text() == "Update available: v9.0.0"
    assert window.update_notice.isVisible()
    assert window.check_updates_action.isEnabled()
    assert settings.value("updates/last_successful_check", type=float) > 0
    assert settings.value("updates/latest_release_json", type=str) == NEW_RELEASE.decode("utf-8")
    reply.deleteLater.assert_called_once()
    window.close()


def test_cached_update_is_visible_on_next_launch_and_can_be_opened(tmp_path, monkeypatch) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication

    from sabl_pdf.ui.update_available_dialog import UpdateAvailableDialog
    from sabl_pdf.ui.window import MainWindow

    settings = QSettings(str(tmp_path / "cached.ini"), QSettings.Format.IniFormat)
    settings.setValue("updates/latest_release_json", NEW_RELEASE.decode("utf-8"))
    application = QApplication.instance() or QApplication([])
    opened = Mock(return_value=0)
    monkeypatch.setattr(UpdateAvailableDialog, "exec", opened)
    window = MainWindow(settings=settings)
    window.show()

    window.update_notice.click()

    assert application is not None
    assert window.update_notice.isVisible()
    opened.assert_called_once()
    assert window.whats_new_action.isEnabled()
    window.close()


def test_current_release_hides_previous_update_notice(tmp_path) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QSettings
    from PySide6.QtNetwork import QNetworkReply
    from PySide6.QtWidgets import QApplication

    from sabl_pdf.ui.window import MainWindow

    settings = QSettings(str(tmp_path / "current.ini"), QSettings.Format.IniFormat)
    settings.setValue("updates/latest_release_json", NEW_RELEASE.decode("utf-8"))
    application = QApplication.instance() or QApplication([])
    window = MainWindow(settings=settings)
    reply = Mock()
    reply.error.return_value = QNetworkReply.NetworkError.NoError
    reply.readAll.return_value = CURRENT_RELEASE

    window._finish_update_check(reply)

    assert application is not None
    assert window._available_update is None
    assert window.update_notice.isHidden()
    window.close()


def test_automatic_network_failure_is_silent_and_preserves_cached_notice(tmp_path, monkeypatch) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QSettings
    from PySide6.QtNetwork import QNetworkReply
    from PySide6.QtWidgets import QApplication, QMessageBox

    from sabl_pdf.ui.window import MainWindow

    settings = QSettings(str(tmp_path / "offline.ini"), QSettings.Format.IniFormat)
    settings.setValue("updates/latest_release_json", NEW_RELEASE.decode("utf-8"))
    application = QApplication.instance() or QApplication([])
    window = MainWindow(settings=settings)
    warning = Mock()
    monkeypatch.setattr(QMessageBox, "warning", warning)
    reply = Mock()
    reply.error.return_value = QNetworkReply.NetworkError.ConnectionRefusedError

    window._finish_update_check(reply)

    assert application is not None
    warning.assert_not_called()
    assert window.update_notice.text() == "Update available: v9.0.0"
    assert settings.value("updates/last_successful_check") is None
    window.close()


def test_manual_network_failure_reports_error(tmp_path, monkeypatch) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QSettings
    from PySide6.QtNetwork import QNetworkReply
    from PySide6.QtWidgets import QApplication, QMessageBox

    from sabl_pdf.ui.window import MainWindow

    application = QApplication.instance() or QApplication([])
    settings = QSettings(str(tmp_path / "error.ini"), QSettings.Format.IniFormat)
    window = MainWindow(settings=settings)
    warning = Mock()
    monkeypatch.setattr(QMessageBox, "warning", warning)
    reply = Mock()
    reply.error.return_value = QNetworkReply.NetworkError.ConnectionRefusedError
    reply.errorString.return_value = "Network unavailable"
    window._manual_update_check = True

    window._finish_update_check(reply)

    assert application is not None
    warning.assert_called_once_with(window, "Update check failed", "Network unavailable")
    window.close()


def test_corrupted_cached_release_does_not_show_update(tmp_path) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication

    from sabl_pdf.ui.window import MainWindow

    application = QApplication.instance() or QApplication([])
    settings = QSettings(str(tmp_path / "bad.ini"), QSettings.Format.IniFormat)
    settings.setValue("updates/latest_release_json", "{")
    window = MainWindow(settings=settings)

    assert application is not None
    assert window.update_notice.isHidden()
    assert window.whats_new_action.isEnabled()
    window.close()


def test_update_dialog_displays_remote_notes_without_installer_execution() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QDialogButtonBox, QTextBrowser

    from sabl_pdf.services.updates import AvailableUpdate
    from sabl_pdf.ui.update_available_dialog import UpdateAvailableDialog

    application = QApplication.instance() or QApplication([])
    dialog = UpdateAvailableDialog(
        "1.0.0",
        AvailableUpdate(
            "9.0.0",
            "## New features\n- Faster pages.",
            "https://github.com/ertanturan/sabl-pdf/releases/tag/v9.0.0",
        ),
    )
    viewer = dialog.findChild(QTextBrowser, "available_update_notes")
    buttons = dialog.findChild(QDialogButtonBox)

    assert application is not None
    assert dialog.windowTitle() == "Simple PDF update available"
    assert viewer is not None
    assert "Faster pages." in viewer.toPlainText()
    assert not viewer.openLinks()
    assert buttons.button(QDialogButtonBox.StandardButton.Close) is not None
    dialog.close()


def test_manual_success_shows_release_notes_and_keeps_update_indicator(tmp_path, monkeypatch) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QSettings
    from PySide6.QtNetwork import QNetworkReply
    from PySide6.QtWidgets import QApplication

    from sabl_pdf.ui.update_available_dialog import UpdateAvailableDialog
    from sabl_pdf.ui.window import MainWindow

    application = QApplication.instance() or QApplication([])
    settings = QSettings(str(tmp_path / "manual-success.ini"), QSettings.Format.IniFormat)
    window = MainWindow(settings=settings)
    opened = Mock(return_value=0)
    monkeypatch.setattr(UpdateAvailableDialog, "exec", opened)
    reply = Mock()
    reply.error.return_value = QNetworkReply.NetworkError.NoError
    reply.readAll.return_value = NEW_RELEASE
    window._manual_update_check = True

    window._finish_update_check(reply)

    assert application is not None
    opened.assert_called_once()
    assert window.update_notice.text() == "Update available: v9.0.0"
    assert not window.update_notice.isHidden()
    window.close()


def test_invalid_automatic_response_does_not_show_a_popup(tmp_path, monkeypatch) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QSettings
    from PySide6.QtNetwork import QNetworkReply
    from PySide6.QtWidgets import QApplication, QMessageBox

    from sabl_pdf.ui.window import MainWindow

    application = QApplication.instance() or QApplication([])
    settings = QSettings(str(tmp_path / "invalid.ini"), QSettings.Format.IniFormat)
    window = MainWindow(settings=settings)
    warning = Mock()
    monkeypatch.setattr(QMessageBox, "warning", warning)
    reply = Mock()
    reply.error.return_value = QNetworkReply.NetworkError.NoError
    reply.readAll.return_value = b'{bad response'

    window._finish_update_check(reply)

    assert application is not None
    warning.assert_not_called()
    assert window.update_notice.isHidden()
    assert settings.value("updates/last_successful_check") is None
    window.close()


def test_update_now_accepts_dialog_and_github_option_remains_available(monkeypatch) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QDesktopServices
    from PySide6.QtWidgets import QApplication, QDialog, QPushButton

    from sabl_pdf.services.updates import AvailableUpdate
    from sabl_pdf.ui.update_available_dialog import UpdateAvailableDialog

    application = QApplication.instance() or QApplication([])
    release_url = "https://github.com/ertanturan/sabl-pdf/releases/tag/v9.0.0"
    dialog = UpdateAvailableDialog("1.0.0", AvailableUpdate("9.0.0", "", release_url))
    install = dialog.findChild(QPushButton, "install_update_button")
    github = dialog.findChild(QPushButton, "view_release_button")
    opened = Mock(return_value=True)
    monkeypatch.setattr(QDesktopServices, "openUrl", opened)

    github.click()
    install.click()

    assert application is not None
    assert install.text() == "Update now"
    assert github.text() == "View on GitHub"
    opened.assert_called_once_with(QUrl(release_url))
    assert dialog.result() == QDialog.DialogCode.Accepted
    dialog.close()


def test_source_run_cannot_launch_installer_but_can_view_github() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QPushButton

    from sabl_pdf.services.updates import AvailableUpdate
    from sabl_pdf.ui.update_available_dialog import UpdateAvailableDialog

    application = QApplication.instance() or QApplication([])
    dialog = UpdateAvailableDialog(
        "1.0.0",
        AvailableUpdate("9.0.0", "", "https://github.com/ertanturan/sabl-pdf/releases/tag/v9.0.0"),
        can_install=False,
    )
    install = dialog.findChild(QPushButton, "install_update_button")
    github = dialog.findChild(QPushButton, "view_release_button")

    assert application is not None
    assert not install.isEnabled()
    assert github.isEnabled()
    dialog.close()
