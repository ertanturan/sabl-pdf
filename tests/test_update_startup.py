from types import SimpleNamespace
from unittest.mock import Mock

from sabl_pdf import main as app_main


def test_application_schedules_automatic_update_check_after_showing_window(monkeypatch) -> None:
    application = Mock()
    application.exec.return_value = 0
    window = Mock()
    timer = SimpleNamespace(singleShot=Mock())
    monkeypatch.setattr(app_main, "QApplication", Mock(return_value=application))
    monkeypatch.setattr(app_main, "MainWindow", Mock(return_value=window))
    monkeypatch.setattr(app_main, "QTimer", timer)
    monkeypatch.setattr(app_main.sys, "argv", ["sabl-pdf"])

    result = app_main.main()

    assert result == 0
    window.show.assert_called_once_with()
    timer.singleShot.assert_called_once_with(0, window.check_for_updates_automatically)
    application.exec.assert_called_once_with()
