#!/usr/bin/env python3
"""Validate Nightly GitHub Release assets against locally built artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from release_lib.constants import (  # noqa: E402
    FORBIDDEN_PUBLIC_ASSET_SUBSTRINGS,
    MANIFEST_NAMES_BY_CHANNEL,
    RELEASE_CHANNEL_NIGHTLY,
)
from release_lib.dispatch import validate_dispatch_inputs  # noqa: E402
from release_lib.manifests import validate_artifact_tree  # noqa: E402
from release_lib.upload_plan import ARTIFACT_GLOBS  # noqa: E402

NIGHTLY_MANIFESTS = set(MANIFEST_NAMES_BY_CHANNEL[RELEASE_CHANNEL_NIGHTLY])

BINARY_GLOBS = ARTIFACT_GLOBS


def _matches_any(name: str, patterns: tuple[str, ...]) -> bool:
    import fnmatch

    return any(fnmatch.fnmatch(name, pat) for pat in patterns)


def assert_public_asset_name(name: str) -> None:
    if name not in NIGHTLY_MANIFESTS and not _matches_any(name, BINARY_GLOBS):
        raise ValueError(f"unsupported public asset name {name!r}")
    lowered = name.lower()
    for fragment in FORBIDDEN_PUBLIC_ASSET_SUBSTRINGS:
        if fragment in lowered:
            raise ValueError(f"forbidden public asset name {name!r}")


def validate_asset_names(names: list[str], version: str, channel: str) -> None:
    if channel != RELEASE_CHANNEL_NIGHTLY:
        raise ValueError("GitHub-only asset validation is only for the nightly channel")
    missing = NIGHTLY_MANIFESTS - set(names)
    if missing:
        raise ValueError(f"GitHub release is missing updater manifests: {sorted(missing)}")

    patterns = {
        "macOS arm64 DMG": re.compile(r"arm64.*\.dmg$", re.I),
        "macOS x64 DMG": re.compile(r"(?:x64|intel).*\.dmg$", re.I),
        "macOS arm64 ZIP": re.compile(r"arm64.*-mac\.zip$", re.I),
        "Windows installer": re.compile(r"\.exe$", re.I),
        "Linux AppImage": re.compile(r"\.AppImage$", re.I),
        "Linux deb": re.compile(r"\.deb$", re.I),
    }
    for label, pattern in patterns.items():
        if not any(pattern.search(name) for name in names):
            raise ValueError(f"GitHub release is missing {label} asset")
    if not any(
        name.endswith("-mac.zip") and "arm64" not in name.lower() for name in names
    ):
        raise ValueError("GitHub release is missing macOS x64 ZIP asset")
    pkg = version.lstrip("v")
    binaries = [
        n
        for n in names
        if n.endswith((".dmg", ".zip", ".exe", ".AppImage", ".deb"))
    ]
    if not binaries or not all(pkg in name for name in binaries):
        raise ValueError("Nightly binary asset names must include the full version")
    for name in names:
        assert_public_asset_name(name)


def _sha256_hex(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def collect_local_release_files(artifacts_root: Path, channel: str) -> dict[str, Path]:
    manifest_names = set(MANIFEST_NAMES_BY_CHANNEL[channel])
    found: dict[str, Path] = {}
    for path in artifacts_root.rglob("*"):
        if not path.is_file():
            continue
        name = path.name
        if name in manifest_names or _matches_any(name, BINARY_GLOBS):
            if name in found:
                raise ValueError(f"duplicate local artifact basename {name!r}")
            found[name] = path
    return found


def _normalize_remote_digest(digest: str | None) -> str | None:
    if not digest:
        return None
    text = digest.strip().lower()
    if text.startswith("sha256:"):
        return text.split(":", 1)[1]
    return text


def validate_remote_assets_match_local(
    release_assets: list[dict],
    local_by_name: dict[str, Path],
) -> None:
    remote_by_name = {a.get("name", ""): a for a in release_assets if a.get("name")}
    if len(remote_by_name) != len(release_assets):
        raise ValueError('duplicate or invalid GitHub asset names')
    if set(remote_by_name) - set(local_by_name):
        raise ValueError('GitHub release contains unvalidated extra assets')
    missing_remote = sorted(set(local_by_name) - set(remote_by_name))
    if missing_remote:
        raise ValueError(
            f"GitHub release missing locally validated assets: {missing_remote}"
        )

    for name, local_path in sorted(local_by_name.items()):
        remote = remote_by_name[name]
        local_size = local_path.stat().st_size
        remote_size = int(remote.get("size") or 0)
        if remote_size != local_size:
            raise ValueError(
                f"size mismatch for {name!r}: GitHub {remote_size} != local {local_size}"
            )
        local_sha = _sha256_hex(local_path)
        remote_sha = _normalize_remote_digest(remote.get("digest"))
        if remote_sha:
            if remote_sha != local_sha:
                raise ValueError(f"sha256 mismatch for {name!r} (GitHub digest vs local)")
            continue
        raise ValueError(f"GitHub asset {name!r} has no SHA256 digest")


def fetch_release(repo: str, version: str) -> dict:
    proc = subprocess.run(
        [
            "gh",
            "release",
            "view",
            version,
            "-R",
            repo,
            "--json",
            "tagName,isPrerelease,assets,body",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise ValueError(proc.stderr.strip() or "gh release view failed")
    return json.loads(proc.stdout)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", default=os.environ.get("RELEASE_CHANNEL", ""))
    parser.add_argument("--version", default=os.environ.get("RELEASE_VERSION", ""))
    parser.add_argument("--source-sha", default=os.environ.get("RELEASE_SOURCE_SHA", ""))
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument(
        "--artifacts-dir",
        default=os.environ.get("RELEASE_ARTIFACTS_DIR", ""),
    )
    args = parser.parse_args()
    try:
        validate_dispatch_inputs(args.channel, args.version, args.source_sha)
        if args.channel.strip().lower() != RELEASE_CHANNEL_NIGHTLY:
            raise ValueError("GitHub-only asset validation is only for the nightly channel")
        if not args.repo:
            raise ValueError("GITHUB_REPOSITORY is required")
        artifacts_root = Path(args.artifacts_dir) if args.artifacts_dir else None
        if not artifacts_root or not artifacts_root.is_dir():
            raise ValueError('locally built artifacts are required for GitHub verification')
        validate_artifact_tree(artifacts_root, args.channel, args.version)
        local_by_name = collect_local_release_files(artifacts_root, args.channel)

        release = fetch_release(args.repo, args.version)
        if release.get("tagName") != args.version or release.get("isPrerelease") is not True:
            raise ValueError("Nightly GitHub release must be a prerelease with the requested tag")
        body = release.get("body") or ""
        if args.source_sha.strip().lower() not in body.lower():
            raise ValueError("release body must contain source_sha evidence")
        if f"Channel: nightly" not in body:
            raise ValueError("release body must declare Channel: nightly")

        assets = release.get("assets") or []
        names = [asset.get("name", "") for asset in assets]
        validate_asset_names(names, args.version, args.channel)
        validate_remote_assets_match_local(assets, local_by_name)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1
    print("GitHub nightly assets validated; no S3/CDN promotion is required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
