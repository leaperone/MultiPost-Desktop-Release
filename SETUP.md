# Release Repository Setup Guide

This document explains how to configure and use this release repository.

## Prerequisites

1. Access to the private repository `leaperone/MultiPost-Desktop`
2. GitHub Personal Access Token (PAT) with appropriate permissions

## Setup Steps

### 1. Create Personal Access Token (PAT)

1. Go to [GitHub Settings > Developer settings > Personal access tokens > Fine-grained tokens](https://github.com/settings/tokens?type=beta)
2. Click "Generate new token"
3. Configure the token:
   - **Token name**: `MultiPost-Desktop-Release`
   - **Expiration**: Choose an appropriate duration
   - **Repository access**: Select "Only select repositories" and choose `leaperone/MultiPost-Desktop`
   - **Permissions**:
     - Contents: Read-only
     - Metadata: Read-only
4. Generate and copy the token

### 2. Add Repository Secrets

Go to this repository's Settings > Secrets and variables > Actions, and add:

| Secret Name | Description |
|-------------|-------------|
| `PRIVATE_REPO_PAT` | The Personal Access Token created above |

### 3. (Optional) macOS Code Signing

For proper macOS builds with code signing and notarization, add these secrets:

| Secret Name | Description |
|-------------|-------------|
| `CSC_LINK` | Base64-encoded .p12 certificate file |
| `CSC_KEY_PASSWORD` | Password for the .p12 certificate |
| `APPLE_ID` | Apple Developer account email |
| `APPLE_APP_SPECIFIC_PASSWORD` | App-specific password for notarization |
| `APPLE_TEAM_ID` | Apple Developer Team ID |

To generate `CSC_LINK`:
```bash
base64 -i certificate.p12 | pbcopy
```

### 4. (Optional) Windows Code Signing

For Windows EV code signing:

| Secret Name | Description |
|-------------|-------------|
| `WIN_CSC_LINK` | Base64-encoded Windows certificate |
| `WIN_CSC_KEY_PASSWORD` | Certificate password |

## Usage

### Method 1: Manual Trigger (Recommended)

1. Go to Actions tab
2. Select "Build and Release" workflow
3. Click "Run workflow"
4. Enter the version tag (e.g., `v1.0.0`)
5. Choose whether it's a pre-release
6. Click "Run workflow"

### Method 2: API Trigger (Automated)

Trigger a build from the private repository using the GitHub API:

```bash
curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer YOUR_PAT" \
  https://api.github.com/repos/leaperone/MultiPost-Desktop-Release/dispatches \
  -d '{
    "event_type": "release-build",
    "client_payload": {
      "version": "v1.0.0",
      "ref": "main",
      "prerelease": false,
      "body": "Release notes here..."
    }
  }'
```

### Method 3: Script from Private Repo

Add this script to the private repository:

```bash
#!/bin/bash
# scripts/trigger-release.sh

VERSION=$1
REF=${2:-main}
PRERELEASE=${3:-false}

if [ -z "$VERSION" ]; then
  echo "Usage: ./trigger-release.sh <version> [ref] [prerelease]"
  echo "Example: ./trigger-release.sh v1.0.0 main false"
  exit 1
fi

curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://api.github.com/repos/leaperone/MultiPost-Desktop-Release/dispatches \
  -d "{
    \"event_type\": \"release-build\",
    \"client_payload\": {
      \"version\": \"$VERSION\",
      \"ref\": \"$REF\",
      \"prerelease\": $PRERELEASE
    }
  }"

echo "Release build triggered for $VERSION"
```

## Workflow Files

| File | Purpose |
|------|---------|
| `build-release.yml` | Manual trigger workflow with version input |
| `build-on-tag.yml` | API-triggered workflow via repository_dispatch |

## Troubleshooting

### Build fails with "repository not found"

- Ensure `PRIVATE_REPO_PAT` secret is set correctly
- Verify the PAT has read access to the private repository

### macOS build fails with signing errors

- Check that code signing secrets are properly configured
- For unsigned builds, the current configuration should work without signing

### Linux snap build fails

- Snapcraft might require additional configuration
- Consider removing `.snap` from the build if not needed

## Security Notes

- The PAT should have minimal required permissions
- Rotate the PAT periodically
- Never commit secrets to the repository
