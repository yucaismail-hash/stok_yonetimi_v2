import asyncio
from datetime import datetime, timezone

import pytest

from app.schemas.academy import AcademyArticleDirectusDto
from app.services.content.academy_service import AcademyArticleNotFoundError, AcademyService
from app.services.content.directus_client import DirectusPayloadError


GOVERNED_AT = datetime(2026, 8, 13, 0, 0, tzinfo=timezone.utc)


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

    async def get_published_articles(self, governed_at=None):
        self.governed_at = governed_at
        return self.articles

    async def get_published_article_by_slug(self, slug, governed_at=None):
        self.governed_at = governed_at
        return self.article


def _service(client):
    return AcademyService(client, now_provider=lambda: GOVERNED_AT)


def test_published_list_mapping():
    client = StubClient(articles=[_article()])
    result = asyncio.run(_service(client).get_articles())
    assert result[0].slug == "stok-yonetimi-nedir"
    assert result[0].readingTime == 8
    assert client.governed_at == GOVERNED_AT


def test_published_detail_mapping():
    result = asyncio.run(_service(StubClient(article=_article())).get_article_by_slug("stok-yonetimi-nedir"))
    assert result.status == "published"
    assert result.sections[0].type == "paragraph"


def test_same_article_has_list_detail_parity_at_governed_time():
    article = _article()
    client = StubClient(articles=[article], article=article)
    service = _service(client)
    listed = asyncio.run(service.get_articles())
    detail = asyncio.run(service.get_article_by_slug(article.slug))
    assert [item.slug for item in listed] == [detail.slug]


@pytest.mark.parametrize("article", [_article("draft", None), _article("archived", None)])
def test_non_published_defense(article):
    with pytest.raises(DirectusPayloadError):
        asyncio.run(_service(StubClient(articles=[article])).get_articles())


def test_missing_published_at_defense():
    with pytest.raises(DirectusPayloadError):
        asyncio.run(_service(StubClient(article=_article(published_at=None))).get_article_by_slug("slug"))


def test_published_exactly_at_governed_time_is_eligible():
    result = asyncio.run(_service(StubClient(articles=[_article()])).get_articles())
    assert len(result) == 1


def test_future_published_article_is_rejected_by_service_defense():
    with pytest.raises(DirectusPayloadError):
        asyncio.run(
            _service(
                StubClient(articles=[_article(published_at="2026-08-13T00:00:01Z")])
            ).get_articles()
        )


def test_naive_governed_time_is_rejected():
    service = AcademyService(
        StubClient(articles=[_article()]),
        now_provider=lambda: datetime(2026, 8, 13),
    )
    with pytest.raises(DirectusPayloadError):
        asyncio.run(service.get_articles())


def test_detail_none_is_service_not_found():
    with pytest.raises(AcademyArticleNotFoundError):
        asyncio.run(_service(StubClient(article=None)).get_article_by_slug("missing"))
