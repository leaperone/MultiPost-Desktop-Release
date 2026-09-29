from __future__ import annotations

import re

from .constants import RELEASE_CHANNEL_NIGHTLY, RELEASE_CHANNEL_RELEASE, VALID_CHANNELS
from .semver import NIGHTLY_VERSION_PATTERN, RELEASE_VERSION_PATTERN

FULL_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def normalize_package_version(release_version: str) -> str:
    v = release_version.strip()
    if v.startswith("v"):
        v = v[1:]
    return v


def desktop_source_ref(release_version: str) -> str:
    version = release_version.strip()
    if not version.startswith("v"):
        raise ValueError("release version must start with v")
    return f"refs/tags/desktop-{version}"


def validate_dispatch_inputs(
    channel: str,
    version: str,
    source_sha: str,
    *,
    require_full_sha: bool = True,
) -> dict[str, str]:
    channel = (channel or "").strip().lower()
    version = (version or "").strip()
    source_sha = (source_sha or "").strip().lower()

    if channel not in VALID_CHANNELS:
        raise ValueError(f"invalid channel {channel!r}; want release or nightly")
    if not version.startswith("v"):
        raise ValueError("version must start with v")

    if channel == RELEASE_CHANNEL_RELEASE:
        if not RELEASE_VERSION_PATTERN.fullmatch(version):
            raise ValueError("release channel requires vX.Y.Z without nightly suffix")
    elif channel == RELEASE_CHANNEL_NIGHTLY:
        if not NIGHTLY_VERSION_PATTERN.fullmatch(version):
            raise ValueError(
                "nightly channel requires vX.Y.Z-nightly.YYYYMMDD.N"
            )

    if require_full_sha:
        if not FULL_SHA_PATTERN.fullmatch(source_sha):
            raise ValueError("source_sha must be a 40-char lowercase git commit id")

    return {
        "channel": channel,
        "version": version,
        "source_sha": source_sha,
        "package_version": normalize_package_version(version),
        "source_ref": desktop_source_ref(version),
    }
