from __future__ import annotations

import base64
import hashlib
import re
from pathlib import Path

from .constants import MANIFEST_NAMES_BY_CHANNEL, forbidden_manifest_names
from .dispatch import normalize_package_version

VERSION_LINE = re.compile(r"^version:\s*(\S+)\s*$", re.MULTILINE)
FILE_BLOCK = re.compile(
    r"^\s*-\s*url:\s*(\S+)\s*$.*?"
    r"^\s*sha512:\s*(\S+)\s*$.*?"
    r"^\s*size:\s*(\d+)\s*$",
    re.MULTILINE | re.DOTALL,
)
TOP_PATH = re.compile(r"^path:\s*(\S+)\s*$", re.MULTILINE)
TOP_SHA512 = re.compile(r"^sha512:\s*(\S+)\s*$", re.MULTILINE)


def collect_artifact_manifests(root: Path) -> list[Path]:
    names = set()
    for group in MANIFEST_NAMES_BY_CHANNEL.values():
        names.update(group)
    found: list[Path] = []
    for path in root.rglob("*"):
        if path.is_file() and path.name in names:
            found.append(path)
    return found


def _sha512_file(path: Path) -> str:
    digest = hashlib.sha512(path.read_bytes()).digest()
    return base64.b64encode(digest).decode("ascii")


def _parse_manifest(text: str) -> tuple[str, list[tuple[str, str, int]]]:
    version_m = VERSION_LINE.search(text)
    if not version_m:
        raise ValueError("manifest missing version:")
    version = version_m.group(1)
    entries: list[tuple[str, str, int]] = []
    for m in FILE_BLOCK.finditer(text):
        entries.append((m.group(1), m.group(2), int(m.group(3))))
    if not entries:
        path_m = TOP_PATH.search(text)
        sha_m = TOP_SHA512.search(text)
        if path_m and sha_m:
            size_m = re.search(r"^size:\s*(\d+)\s*$", text, re.MULTILINE)
            if not size_m:
                raise ValueError("manifest missing size for top-level path")
            entries.append((path_m.group(1), sha_m.group(1), int(size_m.group(1))))
    if not entries:
        raise ValueError("manifest has no file entries")
    return version, entries


def validate_artifact_tree(
    artifacts_root: Path,
    channel: str,
    release_version: str,
) -> None:
    expected_pkg = normalize_package_version(release_version)
    forbidden = set(forbidden_manifest_names(channel))
    expected_names = set(MANIFEST_NAMES_BY_CHANNEL[channel])

    seen_forbidden: list[str] = []
    for path in artifacts_root.rglob("*"):
        if path.is_file() and path.name in forbidden:
            seen_forbidden.append(str(path.relative_to(artifacts_root)))

    if seen_forbidden:
        raise ValueError(
            f"forbidden stable/nightly cross-manifests for {channel}: "
            + ", ".join(sorted(seen_forbidden))
        )

    manifests = [
        p
        for p in artifacts_root.rglob("*")
        if p.is_file() and p.name in expected_names
    ]
    missing = expected_names - {p.name for p in manifests}
    if missing:
        raise ValueError(f"missing manifests for {channel}: {sorted(missing)}")

    for manifest_path in manifests:
        text = manifest_path.read_text(encoding="utf-8")
        version, entries = _parse_manifest(text)
        if version != expected_pkg:
            raise ValueError(
                f"{manifest_path.name}: version {version!r} != {expected_pkg!r}"
            )
        expected_suffix = '-mac.zip' if '-mac.yml' in manifest_path.name else '.AppImage' if '-linux.yml' in manifest_path.name else '.exe'
        if not any(url.endswith(expected_suffix) for url, _, _ in entries):
            raise ValueError(f'{manifest_path.name}: wrong platform artifact type')
        if '-mac.yml' in manifest_path.name:
            zip_urls = [url for url, _, _ in entries if url.endswith('-mac.zip')]
            if not any('arm64' in url for url in zip_urls) or not any('arm64' not in url for url in zip_urls):
                raise ValueError('macOS manifest must include arm64 and x64 archives')
        manifest_dir = manifest_path.parent
        for url, sha512_expected, size_expected in entries:
            if Path(url).name != url or any(char in url for char in ('/', '\\', '|', ':')):
                raise ValueError('Manifest artifact URL must be a local basename')
            if expected_pkg not in url:
                raise ValueError('Manifest artifact filename must contain the full release version')
            artifact = manifest_dir / url
            if not artifact.is_file():
                for candidate in artifacts_root.rglob(url):
                    if candidate.is_file():
                        artifact = candidate
                        break
            if not artifact.is_file():
                raise ValueError(f"{manifest_path.name}: missing artifact {url!r}")
            if artifact.stat().st_size != size_expected:
                raise ValueError(
                    f"{manifest_path.name}: size mismatch for {url!r}"
                )
            actual_sha = _sha512_file(artifact)
            if actual_sha != sha512_expected:
                raise ValueError(
                    f"{manifest_path.name}: sha512 mismatch for {url!r}"
                )
            if expected_pkg not in artifact.name and channel == "nightly":
                raise ValueError(
                    f"nightly artifact name must include version: {artifact.name}"
                )
