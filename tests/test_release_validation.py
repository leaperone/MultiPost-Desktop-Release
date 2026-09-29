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
    def test_nightly_alias_paths(self) -> None:
        dests = {d for _, d, _ in alias_destinations("nightly")}
        self.assertIn("MultiPost-Setup-nightly.exe", dests)
        self.assertNotIn("MultiPost-Setup-latest.exe", dests)

    def test_s3_prefix_isolation(self) -> None:
        self.assertNotEqual(
            S3_PREFIX_BY_CHANNEL["release"],
            S3_PREFIX_BY_CHANNEL["nightly"],
        )

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
            (sub / "nightly-mac.yml").write_text("version: 1.0.0\n", encoding="utf-8")
            lines = build_upload_plan_lines(root, "nightly")
            dests = {line.split("|", 1)[1] for line in lines}
            self.assertIn("MultiPost-mac-nightly.dmg", dests)


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
