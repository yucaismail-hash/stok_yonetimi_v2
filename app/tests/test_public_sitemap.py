import asyncio
import re
from datetime import datetime, timezone
from uuid import UUID

import httpx
import pytest
from fastapi import FastAPI

import app.api.public.sitemap as sitemap_module
from app.api.public import PUBLIC_SITEMAP_PATH_PATTERN
from app.api.public.sitemap import SITEMAP_CACHE_CONTROL, router
from app.schemas.academy import AcademyArticleListItem
from app.services.content.directus_client import DirectusTimeoutError


ARTICLE_ID = UUID("c1e10e42-d621-41e9-ac29-1c7739962f01")


def _article(*, updated_at=None):
    return AcademyArticleListItem(
        id=ARTICLE_ID,
        slug="published-article",
        title="Published Article",
        description="Description",
        category="Category",
        publishedAt=datetime(2026, 8, 13, tzinfo=timezone.utc),
        updatedAt=updated_at,
        readingTime=4,
        featuredImage=None,
        featuredImageAlt=None,
    )


class StubService:
    def __init__(self, articles=None, failure=None):
        self.articles = articles or []
        self.failure = failure

    async def get_articles(self):
        if self.failure:
            raise self.failure
        return self.articles


def _request(monkeypatch, service):
    monkeypatch.setattr(sitemap_module, "get_academy_service", lambda: service)
    app = FastAPI()
    app.include_router(router)

    async def send():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            return await client.get("/sitemap.xml")

    return asyncio.run(send())


def test_sitemap_contains_static_and_published_urls_only(monkeypatch):
    response = _request(monkeypatch, StubService([_article()]))
    assert response.status_code == 200
    assert response.headers["cache-control"] == SITEMAP_CACHE_CONTROL
    assert response.headers["content-type"].startswith("application/xml")
    assert "https://stokonomi.com/</loc>" in response.text
    assert "https://stokonomi.com/akademi</loc>" in response.text
    assert "https://stokonomi.com/akademi/published-article</loc>" in response.text
    assert "draft" not in response.text


def test_sitemap_uses_updated_at_then_published_at(monkeypatch):
    updated_at = datetime(2026, 8, 20, tzinfo=timezone.utc)
    response = _request(monkeypatch, StubService([_article(updated_at=updated_at)]))
    assert updated_at.isoformat() in response.text


def test_sitemap_safely_maps_content_timeout(monkeypatch):
    response = _request(monkeypatch, StubService(failure=DirectusTimeoutError("secret")))
    assert response.status_code == 504
    assert "secret" not in response.text


def test_sitemap_auth_exemption_is_exact():
    assert re.match(PUBLIC_SITEMAP_PATH_PATTERN, "/sitemap.xml")
    assert not re.match(PUBLIC_SITEMAP_PATH_PATTERN, "/sitemap.xml/extra")
    assert not re.match(PUBLIC_SITEMAP_PATH_PATTERN, "/other-sitemap.xml")
