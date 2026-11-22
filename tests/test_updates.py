import pytest

from sabl_pdf.services.updates import (
    AvailableUpdate,
    automatic_check_due,
    parse_latest_release,
    parse_version,
)


def test_parses_stable_version_tag() -> None:
    version = parse_version("v1.12.3")

    assert version == (1, 12, 3)


@pytest.mark.parametrize("tag", ("v01.2.3", "1.2.3", "v1.2.3-beta", "v1.2"))
def test_rejects_invalid_version_tag(tag: str) -> None:
    with pytest.raises(ValueError, match="version is invalid"):
        parse_version(tag)


def test_newer_release_includes_only_its_own_notes() -> None:
    payload = b'{"tag_name":"v1.1.0","body":"## Bugfixes\\n- Fixed edit.","draft":false,"prerelease":false}'

    update = parse_latest_release(payload, "1.0.0")

    assert update == AvailableUpdate(
        "1.1.0",
        "## Bugfixes\n- Fixed edit.",
        "https://github.com/ertanturan/sabl-pdf/releases/tag/v1.1.0",
    )


def test_same_release_is_up_to_date() -> None:
    payload = b'{"tag_name":"v1.0.0","body":"No changes","draft":false,"prerelease":false}'

    update = parse_latest_release(payload, "1.0.0")

    assert update is None


def test_older_release_is_not_an_update() -> None:
    payload = b'{"tag_name":"v0.9.9","body":"Old release","draft":false,"prerelease":false}'

    update = parse_latest_release(payload, "1.0.0")

    assert update is None


@pytest.mark.parametrize(
    "payload",
    (
        b'{"tag_name":"v2.0.0","body":"Candidate","draft":true}',
        b'{"tag_name":"v2.0.0","body":"Candidate","prerelease":true}',
    ),
)
def test_draft_or_prerelease_is_rejected(payload: bytes) -> None:
    with pytest.raises(ValueError, match="stable release"):
        parse_latest_release(payload, "1.0.0")


@pytest.mark.parametrize(
    "payload",
    (
        b'invalid',
        b'[]',
        b'{"tag_name":"not-semver","body":"Notes"}',
        b'{"tag_name":"v2.0.0","body":4}',
        b'{"tag_name":null,"body":"Notes"}',
    ),
)
def test_invalid_metadata_is_rejected(payload: bytes) -> None:
    with pytest.raises(ValueError):
        parse_latest_release(payload, "1.0.0")


def test_release_notes_are_limited_to_64_kib() -> None:
    payload = ('{"tag_name":"v2.0.0","body":"' + "x" * 65537 + '"}').encode("utf-8")

    with pytest.raises(ValueError, match="invalid release information"):
        parse_latest_release(payload, "1.0.0")


@pytest.mark.parametrize(
    ("last", "now", "expected"),
    (
        (0.0, 180000.0, True),
        (100000.0, 186399.0, False),
        (100000.0, 186400.0, True),
        (200000.0, 100000.0, True),
    ),
)
def test_automatic_check_interval(last: float, now: float, expected: bool) -> None:
    due = automatic_check_due(last, now)

    assert due is expected
