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
