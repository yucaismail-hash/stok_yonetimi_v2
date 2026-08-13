# Architecture Changelog

## 2026-08-12 - Phase 3C4 Selective Retraining orchestration closeout

- PostgreSQL closeout verified the complete explicit periodic-equivalent chain: durable scheduler tick, scanner activation, correction-safe job acceptance, cooldown/priority/resource admission, leased worker, Challenger training, and immutable ModelArtifact. At-least-once tick delivery converges to one effective job/runtime/task/fit/artifact.
- Accepted Actual corrections create new candidate evidence; rejected corrections no longer manufacture candidates merely because Forecast Evaluation recalculation time changed. Candidate evidence fingerprints now exclude that volatile operational timestamp while retaining evaluation identity, metrics, points, and accepted revision provenance.
- Scheduler logic is durable and callable but no deployment timer, cron, Render job, startup hook, or always-running loop is configured in this repository. Business Workflow remains unblocked; automatic comparison, promotion, rollback, Forecast switching, Learning mutation, and Decision Intelligence remain inactive.

## 2026-08-12 - Phase 3C4B5C1 periodic scanner tick safety

- Added a durable company-scoped scheduler tick ownership boundary. A cryptographic tick identity binds company, bounded scan window, scheduler policy, cadence bucket, and optional scanner scope; PostgreSQL uniqueness prevents duplicate effective delivery across processes.
- Tick records retain owner/lease, completion summary, and controlled failure evidence. Duplicate delivery resolves completed/running state, failed buckets do not immediately retry, and a later cadence bucket remains independently executable after restart without replaying unbounded history.
- The service is callable only: no timer, cron, startup hook, or background loop was installed. It delegates activation to B5B and does not fit models, run governance, switch Forecasts, or mutate Learning.

## 2026-08-12 - Phase 3C4B5B controlled scanner activation

- Added an explicit `scan_and_activate` bridge separate from pure scanner discovery. It invokes discovery, reuses B4 deterministic ranking, and delegates only admitted candidates to the existing B2 explicit start boundary.
- Cooldown and capacity-blocked jobs remain durable but create no RuntimeExecution, RuntimeTask, fit, or artifact. The B2 admission lease is durable and becomes worker-owned for heartbeat/recovery/release; the scanner process owns no process-local slot. Repeated/concurrent activation retains one job/runtime/task identity.
- No timer, cron, background loop, evaluation-completion trigger, automatic governance, production Forecast switching, or Learning mutation was added.

## 2026-08-12 - Phase 3C4B5A Retraining scanner discovery

- Added an explicit callable RetrainingScanner discovery boundary. It is company- and period-bounded, optionally material/demand scoped, and delegates Tier evaluation to RetrainingEligibilityService and Tier-3 duplicate-safe acceptance to RetrainingJobService.
- Tier 0--2 scopes create no jobs. Tier-3 first discovery creates one durable candidate and repeated/concurrent PostgreSQL scans resolve that same candidate through the existing B1 fingerprint guard. Accepted corrections preserve the B1 new-evidence behavior.
- Scanner reports existing B4 cooldown/priority evidence but never acquires a resource lease, starts RuntimeExecution/RuntimeTask, fits XGBoost, creates an artifact, or invokes governance. No timer, cron, startup hook, or automatic invocation was added.

## 2026-08-12 - Phase 3C4B4 Retraining cooldown, priority, and admission

- Added a durable, versioned retraining admission boundary between a Tier-3 pending job and explicit runtime creation. Cooldown is disabled by default until deployment configuration supplies a duration; configured cooldown preserves new candidate evidence as a durable deferred job rather than discarding it.
- Priority is deterministic and evidence-only, with stable score, candidate creation time, and job ID ordering. PostgreSQL advisory locking plus durable retraining resource leases enforce configurable global background capacity across processes; leases heartbeat, expire/reclaim, fence stale owners, and release after terminal work.
- Retraining admission is independent of the Business Workflow active-company guard and does not block Forecast, Safety Stock, or standalone production analysis. No scanner, automatic enqueue, comparison, promotion, rollback, Learning mutation, or Decision Intelligence activation was added.

## 2026-08-12 - Phase 3C4B3 Retraining artifact-race recovery

