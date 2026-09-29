"""Release channel validation helpers (stdlib only)."""

from .constants import (
    CDN_BASE_BY_CHANNEL,
    MANIFEST_NAMES_BY_CHANNEL,
    S3_PREFIX_BY_CHANNEL,
    alias_destinations,
    forbidden_manifest_names,
)
from .dispatch import (
    desktop_source_ref,
    normalize_package_version,
    validate_dispatch_inputs,
)
from .manifests import collect_artifact_manifests, validate_artifact_tree
from .promotion import parse_version_key, promotion_allowed, version_key_to_str
from .upload_plan import build_upload_plan_lines

__all__ = [
    "CDN_BASE_BY_CHANNEL",
    "MANIFEST_NAMES_BY_CHANNEL",
    "S3_PREFIX_BY_CHANNEL",
    "alias_destinations",
    "forbidden_manifest_names",
    "desktop_source_ref",
    "normalize_package_version",
    "validate_dispatch_inputs",
    "collect_artifact_manifests",
    "validate_artifact_tree",
    "parse_version_key",
    "promotion_allowed",
    "version_key_to_str",
    "build_upload_plan_lines",
]
