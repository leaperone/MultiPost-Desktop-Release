# Release repo channel-aware workflows

This release repository delegates all desktop builds to `.github/workflows/release-desktop-build.yml`.

## Payload contract

| Field | Values |
| --- | --- |
| `channel` | `release` or `nightly` |
| `version` | `vX.Y.Z` or `vX.Y.Z-nightly.YYYYMMDD.N` |
| `source_sha` | 40-char git commit id |

Checkout uses `refs/tags/desktop-<version>` on `leaperone/MultiPost`. CI sets `MULTIPOST_RELEASE_CHANNEL` for electron-builder (implemented in the source monorepo).

## Distribution (permanent)

| Channel | GitHub Release | S3 / CDN |
| --- | --- | --- |
| `release` (stable) | Published after S3 upload + CDN purge | `release/multipost-desktop` on Bitiful; manifests `latest*.yml` |
| `nightly` | **GitHub-only** — downloads and updater manifests live on the prerelease | **None** — no S3 upload, no CDN purge, manual sync workflow refuses Nightly |

Nightly promotion validates workflow artifacts (manifests, digests, version/SHA) and proves GitHub release assets match those files by size and SHA256 before the draft is published. Stable promotion still requires successful S3 upload and CDN visibility checks.

Each release attempt uses a new immutable `vX.Y.Z-nightly.YYYYMMDD.N` tag; CI refuses reusing an existing tag.

## Local validation

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/validate_release_dispatch.py --channel nightly \
  --version v0.5.1-nightly.20260929.1 --source-sha "$(printf '%040d' 0)"
python3 scripts/plan_s3_upload.py --channel nightly  # must fail before any network
```
