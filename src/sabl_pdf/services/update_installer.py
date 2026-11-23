from collections.abc import Callable
from dataclasses import dataclass
import hashlib
import hmac
import json
from pathlib import Path
import re
import tempfile
from urllib.request import Request, urlopen

from sabl_pdf.services.updates import parse_version


RELEASE_API = "https://api.github.com/repos/ertanturan/sabl-pdf/releases/latest"
RELEASE_DOWNLOADS = "https://github.com/ertanturan/sabl-pdf/releases/download"
MAX_INSTALLER_BYTES = 250 * 1024 * 1024
CHUNK_SIZE = 128 * 1024


@dataclass(frozen=True)
class InstallerAsset:
    url: str
    sha256: str
    size: int


def parse_installer_asset(payload: bytes, expected_version: str) -> InstallerAsset:
    tag = f"v{expected_version}"
    parse_version(tag)
    try:
        release = json.loads(payload)
    except (ValueError, UnicodeDecodeError) as error:
        raise ValueError("Invalid release metadata") from error
    if not isinstance(release, dict):
        raise ValueError("Invalid release metadata")
    if release.get("tag_name") != tag or release.get("draft") is not False or release.get("prerelease") is not False:
        raise ValueError("The expected stable release is no longer available")
    assets = release.get("assets")
    if not isinstance(assets, list):
        raise ValueError("Release has no installer assets")
    filename = f"Simple-PDF-Setup-{tag}-x64.exe"
    asset = next(
        (item for item in assets if isinstance(item, dict) and item.get("name") == filename),
        None,
    )
    if asset is None:
        raise ValueError("This release has no Windows installer")
    url = asset.get("browser_download_url")
    digest = asset.get("digest")
    size = asset.get("size")
    if url != f"{RELEASE_DOWNLOADS}/{tag}/{filename}":
        raise ValueError("Installer download URL is not trusted")
    if not isinstance(digest, str) or re.fullmatch(r"sha256:[a-fA-F0-9]{64}", digest) is None:
        raise ValueError("Installer has no valid SHA-256 digest")
    if type(size) is not int or not 0 < size <= MAX_INSTALLER_BYTES:
        raise ValueError("Installer size is invalid")
    return InstallerAsset(url, digest[7:].lower(), size)


def download_verified_installer(
    version: str,
    progress: Callable[[int, int], None],
    cancelled: Callable[[], bool],
    directory: Path | None = None,
) -> Path:
    metadata_request = Request(
        RELEASE_API,
        headers={"User-Agent": "Simple-PDF", "Accept": "application/vnd.github+json"},
    )
    with urlopen(metadata_request, timeout=20) as response:
        payload = response.read(1024 * 1024 + 1)
    if len(payload) > 1024 * 1024:
        raise ValueError("Release metadata is too large")
    asset = parse_installer_asset(payload, version)
    if cancelled():
        raise InterruptedError("Update cancelled")
    folder = directory or Path(tempfile.mkdtemp(prefix="simple-pdf-update-"))
    installer = folder / f"Simple-PDF-Setup-v{version}-x64.exe"
    downloaded = 0
    digest = hashlib.sha256()
    try:
        request = Request(asset.url, headers={"User-Agent": "Simple-PDF"})
        with urlopen(request, timeout=30) as response, installer.open("wb") as output:
            while chunk := response.read(CHUNK_SIZE):
                if cancelled():
                    raise InterruptedError("Update cancelled")
                downloaded += len(chunk)
                if downloaded > asset.size:
                    raise ValueError("Installer exceeds the published size")
                digest.update(chunk)
                output.write(chunk)
                progress(downloaded, asset.size)
        if cancelled():
            raise InterruptedError("Update cancelled")
        if downloaded != asset.size:
            raise ValueError("Installer download is incomplete")
        if not hmac.compare_digest(digest.hexdigest(), asset.sha256):
            raise ValueError("Installer checksum verification failed")
        return installer
    except Exception:
        installer.unlink(missing_ok=True)
        if directory is None:
            folder.rmdir()
        raise
