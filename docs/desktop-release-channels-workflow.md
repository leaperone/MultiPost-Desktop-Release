# Release repo channel-aware workflows

This release repository delegates all desktop builds to `.github/workflows/release-desktop-build.yml`.

## Payload contract

| Field | Values |
| --- | --- |
| `channel` | `release` or `nightly` |
| `version` | `vX.Y.Z` or `vX.Y.Z-nightly.YYYYMMDD.N` |
| `source_sha` | 40-char git commit id |

Checkout uses `refs/tags/desktop-<version>` on `leaperone/MultiPost`. CI sets `MULTIPOST_RELEASE_CHANNEL` for electron-builder (implemented in the source monorepo).

## S3 / CDN

| Channel | S3 prefix | Windows manifest |
| --- | --- | --- |
| release | `release/multipost-desktop` | `latest.yml` |
| nightly | `release/multipost-desktop-nightly` | `nightly.yml` |

Nightly stable download aliases use `*-nightly.*` basenames. Broad S3 cleanup was removed; promotion is guarded by semver checks.

## Local validation

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/validate_release_dispatch.py --channel nightly \
  --version v0.5.1-nightly.20260929.1 --source-sha "$(printf '%040d' 0)"
```
