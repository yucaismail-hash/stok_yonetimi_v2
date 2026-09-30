"""Safe article metadata injection into the current deployed Vite shell."""

from __future__ import annotations

import json

from lxml import html
from lxml.etree import ParserError

from app.schemas.academy import AcademyArticleDetail
from app.services.content.frontend_shell import FrontendShellPayloadError


SITE_URL = "https://www.stokonomi.com"
GLOBAL_OG_IMAGE = f"{SITE_URL}/og/stokonomi-og.png"
GLOBAL_OG_IMAGE_ALT = "Stokonomi - İşletmeler stok değil, belirsizlik yönetiyor."
ORGANIZATION_ID = f"{SITE_URL}/#organization"
SEO_DATA_ATTRIBUTE = "data-stokonomi-seo"

_META_NAMES = {
    "description",
    "robots",
    "twitter:card",
    "twitter:title",
    "twitter:description",
    "twitter:image",
    "twitter:image:alt",
}
_META_PROPERTIES = {
    "og:type",
    "og:url",
    "og:title",
    "og:description",
    "og:site_name",
    "og:locale",
    "og:image",
    "og:image:alt",
    "article:published_time",
    "article:modified_time",
}


def _json_script_payload(value: object) -> str:
    serialized = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return (
        serialized.replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def _append_meta(head, *, key: str, value: str, property_: bool = False) -> None:
    node = html.Element("meta")
    node.set("property" if property_ else "name", key)
    node.set("content", value)
    node.set(SEO_DATA_ATTRIBUTE, "server")
    head.append(node)


def _append_json_ld(head, value: object) -> None:
    node = html.Element("script")
    node.set("type", "application/ld+json")
    node.set(SEO_DATA_ATTRIBUTE, "server")
    node.text = _json_script_payload(value)
    head.append(node)


def render_academy_article_html(shell: str, article: AcademyArticleDetail) -> str:
    try:
        document = html.document_fromstring(shell)
    except (ParserError, ValueError) as exc:
        raise FrontendShellPayloadError("Frontend shell HTML is malformed") from exc
    heads = document.xpath("/html/head")
    if len(heads) != 1:
        raise FrontendShellPayloadError("Frontend shell must contain exactly one head")
    head = heads[0]

    for node in list(head.xpath("title")):
        head.remove(node)
    for node in list(head.xpath('link[@rel="canonical"]')):
        head.remove(node)
    for node in list(head.xpath(f'script[@{SEO_DATA_ATTRIBUTE}]')):
        head.remove(node)
    for node in list(head.xpath("meta")):
        if node.get("name") in _META_NAMES or node.get("property") in _META_PROPERTIES:
            head.remove(node)

    canonical = f"{SITE_URL}/akademi/{article.slug}"
    title = article.seoTitle or article.title
    description = article.seoDescription or article.description
    published = article.publishedAt.isoformat()
    modified = (article.updatedAt or article.publishedAt).isoformat()

    title_node = html.Element("title")
    title_node.set(SEO_DATA_ATTRIBUTE, "server")
    title_node.text = title
    head.append(title_node)
    _append_meta(head, key="description", value=description)
    _append_meta(head, key="robots", value="index, follow")

    canonical_node = html.Element("link")
    canonical_node.set("rel", "canonical")
    canonical_node.set("href", canonical)
    canonical_node.set(SEO_DATA_ATTRIBUTE, "server")
    head.append(canonical_node)

    for key, value in (
        ("og:type", "article"),
        ("og:url", canonical),
        ("og:title", title),
        ("og:description", description),
        ("og:site_name", "Stokonomi"),
        ("og:locale", "tr_TR"),
        ("og:image", GLOBAL_OG_IMAGE),
        ("og:image:alt", GLOBAL_OG_IMAGE_ALT),
        ("article:published_time", published),
        ("article:modified_time", modified),
    ):
        _append_meta(head, key=key, value=value, property_=True)

    for key, value in (
        ("twitter:card", "summary_large_image"),
        ("twitter:title", title),
        ("twitter:description", description),
        ("twitter:image", GLOBAL_OG_IMAGE),
        ("twitter:image:alt", GLOBAL_OG_IMAGE_ALT),
    ):
        _append_meta(head, key=key, value=value)

    _append_json_ld(
        head,
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "@id": f"{canonical}#article",
            "headline": title,
            "description": description,
            "datePublished": published,
            "dateModified": modified,
            "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
            "inLanguage": "tr-TR",
            "image": GLOBAL_OG_IMAGE,
            "publisher": {"@id": ORGANIZATION_ID},
            "author": {"@id": ORGANIZATION_ID},
        },
    )
    _append_json_ld(
        head,
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "Ana Sayfa",
                    "item": f"{SITE_URL}/",
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": "Akademi",
                    "item": f"{SITE_URL}/akademi",
                },
                {
                    "@type": "ListItem",
                    "position": 3,
                    "name": article.title,
                    "item": canonical,
                },
            ],
        },
    )

    faqs = [
        faq
        for section in article.sections
        if section.type == "faq"
        for faq in section.faqs
    ]
    if faqs:
        _append_json_ld(
            head,
            {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": faq.question,
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": faq.answer,
                        },
                    }
                    for faq in faqs
                ],
            },
        )

    return html.tostring(
        document,
        encoding="unicode",
        method="html",
        doctype="<!DOCTYPE html>",
    )
