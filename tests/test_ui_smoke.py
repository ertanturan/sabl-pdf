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

def test_signature_click_place_cancel_and_reuse(tmp_path, monkeypatch) -> None:
    pytest.importorskip("PySide6")
    import fitz
    from PySide6.QtCore import QSettings, Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication
    from sabl_pdf.ui.signature_actions import SignatureActions
    from sabl_pdf.ui.window import MainWindow

    path = tmp_path / "signature.pdf"
    with fitz.open() as document:
        document.new_page(width=400, height=500)
        document.save(path)
    settings = QSettings(str(tmp_path / "signature.ini"), QSettings.Format.IniFormat)
    monkeypatch.setattr(SignatureActions, "_signature_settings", lambda self: settings)

    application = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    window.open_path(path)
    application.processEvents()
    strokes = [[(0.0, 0.0), (0.5, 1.0), (1.0, 0.0)]]

    window._save_signature(strokes)
    window.use_saved_signature()
    assert window.canvas._preview_item is not None
    QTest.mouseClick(
        window.canvas.viewport(),
        Qt.MouseButton.RightButton,
        pos=window.canvas.mapFromScene(100, 100),
    )
    assert window.canvas._preview_item is None
    assert len(window.session.document[0].get_drawings()) == 0

    window.use_saved_signature()
    page = window.canvas._page_rects[0]
    click = window.canvas.mapFromScene(page.left() + 40, page.top() + 90)
    QTest.mouseClick(window.canvas.viewport(), Qt.MouseButton.LeftButton, pos=click)
    assert len(window.session.document[0].get_drawings()) > 0
    assert window._load_saved_signature() == strokes
    monkeypatch.setattr(window, "_confirm_changes", lambda: True)
    window.close()

def test_damaged_pdf_shows_single_warning(tmp_path, monkeypatch) -> None:
    pytest.importorskip("PySide6")
    import fitz
    from PySide6.QtWidgets import QApplication, QMessageBox
    from sabl_pdf.ui.window import MainWindow

    path = tmp_path / "broken.pdf"
    with fitz.open() as document:
        document.new_page().insert_text((30, 30), "Missing")
        data = document.tobytes()
    path.write_bytes(data.replace(b"Contents[6 0 R]", b"Contents[9 0 R]"))
    application = QApplication.instance() or QApplication([])
    window = MainWindow()
    messages = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: messages.append(args[2]))

    window.open_path(path)

    assert application is not None
    assert window.viewer.page_count() == 1
    assert len(messages) == 1
    assert "damaged or missing" in messages[0]
    window.close()


def test_quick_access_and_navigation_toolbars() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtGui import QKeySequence
    from PySide6.QtWidgets import QApplication, QToolBar
    from sabl_pdf.ui.window import MainWindow

    application = QApplication.instance() or QApplication([])
    window = MainWindow()

    assert application is not None
    assert set(window.quick_actions) == {
        "open", "save", "find", "text", "highlight", "sign", "rotate", "compress"
    }
    assert window.quick_actions["find"].shortcut() == QKeySequence("Ctrl+F")
    assert window.findChild(QToolBar, "quick_access") is not None
    assert window.findChild(QToolBar, "page_navigation") is not None
    window.close()


def test_inline_find_navigates_and_clears_highlight(tmp_path) -> None:
    pytest.importorskip("PySide6")
    import fitz
    from PySide6.QtWidgets import QApplication
    from sabl_pdf.ui.window import MainWindow

    path = tmp_path / "searchable.pdf"
    with fitz.open() as document:
        for _ in range(2):
            document.new_page().insert_text((72, 72), "needle in a document")
        document.save(path)

    application = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    window.open_path(path)
    window.search_text()
    window.search_bar.search_input.setText("needle")
    window._search_query("needle")

    assert application is not None
    assert window.search_bar.isVisible()
    assert window.search_bar.results.text() == "1 of 2"
    assert window.canvas._search_highlight is not None

    from PySide6.QtWidgets import QToolButton
    window.search_bar.findChild(QToolButton, "search_next").click()

    assert window.page_index == 1
    assert window.search_bar.results.text() == "2 of 2"

    window._close_search()

    assert not window.search_bar.isVisible()
    assert window.canvas._search_highlight is None
    window.close()


def test_welcome_screen_switches_to_pdf_viewer(sample_pdf) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication
    from sabl_pdf.ui.window import MainWindow

    application = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()

    assert application is not None
    assert window.workspace.currentWidget() is window.welcome
    assert window.welcome.open_requested is not None

    window.open_path(sample_pdf)

    assert window.workspace.currentWidget() is window.document_tabs
    window.close()


