# Directus access contracts

This directory separates repository-owned TARGET access contracts from the
sanitized CURRENT production metadata in `directus/schema/`.

## Academy backend reader target

`academy-service-policy.target.json` defines the minimum policy required by the
CURRENT backend Directus client:

- no administrator access;
- no Data Studio access;
- read-only access to `academy_articles`;
- a server-enforced `status = published AND published_at IS NOT NULL AND
  published_at <= $NOW` filter;
- only the exact fields requested by the list/detail client;
- no create, update, delete, share, schema or system-collection access.

The current backend reads `featured_image` only as its UUID foreign-key value.
It does not expand `directus_files`, query file metadata, or request Directus
assets. Consequently a `directus_files` permission would be broader than the
minimum CURRENT runtime contract and is intentionally absent. A future asset
resolver must define its own safely scoped file policy rather than silently
granting read access to every stored file.

This TARGET policy has not been applied to Production. The actual
`DIRECTUS_SERVICE_TOKEN` identity and policy assignment remain UNKNOWN and are
a D5 production-security acceptance item.

The application does not rely on this TARGET policy alone. D2 sends the same
predicate with one timezone-aware governed instant in every list/detail query
and validates every returned DTO against that instant. This keeps list, detail
and sitemap semantics aligned even before D5 applies and verifies the policy.

Presets are not referenced by the backend client, Academy service, public API,
or sitemap implementation. They are editorial/dashboard state and are outside
the runtime-critical D1 reconstruction contract.
