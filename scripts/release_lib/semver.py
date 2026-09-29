from __future__ import annotations

import re

VERSION_PATTERN = re.compile(
    r"^v?(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
    r"(?:-nightly\.(?P<nightly_date>\d{8})\.(?P<nightly_seq>\d+))?$"
)

NIGHTLY_VERSION_PATTERN = re.compile(
    r"^v\d+\.\d+\.\d+-nightly\.\d{8}\.\d+$"
)

RELEASE_VERSION_PATTERN = re.compile(r"^v\d+\.\d+\.\d+$")


def parse_version_key(version: str) -> tuple[int, int, int, int, int, int]:
    """Sortable key: release beats nightly at the same x.y.z."""
    m = VERSION_PATTERN.match(version.strip())
    if not m:
        raise ValueError(f"invalid desktop version: {version!r}")
    major = int(m.group("major"))
    minor = int(m.group("minor"))
    patch = int(m.group("patch"))
    nightly_date = m.group("nightly_date")
    if nightly_date:
        return (
            major,
            minor,
            patch,
            1,
            int(nightly_date),
            int(m.group("nightly_seq")),
        )
    return (major, minor, patch, 2, 0, 0)


def version_key_to_str(key: tuple[int, int, int, int, int, int]) -> str:
    major, minor, patch, kind, d, seq = key
    if kind == 1:
        return f"{major}.{minor}.{patch}-nightly.{d}.{seq}"
    return f"{major}.{minor}.{patch}"
