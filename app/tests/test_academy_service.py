import asyncio

import pytest

from app.schemas.academy import AcademyArticleDirectusDto
from app.services.content.academy_service import AcademyArticleNotFoundError, AcademyService
from app.services.content.directus_client import DirectusPayloadError


def _article(status="published", published_at="2026-08-13T00:00:00Z"):
    return AcademyArticleDirectusDto.model_validate(
        {
            "id": "c1e10e42-d621-41e9-ac29-1c7739962f01",
            "status": status,
            "sort": None,
            "slug": "stok-yonetimi-nedir",
            "title": "Stok Yönetimi Nedir?",
            "description": "Açıklama",
            "category": "Temel Kavramlar",
            "published_at": published_at,
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
    def __init__(self, *, articles=None, article=None):
        self.articles = [] if articles is None else articles
        self.article = article

    async def get_published_articles(self):
        return self.articles

    async def get_published_article_by_slug(self, slug):
        return self.article


def test_published_list_mapping():
    result = asyncio.run(AcademyService(StubClient(articles=[_article()])).get_articles())
    assert result[0].slug == "stok-yonetimi-nedir"
    assert result[0].readingTime == 8


def test_published_detail_mapping():
    result = asyncio.run(AcademyService(StubClient(article=_article())).get_article_by_slug("stok-yonetimi-nedir"))
    assert result.status == "published"
    assert result.sections[0].type == "paragraph"


@pytest.mark.parametrize("article", [_article("draft", None), _article("archived", None)])
def test_non_published_defense(article):
    with pytest.raises(DirectusPayloadError):
        asyncio.run(AcademyService(StubClient(articles=[article])).get_articles())


def test_missing_published_at_defense():
    with pytest.raises(DirectusPayloadError):
        asyncio.run(AcademyService(StubClient(article=_article(published_at=None))).get_article_by_slug("slug"))


def test_detail_none_is_service_not_found():
    with pytest.raises(AcademyArticleNotFoundError):
        asyncio.run(AcademyService(StubClient(article=None)).get_article_by_slug("missing"))
