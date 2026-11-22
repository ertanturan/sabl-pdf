import pytest

from sabl_pdf.core.session import DocumentSession
from sabl_pdf.services.viewer import ViewerService


def test_render_at_zoom(session: DocumentSession) -> None:
    service = ViewerService(session)

    pixmap = service.render(0, 2.0)

    assert pixmap.width == 600
    assert pixmap.height == 800


def test_search_returns_page_coordinates(session: DocumentSession) -> None:
    service = ViewerService(session)

    matches = service.search("Hello")

    assert len(matches) == 1
    assert matches[0].page == 0
    assert len(matches[0].bounds) == 4


def test_empty_search_returns_no_matches(session: DocumentSession) -> None:
    service = ViewerService(session)

    matches = service.search("   ")

    assert matches == []


def test_zoom_out_of_range_is_rejected(session: DocumentSession) -> None:
    service = ViewerService(session)

    with pytest.raises(ValueError):
        service.render(0, 0)

def test_page_sizes_match_pdf(session: DocumentSession) -> None:
    service = ViewerService(session)

    assert service.page_sizes() == [(300.0, 400.0)]

def test_search_uses_ocr_fallback_on_a_scanned_page(session, monkeypatch) -> None:
    import fitz
    from unittest.mock import Mock

    service = ViewerService(session)
    candidate = Mock(return_value=True)
    textpage = object()
    ocr_get = Mock(return_value=(session.document[0], textpage))
    search_for = Mock(side_effect=[[], [fitz.Rect(10, 20, 90, 40)]])
    monkeypatch.setattr(service._ocr_pages, "is_candidate", candidate)
    monkeypatch.setattr(service._ocr_pages, "get", ocr_get)
    monkeypatch.setattr(fitz.Page, "search_for", search_for)

    matches = service.search("Scanned")

    assert matches[0].bounds == (10.0, 20.0, 90.0, 40.0)
    assert matches[0].page == 0
    assert search_for.call_count == 2
    assert ocr_get.call_count == 1


def test_search_reports_unavailable_ocr_when_no_native_match(session, monkeypatch) -> None:
    import fitz
    from unittest.mock import Mock

    service = ViewerService(session)
    monkeypatch.setattr(service._ocr_pages, "is_candidate", Mock(return_value=True))
    monkeypatch.setattr(
        service._ocr_pages, "get", Mock(side_effect=RuntimeError("OCR unavailable"))
    )
    monkeypatch.setattr(fitz.Page, "search_for", Mock(return_value=[]))

    with pytest.raises(RuntimeError, match="OCR unavailable"):
        service.search("Scanned")


def test_search_rotated_page_has_display_space_bounds(session) -> None:
    service = ViewerService(session)
    session.document[0].set_rotation(90)

    matches = service.search("Hello")

    assert matches[0].bounds == pytest.approx((346.711, 50.0, 361.825, 75.058), abs=0.02)


def test_ocr_text_page_cache_reuses_recognition(session, monkeypatch) -> None:
    import fitz

    service = ViewerService(session)
    monkeypatch.setattr(
        fitz.Page, "get_textpage_ocr",
        lambda page, language, dpi, full: page.get_textpage(),
    )

    first = service._ocr_pages.get(0)
    second = service._ocr_pages.get(0)

    assert first is second
    assert len(first[0].search_for("Hello", textpage=first[1])) == 1