- Explicit retraining retains the existing bounded two-attempt lease policy and now recovers a worker crash after immutable artifact persistence: the artifact link is durably recorded before task/execution/job terminalization, and a lease-reclaimed worker verifies and reuses it without a second fit.
- Concurrent persistence of the same deterministic Challenger artifact is idempotent under PostgreSQL uniqueness. The losing writer removes only its controlled storage file and resolves the authoritative artifact; stale lease completion remains rejected and cannot overwrite the reclaimer.
- Retryable pre-artifact failures retry within the existing bound; deterministic/invalid-artifact failures terminalize, and terminal re-entry is idempotent. No scanner, automatic enqueue, comparison, promotion, production Forecast change, Learning mutation, or Decision Intelligence activation was added.

## 2026-08-12 - Phase 3C4B2 explicit Retraining Job execution

- A Tier-3 `pending` RetrainingJob may now be started only by explicit company-scoped invocation. Start creates exactly one linked durable `retraining` RuntimeExecution and one leased `xgboost_challenger_training` task; concurrent starters resolve `STARTED` and `ALREADY_STARTED` through PostgreSQL locking.
- The dedicated worker reconstructs scope/evidence from durable job and runtime IDs, claims an exclusive lease, invokes explicit Challenger Training, and links a successful immutable ModelArtifact. `NOT_TRAINABLE` is terminal without an artifact; retryable failures use a bounded two-attempt policy and terminalize as `failed` when exhausted.
- No scanner, automatic enqueue, comparison, promotion, rollback, Forecast selection change, Learning mutation, or Decision Intelligence activation was added.

## 2026-08-11 - Phase 3C4B1 durable Retraining Job

- Added a durable company/material/demand scoped `RetrainingJob` candidate boundary. It persists Tier-3 eligibility evidence, training cutoff, product metadata, latest evaluation identity, and a correction-safe evaluation-evidence fingerprint; it does not create a runtime task or run training.
- PostgreSQL uniqueness on `(company_id, candidate_fingerprint)` provides cross-process create-or-existing behavior. Accepted corrections create new evidence/candidate fingerprints; repeated evidence resolves the existing job. Tier 0--2 evidence creates no job.
- Challenger training, ModelArtifact persistence, Champion--Challenger evaluation, promotion, rollback, production Forecast changes, Learning mutation, and Decision Intelligence remain inactive.

## 2026-08-11 - Phase 3C1 Retraining Eligibility verification

- Retraining Eligibility is PostgreSQL verified as a read-only, company/material/demand-type scoped evidence boundary. Stable matching watermark resolves Tier 0; stable new evidence resolves Tier 1; one-signal deterioration resolves Tier 2; sufficient multi-signal evidence resolves Tier 3 as retrain-eligible only.
- Canonical accepted Actual corrections refresh Forecast Evaluation evidence and eligibility; rejected corrections do not. Bounded historical windows remain isolated from later persisted evidence, and fresh-session reconstruction, deterministic rereads, exact cleanup, and zero persistence mutation are verified.
- Tier 3 reaches only the explicit Challenger Training bridge. Tier 0--2 training remains blocked with zero fit; automatic retraining, Challenger training/evaluation, promotion, Learning mutation, and Decision Intelligence remain inactive.

## 2026-08-11 - Phase 3C3B3B2 Controlled Champion Rollback

- Controlled Champion Rollback is development verified as an explicit PostgreSQL-governed pointer operation. It locks the scoped current pointer, enforces stale/idempotent/concurrent safety, validates trusted destination artifacts, appends immutable `ROLLBACK` history, and affects future Forecast resolution only.
- Production Forecast and completed Business Workflow evidence after rollback use the new Champion while historical RuntimeResultReference and Forecast Vintage evidence remains immutable. Runtime resolver fallback is separate: it does not mutate the registry; only explicit rollback changes the pointer. Automatic rollback, retraining, and promotion remain inactive; PHASE 3C1 PostgreSQL verification is complete.

## 2026-08-11 - Phase 3C3B3B1 production Champion Forecast scope

- Production XGBoost Champion Forecast and Business Workflow XGBoost Forecast are development verified. The durable Forecast task resolves the current scoped Champion and preserves demand type, current-canonical cutoff, Champion entry, and immutable artifact provenance through RuntimeResultReference and Forecast Vintage.
- Downstream Safety Stock, Simulation, and Backtest do not resolve or invoke XGBoost. `finished_good`, `semi_finished_good`, and `raw_material` Forecast scopes are verified with explicit, product-level-independent demand types. Production Forecast performs zero XGBoost fits; automatic retraining, Challenger training/evaluation, promotion, Learning mutation, and Decision Intelligence remain inactive. Controlled rollback is pending the next phase; PHASE 3C1 PostgreSQL verification is complete.

