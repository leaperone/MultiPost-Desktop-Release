#!/usr/bin/env bash
set -euo pipefail
manifest=$1
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
: > "$work/artifacts"
: > "$work/aliases"
: > "$work/manifests"
while IFS='|' read -r src dst; do
  case "$dst" in
    latest*.yml|nightly*.yml) phase=manifests ;;
    MultiPost-*-latest.*|MultiPost-*-nightly.*|MultiPost-latest.*|MultiPost-nightly.*) phase=aliases ;;
    *) phase=artifacts ;;
  esac
  printf '%s|%s\n' "$src" "$dst" >> "$work/$phase"
done < "$manifest"
for phase in artifacts aliases manifests; do
  [ -s "$work/$phase" ] || continue
  xargs -a "$work/$phase" -P 6 -d '\n' -I {} bash -c '
    spec=$1; src=${spec%%|*}; dst=${spec##*|}
    aws s3 cp "$src" "s3://$S3_BUCKET/$S3_PATH/$dst" \
      --endpoint-url "$S3_ENDPOINT" --acl public-read
  ' _ {}
done
