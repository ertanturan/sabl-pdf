from io import BytesIO

import fitz
import pytest
from PIL import Image

from sabl_pdf.core.session import DocumentSession
from sabl_pdf.services.redaction import RedactionService, RedactionTarget


def test_find_text_across_pages(tmp_path) -> None:
    source = tmp_path / "search.pdf"
    with fitz.open() as document:
        document.new_page().insert_text((60, 70), "Secret text")
        document.new_page().insert_text((60, 70), "Another Secret text")
        document.save(source)
    session = DocumentSession()
    session.open(source)
    service = RedactionService(session)

    targets = service.find("Secret")

    assert len(targets) == 2
    assert {target.page for target in targets} == {0, 1}
    session.close()


def test_export_removes_text_and_original_pdf_objects(session, tmp_path) -> None:
    service = RedactionService(session)
    destination = tmp_path / "redacted.pdf"
    matches = service.find("Hello")

    report = service.export(matches, destination)

    with fitz.open(destination) as output:
        assert report.regions == 1
        assert output[0].get_text() == ""
        assert len(output[0].get_images(full=True)) == 1
        assert output.embfile_count() == 0
    assert "Hello" in session.document[0].get_text()


def test_redaction_blacks_out_target_pixels(session, tmp_path) -> None:
    service = RedactionService(session)
    target = service.find("Hello")[0]
    destination = tmp_path / "black.pdf"

    service.export([target], destination)

    with fitz.open(destination) as output:
        image_xref = output[0].get_images(full=True)[0][0]
        with Image.open(BytesIO(output.extract_image(image_xref)["image"])) as image:
            x0, y0, x1, y1 = target.bounds
            x = round((x0 + x1) / 2 * image.width / output[0].rect.width)
            y = round((y0 + y1) / 2 * image.height / output[0].rect.height)
            pixel = image.convert("RGB").getpixel((x, y))
        assert pixel == (0, 0, 0)


def test_export_does_not_overwrite_existing_file(session, tmp_path) -> None:
    service = RedactionService(session)
    destination = tmp_path / "existing.pdf"
    destination.write_bytes(b"keep")

    with pytest.raises(FileExistsError):
        service.export(service.find("Hello"), destination)

    assert destination.read_bytes() == b"keep"


def test_export_does_not_overwrite_source(session) -> None:
    service = RedactionService(session)
    before = session.path.read_bytes()

    with pytest.raises(ValueError, match="different file"):
        service.export(service.find("Hello"), session.path)

    assert session.path.read_bytes() == before


def test_export_refuses_empty_or_invalid_targets(session, tmp_path) -> None:
    service = RedactionService(session)

    with pytest.raises(ValueError, match="Select at least"):
        service.export([], tmp_path / "empty.pdf")
    with pytest.raises(ValueError, match="invalid page"):
        service.export([RedactionTarget(50, (1, 2, 3, 4))], tmp_path / "invalid.pdf")


def test_export_removes_hidden_source_metadata_and_attachments(tmp_path) -> None:
    source = tmp_path / "source.pdf"
    with fitz.open() as document:
        document.new_page().insert_text((60, 70), "Sensitive")
        document.set_metadata({"title": "Sensitive"})
        document.embfile_add("secret.txt", b"Sensitive")
        document.save(source)
    session = DocumentSession()
    session.open(source)
    service = RedactionService(session)
    destination = tmp_path / "output.pdf"

    service.export(service.find("Sensitive"), destination)

    with fitz.open(destination) as output:
        assert output.metadata["title"] == ""
        assert output.embfile_count() == 0
        assert "Sensitive" not in output[0].get_text()
    assert b"Sensitive" not in destination.read_bytes()
    session.close()


def test_scanned_image_redaction_preserves_other_pixels(tmp_path) -> None:
    image = Image.new("RGB", (100, 100), (200, 200, 200))
    with BytesIO() as buffer:
        image.save(buffer, format="PNG")
        picture = buffer.getvalue()
    source = tmp_path / "scanned.pdf"
    with fitz.open() as document:
        page = document.new_page(width=100, height=100)
        page.insert_image(page.rect, stream=picture)
        document.save(source)
    session = DocumentSession()
    session.open(source)
    service = RedactionService(session)
    destination = tmp_path / "scanned-redacted.pdf"

    service.export([RedactionTarget(0, (20, 20, 40, 40))], destination)

    with fitz.open(destination) as output:
        image_xref = output[0].get_images(full=True)[0][0]
        with Image.open(BytesIO(output.extract_image(image_xref)["image"])) as result:
            pixels = result.convert("RGB")
            assert pixels.getpixel((60, 60)) == (0, 0, 0)
            assert pixels.getpixel((10, 10)) == (200, 200, 200)
    session.close()
