# Directus D1 CURRENT schema snapshot

Bu klasör Stokonomi Production Directus instance'ının secret-free, repository-owned
CURRENT metadata baseline'ıdır. D1 içerik modelini değiştirmez.

## Provenance

- Source service: `stokonomi-directus`
- Directus: `12.2.0`
- Database vendor reported by Directus: PostgreSQL
- Capture path: authenticated HTTP `GET /schema/snapshot`
- Additional safe metadata: GET-only roles, policies, permissions, flows and
  effective-permission inspection
- Direct production PostgreSQL connection: **not used**
- Content item export: **not performed**
- R2 access: **not performed**

Exact capture time and SHA-256 fingerprints are recorded in
`snapshot_manifest.json`. Reconstruction authority uses a semantic fingerprint:
parsed JSON is serialized with sorted keys, compact separators and UTF-8 before
SHA-256 hashing. This makes LF, CRLF and insignificant JSON whitespace
equivalent without hiding actual schema changes. The original capture-byte
hashes remain recorded as provenance only.

## Files

- `schema.snapshot.json`: Directus-supported schema snapshot. It contains the
  CURRENT `academy_articles` collection, 15 custom fields, system-field index
  metadata and the `featured_image -> directus_files` relation.
- `permissions.snapshot.json`: sanitized roles, policies, permission rules,
  flow result and effective Academy access observed during capture.
- `snapshot_manifest.json`: provenance, counts, hashes and production-operation
  declaration.
- `reconstruction_evidence.json`: two independent clean apply/acceptance runs,
  image identity and converged semantic fingerprint.

## Explicit exclusions

The following are intentionally absent:

- article and other content records;
- users and personal profile data;
- static/temporary tokens and sessions;
- passwords, hashes and TFA secrets;
- authentication-provider data;
- database and object-storage credentials;
- personal preset ownership.

`GET /presets` returned HTTP 403 and unauthenticated `GET /permissions/me`
returned HTTP 403. Those surfaces are recorded as unavailable, not inferred.
The production backend `DIRECTUS_SERVICE_TOKEN` identity and least-privilege
assignment remain UNKNOWN because its value was not available to this D1 capture.

## Apply contract

Only apply this snapshot to an empty disposable/local Directus 12.2.0 instance
with PostgreSQL:

```powershell
powershell -ExecutionPolicy Bypass -File directus/scripts/reconstruct.ps1
```

The wrapper invokes the supported schema command through the CLI bundled in
the pinned production image:

```text
node /directus/cli.js schema apply --yes /directus/schema/schema.snapshot.json
```

After apply, the wrapper restarts the disposable Directus process and waits for
readiness so schema and permission caches are reloaded before acceptance checks.

Never run schema apply against Production from this repository workflow.

## Permission reconstruction boundary

Production currently has the built-in Administrator role/policy and public
policy. No explicit `academy_articles` permission rule was returned. The D1
inspection credential received full Academy access through the Administrator
policy's `admin_access=true`; unauthenticated public access was unavailable.

Directus schema apply does not restore policy/user/token assignment. The local
acceptance test therefore verifies the current server-to-server behavior using
the disposable bootstrap administrator. The repository-owned least-privilege
TARGET is defined separately in `directus/access/`; its Production identity
assignment remains a D5 security acceptance item.
