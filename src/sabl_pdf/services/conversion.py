from pathlib import Path

import fitz

from sabl_pdf.core.session import DocumentSession


class ConversionService:
    def __init__(self, session: DocumentSession) -> None:
        self._session = session

    def images_to_pdf(self, image_paths: list[str | Path]) -> None:
        if not image_paths:
            raise ValueError("Select at least one image")
        staged = fitz.open()
        try:
            for path in image_paths:
                pixmap = fitz.Pixmap(str(path))
                page = staged.new_page(width=pixmap.width, height=pixmap.height)
                page.insert_image(page.rect, pixmap=pixmap)
            self._session.document.insert_pdf(staged)
        finally:
            staged.close()
        self._session.mark_dirty()

    def pdf_to_images(self, destination: str | Path, dpi: int = 150) -> list[Path]:
        if dpi < 36 or dpi > 600:
            raise ValueError("DPI must be between 36 and 600")
        directory = Path(destination)
        directory.mkdir(parents=True, exist_ok=True)
        outputs = []
        for index, page in enumerate(self._session.document):
            path = directory / f"page-{index + 1:03d}.png"
            pixmap = page.get_pixmap(dpi=dpi, alpha=False)
            pixmap.save(str(path))
            outputs.append(path)
        return outputs
