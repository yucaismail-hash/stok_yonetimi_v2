"""Canonical public eligibility policy for Academy content."""

from __future__ import annotations

from datetime import datetime, timezone

from app.schemas.academy import AcademyArticleDirectusDto


def utc_now() -> datetime:
    """Return the governed runtime time as a timezone-aware UTC value."""

    return datetime.now(timezone.utc)


def require_aware(value: datetime, *, name: str) -> datetime:
    """Normalize a timezone-aware datetime to UTC, rejecting ambiguous values."""

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def is_publicly_eligible(
    article: AcademyArticleDirectusDto, governed_at: datetime
) -> bool:
    """Apply the single list/detail/sitemap Academy publication predicate."""

    now = require_aware(governed_at, name="governed_at")
    if article.status != "published" or article.published_at is None:
        return False
    published_at = require_aware(article.published_at, name="published_at")
    return published_at <= now


def directus_datetime(value: datetime) -> str:
    """Serialize governed time deterministically for a Directus filter."""

    return require_aware(value, name="governed_at").isoformat().replace("+00:00", "Z")
