from __future__ import annotations

RELEASE_CHANNEL_RELEASE = "release"
RELEASE_CHANNEL_NIGHTLY = "nightly"
VALID_CHANNELS = frozenset({RELEASE_CHANNEL_RELEASE, RELEASE_CHANNEL_NIGHTLY})

S3_PREFIX_BY_CHANNEL = {
    RELEASE_CHANNEL_RELEASE: "release/multipost-desktop",
    RELEASE_CHANNEL_NIGHTLY: "release/multipost-desktop-nightly",
}

CDN_BASE_BY_CHANNEL = {
    RELEASE_CHANNEL_RELEASE: "https://static.2some.ren/release/multipost-desktop",
    RELEASE_CHANNEL_NIGHTLY: "https://static.2some.ren/release/multipost-desktop-nightly",
}

MANIFEST_NAMES_BY_CHANNEL = {
    RELEASE_CHANNEL_RELEASE: ("latest-mac.yml", "latest.yml", "latest-linux.yml"),
    RELEASE_CHANNEL_NIGHTLY: ("nightly-mac.yml", "nightly.yml", "nightly-linux.yml"),
}

FORBIDDEN_MANIFESTS_BY_CHANNEL = {
    RELEASE_CHANNEL_RELEASE: MANIFEST_NAMES_BY_CHANNEL[RELEASE_CHANNEL_NIGHTLY],
    RELEASE_CHANNEL_NIGHTLY: MANIFEST_NAMES_BY_CHANNEL[RELEASE_CHANNEL_RELEASE],
}


def forbidden_manifest_names(channel: str) -> tuple[str, ...]:
    return FORBIDDEN_MANIFESTS_BY_CHANNEL[channel]


def alias_destinations(channel: str) -> tuple[tuple[str, str, str | None], ...]:
    """Return (glob_pattern, dest_basename, exclude_glob) tuples for stable aliases."""
    if channel == RELEASE_CHANNEL_RELEASE:
        return (
            ("*arm64*.dmg", "MultiPost-mac-latest.dmg", None),
            ("*arm64-mac.zip", "MultiPost-mac-latest.zip", None),
            ("*x64*.dmg", "MultiPost-mac-x64-latest.dmg", None),
            ("*-mac.zip", "MultiPost-mac-x64-latest.zip", "*arm64-mac.zip"),
            ("*.exe", "MultiPost-Setup-latest.exe", None),
            ("*.AppImage", "MultiPost-latest.AppImage", None),
            ("*.deb", "MultiPost-latest.deb", None),
        )
    return (
        ("*arm64*.dmg", "MultiPost-mac-nightly.dmg", None),
        ("*arm64-mac.zip", "MultiPost-mac-nightly.zip", None),
        ("*x64*.dmg", "MultiPost-mac-x64-nightly.dmg", None),
        ("*-mac.zip", "MultiPost-mac-x64-nightly.zip", "*arm64-mac.zip"),
        ("*.exe", "MultiPost-Setup-nightly.exe", None),
        ("*.AppImage", "MultiPost-nightly.AppImage", None),
        ("*.deb", "MultiPost-nightly.deb", None),
    )
