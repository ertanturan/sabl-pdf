import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_whats_new_dialog_displays_version_notes_without_opening_links() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QDialogButtonBox, QTextBrowser

    from sabl_pdf.ui.whats_new_dialog import WhatsNewDialog

    application = QApplication.instance() or QApplication([])
    dialog = WhatsNewDialog("1.2.3", "# v1.2.3\n\n## Bugfixes\n- Fixed page placement.")
    viewer = dialog.findChild(QTextBrowser, "release_notes_text")
    buttons = dialog.findChild(QDialogButtonBox)

    assert application is not None
    assert dialog.windowTitle() == "What's New in Simple PDF v1.2.3"
    assert viewer is not None
    assert "Fixed page placement." in viewer.toPlainText()
    assert not viewer.openLinks()
    assert buttons.button(QDialogButtonBox.StandardButton.Close) is not None
    dialog.close()


def test_whats_new_shows_fallback_when_release_notes_missing() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QTextBrowser

    from sabl_pdf.ui.whats_new_dialog import WhatsNewDialog

    application = QApplication.instance() or QApplication([])
    dialog = WhatsNewDialog("2.0.0", None)
    viewer = dialog.findChild(QTextBrowser, "release_notes_text")

    assert application is not None
    assert viewer is not None
    assert "Simple PDF v2.0.0" in viewer.toPlainText()
    assert "Release notes are unavailable for this version." in viewer.toPlainText()
    dialog.close()


def test_whats_new_can_be_reopened_from_welcome_screen(monkeypatch) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QTextBrowser

    from sabl_pdf.ui.whats_new_dialog import WhatsNewDialog
    from sabl_pdf.ui.window import MainWindow

    dialogs = []
    monkeypatch.setattr(WhatsNewDialog, "exec", lambda dialog: dialogs.append(dialog))
    application = QApplication.instance() or QApplication([])
    window = MainWindow()

    window.whats_new_action.trigger()
    window.whats_new_action.trigger()

    assert application is not None
    assert window.whats_new_action.isEnabled()
    assert window.workspace.currentWidget() is window.welcome
    assert len(dialogs) == 2
    assert "New features" in dialogs[0].findChild(QTextBrowser, "release_notes_text").toPlainText()
    window.close()
