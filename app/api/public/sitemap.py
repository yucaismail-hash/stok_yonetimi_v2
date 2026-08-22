"""Dynamic sitemap backed by the published-only Academy content service."""

from xml.etree.ElementTree import Element, SubElement, tostring

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.schemas.academy import AcademyArticleListItem
from app.services.content.academy_service import get_academy_service
from app.services.content.directus_client import (
    DirectusConfigurationError,
    DirectusPayloadError,
    DirectusTimeoutError,
    DirectusUnavailableError,
    DirectusUpstreamError,
)


router = APIRouter(tags=["SEO"])
SITE_URL = "https://stokonomi.com"
SITEMAP_CACHE_CONTROL = "public, max-age=300, stale-while-revalidate=600"
XMLNS = "http://www.sitemaps.org/schemas/sitemap/0.9"


def _add_url(urlset: Element, location: str, last_modified: str | None = None) -> None:
    entry = SubElement(urlset, "url")
    SubElement(entry, "loc").text = location
    if last_modified:
        SubElement(entry, "lastmod").text = last_modified


def build_sitemap(articles: list[AcademyArticleListItem]) -> bytes:
    urlset = Element("urlset", xmlns=XMLNS)
    _add_url(urlset, f"{SITE_URL}/")
    _add_url(urlset, f"{SITE_URL}/akademi")
    for article in articles:
        last_modified = article.updatedAt or article.publishedAt
        _add_url(
            urlset,
            f"{SITE_URL}/akademi/{article.slug}",
            last_modified.isoformat(),
        )
    return tostring(urlset, encoding="utf-8", xml_declaration=True)


@router.get("/sitemap.xml", response_class=Response)
async def sitemap() -> Response:
    try:
        articles = await get_academy_service().get_articles()
    except DirectusTimeoutError as exc:
        raise HTTPException(status_code=504, detail="Content service timed out") from exc
    except (DirectusUnavailableError, DirectusConfigurationError) as exc:
        raise HTTPException(status_code=503, detail="Content service unavailable") from exc
    except (DirectusUpstreamError, DirectusPayloadError) as exc:
        raise HTTPException(status_code=502, detail="Content service returned an invalid response") from exc

    return Response(
        content=build_sitemap(articles),
        media_type="application/xml",
        headers={"Cache-Control": SITEMAP_CACHE_CONTROL},
    )
