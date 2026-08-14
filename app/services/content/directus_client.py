"""Authenticated, server-side Directus client for Academy content."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import httpx
from pydantic import ValidationError

from app.schemas.academy import AcademyArticleDirectusDto


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
    ) -> None:
        self._config = config or DirectusConfig.from_env()
        self._transport = transport

    async def get_published_articles(self) -> list[AcademyArticleDirectusDto]:
        payload = await self._get_items(
            {
                "filter[status][_eq]": "published",
                "fields": ",".join(LIST_FIELDS),
                "sort": "-published_at,sort",
            }
        )
        articles: list[AcademyArticleDirectusDto] = []
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
            if article.status != "published":
                raise DirectusPayloadError("Directus returned a non-published Academy item")
            articles.append(article)
        return articles

    async def get_published_article_by_slug(
        self, slug: str
    ) -> AcademyArticleDirectusDto | None:
        payload = await self._get_items(
            {
                "filter[_and][0][slug][_eq]": slug,
                "filter[_and][1][status][_eq]": "published",
                "limit": "1",
                "fields": ",".join(DETAIL_FIELDS),
            }
        )
        if not payload:
            return None
        if len(payload) != 1 or not isinstance(payload[0], dict):
            raise DirectusPayloadError("Directus returned an invalid Academy detail result")
        article = self._validate_article(payload[0])
        if article.status != "published":
            raise DirectusPayloadError("Directus returned a non-published Academy item")
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
