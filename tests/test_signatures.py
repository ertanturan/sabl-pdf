from pathlib import Path

import pytest
from PIL import Image

from sabl_pdf.core.session import DocumentSession
from sabl_pdf.services.signatures import SignatureService


def test_import_signature_image(session: DocumentSession, tmp_path: Path) -> None:
    source = tmp_path / "signature.png"
    Image.new("RGBA", (200, 80), (255, 255, 255, 0)).save(source)
    service = SignatureService(session)

    service.import_image(0, (20, 100, 220, 150), source)

    assert len(session.document[0].get_images()) == 1
    assert session.dirty


def test_draw_signature(session: DocumentSession) -> None:
    service = SignatureService(session)

    service.draw(0, (20, 100, 220, 150), [[(0, 0), (0.5, 0.8), (1, 0)]])

    assert len(session.document[0].get_drawings()) > 0


def test_blank_strokes_rejected(session: DocumentSession) -> None:
    service = SignatureService(session)

    with pytest.raises(ValueError):
        service.draw(0, (20, 100, 220, 150), [])
