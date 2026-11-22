import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_first_launch_does_not_show_an_upgrade_notice(tmp_path, monkeypatch) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication

    from sabl_pdf import __version__
    from sabl_pdf.ui.whats_new_dialog import WhatsNewDialog
    from sabl_pdf.ui.window import MainWindow

    opened = []
    monkeypatch.setattr(WhatsNewDialog, "exec", lambda dialog: opened.append(dialog))
    settings = QSettings(str(tmp_path / "first.ini"), QSettings.Format.IniFormat)
    application = QApplication.instance() or QApplication([])
    window = MainWindow(settings=settings)

    application.processEvents()

    assert opened == []
    assert settings.value("releases/last_launched_version") == __version__
    assert window.whats_new_action.isEnabled()
    window.close()


def test_upgraded_version_opens_notes_and_keeps_help_action(tmp_path, monkeypatch) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication

    from sabl_pdf import __version__
    from sabl_pdf.ui.whats_new_dialog import WhatsNewDialog
    from sabl_pdf.ui.window import MainWindow

    opened = []
    monkeypatch.setattr(WhatsNewDialog, "exec", lambda dialog: opened.append(dialog))
    settings = QSettings(str(tmp_path / "upgraded.ini"), QSettings.Format.IniFormat)
    settings.setValue("releases/last_launched_version", "0.0.1")
    application = QApplication.instance() or QApplication([])
    window = MainWindow(settings=settings)

    application.processEvents()
    window.whats_new_action.trigger()

    assert len(opened) == 2
    assert settings.value("releases/last_launched_version") == __version__
    assert window.whats_new_action.isEnabled()
    window.close()


def test_same_version_does_not_repeat_automatic_notice(tmp_path, monkeypatch) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication

    from sabl_pdf import __version__
    from sabl_pdf.ui.whats_new_dialog import WhatsNewDialog
    from sabl_pdf.ui.window import MainWindow

    opened = []
    monkeypatch.setattr(WhatsNewDialog, "exec", lambda dialog: opened.append(dialog))
    settings = QSettings(str(tmp_path / "current.ini"), QSettings.Format.IniFormat)
    settings.setValue("releases/last_launched_version", __version__)
    application = QApplication.instance() or QApplication([])
    window = MainWindow(settings=settings)

    application.processEvents()

    assert opened == []
    assert window.whats_new_action.isEnabled()
    window.close()
