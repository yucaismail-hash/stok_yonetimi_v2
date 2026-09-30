import hashlib
import json
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPOSITORY_ROOT / "directus" / "schema"
ACCESS_DIR = REPOSITORY_ROOT / "directus" / "access"


def _load(name: str):
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def _sha256(name: str) -> str:
    return hashlib.sha256((SCHEMA_DIR / name).read_bytes()).hexdigest()


def test_manifest_fingerprints_match_snapshot_files():
    manifest = _load("snapshot_manifest.json")
    assert manifest["source"] == {
        "service": "stokonomi-directus",
        "environment": "production",
        "directus": "12.2.0",
        "database_vendor": "postgres",
        "access": "HTTP GET metadata only",
        "content_records_exported": False,
    }
    assert manifest["artifacts"]["schema"]["sha256"] == _sha256(
        "schema.snapshot.json"
    )
    assert manifest["artifacts"]["permissions"]["sha256"] == _sha256(
        "permissions.snapshot.json"
    )
    assert manifest["production_requests"]["methods"] == ["GET"]
    assert manifest["production_requests"]["write_methods"] == []
    assert manifest["production_requests"]["direct_database_connection"] is False
    assert manifest["production_requests"]["r2_access"] is False


def test_current_academy_schema_contract_is_exact():
    snapshot = _load("schema.snapshot.json")
    assert snapshot["version"] == 1
    assert snapshot["directus"] == "12.2.0"
    assert snapshot["vendor"] == "postgres"
    assert [item["collection"] for item in snapshot["collections"]] == [
        "academy_articles"
    ]

    fields = {
        item["field"]: item
        for item in snapshot["fields"]
        if item["collection"] == "academy_articles"
    }
    assert set(fields) == {
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
    assert fields["id"]["schema"]["is_primary_key"] is True
    assert fields["id"]["schema"]["is_nullable"] is False
    assert fields["slug"]["schema"]["is_unique"] is True
    assert fields["slug"]["meta"]["required"] is True
    assert fields["status"]["meta"]["required"] is True
    assert fields["published_at"]["schema"]["is_nullable"] is True
    assert fields["featured_image"]["meta"]["special"] == ["file"]

    status_choices = {
        choice["value"]
        for choice in fields["status"]["meta"]["options"]["choices"]
    }
    assert status_choices == {"draft", "published", "archived"}


def test_current_featured_image_relation_is_exact():
    snapshot = _load("schema.snapshot.json")
    assert len(snapshot["relations"]) == 1
    relation = snapshot["relations"][0]
    assert relation["collection"] == "academy_articles"
    assert relation["field"] == "featured_image"
    assert relation["related_collection"] == "directus_files"
    assert relation["schema"]["foreign_key_column"] == "id"
    assert relation["schema"]["on_update"] == "NO ACTION"
    assert relation["schema"]["on_delete"] == "SET NULL"


def test_permission_snapshot_is_sanitized_and_records_partial_boundary():
    snapshot = _load("permissions.snapshot.json")
    assert snapshot["directus"] == "12.2.0"
    assert len(snapshot["roles"]) == 1
    assert len(snapshot["policies"]) == 2
    assert len(snapshot["permissions"]) == 20
    assert snapshot["flows"] == []
    assert snapshot["presets"]["status"] == "unavailable"
    assert snapshot["unknown"] == [
        "DIRECTUS_SERVICE_TOKEN user identity, role/policy assignment, and least-privilege scope"
    ]

    serialized = json.dumps(snapshot)
    for forbidden_key in (
        '"email":',
        '"token":',
        '"password":',
        '"tfa_secret":',
        '"auth_data":',
        '"session":',
    ):
        assert forbidden_key not in serialized


def test_two_clean_reconstruction_runs_converged():
    evidence = _load("reconstruction_evidence.json")
    assert evidence["image"]["cli_version"] == "12.2.0"
    assert evidence["image"]["tags_resolve_to_same_identity"] is True
    assert len(evidence["runs"]) == 2
    fingerprints = {run["schema_fingerprint"] for run in evidence["runs"]}
    assert len(fingerprints) == 1
    for run in evidence["runs"]:
        assert run["clean_database"] is True
        assert run["official_schema_apply"] == "PASS"
        assert run["snapshot_exact_equality"] == "PASS"
        assert run["synthetic_acceptance"] == "PASS"
        assert run["backend_client"] == "PASS"
        assert run["cleanup"] == "PASS"
    assert evidence["converged"] is True
    assert evidence["production_access"] is False
    assert evidence["production_mutations"] == 0


def test_target_academy_service_policy_is_published_only_and_non_admin():
    target = json.loads(
        (ACCESS_DIR / "academy-service-policy.target.json").read_text(
            encoding="utf-8"
        )
    )
    assert target["status"] == "TARGET_NOT_APPLIED"
    assert target["policy"]["admin_access"] is False
    assert target["policy"]["app_access"] is False
    assert len(target["permissions"]) == 1
    permission = target["permissions"][0]
    assert permission["collection"] == "academy_articles"
    assert permission["action"] == "read"
    assert permission["permissions"] == {
        "_and": [
            {"status": {"_eq": "published"}},
            {"published_at": {"_nnull": True}},
            {"published_at": {"_lte": "$NOW"}},
        ]
    }
    assert set(permission["fields"]) == {
        "id",
        "status",
        "sort",
        "slug",
        "title",
        "description",
        "category",
        "published_at",
        "updated_at",
        "reading_time",
        "sections",
        "seo_title",
        "seo_description",
        "featured_image",
        "featured_image_alt",
    }
    assert target["media_boundary"][
        "directus_files_metadata_read_required_by_current_backend"
    ] is False
    assert target["production_assignment"]["status"] == "UNKNOWN"