## 2026-08-11 - Phase 3C3B3A Champion Resolver

- Champion Resolver is development verified as a read-only, company/material/demand-type scoped boundary. Classical and trusted XGBoost Champion resolution, integrity/missing/compatibility fallback, no-classical controlled failure, cutoff compatibility, tenant isolation, demand-type isolation, and fresh-session reconstruction are verified.
- Fallback never mutates the current registry pointer, entries, transitions, artifacts, or Forecast evidence. Production Forecast integration, rollback, and automatic retraining/promotion remain inactive; PHASE 3C1 PostgreSQL verification is complete.

## 2026-08-11 - Phase 3C3B2 controlled Challenger promotion

- Controlled Challenger promotion is development verified. Only an immutable `PROMOTE_CHALLENGER` decision with a trusted same-company artifact can atomically move the PostgreSQL current Champion pointer; entries and transitions remain immutable.
- Same-decision and competing-decision races, stale decisions, non-promotable decisions, artifact integrity, tenant isolation, and demand-type isolation are verified. Production Forecast activation, Forecast resolution, rollback, and automatic retraining/promotion remain inactive. PHASE 3C1 PostgreSQL verification is complete.

## 2026-08-11 - Phase 3C3B1A Champion Registry foundation

- Added immutable Champion identities and transition history, with a PostgreSQL-scoped mutable current pointer for `(company, material, demand type)`. First use bootstraps the existing classical `demand_forecaster_auto_v1` strategy without changing Forecast execution.
- Promotion, rollback, Forecast resolution, automatic retraining/promotion, Learning mutation, and XGBoost production activation remain inactive. PHASE 3C1 PostgreSQL verification is complete.

## 2026-08-11 - Phase 3C3A artifact-backed Champion--Challenger decisions

- Development PostgreSQL verification establishes immutable, tenant-scoped decision evidence over the same out-of-sample Champion/Challenger window. `champion_challenger_policy_v1` uses WAPE as the primary measure, guarded by Bias, MAE, RMSE, and sample strength.
- Trusted Challenger loading verifies artifact checksum and compatibility before a decision. Repeated identical evidence returns the existing immutable decision; changed evidence appends a new decision. Promotion execution, production Forecast selection, Learning Score mutation, and Decision Intelligence remain inactive; XGBoost fit during comparison is zero.
- Automatic Tier-3 retraining remains intentionally inactive; PHASE 3C1 verifies the explicit training boundary.

## 2026-08-10 - Phase 3C2B4-B atomic Business Workflow execution guard

- Added a PostgreSQL partial unique index enforcing one active `business_workflow` execution per company across `created`, `queued`, `running`, `waiting`, and `retrying` states. Duplicate durable acceptance resolves the existing execution as `ALREADY_RUNNING`.
- Same-user, cross-user, UI/ERP, true concurrent-session, dataset-version, terminal re-run, cross-company, standalone coexistence, and fresh-session cases are PostgreSQL verified. The durable acceptance path has no current PricingEngine charge coupling; future charges must apply to `CREATED` only.

## 2026-08-10 - Phase 3C2B4-A Business Workflow execution safety design

- Recorded the initial one-active-Business-Workflow-per-company policy. The planned authoritative implementation is a PostgreSQL partial unique active-workflow index plus controlled `ALREADY_RUNNING` resolution; verification remains pending Phase 3C2B4-B.
- Standalone analyses remain out of scope. The current V2 business-objective endpoint does not yet use the durable Business Workflow acceptance path, and its optional idempotency key is not yet persisted into runtime acceptance.

## 2026-08-10 - Phase 3C2B3 immutable XGBoost Challenger model artifacts

- Added company-scoped immutable `ModelArtifact` metadata and native XGBoost UBJ artifact storage with SHA-256 checksum verification before trusted model loading.
- Artifact persistence is explicit after successful Challenger training. A deterministic fingerprint provides idempotent re-persistence and preserves append-only history when cutoff evidence or configuration changes.
- Production Forecast, automatic retraining, Champion-Challenger governance, promotion, Decision Intelligence, and Learning Score mutation remain inactive. Persisted Tier-3 eligibility and the explicit training bridge are verified.

## 2026-08-10 - Phase 3C2B2 XGBoost Challenger training

