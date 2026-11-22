from pathlib import Path
from unittest.mock import Mock

import pytest

from sabl_pdf import main as startup


def test_main_starts_without_a_document(monkeypatch: pytest.MonkeyPatch) -> None:
    application = Mock()
    application.exec.return_value = 0
    window = Mock()
    monkeypatch.setattr(startup, "QApplication", Mock(return_value=application))
    monkeypatch.setattr(startup, "MainWindow", Mock(return_value=window))
    monkeypatch.setattr(startup.sys, "argv", ["sabl-pdf"])

    result = startup.main()

    assert result == 0
    application.setApplicationName.assert_called_once_with("Simple PDF")
    window.show.assert_called_once_with()
    window.open_path.assert_not_called()


def test_main_opens_command_line_document(monkeypatch: pytest.MonkeyPatch) -> None:
    application = Mock()
    application.exec.return_value = 0
    window = Mock()
    monkeypatch.setattr(startup, "QApplication", Mock(return_value=application))
    monkeypatch.setattr(startup, "MainWindow", Mock(return_value=window))
    monkeypatch.setattr(startup.sys, "argv", ["sabl-pdf", "input.pdf"])

    result = startup.main()

    assert result == 0
    window.open_path.assert_called_once_with(Path("input.pdf"))


def test_main_uses_bundled_ocr_data(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    tessdata = tmp_path / "tessdata"
    tessdata.mkdir()
    application = Mock()
    application.exec.return_value = 0
    monkeypatch.setattr(startup, "QApplication", Mock(return_value=application))
    monkeypatch.setattr(startup, "MainWindow", Mock())
    monkeypatch.setattr(startup.sys, "argv", ["sabl-pdf"])
    monkeypatch.setattr(startup.sys, "executable", str(tmp_path / "Simple PDF.exe"))
    monkeypatch.setattr(startup.sys, "frozen", True, raising=False)
    monkeypatch.delenv("TESSDATA_PREFIX", raising=False)

    result = startup.main()

    assert result == 0
    assert startup.os.environ["TESSDATA_PREFIX"] == str(tessdata)
