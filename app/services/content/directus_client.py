"""Authenticated, server-side Directus client for Academy content."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import httpx
from pydantic import ValidationError

from app.schemas.academy import AcademyArticleDirectusDto
from app.services.content.academy_publication_policy import (
    directus_datetime,
    is_publicly_eligible,
    utc_now,
)


LIST_FIELDS = (
    "id",
    "slug",
    "title",
    "description",
    "category",
    "published_at",
    "updated_at",
    "reading_time",
    "featured_image",
    "featured_image_alt",
    "status",
    "sort",
)

DETAIL_FIELDS = (
    "id",
    "status",
    "sort",
    "slug",
    "title",
    "description",
    "category",
    "published_at",
    "updated_at",
    "reading_time",
    "sections",
    "seo_title",
    "seo_description",
    "featured_image",
    "featured_image_alt",
)

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100


class DirectusError(RuntimeError):
    """Base class for safe Directus client errors."""


class DirectusUnavailableError(DirectusError):
    """Directus could not be reached."""


class DirectusTimeoutError(DirectusError):
    """Directus exceeded the configured timeout."""


class DirectusUpstreamError(DirectusError):
    """Directus returned an unexpected HTTP response."""


class DirectusPayloadError(DirectusError):
    """Directus returned an invalid response payload."""


class DirectusConfigurationError(DirectusError):
    """Directus client configuration is missing or unsafe."""


def _normalize_directus_url(value: str) -> str:
    raw_url = value.strip()
    try:
        parsed = urlsplit(raw_url)
        port = parsed.port
    except ValueError as exc:
        raise DirectusConfigurationError("DIRECTUS_URL is invalid") from exc

    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise DirectusConfigurationError("DIRECTUS_URL must be an absolute HTTPS URL")
    if parsed.username is not None or parsed.password is not None:
        raise DirectusConfigurationError("DIRECTUS_URL must not contain credentials")
    if parsed.query or parsed.fragment:
        raise DirectusConfigurationError("DIRECTUS_URL must not contain query or fragment data")

    hostname = parsed.hostname.lower()
    host = f"[{hostname}]" if ":" in hostname else hostname
    netloc = f"{host}:{port}" if port is not None else host
    path = parsed.path.rstrip("/")
    return urlunsplit(("https", netloc, path, "", ""))


def _parse_timeout(value: str | None) -> float:
    if value is None or not value.strip():
        return 10.0
    try:
        timeout = float(value)
    except ValueError as exc:
        raise DirectusConfigurationError("DIRECTUS_TIMEOUT_SECONDS must be numeric") from exc
    if timeout <= 0 or timeout > 60:
        raise DirectusConfigurationError("DIRECTUS_TIMEOUT_SECONDS must be between 0 and 60")
    return timeout


@dataclass(frozen=True)
class DirectusConfig:
    url: str
    service_token: str = field(repr=False)
    timeout_seconds: float = 10.0

    def __post_init__(self) -> None:
        normalized_url = _normalize_directus_url(self.url)
        token = self.service_token.strip()
        if not token:
            raise DirectusConfigurationError("DIRECTUS_SERVICE_TOKEN is required")
        if self.timeout_seconds <= 0 or self.timeout_seconds > 60:
            raise DirectusConfigurationError("DIRECTUS_TIMEOUT_SECONDS must be between 0 and 60")
        object.__setattr__(self, "url", normalized_url)
        object.__setattr__(self, "service_token", token)

    @classmethod
    def from_env(cls) -> "DirectusConfig":
        url = os.getenv("DIRECTUS_URL", "").strip()
        token = os.getenv("DIRECTUS_SERVICE_TOKEN", "").strip()
        if not url:
            raise DirectusConfigurationError("DIRECTUS_URL is required")
        if not token:
            raise DirectusConfigurationError("DIRECTUS_SERVICE_TOKEN is required")
        return cls(
            url=url,
            service_token=token,
            timeout_seconds=_parse_timeout(os.getenv("DIRECTUS_TIMEOUT_SECONDS")),
        )


class DirectusAcademyClient:
    def __init__(
        self,
        config: DirectusConfig | None = None,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> None:
        if page_size < 1 or page_size > MAX_PAGE_SIZE:
            raise DirectusConfigurationError(
                f"Academy page_size must be between 1 and {MAX_PAGE_SIZE}"
            )
        self._config = config or DirectusConfig.from_env()
        self._transport = transport
        self._page_size = page_size

    async def get_published_articles(
        self, governed_at: datetime | None = None
    ) -> list[AcademyArticleDirectusDto]:
        eligible_at = governed_at or utc_now()
        eligible_at_query = directus_datetime(eligible_at)
        articles: list[AcademyArticleDirectusDto] = []
        seen_ids: set[object] = set()
        seen_slugs: set[str] = set()
        page = 1
        while True:
            payload = await self._get_items(
                {
                    "filter[_and][0][status][_eq]": "published",
                    "filter[_and][1][published_at][_nnull]": "true",
                    "filter[_and][2][published_at][_lte]": eligible_at_query,
                    "fields": ",".join(LIST_FIELDS),
                    "sort": "-published_at,sort,id",
                    "limit": str(self._page_size),
                    "page": str(page),
                }
            )
            if len(payload) > self._page_size:
                raise DirectusPayloadError("Directus exceeded the requested Academy page size")
            for item in payload:
                if not isinstance(item, dict):
                    raise DirectusPayloadError("Directus returned an invalid Academy item")
                # These fields are intentionally excluded from the lightweight list query.
                normalized_item = {
                    **item,
                    "sections": [],
                    "seo_title": None,
                    "seo_description": None,
                }
                article = self._validate_article(normalized_item)
                try:
                    eligible = is_publicly_eligible(article, eligible_at)
                except ValueError as exc:
                    raise DirectusPayloadError(
                        "Directus returned invalid Academy publication time"
                    ) from exc
                if not eligible:
                    raise DirectusPayloadError("Directus returned an ineligible Academy item")
                if article.id in seen_ids or article.slug in seen_slugs:
                    raise DirectusPayloadError("Directus returned a duplicate paginated Academy item")
                seen_ids.add(article.id)
                seen_slugs.add(article.slug)
                articles.append(article)
            if len(payload) < self._page_size:
                break
            page += 1
        return articles

    async def get_published_article_by_slug(
        self, slug: str, governed_at: datetime | None = None
    ) -> AcademyArticleDirectusDto | None:
        eligible_at = governed_at or utc_now()
        payload = await self._get_items(
            {
                "filter[_and][0][slug][_eq]": slug,
                "filter[_and][1][status][_eq]": "published",
                "filter[_and][2][published_at][_nnull]": "true",
                "filter[_and][3][published_at][_lte]": directus_datetime(eligible_at),
                "limit": "1",
                "fields": ",".join(DETAIL_FIELDS),
            }
        )
        if not payload:
            return None
        if len(payload) != 1 or not isinstance(payload[0], dict):
            raise DirectusPayloadError("Directus returned an invalid Academy detail result")
        article = self._validate_article(payload[0])
        try:
            eligible = is_publicly_eligible(article, eligible_at)
        except ValueError as exc:
            raise DirectusPayloadError(
                "Directus returned invalid Academy publication time"
            ) from exc
        if not eligible:
            raise DirectusPayloadError("Directus returned an ineligible Academy item")
        return article

    async def _get_items(self, params: dict[str, str]) -> list[Any]:
        timeout = httpx.Timeout(
            self._config.timeout_seconds,
            connect=min(self._config.timeout_seconds, 5.0),
        )
        headers = {
            "Authorization": f"Bearer {self._config.service_token}",
            "Accept": "application/json",
        }
        try:
            async with httpx.AsyncClient(
                base_url=self._config.url,
                headers=headers,
                timeout=timeout,
                follow_redirects=False,
                transport=self._transport,
            ) as client:
                response = await client.get("/items/academy_articles", params=params)
        except httpx.TimeoutException as exc:
            raise DirectusTimeoutError("Directus request timed out") from exc
        except httpx.RequestError as exc:
            raise DirectusUnavailableError("Directus is unavailable") from exc

        if not response.is_success:
            raise DirectusUpstreamError("Directus returned an unexpected HTTP status")
        try:
            envelope = response.json()
        except ValueError as exc:
            raise DirectusPayloadError("Directus returned invalid JSON") from exc
        if not isinstance(envelope, dict) or not isinstance(envelope.get("data"), list):
            raise DirectusPayloadError("Directus returned an invalid response envelope")
        return envelope["data"]

    @staticmethod
    def _validate_article(payload: dict[str, Any]) -> AcademyArticleDirectusDto:
        try:
            return AcademyArticleDirectusDto.model_validate(payload)
        except ValidationError as exc:
            raise DirectusPayloadError("Directus returned an invalid Academy payload") from exc
