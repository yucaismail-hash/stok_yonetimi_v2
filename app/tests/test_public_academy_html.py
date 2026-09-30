import asyncio
from datetime import datetime, timezone
from uuid import UUID

import httpx
import pytest
from fastapi import FastAPI

import app.api.public.academy_html as html_module
from app.api.public.academy_html import (
    ERROR_CACHE_CONTROL,
    SUCCESS_CACHE_CONTROL,
    router,
)
from app.schemas.academy import AcademyArticleDetail
from app.services.content.academy_service import AcademyArticleNotFoundError
from app.services.content.directus_client import (
    DirectusConfigurationError,
    DirectusPayloadError,
    DirectusTimeoutError,
    DirectusUnavailableError,
    DirectusUpstreamError,
)
from app.services.content.frontend_shell import (
    FrontendShellConfigurationError,
    FrontendShellPayloadError,
    FrontendShellUnavailableError,
)


SHELL = """<!doctype html><html><head><title>Root</title>
<script type="module" src="/assets/index.RUNTIME-HASH.js"></script></head>
<body><div id="root"></div></body></html>"""


def _article():
    return AcademyArticleDetail(
        id=UUID("c1e10e42-d621-41e9-ac29-1c7739962f01"),
        slug="emniyet-stoku-nedir",
        title="Emniyet Stoku Nedir?",
        description="Türkçe açıklama",
        category="Emniyet Stoku",
        publishedAt=datetime(2026, 8, 25, tzinfo=timezone.utc),
        updatedAt=None,
        readingTime=3,
        featuredImage=None,
        featuredImageAlt=None,
        status="published",
        sections=[],
        seoTitle=None,
        seoDescription=None,
    )


class StubService:
    def __init__(self, *, article=None, failure=None):
        self.article = _article() if article is None else article
        self.failure = failure
        self.slugs = []

    async def get_article_by_slug(self, slug):
        self.slugs.append(slug)
        if self.failure:
            raise self.failure
        return self.article


class StubShellProvider:
    def __init__(self, *, shell=SHELL, failure=None):
        self.shell = shell
        self.failure = failure

    async def get_shell(self):
        if self.failure:
            raise self.failure
        return self.shell


def _request(
    monkeypatch,
    method="GET",
    path="/api/public/academy/html/emniyet-stoku-nedir",
    *,
    service=None,
    provider=None,
    headers=None,
):
    service = service or StubService()
    provider = provider or StubShellProvider()
    monkeypatch.setattr(html_module, "get_academy_service", lambda: service)
    monkeypatch.setattr(html_module, "get_frontend_shell_provider", lambda: provider)
    app = FastAPI()
    app.include_router(router)

    async def send():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            return await client.request(method, path, headers=headers)

    return asyncio.run(send()), service


def test_eligible_article_returns_dynamic_html_and_excludes_query_from_canonical(
    monkeypatch,
):
    response, service = _request(
        monkeypatch,
        path="/api/public/academy/html/emniyet-stoku-nedir?utm_source=test",
    )
    assert response.status_code == 200
    assert response.headers["cache-control"] == SUCCESS_CACHE_CONTROL
    assert response.headers["content-type"].startswith("text/html")
    assert "Emniyet Stoku Nedir?" in response.text
    assert 'href="https://www.stokonomi.com/akademi/emniyet-stoku-nedir"' in response.text
    assert "utm_source" not in response.text
    assert "/assets/index.RUNTIME-HASH.js" in response.text
    assert service.slugs == ["emniyet-stoku-nedir"]


@pytest.mark.parametrize("state", ["unknown", "draft", "future", "archived"])
def test_ineligible_or_unknown_article_returns_true_404(monkeypatch, state):
    response, _ = _request(
        monkeypatch,
        service=StubService(
            failure=AcademyArticleNotFoundError(f"{state} private detail")
        ),
    )
    assert response.status_code == 404
    assert response.headers["cache-control"] == ERROR_CACHE_CONTROL
    assert "private detail" not in response.text


@pytest.mark.parametrize("slug", ["Uppercase", "double--dash", "ends-", "a" * 121])
def test_invalid_slug_returns_404_before_content_or_shell_access(monkeypatch, slug):
    service = StubService()
    response, _ = _request(
        monkeypatch,
        path=f"/api/public/academy/html/{slug}",
        service=service,
    )
    assert response.status_code == 404
    assert response.headers["cache-control"] == ERROR_CACHE_CONTROL
    assert service.slugs == []


def test_multi_segment_article_path_is_404_no_store(monkeypatch):
    response, _ = _request(
        monkeypatch,
        path="/api/public/academy/html/valid-slug/extra",
    )
    assert response.status_code == 404
    assert response.headers["cache-control"] == ERROR_CACHE_CONTROL


@pytest.mark.parametrize(
    ("failure", "status"),
    [
        (DirectusUnavailableError("secret"), 503),
        (DirectusConfigurationError("secret"), 503),
        (DirectusTimeoutError("secret"), 504),
        (DirectusUpstreamError("secret"), 502),
        (DirectusPayloadError("secret"), 502),
    ],
)
def test_content_failures_have_governed_status_and_no_store(
    monkeypatch, failure, status
):
    response, _ = _request(monkeypatch, service=StubService(failure=failure))
    assert response.status_code == status
    assert response.headers["cache-control"] == ERROR_CACHE_CONTROL
    assert "secret" not in response.text


@pytest.mark.parametrize(
    ("failure", "status"),
    [
        (FrontendShellUnavailableError("private"), 503),
        (FrontendShellConfigurationError("private"), 503),
        (FrontendShellPayloadError("private"), 502),
    ],
)
def test_shell_failures_have_governed_status_and_no_store(
    monkeypatch, failure, status
):
    response, _ = _request(
        monkeypatch, provider=StubShellProvider(failure=failure)
    )
    assert response.status_code == status
    assert response.headers["cache-control"] == ERROR_CACHE_CONTROL
    assert "private" not in response.text


def test_head_matches_get_status_headers_and_omits_body(monkeypatch):
    get_response, _ = _request(monkeypatch)
    head_response, _ = _request(monkeypatch, method="HEAD")
    assert head_response.status_code == get_response.status_code == 200
    assert head_response.headers["cache-control"] == get_response.headers["cache-control"]
    assert head_response.headers["content-type"].startswith("text/html")
    assert int(head_response.headers["content-length"]) == len(get_response.content)
    assert head_response.content == b""


def test_browser_and_crawler_user_agents_receive_identical_html(monkeypatch):
    agents = ["Mozilla/5.0", "LinkedInBot/1.0", "Twitterbot/1.0", "Googlebot/2.1"]
    bodies = []
    for agent in agents:
        response, _ = _request(monkeypatch, headers={"User-Agent": agent})
        assert response.status_code == 200
        bodies.append(response.content)
    assert len(set(bodies)) == 1


def test_runtime_secrets_never_enter_html(monkeypatch):
    secret_values = ["directus-service-token", "database-secret", "r2-secret"]
    monkeypatch.setenv("DIRECTUS_SERVICE_TOKEN", secret_values[0])
    monkeypatch.setenv("DATABASE_URL", secret_values[1])
    monkeypatch.setenv("STORAGE_MEDIA_SECRET", secret_values[2])
    response, _ = _request(monkeypatch)
    assert response.status_code == 200
    assert all(value not in response.text for value in secret_values)