- Added an explicit, bounded, in-memory XGBoost Challenger Training service over the verified `xgboost_weekly_v1` feature matrix. It uses deterministic categorical codes, a `time_ordered_holdout_v1` split, fixed seed/parameters, and reports validation prediction evidence with WAPE, Bias, MAE, and RMSE.
- Challenger fitting is isolated from DemandForecaster and Forecast Vintage production paths. Automatic retraining, artifact persistence, Champion-Challenger governance, promotion, Decision Intelligence, and Learning Score mutation remain inactive.
- Explicit Tier-3 authorization is accepted; non-Tier-3 authorization is rejected. Persisted Tier-3 eligibility is verified; automatic triggering remains inactive.

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
# 2026-08-12 - Phase 3C5B1 Immutable Learning Evidence

- Added the canonical `LearningEvidence` boundary. Source-specific builders persist immutable, company-scoped, SHA-256-idempotent contributions for accepted Actuals/corrections, Forecast Evaluation, Champion promotion/rollback, and terminal RetrainingJob evidence.
- Accepted corrections append superseding evidence; rejected corrections create none. Pattern Memory, Company Learning projections, Learning Score, Forecast integration, and Decision Intelligence remain inactive.
- **PHASE 3C5B1 COMPLETE:** the canonical terminal `RetrainingJob` source boundary is verified. The broad `verify_phase3c4b1_retraining_jobs.py` runtime timeout is separate test-infrastructure debt; no production RetrainingJob defect was demonstrated.

## 2026-08-12 - Phase 3C5B2A Pattern Intelligence Calculation

- Pattern Intelligence is PostgreSQL verified as a deterministic, read-only, cutoff-safe calculation over canonical accepted Actuals. Stable, structural-change/trend, volatile, intermittent, and lumpy classifications are verified; regular sparse demand is distinguished from lumpy demand by nonzero-demand size variability.
- Accepted corrections change the source fingerprint, rejected corrections and post-cutoff data do not. Demand types are isolated; product level remains metadata; missing periods are explicit. Pattern persistence, Forecast integration, and Decision Intelligence remain inactive.

## 2026-08-12 - Phase 3C5B2B1 Pattern Learning Memory

- Added a durable current Pattern Learning Memory projection keyed by company, material, and demand type. Same evidence is idempotent; accepted corrections refresh the one current row, rejected corrections do not, and an older cutoff cannot overwrite a newer projection.
- Pattern Memory is optional enrichment only. Forecast integration, Company Learning, Learning Score, and Decision Intelligence remain inactive.

## 2026-08-13 - Phase 3C5B2B2 Incremental Pattern Refresh

- Pattern refresh is an incremental caller-selected scope operation keyed by company, material, demand type, and cutoff. Accepted Actuals/corrections refresh only their requested scope; rejected corrections and duplicate/retry delivery converge without semantic change.
- PostgreSQL projection guards provide concurrent convergence and prevent delayed older cutoffs from overwriting newer Pattern Memory. No global rescan, Forecast integration, Company Learning, or Decision Intelligence was added.

## 2026-08-13 - Phase 3C5B3B Incremental Company Learning Refresh

- Added an explicit company-scoped refresh facade that delegates aggregation and score calculation to the durable Company Learning materializer. Caller-selected companies only are refreshed; no global company discovery or rescan is performed.
- Duplicate, concurrent, stale, pre-write-failure, response-loss retry, and fresh-session delivery converge through the persisted source-summary fingerprint and current-row version. Learning score is derived from current canonical evidence, never refresh count. Forecast integration and Decision Intelligence remain inactive.

## 2026-08-13 - Phase 3C5B4A Learning Refresh Orchestration

- Added a callable, evidence-routed orchestration boundary. Canonical Actual acceptance/correction evidence refreshes its exact Pattern scope before Company Learning; Forecast Evaluation, Champion promotion/rollback, and terminal RetrainingJob evidence refresh Company Learning only.
- The orchestrator loads one tenant-scoped `LearningEvidence` row, validates its durable source scope, and has no global scan or automatic delivery hook. Duplicate, delayed, and retried delivery converges through existing Pattern and Company projection fingerprints; Forecast integration and Decision Intelligence remain inactive.

## 2026-08-13 - Phase 3C5B4B1 Durable Learning Evidence Delivery

- Added a durable, tenant-scoped Learning Evidence delivery intent in the same transaction as canonical `LearningEvidence` creation. A committed canonical evidence contribution therefore cannot lose its refresh intent through a process crash.
- Delivery ownership is leased with PostgreSQL claim tokens, heartbeat, expiry reclaim, bounded retry, and terminal deterministic-failure classification. Delivery workers remain explicit: they delegate routing to the callable orchestrator, and no periodic worker, Forecast integration, or Decision Intelligence was activated.

