from pathlib import Path

import fitz
import pytest

from sabl_pdf.core.session import DocumentSession


def test_open_pdf_sets_state(sample_pdf: Path) -> None:
    session = DocumentSession()

    session.open(sample_pdf)

    assert session.path == sample_pdf
    assert len(session.document) == 1
    assert session.dirty is False
    session.close()


def test_save_persists_changes(session: DocumentSession) -> None:
    session.document[0].insert_text((40, 100), "Saved text")
    session.mark_dirty()

    result = session.save()

    with fitz.open(result) as saved:
        assert "Saved text" in saved[0].get_text()
    assert session.dirty is False


def test_save_as_keeps_original(session: DocumentSession, tmp_path: Path) -> None:
    original = session.path
    destination = tmp_path / "saved-as.pdf"

    result = session.save(destination)

    assert result == destination
    assert destination.is_file()
    assert original is not None and original.is_file()


def test_open_missing_file_preserves_previous_document(session: DocumentSession) -> None:
    old_path = session.path

    with pytest.raises(Exception):
        session.open("no-such-file.pdf")

    assert session.path == old_path
    assert len(session.document) == 1


def test_document_requires_open_file() -> None:
    session = DocumentSession()

    with pytest.raises(RuntimeError, match="Open a PDF"):
        _ = session.document


def test_save_as_then_save_updates_new_destination(session: DocumentSession, tmp_path: Path) -> None:
    destination = tmp_path / "renamed.pdf"
    session.save(destination)
    session.document[0].insert_text((40, 130), "Second save")
    session.mark_dirty()

    session.save()

    with fitz.open(destination) as saved:
        assert "Second save" in saved[0].get_text()

def test_open_pdf_with_missing_content_warns_without_losing_pages(tmp_path: Path) -> None:
    source = tmp_path / "broken-content.pdf"
    with fitz.open() as document:
        document.new_page().insert_text((30, 30), "Original content")
        data = document.tobytes()
    data = data.replace(b"Contents[6 0 R]", b"Contents[9 0 R]")
    assert data != b""
    source.write_bytes(data)
    session = DocumentSession()

    session.open(source)

    assert session.open_warnings is True
    assert len(session.document) == 1
    assert source.read_bytes() == data
    session.close()


def test_invalid_pdf_keeps_the_previous_document(session: DocumentSession, tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.pdf"
    invalid.write_bytes(b"This is not a PDF")
    original_path = session.path

    with pytest.raises(ValueError, match="Cannot open this PDF"):
        session.open(invalid)

    assert session.path == original_path
    assert len(session.document) == 1
