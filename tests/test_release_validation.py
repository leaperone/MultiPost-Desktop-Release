#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from release_lib.constants import (  # noqa: E402
    S3_PREFIX_BY_CHANNEL,
    alias_destinations,
)
from release_lib.dispatch import validate_dispatch_inputs  # noqa: E402
from release_lib.promotion import parse_version_key, promotion_allowed  # noqa: E402
from release_lib.upload_plan import build_upload_plan_lines  # noqa: E402


class DispatchValidationTests(unittest.TestCase):
    def test_rejects_missing_channel(self) -> None:
        with self.assertRaises(ValueError):
            validate_dispatch_inputs("", "v1.0.0", "a" * 40)

    def test_nightly_version_shape(self) -> None:
        out = validate_dispatch_inputs(
            "nightly", "v0.5.1-nightly.20260929.1", "f" * 40
        )
        self.assertEqual(out["source_ref"], "refs/tags/desktop-v0.5.1-nightly.20260929.1")

    def test_nightly_has_no_s3_or_cdn_promotion_outputs(self) -> None:
        import subprocess

        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/validate_release_dispatch.py"),
                "--channel",
                "nightly",
                "--version",
                "v0.5.1-nightly.20260929.1",
                "--source-sha",
                "f" * 40,
            ],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        lines = dict(line.split("=", 1) for line in proc.stdout.splitlines() if "=" in line)
        self.assertEqual(lines.get("s3_path"), "")
        self.assertEqual(lines.get("cdn_base"), "")

    def test_release_dispatch_exports_s3_outputs(self) -> None:
        import subprocess

        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/validate_release_dispatch.py"),
                "--channel",
                "release",
                "--version",
                "v0.5.1",
                "--source-sha",
                "a" * 40,
            ],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        lines = dict(line.split("=", 1) for line in proc.stdout.splitlines() if "=" in line)
        self.assertEqual(lines.get("s3_path"), "release/multipost-desktop")
        self.assertIn("static.2some.ren", lines.get("cdn_base", ""))

    def test_release_rejects_nightly_suffix(self) -> None:
        with self.assertRaises(ValueError):
            validate_dispatch_inputs("release", "v0.5.1-nightly.20260929.1", "a" * 40)

    def test_invalid_sha(self) -> None:
        with self.assertRaises(ValueError):
            validate_dispatch_inputs("release", "v0.5.1", "short")


class SemverTests(unittest.TestCase):
    def test_ordering(self) -> None:
        self.assertLess(
            parse_version_key("v0.5.0"),
            parse_version_key("v0.5.1-nightly.20260929.1"),
        )
        self.assertLess(
            parse_version_key("v0.5.1-nightly.20260929.1"),
            parse_version_key("v0.5.1-nightly.20260929.2"),
        )
        self.assertLess(
            parse_version_key("v0.5.1-nightly.20260929.2"),
            parse_version_key("v0.5.1"),
        )

    def test_promotion_refuses_older(self) -> None:
        self.assertFalse(
            promotion_allowed("v0.5.1-nightly.20260929.1", "v0.5.1-nightly.20260929.2")
        )


class UploadPlanTests(unittest.TestCase):
    def test_nightly_rejects_s3_aliases(self) -> None:
        with self.assertRaisesRegex(ValueError, "GitHub-only"):
            alias_destinations("nightly")

    def test_release_s3_prefix_only_for_stable(self) -> None:
        self.assertIn("release", S3_PREFIX_BY_CHANNEL)
        self.assertNotIn("nightly", S3_PREFIX_BY_CHANNEL)

    def test_nightly_upload_plan_fails_before_network(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(ValueError, "GitHub-only"):
                build_upload_plan_lines(root, "nightly")

class UploadPlanIntegrationTests(unittest.TestCase):
    def test_build_plan_lines(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sub = root / "mac-builds"
            sub.mkdir()
            (sub / "MultiPost-1.0.0-arm64.dmg").write_bytes(b"x")
            (sub / "MultiPost-1.0.0-x64.dmg").write_bytes(b"x")
            (sub / "MultiPost-1.0.0-arm64-mac.zip").write_bytes(b"x")
            (sub / "MultiPost-1.0.0-mac.zip").write_bytes(b"x")
            (sub / "MultiPost-1.0.0-setup.exe").write_bytes(b"x")
            (sub / "MultiPost-1.0.0.AppImage").write_bytes(b"x")
            (sub / "multipost_1.0.0_amd64.deb").write_bytes(b"x")
            (sub / "latest-mac.yml").write_text("version: 1.0.0\n", encoding="utf-8")
            lines = build_upload_plan_lines(root, "release")
            dests = {line.split("|", 1)[1] for line in lines}
            self.assertIn("MultiPost-mac-latest.dmg", dests)


if __name__ == "__main__":
    unittest.main()


class ArtifactDigestTests(unittest.TestCase):
    def test_real_digest_and_channel_checks(self):
        import base64, hashlib, tempfile
        from release_lib.manifests import validate_artifact_tree
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            version = '0.5.1-nightly.20260929.1'
            artifacts = {
                'nightly-mac.yml': [f'MultiPost-{version}-mac.zip', f'MultiPost-{version}-arm64-mac.zip'],
                'nightly.yml': [f'multipost-desktop-{version}-setup.exe'],
                'nightly-linux.yml': [f'multipost-desktop-{version}.AppImage'],
            }
            for manifest, names in artifacts.items():
                text = f'version: {version}\nfiles:\n'
                for name in names:
                    content = name.encode()
                    (root / name).write_bytes(content)
                    digest = base64.b64encode(hashlib.sha512(content).digest()).decode()
                    text += f'  - url: {name}\n    sha512: {digest}\n    size: {len(content)}\n'
                (root / manifest).write_text(text)
            validate_artifact_tree(root, 'nightly', 'v'+version)
            (root / artifacts['nightly.yml'][0]).write_bytes(b'corrupted')
            with self.assertRaises(ValueError): validate_artifact_tree(root, 'nightly', 'v'+version)
            (root / 'latest.yml').write_text('version: 0.5.0')
            with self.assertRaises(ValueError): validate_artifact_tree(root, 'nightly', 'v'+version)

    def test_same_version_only_for_verified_recovery(self):
        from release_lib.promotion import promotion_allowed
        self.assertFalse(promotion_allowed('v0.5.1-nightly.20260929.1', '0.5.1-nightly.20260929.1'))
        self.assertTrue(promotion_allowed('v0.5.1-nightly.20260929.1', '0.5.1-nightly.20260929.1', allow_same=True))
        self.assertFalse(promotion_allowed('v0.5.1-nightly.20260929.1', '0.5.1-nightly.20260929.2', allow_same=True))
