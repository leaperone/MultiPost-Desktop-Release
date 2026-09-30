import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_github_release_assets as gh_assets  # noqa: E402

collect_local_release_files = gh_assets.collect_local_release_files
validate_asset_names = gh_assets.validate_asset_names
validate_remote_assets_match_local = gh_assets.validate_remote_assets_match_local


class GithubNightlyAssetTests(unittest.TestCase):
    def names(self):
        version = "0.5.1-nightly.20260930.1"
        return [
            "nightly.yml",
            "nightly-mac.yml",
            "nightly-linux.yml",
            f"multipost-desktop-{version}-arm64.dmg",
            f"multipost-desktop-{version}-x64.dmg",
            f"multipost-desktop-{version}-arm64-mac.zip",
            f"multipost-desktop-{version}-mac.zip",
            f"multipost-desktop-{version}-setup.exe",
            f"multipost-desktop-{version}.AppImage",
            f"multipost-desktop_{version}_amd64.deb",
        ]

    def test_complete_github_asset_set(self):
        validate_asset_names(self.names(), "v0.5.1-nightly.20260930.1", "nightly")

    def test_missing_platform_asset_fails(self):
        with self.assertRaisesRegex(ValueError, "Windows"):
            validate_asset_names(
                [name for name in self.names() if not name.endswith(".exe")],
                "v0.5.1-nightly.20260930.1",
                "nightly",
            )

    def test_release_channel_is_not_github_only(self):
        with self.assertRaisesRegex(ValueError, "only for the nightly"):
            validate_asset_names(self.names(), "v0.5.1", "release")

    def test_digest_match_uses_github_digest_field(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = b"installer-bytes"
            path = root / "multipost-desktop-0.5.1-nightly.20260930.1-setup.exe"
            path.write_bytes(payload)
            local = collect_local_release_files(root, "nightly")
            digest = "sha256:" + hashlib.sha256(payload).hexdigest()
            validate_remote_assets_match_local(
                [{"name": path.name, "size": len(payload), "digest": digest}],
                local,
            )
            for asset in [
                {"name": path.name, "size": len(payload), "digest": "sha256:" + "0" * 64},
                {"name": path.name, "size": len(payload) + 1, "digest": digest},
                {"name": path.name, "size": len(payload)},
            ]:
                with self.assertRaises(ValueError):
                    validate_remote_assets_match_local([asset], local)
            with self.assertRaisesRegex(ValueError, 'extra assets'):
                validate_remote_assets_match_local([
                    {"name": path.name, "size": len(payload), "digest": digest},
                    {"name": 'source.zip', "size": 1, "digest": digest},
                ], local)

    def test_cli_requires_local_artifacts_before_querying_github(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/validate_github_release_assets.py'),
            '--channel', 'nightly', '--version', 'v0.5.1-nightly.20260930.1',
            '--source-sha', 'a' * 40, '--repo', 'org/repo', '--artifacts-dir', '/missing-artifacts'],
            capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('locally built artifacts are required', result.stderr)

    def test_cli_rejects_release_channel(self):
        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/validate_github_release_assets.py"),
                "--channel",
                "release",
                "--version",
                "v0.5.1",
                "--source-sha",
                "a" * 40,
                "--repo",
                "org/repo",
            ],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("only for the nightly", proc.stderr)


if __name__ == "__main__":
    unittest.main()
