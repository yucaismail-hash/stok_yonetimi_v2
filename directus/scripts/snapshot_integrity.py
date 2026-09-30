"""Portable semantic fingerprints for governed Directus JSON artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize JSON deterministically, independent of formatting and line endings."""
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def semantic_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def semantic_sha256_json_bytes(payload: bytes) -> str:
    return semantic_sha256(json.loads(payload.decode("utf-8")))


def semantic_sha256_file(path: Path) -> str:
    return semantic_sha256_json_bytes(path.read_bytes())
