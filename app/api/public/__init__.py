"""Public, unauthenticated API routes with explicitly bounded scope."""

from fastapi import APIRouter

PUBLIC_ACADEMY_PATH_PATTERN = r"^/api/public/academy(?:/|$)"
PUBLIC_SITEMAP_PATH_PATTERN = r"^/sitemap\.xml$"

from app.api.public.academy import router as academy_router  # noqa: E402
from app.api.public.sitemap import router as sitemap_router  # noqa: E402

router = APIRouter()
router.include_router(academy_router)
router.include_router(sitemap_router)

__all__ = ["PUBLIC_ACADEMY_PATH_PATTERN", "PUBLIC_SITEMAP_PATH_PATTERN", "router"]
