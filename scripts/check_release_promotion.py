#!/usr/bin/env python3
"""Refuse promoting an older build over a newer channel manifest."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from release_lib.promotion import promotion_allowed  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", default=os.environ.get("RELEASE_CHANNEL", ""))
    parser.add_argument("--version", default=os.environ.get("RELEASE_VERSION", ""))
    parser.add_argument(
        "--existing-version",
        default=os.environ.get("RELEASE_EXISTING_VERSION", ""),
    )
    parser.add_argument("--allow-same-version", action="store_true")
    args = parser.parse_args()
    existing = args.existing_version.strip() or None
    try:
        ok = promotion_allowed(args.version.strip(), existing, allow_same=args.allow_same_version)
    except ValueError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1
    if not ok:
        print(
            f"::error::refusing promotion: {args.version} is not newer than "
            f"{existing}",
            file=sys.stderr,
        )
        return 1
    print("promotion ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
