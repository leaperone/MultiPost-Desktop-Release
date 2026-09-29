from __future__ import annotations

import fnmatch
from pathlib import Path

from .constants import MANIFEST_NAMES_BY_CHANNEL, alias_destinations

ARTIFACT_GLOBS = (
    "*.dmg",
    "*.zip",
    "*.exe",
    "*.AppImage",
    "*.deb",
    "*.snap",
    "*.blockmap",
)


def _matches_any(name: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatch(name, pat) for pat in patterns)


def _find_unique(root: Path, pattern: str, exclude: str | None = None) -> Path:
    matches = [
        p
        for p in root.rglob("*")
        if p.is_file()
        and fnmatch.fnmatch(p.name, pattern)
        and (not exclude or not fnmatch.fnmatch(p.name, exclude))
    ]
    if len(matches) != 1:
        raise ValueError(
            f"expected exactly one match for pattern={pattern!r}"
            f"{f', exclude={exclude!r}' if exclude else ''}, got {len(matches)}"
        )
    return matches[0]


def build_upload_plan_lines(artifacts_root: Path, channel: str) -> list[str]:
    """Return src|dest lines for S3 upload (dest is object basename)."""
    manifest_names = set(MANIFEST_NAMES_BY_CHANNEL[channel])
    lines: list[str] = []
    seen_dest: set[str] = set()

    def add(src: Path, dest: str) -> None:
        if dest in seen_dest:
            raise ValueError(f"duplicate upload destination {dest!r}")
        seen_dest.add(dest)
        lines.append(f"{src}|{dest}")

    for path in sorted(artifacts_root.rglob("*")):
        if not path.is_file():
            continue
        name = path.name
        if name in manifest_names or _matches_any(name, ARTIFACT_GLOBS):
            add(path, name)

    for pattern, dest, exclude in alias_destinations(channel):
        add(_find_unique(artifacts_root, pattern, exclude), dest)

    return lines
