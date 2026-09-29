#!/usr/bin/env python3
"""Validate built artifacts and updater manifests before S3 promotion."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from release_lib.manifests import validate_artifact_tree  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", default=os.environ.get("RELEASE_CHANNEL", ""))
    parser.add_argument("--version", default=os.environ.get("RELEASE_VERSION", ""))
    parser.add_argument(
        "--artifacts-dir",
        default=os.environ.get("RELEASE_ARTIFACTS_DIR", "artifacts"),
    )
    args = parser.parse_args()
    try:
        validate_artifact_tree(
            Path(args.artifacts_dir), args.channel.strip(), args.version.strip()
        )
    except ValueError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1
    print("artifact validation ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
