import sys
from collections.abc import Callable
from urllib.parse import quote

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices

from sabl_pdf.branding import DISPLAY_NAME


def open_default_apps_settings(
    launch: Callable[[QUrl], bool] = QDesktopServices.openUrl,
) -> bool:
    if sys.platform != "win32":
        return False
    application = quote(DISPLAY_NAME, safe="")
    specific = QUrl(f"ms-settings:defaultapps?registeredAppUser={application}")
    general = QUrl("ms-settings:defaultapps")
    return launch(specific) or launch(general)
