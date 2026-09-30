import json
from copy import deepcopy

from lxml import html

from app.schemas.academy import AcademyArticleDirectusDto, AcademyArticleDetail
from app.services.content.academy_html_renderer import (
    GLOBAL_OG_IMAGE,
    render_academy_article_html,
)


ASSET = "/assets/index.VITE-HASH-987.js"


def _shell():
    return f"""<!DOCTYPE html><html lang="tr"><head>
    <title>Homepage</title>
    <meta name="description" content="Root description">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="https://www.stokonomi.com/">
    <meta property="og:type" content="website">
    <meta property="og:title" content="Root OG">
    <meta name="twitter:title" content="Root Twitter">
    <link rel="icon" href="/brand/icon.png">
    <script type="application/ld+json">{{"@type":"Organization"}}</script>
    <script type="module" crossorigin src="{ASSET}"></script>
    </head><body><div id="root"></div></body></html>"""


def _article_payload():
    return {
        "id": "c1e10e42-d621-41e9-ac29-1c7739962f01",
        "status": "published",
        "sort": None,
        "slug": "emniyet-stoku-nedir",
        "title": "Emniyet Stoku Nedir?",
        "description": "Türkçe açıklama",
        "category": "Emniyet Stoku",
        "published_at": "2026-08-25T10:52:24Z",
        "updated_at": "2026-08-27T21:07:53Z",
        "reading_time": 3,
        "sections": [
            {
                "type": "faq",
                "faqs": [{"question": "Nedir?", "answer": "Güvenli yanıttır."}],
            }
        ],
        "seo_title": "Emniyet Stoku: Ölçüm ve Örnek | Stokonomi",
        "seo_description": "Emniyet stokunu güvenli biçimde öğrenin.",
        "featured_image": None,
        "featured_image_alt": None,
    }


def _article(payload=None):
    dto = AcademyArticleDirectusDto.model_validate(payload or _article_payload())
    return AcademyArticleDetail.from_directus(dto)


def _meta(document, key, *, property_=False):
    attribute = "property" if property_ else "name"
    nodes = document.xpath(f'//meta[@{attribute}="{key}"]')
    assert len(nodes) == 1
    return nodes[0].get("content")


def test_renderer_preserves_shell_and_injects_complete_article_metadata():
    rendered = render_academy_article_html(_shell(), _article())
    document = html.document_fromstring(rendered)
    assert document.xpath("string(/html/head/title)") == "Emniyet Stoku: Ölçüm ve Örnek | Stokonomi"
    assert _meta(document, "description") == "Emniyet stokunu güvenli biçimde öğrenin."
    assert _meta(document, "robots") == "index, follow"
    assert _meta(document, "og:type", property_=True) == "article"
    assert _meta(document, "og:url", property_=True) == "https://www.stokonomi.com/akademi/emniyet-stoku-nedir"
    assert _meta(document, "og:image", property_=True) == GLOBAL_OG_IMAGE
    assert _meta(document, "article:published_time", property_=True).startswith("2026-08-25")
    assert _meta(document, "article:modified_time", property_=True).startswith("2026-08-27")
    assert _meta(document, "twitter:card") == "summary_large_image"
    assert document.xpath('string(//link[@rel="canonical"]/@href)') == "https://www.stokonomi.com/akademi/emniyet-stoku-nedir"
    assert document.xpath('count(//*[@id="root"])') == 1
    assert document.xpath('string(//script[@type="module"]/@src)') == ASSET
    assert document.xpath('string(//link[@rel="icon"]/@href)') == "/brand/icon.png"
    assert "VITE-HASH-987" in rendered

    scripts = document.xpath('//script[@type="application/ld+json"]')
    assert len(scripts) == 4
    server_data = [
        json.loads(node.text)
        for node in scripts
        if node.get("data-stokonomi-seo") == "server"
    ]
    assert [item["@type"] for item in server_data] == [
        "Article",
        "BreadcrumbList",
        "FAQPage",
    ]
    assert server_data[0]["publisher"]["@id"] == "https://www.stokonomi.com/#organization"


def test_faq_json_ld_is_absent_without_faq_evidence():
    payload = _article_payload()
    payload["sections"] = [{"type": "paragraph", "content": "İçerik"}]
    rendered = render_academy_article_html(_shell(), _article(payload))
    document = html.document_fromstring(rendered)
    types = [
        json.loads(node.text)["@type"]
        for node in document.xpath('//script[@data-stokonomi-seo="server"]')
    ]
    assert types == ["Article", "BreadcrumbList"]


def test_metadata_and_json_ld_resist_injection_and_script_breakout():
    payload = deepcopy(_article_payload())
    payload["seo_title"] = 'Türkçe "><script>alert(1)<\\/script>'
    payload["seo_description"] = "Açıklama <img src=x onerror=alert(1)> & güvenli"
    breakout = "<" + "/script><script>alert(1)<" + "/script>"
    payload["sections"] = [
        {
            "type": "faq",
            "faqs": [
                {
                    "question": "Kırılır mı?",
                    "answer": breakout + "\u2028\u2029",
                }
            ],
        }
    ]
    rendered = render_academy_article_html(_shell(), _article(payload))
    document = html.document_fromstring(rendered)
    assert document.xpath("string(/html/head/title)") == payload["seo_title"]
    assert _meta(document, "description") == payload["seo_description"]
    assert len(document.xpath('//script[not(@type="module")]')) == 4
    assert breakout not in rendered
    assert "\\u003c/script\\u003e" in rendered
    assert "\\u0026" in rendered
    assert "\\u2028" in rendered
    assert "\\u2029" in rendered
