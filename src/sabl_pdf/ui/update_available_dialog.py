from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QTextBrowser, QVBoxLayout, QWidget

from sabl_pdf.services.updates import AvailableUpdate


class UpdateAvailableDialog(QDialog):
    def __init__(
        self, installed_version: str, update: AvailableUpdate, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._release_url = update.url
        self.setWindowTitle("SABL PDF update available")
        self.resize(640, 520)
        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(f"Installed: v{installed_version}     Available: v{update.version}", self)
        )
        content = QTextBrowser(self)
        content.setObjectName("available_update_notes")
        content.setOpenLinks(False)
        content.setMarkdown(update.notes or "No release notes were provided.")
        layout.addWidget(content)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        buttons.addButton("View on GitHub", QDialogButtonBox.ButtonRole.ActionRole).clicked.connect(
            self._open_release
        )
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _open_release(self) -> None:
        QDesktopServices.openUrl(QUrl(self._release_url))
