#!/usr/bin/env python3
"""Emit src|dest upload lines for channel-scoped S3 promotion."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from release_lib.upload_plan import build_upload_plan_lines  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", default=os.environ.get("RELEASE_CHANNEL", ""))
    parser.add_argument(
        "--artifacts-dir",
        default=os.environ.get("RELEASE_ARTIFACTS_DIR", "artifacts"),
    )
    args = parser.parse_args()
    try:
        lines = build_upload_plan_lines(
            Path(args.artifacts_dir), args.channel.strip().lower()
        )
    except ValueError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
