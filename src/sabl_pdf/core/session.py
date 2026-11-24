from pathlib import Path

import fitz


class PdfPasswordRequiredError(ValueError):
    pass


class PdfIncorrectPasswordError(ValueError):
    pass


class DocumentSession:
    def __init__(self) -> None:
        self._document: fitz.Document | None = None
        self._path: Path | None = None
        self._dirty = False
        self._open_warnings = False
        self._password: str | None = None
        fitz.TOOLS.mupdf_display_errors(False)

    @property
    def open_warnings(self) -> bool:
        return self._open_warnings

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

    def open(self, path: str | Path, password: str | None = None) -> None:
        candidate = Path(path)
        new_document, warnings = self._load_pdf(candidate, password)
        previous = self._document
        self._document = new_document
        self._path = candidate
        self._dirty = False
        self._open_warnings = warnings
        self._password = password if new_document.needs_pass else None
        if previous is not None:
            previous.close()

    def _load_pdf(
        self, candidate: Path, password: str | None = None
    ) -> tuple[fitz.Document, bool]:
        fitz.TOOLS.mupdf_warnings()
        try:
            document = fitz.open(candidate)
        except (fitz.FileDataError, RuntimeError) as exc:
            raise ValueError("Cannot open this PDF. It may be damaged or incomplete.") from exc
        if not document.is_pdf:
            document.close()
            raise ValueError("The selected file is not a PDF")
        try:
            self._authenticate(document, password)
            return document, self._check_pdf_warnings(document)
        except Exception:
            document.close()
            raise

    def _authenticate(self, document: fitz.Document, password: str | None) -> None:
        if not document.needs_pass:
            return
        if password is None:
            raise PdfPasswordRequiredError("This PDF requires a password")
        if not document.authenticate(password):
            raise PdfIncorrectPasswordError("Incorrect PDF password")

    def _check_pdf_warnings(self, document: fitz.Document) -> bool:
        repaired = bool(document.is_repaired)
        if len(document):
            try:
                document[0].get_pixmap(matrix=fitz.Matrix(0.25, 0.25), alpha=False)
            except (RuntimeError, ValueError):
                repaired = True
        return repaired or bool(fitz.TOOLS.mupdf_warnings())

    def create(self) -> None:
        previous = self._document
        self._document = fitz.open()
        self._path = None
        self._dirty = False
        self._open_warnings = False
        self._password = None
        if previous is not None:
            previous.close()

    def mark_dirty(self) -> None:
        self.document
        self._dirty = True

    def save(self, path: str | Path | None = None, *, password: str | None = None) -> Path:
        destination = Path(path) if path is not None else self._path
        if destination is None:
            raise ValueError("Choose a destination to save the PDF")
        if password is not None and not password:
            raise ValueError("Password must not be empty")
        document = self.document
        same_file = self._path is not None and destination.resolve() == self._path.resolve()
        credentials = password if password is not None else self._password
        if same_file and password is None and document.can_save_incrementally():
            document.saveIncr()
        else:
            self._rewrite_pdf(destination, password, credentials, same_file)
        self._path = destination
        self._password = credentials if self.document.needs_pass else None
        self._dirty = False
        return destination

    def _rewrite_pdf(
        self, destination: Path, password: str | None, credentials: str | None,
        same_file: bool,
    ) -> None:
        output = destination.with_name(f"{destination.stem}.sabl-tmp.pdf") if same_file else destination
        try:
            self._write_pdf(output, password)
            replacement, _ = self._load_pdf(output, credentials)
            replacement.close()
            if same_file:
                self.document.close()
                output.replace(destination)
            reopened, warnings = self._load_pdf(destination, credentials)
            previous = self._document
            self._document = reopened
            self._open_warnings = warnings
            if previous is not None and not previous.is_closed:
                previous.close()
        finally:
            if same_file:
                output.unlink(missing_ok=True)

    def _write_pdf(self, destination: Path, password: str | None) -> None:
        if password is None:
            self.document.save(
                destination, garbage=4, deflate=True, encryption=fitz.PDF_ENCRYPT_KEEP
            )
            return
        self.document.save(
            destination, garbage=4, deflate=True, encryption=fitz.PDF_ENCRYPT_AES_256,
            user_pw=password, owner_pw=password,
        )

    def close(self) -> None:
        if self._document is not None:
            self._document.close()
        self._document = None
        self._path = None
        self._dirty = False
        self._open_warnings = False
        self._password = None
