from PySide6.QtCore import QThread, Signal

from sabl_pdf.services.update_installer import download_verified_installer


class UpdateDownloadThread(QThread):
    progress = Signal(int, int)
    downloaded = Signal(str)
    failed = Signal(str)

    def __init__(self, version: str) -> None:
        super().__init__()
        self._version = version

    def run(self) -> None:
        try:
            path = download_verified_installer(
                self._version, self._report_progress, self.isInterruptionRequested
            )
        except Exception as error:
            self.failed.emit(str(error))
            return
        self.downloaded.emit(str(path))

    def _report_progress(self, received: int, total: int) -> None:
        self.progress.emit(received, total)
