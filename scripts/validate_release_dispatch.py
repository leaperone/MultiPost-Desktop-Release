#!/usr/bin/env python3
"""Validate repository_dispatch / workflow_dispatch release payload."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from release_lib.constants import S3_PREFIX_BY_CHANNEL, CDN_BASE_BY_CHANNEL
from release_lib.dispatch import validate_dispatch_inputs  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", default=os.environ.get("RELEASE_CHANNEL", ""))
    parser.add_argument("--version", default=os.environ.get("RELEASE_VERSION", ""))
    parser.add_argument(
        "--source-sha", default=os.environ.get("RELEASE_SOURCE_SHA", "")
    )
    args = parser.parse_args()
    try:
        result = validate_dispatch_inputs(
            args.channel, args.version, args.source_sha
        )
    except ValueError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1
    result.update({
        'is_prerelease': 'true' if result['channel'] == 'nightly' else 'false',
        'make_latest': 'false' if result['channel'] == 'nightly' else 'true',
        # Nightly is GitHub-only. Keep these outputs empty so an accidental
        # future S3/CDN step fails closed instead of receiving a Nightly path.
        's3_path': S3_PREFIX_BY_CHANNEL[result['channel']] if result['channel'] == 'release' else '',
        'cdn_base': CDN_BASE_BY_CHANNEL[result['channel']] if result['channel'] == 'release' else '',
    })
    for key, value in result.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
