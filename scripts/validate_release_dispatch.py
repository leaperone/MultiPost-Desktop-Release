#!/usr/bin/env python3
"""Validate repository_dispatch / workflow_dispatch release payload."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

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
    for key, value in result.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
