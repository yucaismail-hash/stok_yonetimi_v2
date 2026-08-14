"""Read-only public Academy endpoints."""

from fastapi import APIRouter, HTTPException, Path, Response

from app.schemas.academy import AcademyArticleDetail, AcademyArticleListResponse
from app.services.content.academy_service import AcademyArticleNotFoundError, get_academy_service
from app.services.content.directus_client import (
    DirectusConfigurationError,
    DirectusPayloadError,
    DirectusTimeoutError,
    DirectusUnavailableError,
    DirectusUpstreamError,
)


router = APIRouter(prefix="/api/public/academy", tags=["Public Academy"])
CACHE_CONTROL = "public, max-age=60, stale-while-revalidate=300"
SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
MAX_SLUG_LENGTH = 120


def _safe_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, AcademyArticleNotFoundError):
        return HTTPException(status_code=404, detail="Published Academy article not found")
    if isinstance(exc, DirectusTimeoutError):
        return HTTPException(status_code=504, detail="Content service timed out")
    if isinstance(exc, (DirectusUnavailableError, DirectusConfigurationError)):
        return HTTPException(status_code=503, detail="Content service unavailable")
    if isinstance(exc, (DirectusUpstreamError, DirectusPayloadError)):
        return HTTPException(status_code=502, detail="Content service returned an invalid response")
    return HTTPException(status_code=500, detail="Content service error")


@router.get("/articles", response_model=AcademyArticleListResponse)
async def get_articles(response: Response) -> AcademyArticleListResponse:
    try:
        items = await get_academy_service().get_articles()
    except (
        DirectusConfigurationError,
        DirectusPayloadError,
        DirectusTimeoutError,
        DirectusUnavailableError,
        DirectusUpstreamError,
    ) as exc:
        raise _safe_http_error(exc) from exc
    response.headers["Cache-Control"] = CACHE_CONTROL
    return AcademyArticleListResponse(items=items)


@router.get("/articles/{slug}", response_model=AcademyArticleDetail)
async def get_article_by_slug(
    response: Response,
    slug: str = Path(min_length=1, max_length=MAX_SLUG_LENGTH, pattern=SLUG_PATTERN),
) -> AcademyArticleDetail:
    try:
        article = await get_academy_service().get_article_by_slug(slug)
    except (
        AcademyArticleNotFoundError,
        DirectusConfigurationError,
        DirectusPayloadError,
        DirectusTimeoutError,
        DirectusUnavailableError,
        DirectusUpstreamError,
    ) as exc:
        raise _safe_http_error(exc) from exc
    response.headers["Cache-Control"] = CACHE_CONTROL
    return article
