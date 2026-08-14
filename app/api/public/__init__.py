"""Public, unauthenticated API routes with explicitly bounded scope."""

PUBLIC_ACADEMY_PATH_PATTERN = r"^/api/public/academy(?:/|$)"

from app.api.public.academy import router  # noqa: E402

__all__ = ["PUBLIC_ACADEMY_PATH_PATTERN", "router"]
