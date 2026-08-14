from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.schemas.academy import (
    AcademyArticleDetail,
    AcademyArticleDirectusDto,
    AcademyArticleListItem,
)


def _article_payload(status="published"):
    return {
        "id": "c1e10e42-d621-41e9-ac29-1c7739962f01",
        "status": status,
        "slug": "stok-yonetimi-nedir",
        "title": "Stok Yönetimi Nedir?",
        "description": "Stok yönetimine giriş.",
        "category": "Temel Kavramlar",
        "published_at": "2026-08-13T00:00:00Z" if status == "published" else None,
        "updated_at": "2026-08-14T08:30:00Z",
        "reading_time": 8,
        "sections": [
            {"type": "heading", "level": 2, "content": "Başlık"},
            {"type": "paragraph", "content": "Paragraf"},
            {"type": "table", "headers": ["Kavram", "Açıklama"], "rows": [["ROP", "Sipariş noktası"]]},
            {"type": "faq", "faqs": [{"question": "Nedir?", "answer": "Yanıt."}]},
            {"type": "divider", "content": ""},
        ],
        "seo_title": "SEO başlığı",
        "seo_description": "SEO açıklaması",
        "featured_image": None,
        "featured_image_alt": None,
        "sort": None,
    }


def test_valid_published_article_dto_parses():
    article = AcademyArticleDirectusDto.model_validate(_article_payload())
    assert article.status == "published"
    assert len(article.sections) == 5


def test_draft_article_dto_parses():
    article = AcademyArticleDirectusDto.model_validate(_article_payload("draft"))
    assert article.status == "draft"
    assert article.published_at is None


def test_nullable_updated_at_is_accepted():
    payload = _article_payload()
    payload["updated_at"] = None
    assert AcademyArticleDirectusDto.model_validate(payload).updated_at is None


def test_nullable_featured_image_is_accepted():
    assert AcademyArticleDirectusDto.model_validate(_article_payload()).featured_image is None


def test_invalid_section_type_is_rejected():
    payload = _article_payload()
    payload["sections"] = [{"type": "video", "content": "invalid"}]
    with pytest.raises(ValidationError):
        AcademyArticleDirectusDto.model_validate(payload)


def test_heading_level_four_is_rejected():
    payload = _article_payload()
    payload["sections"] = [{"type": "heading", "level": 4, "content": "Başlık"}]
    with pytest.raises(ValidationError):
        AcademyArticleDirectusDto.model_validate(payload)


def test_malformed_table_row_is_rejected():
    payload = _article_payload()
    payload["sections"] = [{"type": "table", "headers": ["A", "B"], "rows": [["only one"]]}]
    with pytest.raises(ValidationError):
        AcademyArticleDirectusDto.model_validate(payload)


def test_faq_item_missing_answer_is_rejected():
    payload = _article_payload()
    payload["sections"] = [{"type": "faq", "faqs": [{"question": "Nedir?"}]}]
    with pytest.raises(ValidationError):
        AcademyArticleDirectusDto.model_validate(payload)


def test_public_list_mapping_uses_camel_case():
    article = AcademyArticleDirectusDto.model_validate(_article_payload())
    public_item = AcademyArticleListItem.from_directus(article)
    data = public_item.model_dump(mode="json")
    assert data["publishedAt"] == "2026-08-13T00:00:00Z"
    assert data["readingTime"] == 8
    assert data["featuredImage"] is None
    assert "published_at" not in data


def test_public_detail_mapping_uses_camel_case_and_preserves_sections():
    payload = deepcopy(_article_payload())
    article = AcademyArticleDirectusDto.model_validate(payload)
    detail = AcademyArticleDetail.from_directus(article)
    data = detail.model_dump(mode="json")
    assert data["status"] == "published"
    assert data["seoTitle"] == payload["seo_title"]
    assert data["seoDescription"] == payload["seo_description"]
    assert data["sections"][0] == payload["sections"][0]
