"""Published-only Academy content service."""

from collections.abc import Callable, Iterable
from datetime import datetime

from app.schemas.academy import (
    AcademyArticleDetail,
    AcademyArticleDirectusDto,
    AcademyArticleListItem,
)
from app.services.content.directus_client import DirectusAcademyClient, DirectusPayloadError
from app.services.content.academy_publication_policy import (
    is_publicly_eligible,
    require_aware,
    utc_now,
)


class AcademyArticleNotFoundError(LookupError):
    """No published Academy article exists for the requested slug."""


class AcademyService:
    def __init__(
        self,
        client: DirectusAcademyClient,
        *,
        now_provider: Callable[[], datetime] = utc_now,
    ) -> None:
        self._client = client
        self._now_provider = now_provider

    async def get_articles(self) -> list[AcademyArticleListItem]:
        governed_at = self._governed_at()
        articles = await self._client.get_published_articles(governed_at=governed_at)
        self._require_eligible(articles, governed_at)
        try:
            return [AcademyArticleListItem.from_directus(article) for article in articles]
        except ValueError as exc:
            raise DirectusPayloadError("Directus returned invalid public Academy data") from exc

    async def get_article_by_slug(self, slug: str) -> AcademyArticleDetail:
        governed_at = self._governed_at()
        article = await self._client.get_published_article_by_slug(
            slug, governed_at=governed_at
        )
        if article is None:
            raise AcademyArticleNotFoundError("Published Academy article was not found")
        self._require_eligible([article], governed_at)
        try:
            return AcademyArticleDetail.from_directus(article)
        except ValueError as exc:
            raise DirectusPayloadError("Directus returned invalid public Academy data") from exc

    @staticmethod
    def _require_eligible(
        articles: Iterable[AcademyArticleDirectusDto], governed_at: datetime
    ) -> None:
        try:
            all_eligible = all(
                is_publicly_eligible(article, governed_at) for article in articles
            )
        except ValueError as exc:
            raise DirectusPayloadError("Directus returned invalid public Academy data") from exc
        if not all_eligible:
            raise DirectusPayloadError("Directus returned invalid public Academy data")

    def _governed_at(self) -> datetime:
        try:
            return require_aware(self._now_provider(), name="governed_at")
        except ValueError as exc:
            raise DirectusPayloadError("Academy governed time is invalid") from exc


def get_academy_service() -> AcademyService:
    return AcademyService(DirectusAcademyClient())
