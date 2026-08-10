# Architecture Changelog

## 2026-08-10 - Phase 3C2B3 immutable XGBoost Challenger model artifacts

- Added company-scoped immutable `ModelArtifact` metadata and native XGBoost UBJ artifact storage with SHA-256 checksum verification before trusted model loading.
- Artifact persistence is explicit after successful Challenger training. A deterministic fingerprint provides idempotent re-persistence and preserves append-only history when cutoff evidence or configuration changes.
- Production Forecast, automatic retraining, Champion-Challenger governance, promotion, Decision Intelligence, and Learning Score mutation remain inactive. Full persisted Tier-3 triggering remains pending Phase 3C1 verification.

## 2026-08-10 - Phase 3C2B2 XGBoost Challenger training

- Added an explicit, bounded, in-memory XGBoost Challenger Training service over the verified `xgboost_weekly_v1` feature matrix. It uses deterministic categorical codes, a `time_ordered_holdout_v1` split, fixed seed/parameters, and reports validation prediction evidence with WAPE, Bias, MAE, and RMSE.
- Challenger fitting is isolated from DemandForecaster and Forecast Vintage production paths. Automatic retraining, artifact persistence, Champion-Challenger governance, promotion, Decision Intelligence, and Learning Score mutation remain inactive.
- Explicit Tier-3 authorization is accepted; non-Tier-3 authorization is rejected. Full persisted Tier-3 triggering remains pending Phase 3C1 verification.

## 2026-08-10 - Phase 3C2B1 XGBoost weekly feature builder verification

- The cutoff-safe XGBoost weekly feature builder is **DEVELOPMENT VERIFIED** with feature schema `xgboost_weekly_v1`, sourced only from canonical accepted Actual Weekly Observations.
- PostgreSQL evidence verifies cutoff leakage protection, deterministic reconstruction, product-level metadata for `finished_good`, `semi_finished_good`, and `raw_material`, demand-type isolation, and true ISO chronology across 2020-W53 to 2021-W01.
- XGBoost training, challenger fitting, model artifacts, promotion, and Learning integration remain **NOT YET ACTIVE**.

## 2026-08-10 - Phase 3B1 Optional Supplier Business Branch

- Added optional Supplier task generation for Business Workflows only when the encrypted dataset contains valid supplier identities, delivery evidence, and mappings to actual dataset materials. Missing evidence preserves the four-task workflow; partial or invalid evidence is recorded as controlled degradation metadata without fabricated analysis.
- Supplier-present workflows execute the existing DatasetRuntimeProvider, SupplierAdapter, SupplierPerformanceAnalyzer, and durable RuntimeResultReference path as a fifth required task. Progress is 20% per generated task, aggregate results include Supplier only when present, and product level is not restricted to raw materials.
- Supplier evidence remains an independent enrichment branch: it does not yet alter Safety Stock or Simulation mathematics. Learning, retraining, Champion-Challenger, and Event Intelligence are not invoked.

## 2026-08-10 - Phase 3AA6 Forecast Performance History and Learning Evidence

- Added a derived, read-only weekly Forecast Performance History and versioned internal evidence contract sourced exclusively from durable Forecast Evaluation points; no migration was required.
- History provides company, product-level, group, class, SKU, and demand-type-isolated evidence with explicit sample count, period coverage, metric contract provenance, source evaluation identities, WAPE/Bias/MAE/RMSE/sMAPE, and conditional Forecast Accuracy.
- Learning score values are carried as historical snapshots only. Current evaluation changes from approved actual corrections or new actual arrivals propagate on the next read. Retraining, XGBoost, model promotion, Champion-Challenger, Decision Intelligence, and Event Learning remain inactive.

## 2026-08-10 - Phase 3AA5 Forecast-to-Actual evaluation

- Added durable normalized Forecast Evaluation headers and current point evidence, pairing canonical accepted actuals only with Phase 3AA4 effective forecasts. Forecast selection remains the Effective Forecast Timeline authority and hindsight remains prohibited.
- Point evidence stores immutable forecast provenance, actual observation and accepted revision provenance, forecast-time product snapshots, nullable learning score, and raw signed/absolute/squared errors. Approved actual corrections recompute current evaluation evidence; rejected corrections do not.
- Versioned metrics implement WAPE as primary, `actual - forecast` bias, MAE, RMSE, sMAPE, and the conditional presentation metric `max(0, 1 - WAPE)`. WAPE is explicitly unavailable for a zero actual denominator; MAPE is not primary. Event evaluation and Learning integration remain pending.

## 2026-08-10 - Phase 3AA4 Effective Forecast Timeline

- Added the derived, read-only Effective Forecast Timeline service over immutable Forecast Vintage headers and points; no persistence table or migration was needed.
- For each company, SKU, target period, and demand type, it selects the latest Vintage whose durable `forecast_available_at` is strictly before the ISO target-week start. Hindsight use is prohibited, and malformed cutoff/target overlap is rejected without mutating source evidence.
- The projection preserves snapshot product dimensions, model and interval evidence, durable result-reference provenance, and nullable learning-score-at-run fields. Actual data is not required; Forecast Evaluation remains **PENDING 3AA5**.

## 2026-08-10 — Phase 3AA3 Forecast Vintage and target-period persistence

- Added immutable Forecast Vintage headers and normalized SKU target-period points projected from validated durable Forecast RuntimeResultReferences.
- Target periods are canonical ISO weeks generated from immutable input cutoff provenance; availability is the persisted Forecast result timestamp. Multiple vintages and overlapping target periods coexist.
- Learning score snapshot fields are schema-ready but not activated. Effective timeline is **PENDING 3AA4**; Forecast Evaluation is **PENDING 3AA5**.

