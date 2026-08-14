import asyncio
from urllib.parse import parse_qs

import httpx
import pytest

from app.services.content.directus_client import (
    DETAIL_FIELDS,
    LIST_FIELDS,
    DirectusAcademyClient,
    DirectusConfig,
    DirectusConfigurationError,
    DirectusPayloadError,
    DirectusTimeoutError,
    DirectusUnavailableError,
    DirectusUpstreamError,
)


TOKEN = "test-service-token-secret"


def _config(url="https://cms.example.com/"):
    return DirectusConfig(url=url, service_token=TOKEN, timeout_seconds=2)


def _item(status="published", *, detail=False):
    item = {
        "id": "c1e10e42-d621-41e9-ac29-1c7739962f01",
        "status": status,
        "sort": None,
        "slug": "stok-yonetimi-nedir",
        "title": "Stok Yönetimi Nedir?",
        "description": "Açıklama",
        "category": "Temel Kavramlar",
        "published_at": "2026-08-13T00:00:00Z",
        "updated_at": None,
        "reading_time": 8,
        "featured_image": None,
        "featured_image_alt": None,
    }
    if detail:
        item.update(
            sections=[{"type": "paragraph", "content": "İçerik"}],
            seo_title=None,
            seo_description=None,
        )
    return item


def _run(coro):
    return asyncio.run(coro)


def test_list_request_uses_published_filter_and_explicit_fields():
    async def handler(request):
        query = parse_qs(request.url.query.decode())
        assert query["filter[status][_eq]"] == ["published"]
        assert query["fields"] == [",".join(LIST_FIELDS)]
        assert query["fields"] != ["*"]
        assert query["sort"] == ["-published_at,sort"]
        return httpx.Response(200, json={"data": [_item()]})

    result = _run(DirectusAcademyClient(_config(), transport=httpx.MockTransport(handler)).get_published_articles())
    assert result[0].status == "published"


def test_detail_request_uses_slug_and_published_filters():
    async def handler(request):
        query = parse_qs(request.url.query.decode())
        assert query["filter[_and][0][slug][_eq]"] == ["stok-yonetimi-nedir"]
        assert query["filter[_and][1][status][_eq]"] == ["published"]
        assert query["limit"] == ["1"]
        assert query["fields"] == [",".join(DETAIL_FIELDS)]
        return httpx.Response(200, json={"data": [_item(detail=True)]})

    client = DirectusAcademyClient(_config(), transport=httpx.MockTransport(handler))
    assert _run(client.get_published_article_by_slug("stok-yonetimi-nedir")).slug == "stok-yonetimi-nedir"


def test_detail_empty_data_returns_none():
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"data": []}))
    client = DirectusAcademyClient(_config(), transport=transport)
    assert _run(client.get_published_article_by_slug("missing")) is None


@pytest.mark.parametrize(
    ("exception", "expected"),
    [
        (httpx.ReadTimeout("late"), DirectusTimeoutError),
        (httpx.ConnectError("offline"), DirectusUnavailableError),
    ],
)
def test_transport_errors_are_mapped(exception, expected):
    def handler(request):
        raise exception

    client = DirectusAcademyClient(_config(), transport=httpx.MockTransport(handler))
    with pytest.raises(expected):
        _run(client.get_published_articles())


def test_upstream_500_is_mapped_without_body():
    transport = httpx.MockTransport(lambda request: httpx.Response(500, text="sensitive upstream body"))
    client = DirectusAcademyClient(_config(), transport=transport)
    with pytest.raises(DirectusUpstreamError, match="unexpected HTTP status") as error:
        _run(client.get_published_articles())
    assert "sensitive" not in str(error.value)


def test_invalid_json_is_mapped():
    transport = httpx.MockTransport(lambda request: httpx.Response(200, text="not-json"))
    client = DirectusAcademyClient(_config(), transport=transport)
    with pytest.raises(DirectusPayloadError, match="invalid JSON"):
        _run(client.get_published_articles())


def test_invalid_directus_dto_is_mapped():
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"data": [{"status": "published"}]}))
    client = DirectusAcademyClient(_config(), transport=transport)
    with pytest.raises(DirectusPayloadError, match="invalid Academy payload"):
        _run(client.get_published_articles())


def test_authorization_header_is_present_without_secret_leakage():
    async def handler(request):
        assert request.headers["Authorization"] == f"Bearer {TOKEN}"
        assert request.headers["Accept"] == "application/json"
        return httpx.Response(200, json={"data": []})

    config = _config()
    client = DirectusAcademyClient(config, transport=httpx.MockTransport(handler))
    _run(client.get_published_articles())
    assert TOKEN not in repr(config)
    assert TOKEN not in repr(client)


@pytest.mark.parametrize(
    "url",
    [
        "",
        "cms.example.com",
        "http://cms.example.com",
        "https://user:password@cms.example.com",
        "https://cms.example.com?preview=true",
        "https://cms.example.com#fragment",
    ],
)
def test_invalid_directus_urls_are_rejected(url):
    with pytest.raises(DirectusConfigurationError):
        _config(url)
