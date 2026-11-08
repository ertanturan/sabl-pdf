from pathlib import Path

import pytest
from PIL import Image

from sabl_pdf.core.session import DocumentSession
from sabl_pdf.services.conversion import ConversionService


def test_pdf_to_images(session: DocumentSession, tmp_path: Path) -> None:
    service = ConversionService(session)

    files = service.pdf_to_images(tmp_path / "pages", dpi=72)

    assert len(files) == 1
    with Image.open(files[0]) as image:
        assert image.size == (300, 400)


def test_images_to_pdf(session: DocumentSession, tmp_path: Path) -> None:
    image = tmp_path / "input.png"
    Image.new("RGB", (40, 60), "white").save(image)
    service = ConversionService(session)

    service.images_to_pdf([image])

    assert len(session.document) == 2
    assert session.document[1].rect.width == 40


def test_invalid_dpi_rejected(session: DocumentSession, tmp_path: Path) -> None:
    service = ConversionService(session)

    with pytest.raises(ValueError):
        service.pdf_to_images(tmp_path, dpi=1)
