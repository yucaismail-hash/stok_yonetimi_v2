"""Bounded acquisition and caching of the trusted deployed Vite HTML shell."""

from __future__ import annotations

import asyncio
import logging
import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

import httpx
from lxml import etree, html
from lxml.etree import ParserError


PRODUCTION_SHELL_URL = "https://www.stokonomi.com/index.html"
DEFAULT_TTL_SECONDS = 300.0
DEFAULT_MAX_BYTES = 512 * 1024
DEFAULT_MAX_STALE_SECONDS = 24 * 60 * 60.0
logger = logging.getLogger(__name__)


class FrontendShellError(RuntimeError):
    """Base class for sanitized frontend-shell failures."""


class FrontendShellConfigurationError(FrontendShellError):
    """The trusted shell source is missing or unsafe."""


class FrontendShellUnavailableError(FrontendShellError):
    """The trusted shell source could not provide a usable response."""


class FrontendShellPayloadError(FrontendShellError):
    """The trusted shell response violated the HTML contract."""


def _normalize_shell_url(value: str) -> str:
    raw = value.strip()
    try:
        parsed = urlsplit(raw)
        port = parsed.port
    except ValueError as exc:
        raise FrontendShellConfigurationError("Frontend shell URL is invalid") from exc
    if (
        parsed.scheme.lower() != "https"
        or parsed.hostname is None
        or parsed.hostname.lower() != "www.stokonomi.com"
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
        or parsed.path != "/index.html"
        or parsed.query
        or parsed.fragment
    ):
        raise FrontendShellConfigurationError("Frontend shell URL is not trusted")
    return urlunsplit(("https", "www.stokonomi.com", "/index.html", "", ""))


@dataclass(frozen=True)
class FrontendShellConfig:
    url: str
    ttl_seconds: float = DEFAULT_TTL_SECONDS
    max_bytes: int = DEFAULT_MAX_BYTES
    timeout_seconds: float = 3.0
    max_stale_seconds: float = DEFAULT_MAX_STALE_SECONDS

    def __post_init__(self) -> None:
        if self.ttl_seconds <= 0 or self.ttl_seconds > 3600:
            raise FrontendShellConfigurationError("Frontend shell TTL is out of range")
        if self.max_bytes < 1024 or self.max_bytes > 2 * 1024 * 1024:
            raise FrontendShellConfigurationError("Frontend shell size limit is out of range")
        if self.timeout_seconds <= 0 or self.timeout_seconds > 10:
            raise FrontendShellConfigurationError("Frontend shell timeout is out of range")
        if self.max_stale_seconds < self.ttl_seconds or self.max_stale_seconds > 7 * 86400:
            raise FrontendShellConfigurationError(
                "Frontend shell stale limit is out of range"
            )
        object.__setattr__(self, "url", _normalize_shell_url(self.url))

    @classmethod
    def from_env(cls) -> "FrontendShellConfig":
        value = os.getenv("ACADEMY_FRONTEND_SHELL_URL", "").strip()
        if not value:
            raise FrontendShellConfigurationError(
                "ACADEMY_FRONTEND_SHELL_URL is required"
            )
        return cls(url=value)


@dataclass(frozen=True)
class FrontendShell:
    content: str
    etag: str | None
    last_modified: str | None
    fetched_at: float


def validate_shell_document(content: str) -> None:
    """Reject shells that cannot safely boot the deployed React application."""

    try:
        pull_parser = etree.HTMLPullParser(events=("start",))
        pull_parser.feed(content)
        pull_parser.close()
        head_start_count = sum(
            1 for _, element in pull_parser.read_events() if element.tag == "head"
        )
        document = html.document_fromstring(content)
    except (etree.XMLSyntaxError, ParserError, ValueError) as exc:
        raise FrontendShellPayloadError("Frontend shell HTML is malformed") from exc
    heads = document.xpath("/html/head")
    roots = document.xpath('//*[@id="root"]')
    module_scripts = document.xpath(
        '/html/head/script[@type="module" and starts-with(@src, "/assets/")]'
    )
    if head_start_count != 1 or len(heads) != 1:
        raise FrontendShellPayloadError("Frontend shell must contain exactly one head")
    if len(roots) != 1:
        raise FrontendShellPayloadError("Frontend shell must contain one React root")
    if not module_scripts:
        raise FrontendShellPayloadError("Frontend shell module script is missing")