def test_page_thumbnails_select_and_follow_pages(tmp_path) -> None:
    pytest.importorskip("PySide6")
    import fitz
    from PySide6.QtWidgets import QApplication
    from sabl_pdf.ui.window import MainWindow

    path = tmp_path / "thumbnail-pages.pdf"
    with fitz.open() as document:
        for number in range(3):
            document.new_page(width=350, height=450).insert_text((30, 30), str(number))
        document.save(path)

    application = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    window.open_path(path)
    application.processEvents()

    assert window.thumbnails.pages.count() == 3
    assert window.thumbnails.isVisible()

    window.thumbnails.pages.setCurrentRow(2)
    application.processEvents()

    assert window.page_index == 2
    window.canvas.scroll_to_page(1)
    application.processEvents()
    assert window.thumbnails.pages.currentRow() == 1
    window.close()


def test_document_actions_and_active_tool_feedback(sample_pdf) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication
    from sabl_pdf.ui.window import MainWindow

    application = QApplication.instance() or QApplication([])
    window = MainWindow()

    assert application is not None
    assert window.quick_actions["open"].isEnabled()
    assert not window.quick_actions["text"].isEnabled()
    assert not window.quick_actions["compress"].isEnabled()

    window.open_path(sample_pdf)

    assert window.quick_actions["text"].isEnabled()
    assert window.quick_actions["compress"].isEnabled()

    window.add_text_box()

    assert window.quick_actions["text"].isChecked()
    assert window.canvas._selection_enabled

    window._cancel_active_tool()

    assert not window.quick_actions["text"].isChecked()
    assert not window.canvas._selection_enabled
    window.close()


def test_toolbar_preferences_persist(tmp_path) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QSettings
    from PySide6.QtGui import QKeySequence
    from PySide6.QtWidgets import QApplication
    from sabl_pdf.ui.window import MainWindow

    settings = QSettings(str(tmp_path / "toolbar.ini"), QSettings.Format.IniFormat)
    application = QApplication.instance() or QApplication([])
    window = MainWindow(settings=settings)

    assert application is not None
    assert window.quick_actions["highlight"].shortcut() == QKeySequence("Ctrl+Shift+H")

    window.toolbar_toggles["highlight"].setChecked(False)

    assert window.quick_actions["highlight"] not in window._quick_toolbar.actions()
    window.close()

    reopened = MainWindow(settings=settings)

    assert not reopened.toolbar_toggles["highlight"].isChecked()
    assert reopened.quick_actions["highlight"] not in reopened._quick_toolbar.actions()

    reopened._reset_toolbar()

    assert reopened.toolbar_toggles["highlight"].isChecked()
    assert reopened.quick_actions["highlight"] in reopened._quick_toolbar.actions()
    reopened.close()


def test_document_tabs_keep_separate_documents_and_view_state(tmp_path, monkeypatch) -> None:
    pytest.importorskip("PySide6")
    import fitz
    from PySide6.QtWidgets import QApplication
    from sabl_pdf.ui.window import MainWindow

    first = tmp_path / "first.pdf"
    second = tmp_path / "second.pdf"
    with fitz.open() as document:
        document.new_page().insert_text((50, 50), "First document")
        document.new_page().insert_text((50, 50), "Second page")
        document.save(first)
    with fitz.open() as document:
        document.new_page().insert_text((50, 50), "Other document")
        document.save(second)

    application = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    window.open_path(first)
    window.zoom = 1.4
    window.canvas.scroll_to_page(1)
    window.page_index = 1
    window.text_boxes.add(0, (30, 60, 220, 120), "First only")
    window._after_edit()
    window.open_path(second)

    assert application is not None
    assert window.document_tabs.count() == 2
    assert "Other document" in window.viewer.text(0)
    assert not window.text_boxes.list(0)

    window.document_tabs.setCurrentIndex(0)

    assert "First document" in window.viewer.text(0)
    assert window.page_index == 1
    assert window.zoom == 1.4
    assert len(window.text_boxes.list(0)) == 1
    assert "*" in window.document_tabs.tabText(0)

    window.open_path(first)

    assert window.document_tabs.count() == 2
    assert window.document_tabs.currentIndex() == 0

    monkeypatch.setattr(window, "_confirm_changes", lambda: True)
    window.close()


def test_tab_close_respects_cancel_and_returns_to_welcome(tmp_path, monkeypatch) -> None:
    pytest.importorskip("PySide6")
    import fitz
    from PySide6.QtWidgets import QApplication, QMessageBox
    from sabl_pdf.ui.window import MainWindow

    path = tmp_path / "unsaved.pdf"
    with fitz.open() as document:
        document.new_page()
        document.save(path)

    application = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    window.open_path(path)
    window.session.mark_dirty()
    window._refresh()
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Cancel
    )

    window._close_document_tab(0)

    assert application is not None
    assert window.document_tabs.count() == 1
    assert window.session.dirty

    monkeypatch.setattr(
        QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Discard
    )
    window._close_document_tab(0)

    assert window.document_tabs.count() == 0
    assert window.workspace.currentWidget() is window.welcome
    assert not window.quick_actions["save"].isEnabled()
    window.close()
