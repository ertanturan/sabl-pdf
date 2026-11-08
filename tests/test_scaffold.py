from sabl_pdf import __version__


def test_version_is_defined() -> None:
    version = __version__

    assert version == "0.1.0"
