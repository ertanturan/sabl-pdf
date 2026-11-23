import fitz

from sabl_pdf.core.session import DocumentSession
from sabl_pdf.services.text_selection import TextSelectionService


def test_selects_characters_from_native_pdf(tmp_path) -> None:
    path = tmp_path / "letters.pdf"
    with fitz.open() as document:
        document.new_page(width=300, height=300).insert_text((40, 60), "Hello world")
        document.save(path)
    session = DocumentSession()
    session.open(path)
    service = TextSelectionService(session)
    chars = session.document[0].get_text("rawdict")["blocks"][0]["lines"][0]["spans"][0]["chars"]

    result = service.select(0, (chars[0]["bbox"][0], 55), (chars[4]["bbox"][2], 55))

    assert result is not None
    assert result.text == "Hello"
    assert len(result.rects) == 1
    assert result.page == 0
    session.close()


def test_selection_across_lines_includes_newline(tmp_path) -> None:
    path = tmp_path / "lines.pdf"
    with fitz.open() as document:
        document.new_page().insert_text((40, 60), "Hello\nworld")
        document.save(path)
    session = DocumentSession()
    session.open(path)
    service = TextSelectionService(session)
    lines = session.document[0].get_text("rawdict")["blocks"][0]["lines"]
    first = lines[0]["spans"][0]["chars"][0]["bbox"]
    last = lines[1]["spans"][0]["chars"][-1]["bbox"]

    result = service.select(0, (first[0], 55), (last[2], last[1] + 1))

    assert result is not None
    assert result.text == "Hello\nworld"
    assert len(result.rects) == 2
    session.close()


def test_rejects_selection_started_outside_text(session) -> None:
    service = TextSelectionService(session)

    result = service.select(0, (250, 350), (280, 380))

    assert result is None


def test_rejects_click_without_drag(session) -> None:
    service = TextSelectionService(session)
    char = session.document[0].get_text("rawdict")["blocks"][0]["lines"][0]["spans"][0]["chars"][0]["bbox"]

    result = service.select(0, (char[0] + 1, char[1] + 1), (char[0] + 1, char[1] + 1))

    assert result is None

def test_drag_can_start_near_the_first_glyph(session) -> None:
    service = TextSelectionService(session)

    selection = service.select(0, (42, 45), (58, 45))

    assert selection is not None
    assert selection.text == "H"


def test_ocr_fallback_supplies_selectable_characters(session, monkeypatch) -> None:
    from unittest.mock import Mock
    from sabl_pdf.services.text_selection import TextGlyph

    service = TextSelectionService(session)
    glyphs = [
        TextGlyph("N", 0, (50.0, 40.0, 60.0, 55.0)),
        TextGlyph("e", 0, (60.0, 40.0, 70.0, 55.0)),
    ]
    selection_glyphs = Mock(side_effect=[[], glyphs])
    monkeypatch.setattr(service, "_glyphs", selection_glyphs)
    monkeypatch.setattr(service._ocr_pages, "is_candidate", Mock(return_value=True))
    ocr_get = Mock(return_value=(session.document[0], session.document[0].get_textpage()))
    monkeypatch.setattr(service._ocr_pages, "get", ocr_get)

    selection = service.select(0, (51, 47), (70, 47))

    assert selection is not None
    assert selection.text == "Ne"
    assert ocr_get.call_count == 1
    assert selection_glyphs.call_count == 2
