# DIRECTUS-D4B dynamic Academy article HTML

Status: **D4B IMPLEMENTED / LOCAL-VERIFIED**
Release status: **P10G-B PRODUCTION CANARY PENDING**

This repository now contains the backend portion of the D4A-approved dynamic
metadata-shell architecture. No Render rewrite, deployment, DNS change,
Directus mutation, R2 change, or Production canary is included in D4B.

## Endpoint and article authority

`GET|HEAD /api/public/academy/html/{slug}` uses the existing `AcademyService`.
It does not query Directus directly and does not own a second publication rule.
Consequently only the D2-eligible universe can receive successful HTML:

`status = published AND published_at IS NOT NULL AND published_at <= governed_time`

Unknown, draft, future, archived, syntactically invalid, and multi-segment paths
return a true 404 from the endpoint.

## Trusted shell contract

Runtime configuration must explicitly provide:

`ACADEMY_FRONTEND_SHELL_URL=https://www.stokonomi.com/index.html`

The configuration accepts only HTTPS, the exact `www.stokonomi.com` host, and
the exact `/index.html` path, with no credentials, query, fragment, alternate
port, or redirect following. Missing or unsafe configuration fails closed.

The provider uses bounded timeouts and a 512 KiB response limit. It requires
HTTP 200, `text/html`, exactly one source `head`, one React `#root`, and a
root-relative `/assets/` module script. It maintains a five-minute in-process
shell cache, uses ETag/Last-Modified conditional refresh, coalesces concurrent
refreshes, and may use a last-known-good shell for at most 24 hours on
network/HTTP availability failure. Stale use emits a sanitized warning. A
malformed replacement shell is not accepted as new truth.

The shell cache is independent from article and CDN response caching. It
contains no article metadata.

## HTML and metadata contract

`lxml` parses and serializes the shell; article data is never inserted through
regex or raw string replacement. Body, React root, module scripts, stylesheets,
hashed asset references, favicon, brand nodes, and unrelated safe head nodes
are preserved. Conflicting root title, description, canonical, robots, Open
Graph, Twitter, article-time, and server-owned JSON-LD nodes are replaced
deterministically.

The response contains article title/description fallbacks, canonical URL,
`index, follow`, article Open Graph fields, publication/modification times,
Twitter large-card fields, and the current global Stokonomi OG image. Directus
file UUID/R2 resolution remains D3 scope.

Server-rendered Article and BreadcrumbList JSON-LD are always emitted. FAQPage
is emitted only from a valid FAQ section already admitted by the Academy DTO.
Publisher and author reference `https://www.stokonomi.com/#organization`.
Every server-owned JSON-LD script carries `data-stokonomi-seo="server"` so the
existing React SEO component can replace it after SPA navigation.

JSON-LD is serialized as JSON and additionally escapes `<`, `>`, `&`, U+2028,
and U+2029. Metadata is assigned through parser text/attribute APIs. Request
input cannot select the shell host, Directus credentials stay server-side, and
no User-Agent branch exists.

## HTTP and cache semantics

| State | Status | Cache-Control |
|---|---:|---|
| Eligible article | 200 | `public, max-age=0, s-maxage=60, stale-while-revalidate=300` |
| Unknown/ineligible/invalid | 404 | `no-store` |
| Directus invalid/upstream payload | 502 | `no-store` |
| Directus/config unavailable | 503 | `no-store` |
| Directus timeout | 504 | `no-store` |
| Shell invalid | 502 | `no-store` |
| Shell unavailable without cache | 503 | `no-store` |

HEAD evaluates the same content and shell authorities as GET, returns the same
status and relevant headers, supplies the would-be representation length, and
omits the body.

## Production boundary and pending canary

The repository endpoint is not publicly routed. Production remains on the
existing SPA fallback until a separately authorized canary applies an exact
Render rule before `/* -> /index.html`:

`/akademi/:slug -> https://stok-yonetimi-api.onrender.com/api/public/academy/html/:slug`

The canary must first use one exact published-article path and verify GET/HEAD,
404/5xx propagation, cache headers, query-bearing URLs, unchanged browser URL,
hashed asset loading, React boot, metadata source, and identical browser/bot
HTML. P10G-B must not be marked complete until that canary passes.

Rollback is to remove the Academy rewrite. The existing SPA fallback then
resumes ownership immediately; the dormant backend endpoint can be rolled back
separately.
