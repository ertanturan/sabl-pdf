from pathlib import Path

import fitz
import pytest

from sabl_pdf.core.session import DocumentSession


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    path = tmp_path / "sample.pdf"
    with fitz.open() as pdf:
        page = pdf.new_page(width=300, height=400)
        page.insert_text((50, 50), "Hello SABL")
        pdf.save(path)
    return path


@pytest.fixture
def session(sample_pdf: Path):
    document_session = DocumentSession()
    document_session.open(sample_pdf)
    yield document_session
    document_session.close()
