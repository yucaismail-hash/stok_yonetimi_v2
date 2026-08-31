# FU2 V3 effective-history PostgreSQL verification

`20260806_01` is a **no-DDL legacy schema baseline marker**.  It can only be
used after a database already contains the supported legacy schema; it cannot
bootstrap an empty PostgreSQL database.

## Supported local/test path

1. Provision a disposable PostgreSQL database from a sanitized restore of the
   supported legacy production-equivalent schema.  Do not use a cloud or
   production `DATABASE_URL`.
2. Set `DATABASE_ENVIRONMENT=test` and the disposable database URL.
3. Stamp the restored legacy database at `20260806_01` only if it is not
   already stamped, then upgrade through the repository head (currently
   `20260814_02`, including V3 product inputs).
4. Run `scripts/verify_fu2_v3a_postgres.py`.  Its persisted fixture verifies
   atomic acceptance, rollback safety, DatasetVersion preservation, Actual
   Ledger integration, runtime reconstruction, sales/consumption, service
   level, tenant isolation, idempotency/corrections, and the no-heavy-analytics
   workflow input boundary.
5. Run the focused current-incoming-supply unit suite before any optional
   workflow integration test.  It does not require a database.

## Why empty bootstrap is blocked

The repository does not contain a DDL migration for the pre-existing legacy
schema.  `Base.metadata.create_all()` is not an approved substitute and also
encounters an unrelated legacy FK type mismatch (`sector_intelligence.sector_id`
versus the UUID `sectors` key).  Do not add a migration or alter production
models to work around this verification prerequisite.

The missing prerequisite is a supported sanitized legacy-schema restore (or a
separately approved reproducible legacy baseline asset).  Until it exists,
the V3 persisted effective-history integration fixture remains unexecuted.
