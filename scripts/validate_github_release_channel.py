#!/usr/bin/env python3
"""Ensure GitHub Release flags match the selected channel."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from release_lib.constants import RELEASE_CHANNEL_NIGHTLY, RELEASE_CHANNEL_RELEASE
from release_lib.dispatch import validate_dispatch_inputs  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", default=os.environ.get("RELEASE_CHANNEL", ""))
    parser.add_argument("--version", default=os.environ.get("RELEASE_VERSION", ""))
    parser.add_argument(
        "--source-sha", default=os.environ.get("RELEASE_SOURCE_SHA", "")
    )
    parser.add_argument(
        "--repo", default=os.environ.get("GITHUB_REPOSITORY", "")
    )
    args = parser.parse_args()
    try:
        validate_dispatch_inputs(args.channel, args.version, args.source_sha)
    except ValueError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1

    if not args.repo:
        print("::error::GITHUB_REPOSITORY is required", file=sys.stderr)
        return 1

    proc = subprocess.run(
        [
            "gh",
            "release",
            "view",
            args.version.strip(),
            "-R",
            args.repo,
            "--json",
            "tagName,isPrerelease,body",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(f"::error::gh release view failed: {proc.stderr.strip()}", file=sys.stderr)
        return 1

    data = json.loads(proc.stdout)
    tag = data.get("tagName", "")
    prerelease = bool(data.get("isPrerelease"))
    body = data.get("body") or ""

    if tag != args.version.strip():
        print(
            f"::error::release tag {tag!r} != requested {args.version!r}",
            file=sys.stderr,
        )
        return 1

    channel = args.channel.strip().lower()
    if channel == RELEASE_CHANNEL_NIGHTLY and not prerelease:
        print(
            "::error::nightly sync refuses a non-prerelease GitHub release",
            file=sys.stderr,
        )
        return 1
    if channel == RELEASE_CHANNEL_RELEASE and prerelease:
        print(
            "::error::release sync refuses a prerelease GitHub release",
            file=sys.stderr,
        )
        return 1

    sha = args.source_sha.strip().lower()
    if sha and sha not in body.lower():
        print(
            "::error::release body must contain source_sha evidence",
            file=sys.stderr,
        )
        return 1

    print("github release channel validation ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
