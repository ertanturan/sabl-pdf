import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PySide6 = pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication

from sabl_pdf.ui.window import MainWindow


def test_main_window_opens_pdf(sample_pdf) -> None:
    application = QApplication.instance() or QApplication([])
    window = MainWindow()

    window.open_path(sample_pdf)

    assert window.viewer.page_count() == 1
    assert "sample.pdf" in window.windowTitle()
    window.close()
