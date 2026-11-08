import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_main_window_opens_pdf(sample_pdf) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from sabl_pdf.ui.window import MainWindow

    application = QApplication.instance() or QApplication([])
    window = MainWindow()

    window.open_path(sample_pdf)

    assert application is not None
    assert window.viewer.page_count() == 1
    assert "sample.pdf" in window.windowTitle()
    window.close()

def test_scrolls_through_all_pdf_pages(tmp_path) -> None:
    pytest.importorskip("PySide6")
    import fitz
    from PySide6.QtWidgets import QApplication
    from sabl_pdf.ui.window import MainWindow

    path = tmp_path / "many.pdf"
    with fitz.open() as document:
        for number in range(4):
            document.new_page(width=300, height=500).insert_text((30, 30), str(number))
        document.save(path)

    application = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.resize(520, 420)
    window.show()

    window.open_path(path)
    application.processEvents()
    assert len(window.canvas._page_rects) == 4
    assert window.canvas.verticalScrollBar().maximum() > 0

    window.canvas.scroll_to_page(3)
    application.processEvents()
    assert window.page_index == 3
    assert 3 in window.canvas._page_items
    window.close()

def test_click_places_text_box_on_scrolled_page(tmp_path, monkeypatch) -> None:
    pytest.importorskip("PySide6")
    import fitz
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QInputDialog
    from sabl_pdf.ui.window import MainWindow

    path = tmp_path / "two-pages.pdf"
    with fitz.open() as document:
        document.new_page(width=300, height=450)
        document.new_page(width=300, height=450)
        document.save(path)

    application = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.resize(540, 460)
    window.show()
    window.open_path(path)
    window.canvas.scroll_to_page(1)
    application.processEvents()

    monkeypatch.setattr(QInputDialog, "getMultiLineText", lambda *args: ("Test box", True))
    window.add_text_box()
    page = window.canvas._page_rects[1]
    point = window.canvas.mapFromScene(page.left() + 30, page.top() + 35)
    QTest.mouseClick(window.canvas.viewport(), Qt.MouseButton.LeftButton, pos=point)
    application.processEvents()

    assert len(window.text_boxes.list(0)) == 0
    assert len(window.text_boxes.list(1)) == 1
    assert window.text_boxes.list(1)[0].content == "Test box"
    monkeypatch.setattr(window, "_confirm_changes", lambda: True)
    window.close()
