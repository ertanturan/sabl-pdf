import fitz
import pytest
from PIL import Image

from sabl_pdf.services.annotations import AnnotationService
from sabl_pdf.services.placed_items import PlacedItemService
from sabl_pdf.services.signatures import SignatureService
from sabl_pdf.services.text_boxes import TextBoxService


def test_move_text_box_preserves_content(session) -> None:
    text = TextBoxService(session)
    service = PlacedItemService(session)
    xref = text.add(0, (20, 100, 150, 145), "Keep this text")

    moved_xref = service.move(0, xref, (60, 115, 190, 160))

    assert moved_xref == xref
    assert text.list(0)[0].content == "Keep this text"
    assert tuple(text.list(0)[0].bounds) == pytest.approx((60, 115, 190, 160))
    assert session.dirty


def test_move_drawn_signature_then_delete(session) -> None:
    service = PlacedItemService(session)
    xref = SignatureService(session).draw(
        0, (20, 100, 200, 150), [[(0, 0), (0.5, 1), (1, 0)]]
    )
    original = next(item for item in service.list() if item.xref == xref)
    rect = fitz.Rect(original.bounds) + fitz.Rect(30, 20, 30, 20)

    new_xref = service.move(0, xref, tuple(rect))

    moved = next(item for item in service.list() if item.xref == new_xref)
    assert moved.kind == "Ink"
    assert moved.bounds == pytest.approx(tuple(rect))
    service.delete(0, new_xref)
    assert not service.list()


@pytest.mark.parametrize("kind", ["highlight", "underline"])
def test_move_text_markup(session, kind: str) -> None:
    service = PlacedItemService(session)
    xref = AnnotationService(session).mark_text(
        0, tuple(session.document[0].search_for("Hello")[0]), kind
    )
    original = next(item for item in service.list() if item.xref == xref)
    new_rect = fitz.Rect(original.bounds) + fitz.Rect(0, 25, 0, 25)

    new_xref = service.move(0, xref, tuple(new_rect))

    moved = next(item for item in service.list() if item.xref == new_xref)
    assert moved.kind.lower() == kind
    assert moved.bounds == pytest.approx(tuple(new_rect))


def test_move_imported_signature_persists_after_reopen(session, tmp_path) -> None:
    image = tmp_path / "signature.png"
    Image.new("RGBA", (40, 20), (255, 0, 0, 255)).save(image)
    service = PlacedItemService(session)
    xref = SignatureService(session).import_image(0, (20, 100, 180, 155), image)

    moved_xref = service.move(0, xref, (35, 120, 195, 175))
    path = tmp_path / "stamped.pdf"
    session.save(path)
    items = service.list()

    assert moved_xref == xref
    assert items[0].kind == "Stamp"
    assert items[0].bounds == pytest.approx((35, 120, 195, 175))
    assert session.document[0].get_pixmap().pixel(50, 135)[0] > 200


def test_delete_note_and_reject_invalid_moves(session) -> None:
    service = PlacedItemService(session)
    xref = AnnotationService(session).add_note(0, (50, 80), "Review")

    with pytest.raises(ValueError):
        service.move(0, xref, (-100, -100, -82, -82))

    assert next(item for item in service.list() if item.xref == xref).kind == "Text"
    service.delete(0, xref)
    assert not service.list()


def test_move_text_box_between_pages_preserves_content_after_reopen(session, tmp_path) -> None:
    session.document.new_page(width=300, height=400)
    service = PlacedItemService(session)
    text = TextBoxService(session)
    xref = text.add(0, (20, 100, 150, 145), "Moved text")

    new_xref = service.move(0, xref, (60, 115, 190, 160), target_page_index=1)

    assert new_xref != xref
    assert text.list(0) == []
    assert text.list(1)[0].content == "Moved text"
    assert text.list(1)[0].bounds == pytest.approx((60, 115, 190, 160))
    session.save(tmp_path / "moved-text.pdf")
    assert text.list(1)[0].content == "Moved text"


def test_move_drawn_signature_between_pages(session) -> None:
    session.document.new_page(width=300, height=400)
    service = PlacedItemService(session)
    xref = SignatureService(session).draw(
        0, (20, 100, 200, 150), [[(0, 0), (0.5, 1), (1, 0)]]
    )
    original = next(item for item in service.list() if item.xref == xref)
    new_bounds = tuple(fitz.Rect(original.bounds) + fitz.Rect(20, 45, 20, 45))

    moved_xref = service.move(0, xref, new_bounds, target_page_index=1)

    assert all(item.page != 0 for item in service.list())
    moved = next(item for item in service.list() if item.xref == moved_xref)
    assert moved.page == 1
    assert moved.kind == "Ink"
    assert moved.bounds == pytest.approx(new_bounds)
    service.delete(1, moved_xref)
    assert service.list() == []


def test_move_imported_signature_between_pages_preserves_image(session, tmp_path) -> None:
    session.document.new_page(width=300, height=400)
    image = tmp_path / "cross-page-signature.png"
    Image.new("RGB", (60, 20), (250, 0, 0)).save(image)
    service = PlacedItemService(session)
    xref = SignatureService(session).import_image(0, (20, 100, 160, 140), image)
    original_appearance = session.document.xref_get_key(xref, "AP")[1]

    moved_xref = service.move(0, xref, (55, 150, 195, 190), target_page_index=1)

    assert not list(session.document[0].annots() or ())
    assert session.document.xref_get_key(moved_xref, "AP")[1] == original_appearance
    session.save(tmp_path / "moved-signature.pdf")
    target = session.document[1]
    assert next(target.annots()).type[0] == fitz.PDF_ANNOT_STAMP
    pixel = target.get_pixmap().pixel(70, 165)
    assert pixel[0] > 200
    assert pixel[1] < 80


@pytest.mark.parametrize("kind", ["highlight", "underline"])
def test_move_markup_between_pages(session, kind: str) -> None:
    session.document.new_page(width=300, height=400)
    service = PlacedItemService(session)
    xref = AnnotationService(session).mark_text(
        0, tuple(session.document[0].search_for("Hello")[0]), kind
    )
    original = next(item for item in service.list() if item.xref == xref)
    new_bounds = tuple(fitz.Rect(original.bounds) + fitz.Rect(0, 60, 0, 60))

    moved_xref = service.move(0, xref, new_bounds, target_page_index=1)

    moved = next(item for item in service.list() if item.xref == moved_xref)
    assert moved.page == 1
    assert moved.kind.lower() == kind
    assert moved.bounds == pytest.approx(new_bounds)
    assert all(item.page != 0 for item in service.list())


def test_invalid_cross_page_move_keeps_original_annotation(session) -> None:
    session.document.new_page(width=100, height=150)
    service = PlacedItemService(session)
    xref = TextBoxService(session).add(0, (20, 100, 150, 145), "Stay here")

    with pytest.raises(ValueError):
        service.move(0, xref, (0, 20, 130, 65), target_page_index=1)

    assert TextBoxService(session).list(0)[0].xref == xref
    assert list(session.document[1].annots() or ()) == []
