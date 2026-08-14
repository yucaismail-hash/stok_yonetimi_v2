"""Strict Academy CMS DTOs and public API response contracts."""

from datetime import datetime
from typing import Annotated, Literal, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, model_validator


class AcademySchema(BaseModel):
    """Reject fields that are not part of the Academy content contract."""

    model_config = ConfigDict(extra="forbid")


class HeadingSection(AcademySchema):
    type: Literal["heading"]
    content: StrictStr
    level: Literal[2, 3]


class ParagraphSection(AcademySchema):
    type: Literal["paragraph"]
    content: StrictStr


class BulletListSection(AcademySchema):
    type: Literal["bulletList"]
    items: list[StrictStr]


class NumberedListSection(AcademySchema):
    type: Literal["numberedList"]
    items: list[StrictStr]


class CalloutSection(AcademySchema):
    type: Literal["callout"]
    content: StrictStr


class FormulaSection(AcademySchema):
    type: Literal["formula"]
    content: StrictStr


class ExampleSection(AcademySchema):
    type: Literal["example"]
    content: StrictStr


class TableSection(AcademySchema):
    type: Literal["table"]
    headers: list[StrictStr]
    rows: list[list[StrictStr]]

    @model_validator(mode="after")
    def rows_match_headers(self) -> "TableSection":
        if any(len(row) != len(self.headers) for row in self.rows):
            raise ValueError("each table row must match the header count")
        return self


class FAQItem(AcademySchema):
    question: StrictStr
    answer: StrictStr


class FAQSection(AcademySchema):
    type: Literal["faq"]
    faqs: list[FAQItem]


class DividerSection(AcademySchema):
    type: Literal["divider"]
    # The renderer ignores this value, but the current source article contains it.
    content: StrictStr | None = None


AcademySection = Annotated[
    Union[
        HeadingSection,
        ParagraphSection,
        BulletListSection,
        NumberedListSection,
        CalloutSection,
        FormulaSection,
        ExampleSection,
        TableSection,
        FAQSection,
        DividerSection,
    ],
    Field(discriminator="type"),
]


AcademyArticleStatus = Literal["draft", "published", "archived"]


class AcademyArticleDirectusDto(AcademySchema):
    id: UUID
    status: AcademyArticleStatus
    slug: StrictStr
    title: StrictStr
    description: StrictStr
    category: StrictStr
    published_at: datetime | None
    updated_at: datetime | None
    reading_time: StrictInt
    sections: list[AcademySection]
    seo_title: StrictStr | None
    seo_description: StrictStr | None
    featured_image: UUID | None
    featured_image_alt: StrictStr | None
    sort: StrictInt | None


class AcademyArticleListItem(AcademySchema):
    id: UUID
    slug: StrictStr
    title: StrictStr
    description: StrictStr
    category: StrictStr
    publishedAt: datetime
    updatedAt: datetime | None
    readingTime: StrictInt
    featuredImage: UUID | None
    featuredImageAlt: StrictStr | None

    @classmethod
    def from_directus(cls, article: AcademyArticleDirectusDto) -> "AcademyArticleListItem":
        if article.status != "published" or article.published_at is None:
            raise ValueError("public Academy responses require a published article")
        return cls(
            id=article.id,
            slug=article.slug,
            title=article.title,
            description=article.description,
            category=article.category,
            publishedAt=article.published_at,
            updatedAt=article.updated_at,
            readingTime=article.reading_time,
            featuredImage=article.featured_image,
            featuredImageAlt=article.featured_image_alt,
        )


class AcademyArticleDetail(AcademyArticleListItem):
    status: Literal["published"]
    sections: list[AcademySection]
    seoTitle: StrictStr | None
    seoDescription: StrictStr | None

    @classmethod
    def from_directus(cls, article: AcademyArticleDirectusDto) -> "AcademyArticleDetail":
        list_item = AcademyArticleListItem.from_directus(article)
        return cls(
            **list_item.model_dump(),
            status="published",
            sections=article.sections,
            seoTitle=article.seo_title,
            seoDescription=article.seo_description,
        )


class AcademyArticleListResponse(AcademySchema):
    items: list[AcademyArticleListItem]
