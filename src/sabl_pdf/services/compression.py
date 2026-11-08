from pathlib import Path

import fitz

from sabl_pdf.core.session import DocumentSession


class CompressionService:
    def __init__(self, session: DocumentSession) -> None:
        self._session = session

    def optimise(self, destination: str | Path, *, image_quality: int | None = None) -> Path:
        output = Path(destination)
        if self._session.path is not None and output.resolve() == self._session.path.resolve():
            raise ValueError("Choose a different output file for compression")
        if image_quality is not None and not 1 <= image_quality <= 100:
            raise ValueError("Image quality must be between 1 and 100")
        with fitz.open(stream=self._session.document.tobytes(), filetype="pdf") as copy:
            if image_quality is not None:
                copy.rewrite_images(quality=image_quality)
            copy.save(
                output, garbage=4, deflate=True, deflate_images=True,
                deflate_fonts=True, use_objstms=1,
            )
        return output
