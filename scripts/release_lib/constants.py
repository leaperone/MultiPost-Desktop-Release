from __future__ import annotations

RELEASE_CHANNEL_RELEASE = "release"
RELEASE_CHANNEL_NIGHTLY = "nightly"
VALID_CHANNELS = frozenset({RELEASE_CHANNEL_RELEASE, RELEASE_CHANNEL_NIGHTLY})

S3_PREFIX_BY_CHANNEL = {
    RELEASE_CHANNEL_RELEASE: "release/multipost-desktop",
}

CDN_BASE_BY_CHANNEL = {
    RELEASE_CHANNEL_RELEASE: "https://static.2some.ren/release/multipost-desktop",
}

MANIFEST_NAMES_BY_CHANNEL = {
    RELEASE_CHANNEL_RELEASE: ("latest-mac.yml", "latest.yml", "latest-linux.yml"),
    RELEASE_CHANNEL_NIGHTLY: ("nightly-mac.yml", "nightly.yml", "nightly-linux.yml"),
}

FORBIDDEN_MANIFESTS_BY_CHANNEL = {
    RELEASE_CHANNEL_RELEASE: MANIFEST_NAMES_BY_CHANNEL[RELEASE_CHANNEL_NIGHTLY],
    RELEASE_CHANNEL_NIGHTLY: MANIFEST_NAMES_BY_CHANNEL[RELEASE_CHANNEL_RELEASE],
}

FORBIDDEN_PUBLIC_ASSET_SUBSTRINGS = (
    ".env",
    "credential",
    "secret",
    "prompt",
    ".p12",
    ".pem",
    "private_repo",
    "id_rsa",
)


def require_s3_eligible_channel(channel: str) -> None:
    """Refuse S3/CDN planning or upload for GitHub-only channels before network I/O."""
    normalized = channel.strip().lower()
    if normalized == RELEASE_CHANNEL_NIGHTLY:
        raise ValueError(
            "nightly channel is GitHub-only; S3/CDN upload and sync are not permitted"
        )
    if normalized not in S3_PREFIX_BY_CHANNEL:
        raise ValueError(f"invalid channel {channel!r} for S3 operations")


def forbidden_manifest_names(channel: str) -> tuple[str, ...]:
    return FORBIDDEN_MANIFESTS_BY_CHANNEL[channel]


def alias_destinations(channel: str) -> tuple[tuple[str, str, str | None], ...]:
    """Return (glob_pattern, dest_basename, exclude_glob) tuples for stable aliases."""
    require_s3_eligible_channel(channel)
    return (
        ("*arm64*.dmg", "MultiPost-mac-latest.dmg", None),
        ("*arm64-mac.zip", "MultiPost-mac-latest.zip", None),
        ("*x64*.dmg", "MultiPost-mac-x64-latest.dmg", None),
        ("*-mac.zip", "MultiPost-mac-x64-latest.zip", "*arm64-mac.zip"),
        ("*.exe", "MultiPost-Setup-latest.exe", None),
        ("*.AppImage", "MultiPost-latest.AppImage", None),
        ("*.deb", "MultiPost-latest.deb", None),
    )
