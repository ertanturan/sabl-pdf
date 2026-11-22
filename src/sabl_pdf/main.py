import os
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from sabl_pdf.branding import DISPLAY_NAME
from sabl_pdf.ui.window import MainWindow


def main() -> int:
    bundle_directory = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[2]
    tessdata_directory = bundle_directory / "tessdata"
    if tessdata_directory.is_dir():
        os.environ.setdefault("TESSDATA_PREFIX", str(tessdata_directory))
    application = QApplication(sys.argv)
    application.setApplicationName(DISPLAY_NAME)
    window = MainWindow()
    if len(sys.argv) > 1:
        window.open_path(Path(sys.argv[1]))
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
