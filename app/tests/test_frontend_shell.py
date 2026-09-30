import asyncio

import httpx
import pytest

from app.services.content.frontend_shell import (
    PRODUCTION_SHELL_URL,
    FrontendShellConfig,
    FrontendShellConfigurationError,
    FrontendShellPayloadError,
    FrontendShellProvider,
    FrontendShellUnavailableError,
)


def _shell(asset="/assets/index.ABC123.js"):
    return f"""<!doctype html><html><head><title>Root</title>
    <script type="module" crossorigin src="{asset}"></script></head>
    <body><div id="root"></div></body></html>"""


def _run(coro):
    return asyncio.run(coro)


def _provider(
    handler,
    *,
    clock=lambda: 0.0,
    ttl=300,
    max_bytes=512 * 1024,
    max_stale=86400,
):
    return FrontendShellProvider(
        FrontendShellConfig(
            url=PRODUCTION_SHELL_URL,
            ttl_seconds=ttl,
            max_bytes=max_bytes,
            max_stale_seconds=max_stale,
        ),
        transport=httpx.MockTransport(handler),
        monotonic=clock,
    )


def test_healthy_shell_is_fetched_once_and_cached():
    calls = 0

    async def handler(request):
        nonlocal calls
        calls += 1
        assert str(request.url) == PRODUCTION_SHELL_URL
        assert request.headers["accept"] == "text/html"
        return httpx.Response(
            200,
            headers={"Content-Type": "text/html; charset=utf-8", "ETag": '"v1"'},
            text=_shell(),
        )

    provider = _provider(handler)
    assert _run(provider.get_shell()) == _shell()
    assert _run(provider.get_shell()) == _shell()
    assert calls == 1


def test_etag_and_last_modified_conditional_304_refresh():
    now = [0.0]
    calls = 0

    async def handler(request):
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(
                200,
                headers={
                    "Content-Type": "text/html",
                    "ETag": '"v1"',
                    "Last-Modified": "Wed, 30 Sep 2026 00:00:00 GMT",
                },
                text=_shell(),
            )
        assert request.headers["if-none-match"] == '"v1"'
        assert request.headers["if-modified-since"] == "Wed, 30 Sep 2026 00:00:00 GMT"
        return httpx.Response(304)

    provider = _provider(handler, clock=lambda: now[0], ttl=1)
    assert _run(provider.get_shell()) == _shell()
    now[0] = 2
    assert _run(provider.get_shell()) == _shell()
    assert calls == 2


def test_last_known_good_is_used_for_network_refresh_failure():
    now = [0.0]
    calls = 0

    async def handler(request):
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(
                200, headers={"Content-Type": "text/html"}, text=_shell()
            )
        raise httpx.ConnectError("private network detail", request=request)

    provider = _provider(handler, clock=lambda: now[0], ttl=1)
    assert _run(provider.get_shell()) == _shell()
    now[0] = 2
    assert _run(provider.get_shell()) == _shell()
    assert calls == 2


def test_last_known_good_expires_at_the_bounded_stale_limit():
    now = [0.0]
    calls = 0

    async def handler(request):
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(
                200, headers={"Content-Type": "text/html"}, text=_shell()
            )
        raise httpx.ConnectError("down", request=request)

    provider = _provider(handler, clock=lambda: now[0], ttl=1, max_stale=2)
    assert _run(provider.get_shell()) == _shell()
    now[0] = 3
    with pytest.raises(FrontendShellUnavailableError):
        _run(provider.get_shell())


def test_concurrent_cold_requests_share_one_refresh():
    calls = 0

    async def handler(request):
        nonlocal calls
        calls += 1
        await asyncio.sleep(0)
        return httpx.Response(
            200, headers={"Content-Type": "text/html"}, text=_shell()
        )

    provider = _provider(handler)

    async def fetch_both():
        return await asyncio.gather(provider.get_shell(), provider.get_shell())

    assert _run(fetch_both()) == [_shell(), _shell()]
    assert calls == 1


@pytest.mark.parametrize(
    ("handler", "error"),
    [
        (
            lambda request: (_ for _ in ()).throw(httpx.ReadTimeout("late", request=request)),
            FrontendShellUnavailableError,
        ),
        (
            lambda request: (_ for _ in ()).throw(httpx.ConnectError("down", request=request)),
            FrontendShellUnavailableError,
        ),
        (lambda request: httpx.Response(503), FrontendShellUnavailableError),
        (
            lambda request: httpx.Response(
                200, headers={"Content-Type": "application/json"}, text="{}"
            ),
            FrontendShellPayloadError,
        ),
        (
            lambda request: httpx.Response(
                200,
                headers={"Content-Type": "text/html"},
                text="<html><head></head><head><script type='module' src='/assets/a.js'></script></head><body><div id='root'></div></body></html>",
            ),
            FrontendShellPayloadError,
        ),
        (
            lambda request: httpx.Response(
                200,
                headers={"Content-Type": "text/html"},
                text="<html><head></head><body><div id='root'></div></body></html>",
            ),
            FrontendShellPayloadError,
        ),
        (
            lambda request: httpx.Response(
                200,
                headers={"Content-Type": "text/html"},
                text="<html><head><script type='module' src='/assets/a.js'></script></head><body></body></html>",
            ),
            FrontendShellPayloadError,
        ),
        (
            lambda request: httpx.Response(
                200,
                headers={"Content-Type": "text/html"},
                text="<html><body><div id='root'></div></body></html>",
            ),
            FrontendShellPayloadError,
        ),
    ],
)
def test_shell_failures_are_sanitized_and_classified(handler, error):
    with pytest.raises(error) as exc:
        _run(_provider(handler).get_shell())
    assert "private network detail" not in str(exc.value)


def test_oversized_stream_is_rejected():
    shell = _shell() + (" " * 2000)
    handler = lambda request: httpx.Response(
        200, headers={"Content-Type": "text/html"}, text=shell
    )
    with pytest.raises(FrontendShellPayloadError, match="size limit"):
        _run(_provider(handler, max_bytes=1024).get_shell())


@pytest.mark.parametrize(
    "url",
    [
        "",
        "http://www.stokonomi.com/index.html",
        "https://evil.example/index.html",
        "https://www.stokonomi.com/other.html",
        "https://www.stokonomi.com/index.html?next=https://evil.example",
        "https://user:pass@www.stokonomi.com/index.html",
    ],
)
def test_arbitrary_or_unsafe_shell_source_is_impossible(url):
    with pytest.raises(FrontendShellConfigurationError):
        FrontendShellConfig(url=url)
