from pathlib import Path
from unittest.mock import Mock

import fitz
import pytest


@pytest.fixture
def encrypted_pdf(sample_pdf: Path, tmp_path: Path) -> Path:
    destination = tmp_path / "encrypted.pdf"
    with fitz.open(sample_pdf) as document:
        document.save(
            destination, encryption=fitz.PDF_ENCRYPT_AES_256,
            user_pw="secret", owner_pw="secret",
        )
    return destination


def test_open_encrypted_pdf_prompts_for_masked_password(encrypted_pdf: Path, monkeypatch) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QInputDialog, QLineEdit
    from sabl_pdf.ui.window import MainWindow

    application = QApplication.instance() or QApplication([])
    window = MainWindow()
    prompt = Mock(return_value=("secret", True))
    monkeypatch.setattr(QInputDialog, "getText", prompt)

    window.open_path(encrypted_pdf)

    assert application is not None
    assert window.document_tabs.count() == 1
    assert "Hello SABL" in window.viewer.text(0)
    assert prompt.call_args.args[3] == QLineEdit.EchoMode.Password
    window.close()


def test_open_retries_after_incorrect_password(encrypted_pdf: Path, monkeypatch) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QInputDialog, QMessageBox
    from sabl_pdf.ui.window import MainWindow

    application = QApplication.instance() or QApplication([])
    window = MainWindow()
    prompt = Mock(side_effect=[("wrong", True), ("secret", True)])
    monkeypatch.setattr(QInputDialog, "getText", prompt)
    warning = Mock()
    monkeypatch.setattr(QMessageBox, "warning", warning)

    window.open_path(encrypted_pdf)

    assert application is not None
    assert prompt.call_count == 2
    warning.assert_called_once()
    assert "Hello SABL" in window.viewer.text(0)
    window.close()


def test_cancel_password_prompt_keeps_current_tab(
    sample_pdf: Path, encrypted_pdf: Path, monkeypatch
) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QInputDialog
    from sabl_pdf.ui.window import MainWindow

    application = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.open_path(sample_pdf)
    monkeypatch.setattr(QInputDialog, "getText", lambda *args: ("", False))

    window.open_path(encrypted_pdf)

    assert application is not None
    assert window.document_tabs.count() == 1
    assert window.session.path == sample_pdf
    window.close()


def test_protection_dialog_requires_nonempty_password() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QDialog
    from sabl_pdf.ui.password_protection_dialog import PasswordProtectionDialog

    application = QApplication.instance() or QApplication([])
    dialog = PasswordProtectionDialog()

    dialog.accept()

    assert application is not None
    assert dialog.result() != QDialog.DialogCode.Accepted
    assert dialog.error.text() == "Enter a password."
    dialog.close()


def test_protection_dialog_requires_matching_passwords() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QDialog
    from sabl_pdf.ui.password_protection_dialog import PasswordProtectionDialog

    application = QApplication.instance() or QApplication([])
    dialog = PasswordProtectionDialog()
    dialog.password_edit.setText("secret")
    dialog.confirm_edit.setText("other")

    dialog.accept()

    assert application is not None
    assert dialog.result() != QDialog.DialogCode.Accepted
    assert dialog.error.text() == "Passwords do not match."
    dialog.close()


def test_protection_dialog_accepts_matching_masked_passwords() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QDialog, QLineEdit
    from sabl_pdf.ui.password_protection_dialog import PasswordProtectionDialog

    application = QApplication.instance() or QApplication([])
    dialog = PasswordProtectionDialog()
    dialog.password_edit.setText("secret")
    dialog.confirm_edit.setText("secret")

    dialog.accept()

    assert application is not None
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert dialog.password == "secret"
    assert dialog.password_edit.echoMode() == QLineEdit.EchoMode.Password
    assert dialog.confirm_edit.echoMode() == QLineEdit.EchoMode.Password
    dialog.close()


def test_protect_pdf_creates_encrypted_copy(sample_pdf: Path, tmp_path: Path, monkeypatch) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QDialog, QFileDialog
    from sabl_pdf.ui.password_protection_dialog import PasswordProtectionDialog
    from sabl_pdf.ui.window import MainWindow

    application = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.open_path(sample_pdf)
    destination = tmp_path / "protected.pdf"
    monkeypatch.setattr(PasswordProtectionDialog, "exec", lambda self: QDialog.DialogCode.Accepted)
    monkeypatch.setattr(PasswordProtectionDialog, "password", property(lambda self: "secret"))
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: (str(destination), ""))

    window.protect_pdf()

    assert application is not None
    assert window.session.path == destination
    with fitz.open(destination) as document:
        assert document.needs_pass
        assert document.authenticate("secret")
        assert "Hello SABL" in document[0].get_text()
    with fitz.open(sample_pdf) as original:
        assert not original.needs_pass
    window.close()


def test_protect_action_is_disabled_without_document(sample_pdf: Path) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication
    from sabl_pdf.ui.window import MainWindow

    application = QApplication.instance() or QApplication([])
    window = MainWindow()

    assert application is not None
    assert not window.protect_pdf_action.isEnabled()

    window.open_path(sample_pdf)

    assert window.protect_pdf_action.isEnabled()
    window.close()
