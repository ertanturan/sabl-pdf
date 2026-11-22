import fitz

from sabl_pdf.core.session import DocumentSession


class OcrTextPages:
    def __init__(self, session: DocumentSession) -> None:
        self._session = session
        self._document: fitz.Document | None = None
        self._pages: dict[int, tuple[fitz.Page, fitz.TextPage]] = {}

    def is_candidate(self, page: fitz.Page) -> bool:
        images = page.get_image_info()
        if not page.get_text("words"):
            return bool(images or page.get_drawings())
        minimum_area = page.rect.get_area() * 0.5
        return any(
            fitz.Rect(image["bbox"]).get_area() >= minimum_area for image in images
        )

    def get(self, page_index: int) -> tuple[fitz.Page, fitz.TextPage]:
        document = self._session.document
        if document is not self._document:
            self.clear()
            self._document = document
        if page_index not in self._pages:
            try:
                page = document[page_index]
                textpage = page.get_textpage_ocr(language="eng", dpi=150, full=True)
                self._pages[page_index] = (page, textpage)
            except RuntimeError as exc:
                raise RuntimeError(
                    "This page needs OCR. Install Tesseract English language data "
                    "to find or select text in scanned PDFs."
                ) from exc
        return self._pages[page_index]

    def clear(self) -> None:
        self._pages.clear()
