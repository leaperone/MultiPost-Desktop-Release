#!/usr/bin/env bash
set -euo pipefail
manifest=$1
concurrency=${UPLOAD_CONCURRENCY:-2}
retry_delay=${UPLOAD_RETRY_DELAY:-5}
case "$concurrency" in 1|2|3|4|5|6) ;; *) echo 'Invalid upload concurrency' >&2; exit 2 ;; esac
case "$retry_delay" in ''|*[!0-9]*) echo 'Invalid retry delay' >&2; exit 2 ;; esac
export AWS_RETRY_MODE=${AWS_RETRY_MODE:-adaptive}
export AWS_MAX_ATTEMPTS=${AWS_MAX_ATTEMPTS:-8}
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

upload_one() {
  local src=$1 dst=$2 attempt
  for attempt in 1 2 3; do
    echo "Uploading $dst (attempt $attempt/3)"
    if aws s3 cp "$src" "s3://$S3_BUCKET/$S3_PATH/$dst" \
      --endpoint-url "$S3_ENDPOINT" --acl public-read \
      --cli-connect-timeout 30 --cli-read-timeout 180 --only-show-errors --no-progress; then
      return 0
    fi
    [ "$attempt" = 3 ] || sleep "$((retry_delay * attempt))"
  done
  echo "Upload failed after retries: $dst" >&2
  return 1
}

for phase in artifacts aliases manifests; do
  [ -s "$work/$phase" ] || continue
  pids=()
  failed=0
  while IFS='|' read -r src dst; do
    upload_one "$src" "$dst" &
    pids+=("$!")
    if [ "${#pids[@]}" -ge "$concurrency" ]; then
      if ! wait "${pids[0]}"; then failed=1; fi
      pids=("${pids[@]:1}")
      [ "$failed" = 0 ] || break
    fi
  done < "$work/$phase"
  if [ "${#pids[@]}" -gt 0 ]; then
    for pid in "${pids[@]}"; do
      if ! wait "$pid"; then failed=1; fi
    done
  fi
  # A manifest must never advertise a release whose artifacts failed to upload.
  [ "$failed" = 0 ] || exit 1
done
