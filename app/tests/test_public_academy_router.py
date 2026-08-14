import asyncio
import re

import httpx
import pytest
from fastapi import FastAPI

import app.api.public.academy as academy_router_module
from app.api.public import PUBLIC_ACADEMY_PATH_PATTERN
from app.api.public.academy import CACHE_CONTROL, router
from app.schemas.academy import AcademyArticleDirectusDto
from app.services.content.academy_service import AcademyService
from app.services.content.directus_client import (
    DirectusConfigurationError,
    DirectusPayloadError,
    DirectusTimeoutError,
    DirectusUnavailableError,
    DirectusUpstreamError,
)


def _article():
    return AcademyArticleDirectusDto.model_validate(
        {
            "id": "c1e10e42-d621-41e9-ac29-1c7739962f01",
            "status": "published",
            "sort": None,
            "slug": "stok-yonetimi-nedir",
            "title": "Stok Yönetimi Nedir?",
            "description": "Açıklama",
            "category": "Temel Kavramlar",
            "published_at": "2026-08-13T00:00:00Z",
            "updated_at": None,
            "reading_time": 8,
            "sections": [{"type": "paragraph", "content": "İçerik"}],
            "seo_title": None,
            "seo_description": None,
            "featured_image": None,
            "featured_image_alt": None,
        }
    )


class StubClient:
    def __init__(self, *, failure=None, missing=False):
        self.failure = failure
        self.missing = missing
        self.list_calls = 0
        self.detail_slugs = []

    async def get_published_articles(self):
        self.list_calls += 1
        if self.failure:
            raise self.failure
        return [_article()]

    async def get_published_article_by_slug(self, slug):
        self.detail_slugs.append(slug)
        if self.failure:
            raise self.failure
        return None if self.missing else _article()


def _request(method, path):
    app = FastAPI()
    app.include_router(router)

    async def send():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as http:
            return await http.request(method, path)

    return asyncio.run(send())


def _use_client(monkeypatch, client):
    service = AcademyService(client)
    monkeypatch.setattr(academy_router_module, "get_academy_service", lambda: service)
    return client


def test_list_returns_200_without_auth_and_has_cache_header(monkeypatch):
    _use_client(monkeypatch, StubClient())
    response = _request("GET", "/api/public/academy/articles")
    assert response.status_code == 200
    assert response.json()["items"][0]["slug"] == "stok-yonetimi-nedir"
    assert response.headers["cache-control"] == CACHE_CONTROL


def test_detail_returns_200(monkeypatch):
    _use_client(monkeypatch, StubClient())
    response = _request("GET", "/api/public/academy/articles/stok-yonetimi-nedir")
    assert response.status_code == 200
    assert response.json()["status"] == "published"


def test_unknown_article_returns_404_without_long_cache(monkeypatch):
    _use_client(monkeypatch, StubClient(missing=True))
    response = _request("GET", "/api/public/academy/articles/missing")
    assert response.status_code == 404
    assert "cache-control" not in response.headers


@pytest.mark.parametrize(
    ("failure", "status"),
    [
        (DirectusUnavailableError("safe"), 503),
        (DirectusConfigurationError("safe"), 503),
        (DirectusTimeoutError("safe"), 504),
        (DirectusUpstreamError("safe"), 502),
        (DirectusPayloadError("safe"), 502),
    ],
)
def test_directus_errors_are_safely_mapped(monkeypatch, failure, status):
    _use_client(monkeypatch, StubClient(failure=failure))
    response = _request("GET", "/api/public/academy/articles")
    assert response.status_code == status
    assert "cache-control" not in response.headers
    assert "safe" not in response.text


@pytest.mark.parametrize("slug", ["Uppercase", "double--dash", "ends-", "a" * 121])
def test_invalid_slug_is_rejected_before_service(monkeypatch, slug):
    client = _use_client(monkeypatch, StubClient())
    response = _request("GET", f"/api/public/academy/articles/{slug}")
    assert response.status_code == 422
    assert client.detail_slugs == []


def test_query_cannot_override_published_filter(monkeypatch):
    client = _use_client(monkeypatch, StubClient())
    response = _request("GET", "/api/public/academy/articles?status=draft&filter=anything")
    assert response.status_code == 200
    assert client.list_calls == 1


def test_auth_exemption_boundary_does_not_cover_other_routes():
    assert re.match(PUBLIC_ACADEMY_PATH_PATTERN, "/api/public/academy")
    assert re.match(PUBLIC_ACADEMY_PATH_PATTERN, "/api/public/academy/articles")
    assert not re.match(PUBLIC_ACADEMY_PATH_PATTERN, "/api/public/academyx")
    assert not re.match(PUBLIC_ACADEMY_PATH_PATTERN, "/api/public/other")
    assert not re.match(PUBLIC_ACADEMY_PATH_PATTERN, "/api/private")
