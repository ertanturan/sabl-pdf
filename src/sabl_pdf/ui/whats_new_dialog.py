from PySide6.QtWidgets import QDialog, QDialogButtonBox, QTextBrowser, QVBoxLayout, QWidget


class WhatsNewDialog(QDialog):
    def __init__(self, version: str, notes: str | None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"What's New in SABL PDF v{version}")
        self.resize(640, 520)
        layout = QVBoxLayout(self)
        content = QTextBrowser(self)
        content.setObjectName("release_notes_text")
        content.setOpenLinks(False)
        content.setMarkdown(
            notes or f"# SABL PDF v{version}\n\nRelease notes are unavailable for this version."
        )
        layout.addWidget(content)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