## 2026-08-10 — Phase 3AA2 canonical actual weekly observation and revision ledger

- Added canonical normalized weekly actual truth keyed by company, material code, ISO period, and demand type, alongside an append-only proposed/accepted/rejected revision ledger.
- Dataset encrypted blobs remain source-upload evidence. Identical reuploads are idempotent; new weeks are accepted without correction approval; changed historical values require explicit approval before current truth changes.
- Product level (`finished_good`, `semi_finished_good`, `raw_material`), product group/class, demand type, dataset provenance, tenant scope, and fresh-session reconstruction are verified. Forecast Vintage remains **PENDING 3AA3**; Evaluation remains **PENDING**.

## 2026-08-10 — Phase 3A5 Business Workflow result aggregation

- Completed Business Workflows can now compose one durable execution-scoped `business_workflow` envelope exclusively from validated PostgreSQL RuntimeResultReferences.
- The aggregate preserves all four task results and their result-reference identities, is idempotent through existing execution-scope uniqueness, and is retrievable through the application aggregation boundary after fresh-process reconstruction.
- Aggregation is prohibited for partial and failed workflows. No analytical engine, Learning, or Decision Intelligence is invoked.

## 2026-08-10 — Phase 3A4 Business Workflow failure propagation

- Required Business Workflow task failures now persist a failed RuntimeTaskAttempt and terminal failed RuntimeExecution without creating a validated result for the failing task.
- PostgreSQL probes verified Forecast, Safety Stock, Simulation, and Backtest failure outcomes; successful upstream evidence is preserved, downstream tasks remain pending with terminal scheduler blocking evidence, and failed re-entry creates no attempts or results.
- Automatic retry is **NOT IMPLEMENTED**. Expired-lease retry policy remains an **OPEN GAP**. Workflow aggregation remains **PENDING 3A5**.

## 2026-08-10 — Phase 3A3 cross-process Business Workflow recovery

- Business Workflow cross-process recovery is **DEVELOPMENT VERIFIED** using PostgreSQL as the sole authoritative source after Forecast, Safety Stock, Simulation, and completed-workflow object-graph loss.
- Fresh recovery preserves progress, completed tasks, validated result references, Simulation Forecast/Safety Stock provenance, and Backtest `VALIDATE_SELECTED` Safety Stock provenance. Completed re-entry creates neither a new attempt nor a duplicate result reference.
- Expired-lease recovery is a **DOCUMENTED GAP** for Business Workflow tasks: their current `max_attempts=1` contract prevents an expired claim from being reclaimed without a future retry-policy decision.
- Failure propagation remains **PENDING 3A4**; workflow aggregation remains **PENDING 3A5**.

## 2026-08-07 â€” Phase 2F first real Simulation execution

- Standalone Simulation durable execution is **DEVELOPMENT VERIFIED** with one Simulation task and real Monte Carlo output.
- No hidden Forecast or Safety Stock task is created. Business upstream input reuse is verified; recomputation is prohibited.
- Fresh-process result retrieval is verified; Learning and Decision Intelligence are not invoked.

## 2026-08-07 â€” Phase 2E capability dataflow contract

- Validated same-tenant, version-compatible RuntimeResultReference transfer and provenance are binding.
- Business Simulation input consumes Forecast and Safety Stock upstream evidence without recalculation; Standalone fallback is explicit.
- Backtest rolling recalculation remains required, with Business `VALIDATE_SELECTED` no-reselection and Standalone comparison compatibility.

## 2026-08-07 â€” Phase 2E first real Safety Stock execution

- Standalone Safety Stock durable execution is **DEVELOPMENT VERIFIED** with exactly one Safety Stock runtime task.
- `ComprehensiveSafetyStockOptimizer` is connected through `CapabilityExecutor`; its classic, Croston, Syntetos-Boylan, bootstrapping, ML-based, and hybrid candidates are preserved.
- Existing endpoint selection of `hybrid_ss` is preserved; a dynamic automatic candidate-winner selector remains a gap. Service level supports system default (`0.95`) with validated manual override.
- Supplier input is optional enrichment and supplier-free execution is verified. Fresh-process durable status/result retrieval is verified.
- Learning and Decision Intelligence are not invoked.

## 2026-08-07 — Phase 2C durable runtime verification

- Phase 2C Durable Runtime: **COMPLETE**.
- PostgreSQL RuntimeStore, fresh-session recovery, claim/lease/attempt, completion/failure, checkpoint/progress, optimistic concurrency, cancellation/terminal protection, tenant isolation, and runtime result scope: **VERIFIED**.
- Development synthetic-probe cleanup: **VERIFIED — ZERO RESIDUE**.
- Distributed queue/worker remains **NOT YET IMPLEMENTED**; real capability execution is **NEXT**.

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

## 2026-08-07 — Phase 2C-M1: Durable Runtime Governance

- ADR-029 through ADR-032 were accepted.
- The canonical additive runtime entity model, RuntimeStore ownership, worker claim/lease/idempotency model, and result-reference policy were approved.
- No ORM model, migration, database table, runtime behavior, or route was created or changed.

## 2026-08-07 — Phase 2C-M2I: Runtime ORM and additive migration

- Added the five canonical runtime ORM models and manually authored revision `20260807_01_runtime_store_core`.
- The migration is structurally verified only; no development Neon migration was applied.
- Runtime consumers, repositories, routes, workers, queues, and downstream products remain unchanged.

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
