"""Published-only Academy content service."""

from collections.abc import Iterable

from app.schemas.academy import (
    AcademyArticleDetail,
    AcademyArticleDirectusDto,
    AcademyArticleListItem,
)
from app.services.content.directus_client import DirectusAcademyClient, DirectusPayloadError


class AcademyArticleNotFoundError(LookupError):
    """No published Academy article exists for the requested slug."""


class AcademyService:
    def __init__(self, client: DirectusAcademyClient) -> None:
        self._client = client

    async def get_articles(self) -> list[AcademyArticleListItem]:
        articles = await self._client.get_published_articles()
        self._require_published(articles)
        try:
            return [AcademyArticleListItem.from_directus(article) for article in articles]
        except ValueError as exc:
            raise DirectusPayloadError("Directus returned invalid public Academy data") from exc

    async def get_article_by_slug(self, slug: str) -> AcademyArticleDetail:
        article = await self._client.get_published_article_by_slug(slug)
        if article is None:
            raise AcademyArticleNotFoundError("Published Academy article was not found")
        self._require_published([article])
        try:
            return AcademyArticleDetail.from_directus(article)
        except ValueError as exc:
            raise DirectusPayloadError("Directus returned invalid public Academy data") from exc

    @staticmethod
    def _require_published(articles: Iterable[AcademyArticleDirectusDto]) -> None:
        if any(article.status != "published" or article.published_at is None for article in articles):
            raise DirectusPayloadError("Directus returned invalid public Academy data")


def get_academy_service() -> AcademyService:
    return AcademyService(DirectusAcademyClient())
