from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QTextBrowser, QVBoxLayout, QWidget

from sabl_pdf.services.updates import AvailableUpdate


class UpdateAvailableDialog(QDialog):
    def __init__(
        self, installed_version: str, update: AvailableUpdate, parent: QWidget | None = None, can_install: bool = True
    ) -> None:
        super().__init__(parent)
        self._release_url = update.url
        self.setWindowTitle("Simple PDF update available")
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
        install = buttons.addButton("Update now", QDialogButtonBox.ButtonRole.AcceptRole)
        install.setObjectName("install_update_button")
        install.setEnabled(can_install)
        if not can_install:
            install.setToolTip("Automatic installation requires the installed Windows application")
        install.clicked.connect(self.accept)
        view_release = buttons.addButton("View on GitHub", QDialogButtonBox.ButtonRole.ActionRole)
        view_release.setObjectName("view_release_button")
        view_release.clicked.connect(self._open_release)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _open_release(self) -> None:
        QDesktopServices.openUrl(QUrl(self._release_url))
