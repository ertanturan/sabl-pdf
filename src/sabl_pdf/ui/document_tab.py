from collections.abc import Callable

from PySide6.QtWidgets import QVBoxLayout, QWidget

from sabl_pdf.core.session import DocumentSession
from sabl_pdf.services.annotations import AnnotationService
from sabl_pdf.services.compression import CompressionService
from sabl_pdf.services.conversion import ConversionService
from sabl_pdf.services.forms import FormService
from sabl_pdf.services.ocr import OcrService
from sabl_pdf.services.pages import PageService
from sabl_pdf.services.signatures import SignatureService
from sabl_pdf.services.text_boxes import TextBoxService
from sabl_pdf.services.viewer import SearchMatch, ViewerService
from sabl_pdf.ui.canvas import PdfCanvas


class DocumentTab(QWidget):
    def __init__(self, session: DocumentSession, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.session = session
        self.viewer = ViewerService(session)
        self.text_boxes = TextBoxService(session)
        self.forms = FormService(session)
        self.signatures = SignatureService(session)
        self.pages = PageService(session)
        self.annotations = AnnotationService(session)
        self.compression = CompressionService(session)
        self.conversion = ConversionService(session)
        self.ocr = OcrService(session)
        self.page_index = 0
        self.zoom = 1.0
        self.selection_action: Callable[[tuple], None] | None = None
        self.active_tool: str | None = None
        self.search_matches: list[SearchMatch] = []
        self.search_index = -1
        self.search_query = ""
        self.search_open = False
        self.canvas = PdfCanvas()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

    def title(self) -> str:
        name = self.session.path.name if self.session.path else "Untitled"
        return f"{name} *" if self.session.dirty else name
