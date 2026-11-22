from dataclasses import dataclass
import json
import re


VERSION_PATTERN = re.compile(r"^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
CHECK_INTERVAL_SECONDS = 86400


@dataclass(frozen=True)
class AvailableUpdate:
    version: str
    notes: str
    url: str


def parse_version(tag: str) -> tuple[int, int, int]:
    match = VERSION_PATTERN.fullmatch(tag)
    if match is None:
        raise ValueError("GitHub release version is invalid")
    return tuple(int(part) for part in match.groups())


def parse_latest_release(payload: bytes, installed_version: str) -> AvailableUpdate | None:
    try:
        data = json.loads(payload)
    except (ValueError, UnicodeDecodeError) as error:
        raise ValueError("GitHub returned invalid release information") from error
    if not isinstance(data, dict):
        raise ValueError("GitHub returned invalid release information")
    tag = data.get("tag_name")
    notes = data.get("body") or ""
    if not isinstance(tag, str) or not isinstance(notes, str) or len(notes) > 65536:
        raise ValueError("GitHub returned invalid release information")
    current = parse_version(f"v{installed_version}")
    available = parse_version(tag)
    if data.get("draft") or data.get("prerelease"):
        raise ValueError("GitHub did not return a stable release")
    if available <= current:
        return None
    url = f"https://github.com/ertanturan/sabl-pdf/releases/tag/{tag}"
    return AvailableUpdate(tag[1:], notes, url)


def automatic_check_due(last_checked: float, now: float) -> bool:
    return last_checked <= 0 or now < last_checked or now - last_checked >= CHECK_INTERVAL_SECONDS
