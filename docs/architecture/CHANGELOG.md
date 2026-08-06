# Architecture Changelog

## 2026-08-06 — Phase 2C-M0B: Development Neon baseline stamped

- The explicitly classified development Neon PostgreSQL database was stamped at baseline revision `20260806_01`.
- The baseline revision contains no DDL or DML; no migration upgrade, downgrade, runtime-table creation, or legacy schema script was run.
- Post-stamp readiness is current and managed PostgreSQL startup remains non-mutating.
- `ALLOW_UNVERSIONED_MANAGED_SCHEMA` was not enabled for the stamp.

## 2026-08-06 — Phase 2C-M0: Alembic bootstrap and startup schema control

- Alembic tooling and a no-DDL legacy-schema baseline revision were implemented; the baseline is not stamped.
- Managed PostgreSQL startup schema mutation is disabled and read-only schema readiness is implemented.
- Explicit local/test disposable bootstrap and unversioned managed-schema transition controls were added.
- No migration, stamp, live-database mutation, runtime table, route, worker, queue, or capability activation occurred.

## 2026-08-06 — Phase 2B-R1: Capability Design Principles

- Appended the binding Capability Design Principles revision to DOCUMENT_05.
- No ADR was created or changed; no runtime behavior changed.
- The revision is the design reference for Forecast, Safety Stock, Simulation, Backtest, Supplier, Learning, Decision Intelligence, and LLM-based explanation development.

## 2026-08-06 — Phase 2C: ADR-033 migration authority governance

- Accepted ADR-033: Alembic is the sole authority for managed PostgreSQL schema changes.
- Recorded explicit environment classification, migration-history ownership, managed-startup non-mutation, and legacy schema-script transition policy.
- No migration tooling, runtime code, startup behavior, database schema, data, or deployment command changed.

## 2026-08-06 — Phase 2B Gate 1: Capability runtime and error governance

- Accepted ADR-021 through ADR-028.
- Recorded the capability-execution boundary, durable-store authority, worker strategy, explicit data-passing contract, future SKU merge model, downstream handoff, two-tier runtime failure policy, and application-owned user-notice language.
- No runtime code, queue, worker, durable store, route, or downstream pipeline was activated in this governance gate.

## 2026-08-06 — Phase 2B Gates 2–3: Capability contracts and controlled executor

- Added frozen capability request, error, and result contracts; they are implemented but not yet consumed.
- Added the pure application-owned user execution-notice contract and technical-code mapper; API wiring is pending.
- Added a dependency-injected CapabilityExecutor verified only with controlled doubles; production wiring is pending.
- No capability, route, queue, worker, durable store, repository, migration, Learning, Decision Intelligence, Dynamic Plan, or Artifact behavior was activated.

## 2026-08-06 — Phase 1P: Execution contracts Batch 1

- Implemented `WorkflowDispatchRequest`, `WorkflowDispatchResult`, `ExecutionStatusSnapshot`, and `ExecutionResultEnvelope` in `app/engine/contracts.py`.
- Contracts are frozen, versioned, independently validated, and not yet consumed by dispatcher, engine, orchestrator, routes, schemas, persistence, or application services.
- No runtime-context alignment, adapter, consumer migration, or workflow-execution implementation was performed.

## 2026-08-06 — Phase 1O: ADR-019 governance approval

- Accepted ADR-019: Execution Contract Field, Stage, Identity and Time Standard.
- Approved separate runtime-state and processing-stage concepts, dispatcher execution-ID ownership, timezone-aware UTC timestamps, and versioned frozen execution contracts.
- Contract implementation is not recorded as complete until its isolated Batch 1 validation succeeds.

## 2026-08-06 — Phase 1K: Runtime contract governance approval

- Accepted ADR-012: ExecutionContext and Execution-State Authority.
- Approved engine ExecutionContext as runtime authority and engine ExecutionState as runtime-state authority.
- Accepted ADR-018: Workflow and Runtime Dispatch Contract.
- Approved WorkflowEngine asynchronous dispatch role and ExecutionOrchestrator runtime ownership.
- Approved runtime-store plus repository-persistence ownership.
- No runtime dispatch, context adapter, status/result, or persistence implementation was performed.

## 2026-08-06 — Phase 1E: ADR-011 governance approval

- Accepted ADR-011: Official ExecutionService Public Facade and Layer Ownership.
- Approved `app/services/execution/execution_service.py` as the official public ExecutionService facade path.
- Formally separated delegated application use-case responsibility from engine runtime lifecycle responsibility.
- No facade runtime implementation was performed.

## 2026-08-05 — Phase 1C: Architecture Governance Baseline

- Recorded Documents 01–07 as the current architecture authority.
- Recorded canonical and transition component registries.
- Recorded accepted and unresolved ADR items.
- Recorded Phase 1A Architecture Inventory completion.
- Recorded Phase 1B Canonical Alignment Roadmap completion.

## 2026-08-05 — Phase 0: Stabilization complete

- Completed confirmed import and loadability repairs.
- Corrected invalid standard-library UUID and typing import issues identified during stabilization.
- Corrected confirmed dataclass inherited/default field-order loadability issues.
- Corrected confirmed SQLAlchemy model symbol/import issues.
- Corrected confirmed public package export and circular-import boundaries.
- Corrected ResponseBuilder, authentication request-schema, and artifact repository import blockers.
- Declared `uuid7==0.1.0` and restored UUIDv7 generation through `uuid_extensions.uuid7`.
- Completed AST, compile, model, package, and fresh-process import validation during Phase 0 closure.

## Architecture specification milestone

- Documents 01–07 are recorded as completed architecture specifications and the active authority baseline.
- No architecture-document revision, endpoint migration, schema migration, database data migration, legacy removal, or business-feature development is recorded as completed by Phase 0 or Phase 1C.

## 2026-08-06 — Revision — Product Architecture Phase 1

- Formalized the approved Product Architecture concepts: Standalone Analysis, Business Workflow, Forecast Business Workflow, Safety Stock Business Workflow, Dynamic Operational Plan, External Intelligence, AI Parameter Optimizer, and AI Artifact.
- This is a documentation-only governance update.
- No runtime behavior changed.
- No routes changed.
- No schemas changed.
- No repositories changed.
- No execution engine changed.
- No business logic changed.

## 2026-08-06 — Phase 1AG: ADR-020 accepted

- Accepted ADR-020: Product Levels, Workflow Intent Types and Dynamic Operational Plan Outputs.
- Formalized Level 1 Standalone Analysis and Level 2 Business Workflow.
- Approved Forecast and Safety Stock Business Workflow sequences, including mandatory Simulation and Backtest positions.
- Separated Single Analysis and Business Workflow execution-intent domains through `objective_type XOR analysis_type`.
- No runtime implementation was performed during Gate 1.

## 2026-08-06 — Phase 1AH: Documents 01–07 Product Architecture revisions

- Documents 01–07 Product Architecture Phase 1 revisions: **COMPLETED — BINDING**.
- Appended bounded ADR-020-referenced product architecture revisions to each authoritative specification document.
- Runtime/code alignment remains pending.
- No runtime, route, schema, model, repository, migration, test, requirements, or business code changed.
