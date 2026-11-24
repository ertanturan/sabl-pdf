from pathlib import Path

import fitz
import pytest

from sabl_pdf.core.session import (
    DocumentSession,
    PdfIncorrectPasswordError,
    PdfPasswordRequiredError,
)


@pytest.fixture
def encrypted_pdf(sample_pdf: Path, tmp_path: Path) -> Path:
    destination = tmp_path / "encrypted.pdf"
    with fitz.open(sample_pdf) as document:
        document.save(
            destination, encryption=fitz.PDF_ENCRYPT_AES_256,
            user_pw="secret", owner_pw="secret",
        )
    return destination


def test_password_required_preserves_previous_session(
    session: DocumentSession, encrypted_pdf: Path
) -> None:
    previous = session.path

    with pytest.raises(PdfPasswordRequiredError, match="requires a password"):
        session.open(encrypted_pdf)

    assert session.path == previous
    assert "Hello SABL" in session.document[0].get_text()


def test_wrong_password_preserves_previous_session(
    session: DocumentSession, encrypted_pdf: Path
) -> None:
    previous = session.path

    with pytest.raises(PdfIncorrectPasswordError, match="Incorrect PDF password"):
        session.open(encrypted_pdf, password="wrong")

    assert session.path == previous
    assert len(session.document) == 1


def test_open_encrypted_pdf_with_password(encrypted_pdf: Path) -> None:
    session = DocumentSession()

    session.open(encrypted_pdf, password="secret")

    assert session.path == encrypted_pdf
    assert "Hello SABL" in session.document[0].get_text()
    with fitz.open(encrypted_pdf) as locked:
        assert locked.needs_pass
    session.close()


def test_protect_pdf_uses_aes_256(session: DocumentSession, tmp_path: Path) -> None:
    destination = tmp_path / "protected.pdf"

    result = session.save(destination, password="new-secret")

    assert result == destination
    with fitz.open(destination) as document:
        assert document.needs_pass
        assert document.authenticate("new-secret")
        assert document.metadata["encryption"] == "Standard V5 R6 256-bit AES"
        assert "Hello SABL" in document[0].get_text()
    assert session.path == destination
    assert not session.dirty


def test_empty_password_is_rejected(session: DocumentSession, tmp_path: Path) -> None:
    destination = tmp_path / "not-created.pdf"

    with pytest.raises(ValueError, match="Password must not be empty"):
        session.save(destination, password="")

    assert not destination.exists()
    assert session.path != destination


def test_save_existing_encrypted_pdf_retains_encryption(encrypted_pdf: Path) -> None:
    session = DocumentSession()
    session.open(encrypted_pdf, password="secret")
    session.document[0].insert_text((40, 90), "Additional text")
    session.mark_dirty()

    session.save()

    with fitz.open(encrypted_pdf) as document:
        assert document.needs_pass
        assert document.authenticate("secret")
        assert "Additional text" in document[0].get_text()
    assert not session.dirty
    session.close()


def test_save_as_retains_open_password(encrypted_pdf: Path, tmp_path: Path) -> None:
    session = DocumentSession()
    session.open(encrypted_pdf, password="secret")
    destination = tmp_path / "copy.pdf"

    session.save(destination)

    with fitz.open(destination) as document:
        assert document.needs_pass
        assert document.authenticate("secret")
        assert "Hello SABL" in document[0].get_text()
    assert session.path == destination
    session.close()


def test_replace_existing_password_in_place(encrypted_pdf: Path) -> None:
    session = DocumentSession()
    session.open(encrypted_pdf, password="secret")

    session.save(password="replacement")

    with fitz.open(encrypted_pdf) as document:
        assert document.needs_pass
        assert document.authenticate("secret") == 0
        assert document.authenticate("replacement")
        assert "Hello SABL" in document[0].get_text()
    session.close()


def test_new_document_after_encrypted_file_is_not_protected(
    encrypted_pdf: Path, tmp_path: Path
) -> None:
    session = DocumentSession()
    session.open(encrypted_pdf, password="secret")
    destination = tmp_path / "new.pdf"

    session.create()
    session.document.new_page()
    session.save(destination)

    with fitz.open(destination) as document:
        assert not document.needs_pass
    session.close()


def test_original_is_unchanged_when_creating_protected_copy(
    session: DocumentSession, tmp_path: Path
) -> None:
    original = session.path
    destination = tmp_path / "protected-copy.pdf"

    session.save(destination, password="password")

    assert original is not None
    with fitz.open(original) as document:
        assert not document.needs_pass
        assert "Hello SABL" in document[0].get_text()
