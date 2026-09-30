from datetime import datetime, timezone

import pytest

from app.schemas.academy import AcademyArticleDirectusDto
from app.services.content.academy_publication_policy import is_publicly_eligible


GOVERNED_AT = datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)


def _article(status, published_at):
    return AcademyArticleDirectusDto.model_validate(
        {
            "id": "c1e10e42-d621-41e9-ac29-1c7739962f01",
            "status": status,
            "sort": None,
            "slug": "policy-matrix",
            "title": "Policy Matrix",
            "description": "Synthetic policy test.",
            "category": "Test",
            "published_at": published_at,
            "updated_at": None,
            "reading_time": 1,
            "sections": [],
            "seo_title": None,
            "seo_description": None,
            "featured_image": None,
            "featured_image_alt": None,
        }
    )


@pytest.mark.parametrize(
    ("status", "published_at", "expected"),
    [
        ("draft", "2026-09-29T11:59:59Z", False),
        ("draft", "2026-09-29T12:00:01Z", False),
        ("published", None, False),
        ("published", "2026-09-29T12:00:00Z", True),
        ("published", "2026-09-29T12:00:01Z", False),
        ("archived", "2026-09-29T11:59:59Z", False),
    ],
)
def test_canonical_publication_eligibility_matrix(status, published_at, expected):
    assert is_publicly_eligible(_article(status, published_at), GOVERNED_AT) is expected
