from io import BytesIO
from pathlib import Path
from unittest.mock import Mock

import pytest

from sabl_pdf.services.update_installer import (
    InstallerAsset,
    download_verified_installer,
    parse_installer_asset,
)


INSTALLER_CONTENT = b"simple-pdf-test-installer"
INSTALLER_HASH = "9becd61db975a971574489a4546f11c7d14f9bcd803c6433ff1eb7b4de3cde17"
INSTALLER_URL = "https://github.com/ertanturan/sabl-pdf/releases/download/v2.0.0/Simple-PDF-Setup-v2.0.0-x64.exe"
VALID_RELEASE = (
    b'{"tag_name":"v2.0.0","draft":false,"prerelease":false,"assets":['
    b'{"name":"Simple-PDF-Setup-v2.0.0-x64.exe",'
    b'"browser_download_url":"https://github.com/ertanturan/sabl-pdf/releases/download/'
    b'v2.0.0/Simple-PDF-Setup-v2.0.0-x64.exe",'
    b'"digest":"sha256:9becd61db975a971574489a4546f11c7d14f9bcd803c6433ff1eb7b4de3cde17",'
    b'"size":25}]}'
)
BAD_CHECKSUM_RELEASE = (
    b'{"tag_name":"v2.0.0","draft":false,"prerelease":false,"assets":['
    b'{"name":"Simple-PDF-Setup-v2.0.0-x64.exe",'
    b'"browser_download_url":"https://github.com/ertanturan/sabl-pdf/releases/download/'
    b'v2.0.0/Simple-PDF-Setup-v2.0.0-x64.exe",'
    b'"digest":"sha256:0000000000000000000000000000000000000000000000000000000000000000",'
    b'"size":25}]}'
)
MISSING_DIGEST_RELEASE = (
    b'{"tag_name":"v2.0.0","draft":false,"prerelease":false,"assets":['
    b'{"name":"Simple-PDF-Setup-v2.0.0-x64.exe",'
    b'"browser_download_url":"https://github.com/ertanturan/sabl-pdf/releases/download/'
    b'v2.0.0/Simple-PDF-Setup-v2.0.0-x64.exe","size":25}]}'
)
UNTRUSTED_URL_RELEASE = (
    b'{"tag_name":"v2.0.0","draft":false,"prerelease":false,"assets":['
    b'{"name":"Simple-PDF-Setup-v2.0.0-x64.exe",'
    b'"browser_download_url":"https://example.com/installer.exe",'
    b'"digest":"sha256:9becd61db975a971574489a4546f11c7d14f9bcd803c6433ff1eb7b4de3cde17",'
    b'"size":25}]}'
)


def test_installer_asset_uses_expected_release_and_checksum() -> None:
    asset = parse_installer_asset(VALID_RELEASE, "2.0.0")

    assert asset == InstallerAsset(INSTALLER_URL, INSTALLER_HASH, 25)


@pytest.mark.parametrize(
    ("payload", "error_message"),
    (
        (MISSING_DIGEST_RELEASE, "SHA-256"),
        (UNTRUSTED_URL_RELEASE, "not trusted"),
        (b'{"tag_name":"v2.0.0","draft":false,"prerelease":false,"assets":[]}', "no Windows installer"),
        (b'{"tag_name":"v2.0.0","draft":true,"prerelease":false,"assets":[]}', "stable release"),
        (b'{"tag_name":"v2.0.0","draft":false,"prerelease":true,"assets":[]}', "stable release"),
        (b"bad json", "Invalid release metadata"),
    ),
)
def test_rejects_untrusted_installer_metadata(payload: bytes, error_message: str) -> None:
    with pytest.raises(ValueError, match=error_message):
        parse_installer_asset(payload, "2.0.0")


def test_rejects_release_changed_after_update_notice() -> None:
    with pytest.raises(ValueError, match="expected stable release"):
        parse_installer_asset(VALID_RELEASE, "3.0.0")


def test_download_verifies_checksum_before_returning_path(tmp_path: Path, monkeypatch) -> None:
    progress = Mock()
    cancelled = Mock(return_value=False)
    network = Mock(side_effect=[BytesIO(VALID_RELEASE), BytesIO(INSTALLER_CONTENT)])
    monkeypatch.setattr("sabl_pdf.services.update_installer.urlopen", network)

    installer = download_verified_installer("2.0.0", progress, cancelled, tmp_path)

    assert installer == tmp_path / "Simple-PDF-Setup-v2.0.0-x64.exe"
    assert installer.read_bytes() == INSTALLER_CONTENT
    progress.assert_called_once_with(25, 25)
    assert network.call_count == 2


def test_checksum_mismatch_deletes_download(tmp_path: Path, monkeypatch) -> None:
    progress = Mock()
    cancelled = Mock(return_value=False)
    network = Mock(side_effect=[BytesIO(BAD_CHECKSUM_RELEASE), BytesIO(INSTALLER_CONTENT)])
    monkeypatch.setattr("sabl_pdf.services.update_installer.urlopen", network)

    with pytest.raises(ValueError, match="checksum verification failed"):
        download_verified_installer("2.0.0", progress, cancelled, tmp_path)

    assert not (tmp_path / "Simple-PDF-Setup-v2.0.0-x64.exe").exists()


def test_incomplete_download_is_rejected(tmp_path: Path, monkeypatch) -> None:
    progress = Mock()
    cancelled = Mock(return_value=False)
    network = Mock(side_effect=[BytesIO(VALID_RELEASE), BytesIO(b"truncated")])
    monkeypatch.setattr("sabl_pdf.services.update_installer.urlopen", network)

    with pytest.raises(ValueError, match="incomplete"):
        download_verified_installer("2.0.0", progress, cancelled, tmp_path)

    assert not (tmp_path / "Simple-PDF-Setup-v2.0.0-x64.exe").exists()


def test_cancelling_before_download_does_not_request_binary(tmp_path: Path, monkeypatch) -> None:
    progress = Mock()
    cancelled = Mock(return_value=True)
    network = Mock(return_value=BytesIO(VALID_RELEASE))
    monkeypatch.setattr("sabl_pdf.services.update_installer.urlopen", network)

    with pytest.raises(InterruptedError, match="cancelled"):
        download_verified_installer("2.0.0", progress, cancelled, tmp_path)

    network.assert_called_once()


def test_cancelling_during_download_deletes_partial_file(tmp_path: Path, monkeypatch) -> None:
    progress = Mock()
    cancelled = Mock(side_effect=[False, True])
    network = Mock(side_effect=[BytesIO(VALID_RELEASE), BytesIO(INSTALLER_CONTENT)])
    monkeypatch.setattr("sabl_pdf.services.update_installer.urlopen", network)

    with pytest.raises(InterruptedError, match="cancelled"):
        download_verified_installer("2.0.0", progress, cancelled, tmp_path)

    assert not (tmp_path / "Simple-PDF-Setup-v2.0.0-x64.exe").exists()
