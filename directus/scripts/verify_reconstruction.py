"""Verify a disposable Directus reconstruction with synthetic local content only."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import httpx

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from app.services.content.directus_client import DirectusAcademyClient, DirectusConfig


BASE_URL = os.getenv("DIRECTUS_D1_URL", "http://localhost:18055").rstrip("/")
ADMIN_EMAIL = os.getenv("DIRECTUS_D1_ADMIN_EMAIL", "d1-admin@example.com")
ADMIN_PASSWORD = os.getenv(
    "DIRECTUS_D1_ADMIN_PASSWORD", "directus-d1-local-admin-password"
)

EXPECTED_FIELDS = {
    "id",
    "sort",
    "updated_at",
    "status",
    "slug",
    "title",
    "description",
    "category",
    "published_at",
    "reading_time",
    "sections",
    "seo_title",
    "seo_description",
    "featured_image_alt",
    "featured_image",
}


def require_success(response: httpx.Response, operation: str) -> None:
    if not response.is_success:
        raise AssertionError(f"{operation} failed with HTTP {response.status_code}")


async def verify() -> None:
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=20.0) as client:
        ping = await client.get("/server/ping")
        require_success(ping, "Directus ping")

        login = await client.post(
            "/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "mode": "json"},
        )
        require_success(login, "local admin login")
        token = login.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        collection = await client.get("/collections/academy_articles", headers=headers)
        require_success(collection, "academy_articles metadata")

        fields_response = await client.get("/fields/academy_articles", headers=headers)
        require_success(fields_response, "academy_articles fields")
        fields = {item["field"]: item for item in fields_response.json()["data"]}
        assert set(fields) == EXPECTED_FIELDS
        assert fields["slug"]["schema"]["is_unique"] is True
        assert fields["status"]["meta"]["required"] is True
        assert fields["published_at"]["schema"]["is_nullable"] is True

        relations_response = await client.get(
            "/relations/academy_articles", headers=headers
        )
        require_success(relations_response, "academy_articles relations")
        relations = relations_response.json()["data"]
        assert any(
            relation["field"] == "featured_image"
            and relation["related_collection"] == "directus_files"
            and relation["schema"]["on_delete"] == "SET NULL"
            for relation in relations
        )

        snapshot_response = await client.get("/schema/snapshot", headers=headers)
        require_success(snapshot_response, "reconstructed schema snapshot")
        reconstructed_snapshot = snapshot_response.json()["data"]
        governed_snapshot = json.loads(
            (REPOSITORY_ROOT / "directus" / "schema" / "schema.snapshot.json").read_text(
                encoding="utf-8"
            )
        )
        assert reconstructed_snapshot == governed_snapshot
        canonical_snapshot = json.dumps(
            reconstructed_snapshot,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        schema_fingerprint = hashlib.sha256(canonical_snapshot).hexdigest()

        suffix = uuid4().hex[:12]
        common = {
            "title": "D1 Synthetic Article",
            "description": "Synthetic local reconstruction verification content.",
            "category": "D1 Synthetic",
            "reading_time": 1,
            "sections": [{"type": "paragraph", "content": "Synthetic local content."}],
            "seo_title": None,
            "seo_description": None,
            "featured_image": None,
            "featured_image_alt": None,
            "sort": None,
        }
        draft_slug = f"d1-synthetic-draft-{suffix}"
        published_slugs = [f"d2-synthetic-published-{index}-{suffix}" for index in range(3)]
        future_slug = f"d2-synthetic-future-{suffix}"

        draft = await client.post(
            "/items/academy_articles",
            headers=headers,
            json={
                **common,
                "slug": draft_slug,
                "status": "draft",
                "published_at": None,
            },
        )
        require_success(draft, "synthetic draft creation")

        governed_at = datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)
        published_times = [
            "2026-01-01T00:00:00Z",
            "2026-06-01T00:00:00Z",
            "2026-09-29T12:00:00Z",
        ]
        for slug, published_at in zip(published_slugs, published_times, strict=True):
            published = await client.post(
                "/items/academy_articles",
                headers=headers,
                json={
                    **common,
                    "slug": slug,
                    "status": "published",
                    "published_at": published_at,
                },
            )
            require_success(published, "synthetic published creation")

        future = await client.post(
            "/items/academy_articles",
            headers=headers,
            json={
                **common,
                "slug": future_slug,
                "status": "published",
                "published_at": "2026-09-29T12:00:01Z",
            },
        )
        require_success(future, "synthetic future-published creation")

    academy_client = DirectusAcademyClient(
        DirectusConfig(url=BASE_URL.replace("http://", "https://"), service_token=token),
        transport=httpx.AsyncHTTPTransport(),
        page_size=2,
    )
    # DirectusConfig deliberately requires HTTPS in application runtime. Mutate
    # only this frozen local test instance after validation so the disposable
    # HTTP stack can exercise the real client without weakening production code.
    object.__setattr__(academy_client._config, "url", BASE_URL)
    articles = await academy_client.get_published_articles(governed_at)
    slugs = [article.slug for article in articles]
    assert slugs == list(reversed(published_slugs))
    assert draft_slug not in slugs
    assert future_slug not in slugs
    assert len(slugs) == len(set(slugs))
    boundary = await academy_client.get_published_article_by_slug(
        published_slugs[-1], governed_at
    )
    assert boundary is not None
    assert await academy_client.get_published_article_by_slug(future_slug, governed_at) is None

    print(f"DIRECTUS_D1_SCHEMA_FINGERPRINT={schema_fingerprint}")
    print("DIRECTUS_D2_MULTI_PAGE_ELIGIBILITY_PASS")
    print("DIRECTUS_D1_RECONSTRUCTION_ACCEPTANCE_PASS")


if __name__ == "__main__":
    asyncio.run(verify())