class FrontendShellProvider:
    def __init__(
        self,
        config: FrontendShellConfig,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._config = config
        self._transport = transport
        self._monotonic = monotonic
        self._cached: FrontendShell | None = None
        self._refresh_lock = asyncio.Lock()

    async def get_shell(self) -> str:
        now = self._monotonic()
        if self._is_fresh(now):
            return self._cached.content  # type: ignore[union-attr]

        async with self._refresh_lock:
            now = self._monotonic()
            if self._is_fresh(now):
                return self._cached.content  # type: ignore[union-attr]
            try:
                refreshed = await self._refresh(now)
            except FrontendShellUnavailableError:
                if self._is_stale_usable(now):
                    logger.warning(
                        "Using bounded last-known-good frontend shell after refresh failure"
                    )
                    return self._cached.content
                raise
            self._cached = refreshed
            return refreshed.content

    def _is_fresh(self, now: float) -> bool:
        return (
            self._cached is not None
            and now - self._cached.fetched_at < self._config.ttl_seconds
        )

    def _is_stale_usable(self, now: float) -> bool:
        return (
            self._cached is not None
            and now - self._cached.fetched_at <= self._config.max_stale_seconds
        )

    async def _refresh(self, now: float) -> FrontendShell:
        headers = {"Accept": "text/html"}
        if self._cached is not None:
            if self._cached.etag:
                headers["If-None-Match"] = self._cached.etag
            if self._cached.last_modified:
                headers["If-Modified-Since"] = self._cached.last_modified

        timeout = httpx.Timeout(
            self._config.timeout_seconds,
            connect=min(self._config.timeout_seconds, 2.0),
        )
        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=False,
                transport=self._transport,
            ) as client:
                async with client.stream(
                    "GET", self._config.url, headers=headers
                ) as response:
                    if response.status_code == 304:
                        if self._cached is None:
                            raise FrontendShellPayloadError(
                                "Frontend shell returned an invalid conditional response"
                            )
                        return FrontendShell(
                            content=self._cached.content,
                            etag=response.headers.get("etag") or self._cached.etag,
                            last_modified=response.headers.get("last-modified")
                            or self._cached.last_modified,
                            fetched_at=now,
                        )
                    if response.status_code != 200:
                        raise FrontendShellUnavailableError(
                            "Frontend shell returned an unexpected HTTP status"
                        )
                    media_type = response.headers.get("content-type", "").split(";", 1)[0]
                    if media_type.strip().lower() != "text/html":
                        raise FrontendShellPayloadError(
                            "Frontend shell returned an invalid content type"
                        )
                    declared_size = response.headers.get("content-length")
                    if declared_size:
                        try:
                            if int(declared_size) > self._config.max_bytes:
                                raise FrontendShellPayloadError(
                                    "Frontend shell exceeded its size limit"
                                )
                        except ValueError as exc:
                            raise FrontendShellPayloadError(
                                "Frontend shell returned an invalid content length"
                            ) from exc
                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        if len(body) > self._config.max_bytes:
                            raise FrontendShellPayloadError(
                                "Frontend shell exceeded its size limit"
                            )
        except httpx.TimeoutException as exc:
            raise FrontendShellUnavailableError("Frontend shell request timed out") from exc
        except httpx.RequestError as exc:
            raise FrontendShellUnavailableError("Frontend shell is unavailable") from exc

        try:
            content = bytes(body).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise FrontendShellPayloadError("Frontend shell is not valid UTF-8") from exc
        validate_shell_document(content)
        return FrontendShell(
            content=content,
            etag=response.headers.get("etag"),
            last_modified=response.headers.get("last-modified"),
            fetched_at=now,
        )
