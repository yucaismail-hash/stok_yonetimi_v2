import asyncio
from datetime import datetime, timezone
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
GOVERNED_AT = datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc)


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
        assert query["filter[_and][0][status][_eq]"] == ["published"]
        assert query["filter[_and][1][published_at][_nnull]"] == ["true"]
        assert query["filter[_and][2][published_at][_lte]"] == ["2026-08-13T12:00:00Z"]
        assert query["fields"] == [",".join(LIST_FIELDS)]
        assert query["fields"] != ["*"]
        assert query["sort"] == ["-published_at,sort,id"]
        assert query["limit"] == ["50"]
        assert query["page"] == ["1"]
        return httpx.Response(200, json={"data": [_item()]})

    result = _run(
        DirectusAcademyClient(
            _config(), transport=httpx.MockTransport(handler)
        ).get_published_articles(GOVERNED_AT)
    )
    assert result[0].status == "published"


def test_detail_request_uses_slug_and_published_filters():
    async def handler(request):
        query = parse_qs(request.url.query.decode())
        assert query["filter[_and][0][slug][_eq]"] == ["stok-yonetimi-nedir"]
        assert query["filter[_and][1][status][_eq]"] == ["published"]
        assert query["filter[_and][2][published_at][_nnull]"] == ["true"]
        assert query["filter[_and][3][published_at][_lte]"] == ["2026-08-13T12:00:00Z"]
        assert query["limit"] == ["1"]
        assert query["fields"] == [",".join(DETAIL_FIELDS)]
        return httpx.Response(200, json={"data": [_item(detail=True)]})

    client = DirectusAcademyClient(_config(), transport=httpx.MockTransport(handler))
    assert _run(
        client.get_published_article_by_slug("stok-yonetimi-nedir", GOVERNED_AT)
    ).slug == "stok-yonetimi-nedir"


def test_list_fetches_all_pages_without_truncation():
    calls = []

    async def handler(request):
        query = parse_qs(request.url.query.decode())
        page = int(query["page"][0])
        calls.append(page)
        if page == 1:
            first = _item()
            second = {**_item(), "id": "c1e10e42-d621-41e9-ac29-1c7739962f02", "slug": "ikinci"}
            return httpx.Response(200, json={"data": [first, second]})
        third = {**_item(), "id": "c1e10e42-d621-41e9-ac29-1c7739962f03", "slug": "ucuncu"}
        return httpx.Response(200, json={"data": [third]})

    client = DirectusAcademyClient(
        _config(), transport=httpx.MockTransport(handler), page_size=2
    )
    result = _run(client.get_published_articles(GOVERNED_AT))
    assert calls == [1, 2]
    assert [item.slug for item in result] == ["stok-yonetimi-nedir", "ikinci", "ucuncu"]


def test_exact_page_boundary_fetches_the_terminal_empty_page():
    calls = []

    async def handler(request):
        page = int(parse_qs(request.url.query.decode())["page"][0])
        calls.append(page)
        if page == 1:
            second = {
                **_item(),
                "id": "c1e10e42-d621-41e9-ac29-1c7739962f02",
                "slug": "ikinci",
            }
            return httpx.Response(200, json={"data": [_item(), second]})
        return httpx.Response(200, json={"data": []})

    client = DirectusAcademyClient(
        _config(), transport=httpx.MockTransport(handler), page_size=2
    )
    result = _run(client.get_published_articles(GOVERNED_AT))
    assert calls == [1, 2]
    assert len(result) == 2


def test_duplicate_across_pages_fails_closed():
    async def handler(request):
        return httpx.Response(200, json={"data": [_item()]})

    client = DirectusAcademyClient(
        _config(), transport=httpx.MockTransport(handler), page_size=1
    )
    with pytest.raises(DirectusPayloadError, match="duplicate paginated"):
        _run(client.get_published_articles(GOVERNED_AT))


def test_malformed_item_fails_the_whole_list_without_silent_skip():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200, json={"data": [_item(), {"status": "published"}]}
        )
    )
    client = DirectusAcademyClient(_config(), transport=transport)
    with pytest.raises(DirectusPayloadError, match="invalid Academy payload"):
        _run(client.get_published_articles(GOVERNED_AT))


def test_upstream_future_item_fails_closed_even_if_filter_is_ignored():
    future = {**_item(), "published_at": "2026-08-13T12:00:01Z"}
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"data": [future]})
    )
    client = DirectusAcademyClient(_config(), transport=transport)
    with pytest.raises(DirectusPayloadError, match="ineligible"):
        _run(client.get_published_articles(GOVERNED_AT))


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
