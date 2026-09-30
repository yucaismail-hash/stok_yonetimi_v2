"""Public request-time Academy metadata shell."""

from __future__ import annotations

import re
from functools import lru_cache

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, Response

from app.api.public.academy import MAX_SLUG_LENGTH, SLUG_PATTERN
from app.services.content.academy_html_renderer import render_academy_article_html
from app.services.content.academy_service import (
    AcademyArticleNotFoundError,
    get_academy_service,
)
from app.services.content.directus_client import (
    DirectusConfigurationError,
    DirectusPayloadError,
    DirectusTimeoutError,
    DirectusUnavailableError,
    DirectusUpstreamError,
)
from app.services.content.frontend_shell import (
    FrontendShellConfig,
    FrontendShellConfigurationError,
    FrontendShellPayloadError,
    FrontendShellProvider,
    FrontendShellUnavailableError,
)


router = APIRouter(prefix="/api/public/academy", tags=["Public Academy HTML"])
SUCCESS_CACHE_CONTROL = "public, max-age=0, s-maxage=60, stale-while-revalidate=300"
ERROR_CACHE_CONTROL = "no-store"
_SLUG = re.compile(SLUG_PATTERN)


@lru_cache(maxsize=1)
def get_frontend_shell_provider() -> FrontendShellProvider:
    return FrontendShellProvider(FrontendShellConfig.from_env())


def _error(status_code: int, detail: str, exc: Exception | None = None) -> HTTPException:
    error = HTTPException(
        status_code=status_code,
        detail=detail,
        headers={"Cache-Control": ERROR_CACHE_CONTROL},
    )
    if exc is not None:
        error.__cause__ = exc
    return error


@router.api_route("/html/{slug}", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def get_academy_article_html(request: Request, slug: str) -> Response:
    if len(slug) > MAX_SLUG_LENGTH or _SLUG.fullmatch(slug) is None:
        raise _error(404, "Published Academy article not found")

    try:
        article = await get_academy_service().get_article_by_slug(slug)
    except AcademyArticleNotFoundError as exc:
        raise _error(404, "Published Academy article not found", exc) from exc
    except DirectusTimeoutError as exc:
        raise _error(504, "Content service timed out", exc) from exc
    except (DirectusUnavailableError, DirectusConfigurationError) as exc:
        raise _error(503, "Content service unavailable", exc) from exc
    except (DirectusUpstreamError, DirectusPayloadError) as exc:
        raise _error(502, "Content service returned an invalid response", exc) from exc

    try:
        shell = await get_frontend_shell_provider().get_shell()
        rendered = render_academy_article_html(shell, article)
    except (FrontendShellUnavailableError, FrontendShellConfigurationError) as exc:
        raise _error(503, "Frontend shell unavailable", exc) from exc
    except FrontendShellPayloadError as exc:
        raise _error(502, "Frontend shell is invalid", exc) from exc

    headers = {"Cache-Control": SUCCESS_CACHE_CONTROL}
    if request.method == "HEAD":
        headers["Content-Length"] = str(len(rendered.encode("utf-8")))
        return Response(status_code=200, media_type="text/html", headers=headers)
    return HTMLResponse(content=rendered, status_code=200, headers=headers)


@router.api_route(
    "/html/{invalid_path:path}",
    methods=["GET", "HEAD"],
    include_in_schema=False,
)
async def reject_invalid_academy_html_path(invalid_path: str) -> Response:
    raise _error(404, "Published Academy article not found")
