from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit, QVBoxLayout, QWidget,
)


class PasswordProtectionDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Protect PDF with password")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "A password will be required to open the saved PDF. "
            "Encryption uses AES-256 and may invalidate digital signatures."
        ))
        form = QFormLayout()
        self.password_edit = QLineEdit(self)
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setObjectName("password_entry")
        self.confirm_edit = QLineEdit(self)
        self.confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_edit.setObjectName("password_confirmation")
        form.addRow("Password", self.password_edit)
        form.addRow("Confirm password", self.confirm_edit)
        layout.addLayout(form)
        self.error = QLabel("", self)
        self.error.setObjectName("password_error")
        layout.addWidget(self.error)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.password_edit.setFocus()

    @property
    def password(self) -> str:
        return self.password_edit.text()

    def accept(self) -> None:
        if not self.password:
            self.error.setText("Enter a password.")
            return
        if self.password != self.confirm_edit.text():
            self.error.setText("Passwords do not match.")
            return
        super().accept()
