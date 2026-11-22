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
