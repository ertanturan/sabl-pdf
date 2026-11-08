from pathlib import Path

import fitz


class DocumentSession:
    def __init__(self) -> None:
        self._document: fitz.Document | None = None
        self._path: Path | None = None
        self._dirty = False

    @property
    def document(self) -> fitz.Document:
        if self._document is None or self._document.is_closed:
            raise RuntimeError("Open a PDF first")
        return self._document

    @property
    def path(self) -> Path | None:
        return self._path

    @property
    def dirty(self) -> bool:
        return self._dirty

    def open(self, path: str | Path) -> None:
        candidate = Path(path)
        new_document = fitz.open(candidate)
        if not new_document.is_pdf:
            new_document.close()
            raise ValueError("The selected file is not a PDF")
        previous = self._document
        self._document = new_document
        self._path = candidate
        self._dirty = False
        if previous is not None:
            previous.close()

    def create(self) -> None:
        previous = self._document
        self._document = fitz.open()
        self._path = None
        self._dirty = False
        if previous is not None:
            previous.close()

    def mark_dirty(self) -> None:
        self.document
        self._dirty = True

    def save(self, path: str | Path | None = None) -> Path:
        destination = Path(path) if path is not None else self._path
        if destination is None:
            raise ValueError("Choose a destination to save the PDF")
        document = self.document
        if self._path is not None and destination.resolve() == self._path.resolve():
            if document.can_save_incrementally():
                document.saveIncr()
            else:
                temporary = destination.with_name(f"{destination.stem}.sabl-tmp.pdf")
                try:
                    document.save(temporary, garbage=4, deflate=True)
                    document.close()
                    temporary.replace(destination)
                    self._document = fitz.open(destination)
                finally:
                    temporary.unlink(missing_ok=True)
        else:
            document.save(destination, garbage=4, deflate=True)
            document.close()
            self._document = fitz.open(destination)
        self._path = destination
        self._dirty = False
        return destination

    def close(self) -> None:
        if self._document is not None:
            self._document.close()
        self._document = None
        self._path = None
        self._dirty = False
