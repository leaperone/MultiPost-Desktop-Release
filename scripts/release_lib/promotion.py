from __future__ import annotations

from .semver import parse_version_key, version_key_to_str


def promotion_allowed(new_version: str, existing_version: str | None, *, allow_same: bool = False) -> bool:
    """True when new_version is strictly newer than existing manifest version."""
    new_key = parse_version_key(new_version)
    if not existing_version:
        return True
    existing_key = parse_version_key(existing_version)
    return new_key > existing_key or (allow_same and new_key == existing_key)


__all__ = ["parse_version_key", "version_key_to_str", "promotion_allowed"]