## 2026-08-13 - Phase 3C5B4B2 Learning Delivery Worker

- Added a bounded, company-scoped worker that claims only from the durable delivery ledger and delegates every route to the existing Learning Refresh Orchestrator. It supports one-item and caller-limited batch consumption; no deployment timer, daemon, cron, or startup hook is configured.
- PostgreSQL verification covers exclusive claims, heartbeat and reclaim, stale-worker rejection, retry and terminal failure, post-orchestrator crash recovery, correction safety, tenant isolation, and idempotent Pattern/Company projection convergence. Forecast, Supplier Learning, Event Intelligence, and Decision Intelligence remain inactive.

## 2026-08-13 - Phase 3C6B1 Supplier Delivery Observation Ledger

- Added canonical company-scoped observed supplier-delivery facts with supplier-material identity, source references, dispatch/receipt and promise-deviation semantics, optional ordered/received quantities, and deterministic current evidence fingerprints. Declared Supplier master fields are not learning truth.
- Accepted corrections retain auditable prior/proposed snapshots and advance current observed truth; rejected corrections remain auditable but leave it unchanged. Supplier Learning, Safety Stock mathematics, Supplier Business behavior, LearningEvidence emission, and Decision Intelligence remain inactive.

## 2026-08-13 - Phase 3C6B2 Read-Only Supplier Learning Calculation

- Added deterministic, company/supplier/material-scoped calculation over canonical observed supplier deliveries. `supplier_learning_policy_v1` requires eight dispatch-to-receipt lead-time observations and derives Reliable, Variable, Late-Prone, Fulfillment-Risk, Deteriorating, or Mixed-Risk classifications only from observed metricsâ€”never manual Supplier scores.
- Promise reliability and fulfillment remain separate optional metrics. The calculation is cutoff-safe and correction-aware, returns a SHA-256 source fingerprint and evidence-quality confidence, and creates no Supplier Learning memory, LearningEvidence, Safety Stock input, Supplier-analysis change, or Decision Intelligence action.

## 2026-08-13 - Phase 3C6B3 Durable Supplier Learning Memory

- Added the mutable current `SupplierLearningMemory` projection with unique company + supplier + material identity. The materializer accepts only trusted `SupplierLearningService` results, persists compact metrics and canonical observation/revision lineage, and is idempotent on the source fingerprint.
- Accepted canonical corrections and later cutoffs refresh the same row; rejected corrections are unchanged. Older cutoff or obsolete same-cutoff results cannot overwrite newer current evidence. Supplier analysis, Safety Stock integration, LearningEvidence emission, and Decision Intelligence remain inactive.

## 2026-08-13 - Phase 3C6B4 Incremental Supplier Learning Refresh / Delivery

- Added exact company/supplier/material Supplier Learning refresh routing. Canonical observed-delivery and accepted-correction LearningEvidence events atomically create the existing durable delivery intent, and the existing leased worker routes them only to SupplierLearningMemory.
- Duplicate, concurrent, stale, retried, and post-refresh-crash deliveries converge through fingerprints and projection idempotency. Rejected corrections emit no supplier evidence; Company Learning, Pattern Learning, Supplier analysis, Safety Stock, and Decision Intelligence remain inactive.

## 2026-08-13 - Phase 3C6B5 Read-Only Supplier Learning Enrichment

- Added an optional, company/supplier/material-scoped resolver that exposes compact durable Supplier Learning provenance only when its cutoff is compatible with the analysis context. Missing or incompatible evidence remains an explicit non-blocking fallback.
- Learned evidence attaches as distinct explainability metadata. The existing Safety Stock operational lead-time source and mathematics are unchanged; no Supplier Learning task, writeback, Supplier-analysis change, Safety Stock integration, or Decision Intelligence activation was added.

## 2026-08-13 - Phase 3C5B3A Company Learning Foundation

- Added a company-scoped V2 current projection with deterministic evidence-maturity score. The 0–100 score measures durable evidence coverage, scope maturity, source diversity, and reconstructability—not Forecast accuracy or business performance.
- Pattern, Learning Evidence, Forecast Evaluation, Retraining, and Champion summaries are read-only. Forecast integration, Supplier/Event Learning, and Decision Intelligence remain inactive.
