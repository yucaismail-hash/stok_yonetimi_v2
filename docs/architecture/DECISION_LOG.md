# Stokonomi Architecture Decision Log

**Date baseline:** 2026-08-05

## Accepted decisions

### ADR-001 — Architecture authority

- **Status:** Accepted
- **Context:** Documents 01–07 define the architecture specification.
- **Decision:** Documents 01–07 are the current single source of truth. Code must conform to the documents; document changes require explicit approval and ADR.
- **Consequences:** Alignment work may not silently redesign architecture.
- **Affected components:** Entire repository.
- **Next action:** Maintain canonical registry and exception log.

### ADR-002 — Official WorkflowEngine path

- **Status:** Accepted
- **Context:** Parallel engine implementations exist.
- **Decision:** `app/engine/workflow_engine.py` is the official Workflow Engine path.
- **Consequences:** `app/orchestration/workflow_engine.py` remains a transition component until compatibility evidence exists.
- **Affected components:** Workflow dispatcher, orchestration package, V2 decision route.
- **Next action:** ADR-013 and workflow consolidation phase.

### ADR-003 — Official orchestrator path

- **Status:** Accepted
- **Context:** Execution coordination requires a canonical owner.
- **Decision:** `app/engine/orchestrator.py` is the official Execution Orchestrator path.
- **Consequences:** Dispatcher-to-orchestrator flow is canonical.
- **Affected components:** Workflow dispatcher, execution engine.
- **Next action:** Verify execution contract alignment.

### ADR-004 — Official ExecutionContext target

- **Status:** Accepted
- **Context:** Documents identify the engine ExecutionContext path; an application-side duplicate exists.
- **Decision:** `app/engine/execution_context.py` is the official target path.
- **Consequences:** Existing application context remains transition-only pending ADR-012.
- **Affected components:** Dispatcher, handlers, execution services, execution state types.
- **Next action:** Define context/state compatibility.

### ADR-005 — Official LearningEngine path

- **Status:** Accepted
- **Context:** Parallel learning surfaces exist.
- **Decision:** `app/learning/learning_engine.py` is the official Learning Engine path.
- **Consequences:** `app/services/learning*` remains transition-only until equivalence is verified.
- **Affected components:** Learning components and legacy API consumers.
- **Next action:** Learning consolidation phase.

### ADR-006 — Official Decision Intelligence path

- **Status:** Accepted
- **Context:** Decision architecture requires a sole official decision producer.
- **Decision:** `app/decision_intelligence/decision_intelligence_engine.py` is the official Decision Intelligence path.
- **Consequences:** `app/services/ai/ai_decision_engine.py` remains transition-only.
- **Affected components:** Decision, narrative, artifact, legacy AI paths.
- **Next action:** DI persistence-boundary alignment.

### ADR-007 — Official repository and application paths

- **Status:** Accepted
- **Context:** Data access and use-case coordination need named owners.
- **Decision:** `app/repositories/*` is the official Repository Layer and `app/application/*` is the official Application Layer.
- **Consequences:** API bypasses and direct persistence ownership require alignment.
- **Affected components:** Repositories, application services, API, DI.
- **Next action:** API and DI boundary phases.

### ADR-008 — Legacy cleanup gate

- **Status:** Accepted
- **Context:** Duplicate/legacy paths still have consumers or unverified runtime use.
- **Decision:** No legacy or transition component may be removed until behavioral equivalence and removal-gate evidence are accepted.
- **Consequences:** Consolidation is additive/compatible before cleanup.
- **Affected components:** All transition components.
- **Next action:** Maintain transition registry.

### ADR-009 — UUIDv7 generation

- **Status:** Accepted
- **Context:** UUID4 compatibility fallback did not preserve chronological UUIDv7 semantics.
- **Decision:** `BaseModel.id` uses `uuid_extensions.uuid7`; `requirements.txt` declares `uuid7==0.1.0`.
- **Consequences:** Future generated identifiers are UUID version 7; no schema or data migration was performed in Phase 0.
- **Affected components:** `app/models/base.py`, requirements manifest.
- **Next action:** No further UUID change in current alignment phases.

### ADR-010 — Phase 0 Stabilization closure

- **Status:** Accepted
- **Context:** Foundational import and loadability blockers prevented reliable architecture work.
- **Decision:** Phase 0 is complete after import/loadability stabilization and package validation.
- **Consequences:** Phase 1 may proceed without changing business behavior as a Phase 0 objective.
- **Affected components:** Package imports, model imports, V2 dependencies, UUID generation.
- **Next action:** Canonical alignment governance and ADR work.

## Accepted decisions

### ADR-011 — Official ExecutionService Public Facade and Layer Ownership

- **Date:** 2026-08-06
- **Status:** Accepted
- **Context:** Document 01 designates `app/services/execution/execution_service.py` as the official ExecutionService path. That file is absent. `app/application/services/execution/execution_service.py` provides active application use-case operations, while `app/engine/execution_service.py` provides runtime lifecycle operations.
- **Decision:** `app/services/execution/execution_service.py::ExecutionService` is the approved official public execution facade. It delegates application use cases to `app/application/services/execution/execution_service.py`. Runtime lifecycle responsibility remains in `app/engine/execution_service.py`.
- **Responsibility boundaries:** The facade must not execute capabilities; create or mutate ExecutionContext; manage scheduler, workers, retry, timeout, cancellation, or result collection; access repositories or database sessions; create Learning output, Decisions, or Artifacts; duplicate application/engine business logic; or become an API route implementation.
- **Alternatives rejected:** Making the application path official would change the accepted Document 01 path. Leaving no unified public service would retain the missing canonical path. A unified implementation without a facade boundary risks duplicating or merging application and engine responsibilities.
- **Consequences:** The public path is now approved but not implemented. The application service remains the active delegated use-case component and the engine service remains the active delegated runtime component. No consumer, route, import, or runtime behavior changes through this ADR.
- **Compatibility strategy:** Preserve existing application and engine service imports and contracts during facade introduction. Migrate consumers only after behavioral-equivalence verification.
- **Rollback strategy:** Keep both transition implementations in place. Revert each future consumer migration to its preceding import path if contract parity fails.
- **Removal gates:** Require behavioral-equivalence evidence, import/public-API verification, no remaining consumers, ADR-012 context/state compatibility resolution, and explicit deprecation approval before any transition component is removed.
- **Affected components:** `app/services/execution/`, `app/application/services/execution/execution_service.py`, `app/engine/execution_service.py`, future V2 execution/analysis consumers, and application package exports.
- **Next action:** PHASE 1F — EXECUTIONSERVICE FACADE IMPLEMENTATION PLAN.

### ADR-012 — ExecutionContext and Execution-State Authority

- **Date:** 2026-08-06
- **Status:** Accepted
- **Context:** Application and engine ExecutionContext implementations coexist. Dispatcher currently creates the application context, while Document 01 identifies `app/engine/execution_context.py` as the canonical runtime path. Application `ExecutionStatus` and engine `ExecutionState` also differ.
- **Decision:** `app/engine/execution_context.py::ExecutionContext` is the authoritative runtime context. `app/engine/enums.py::ExecutionState` is the authoritative runtime-state enum. `app/application/execution/execution_context.py` remains a transition request-context representation only. WorkflowDispatcher will eventually forward a versioned dispatch request, and WorkflowEngine will initialize or create the canonical engine context after planning.
- **Responsibility boundaries:** Application ExecutionStatus remains a transition API/application representation until an explicit, verified mapping to ExecutionState exists. The application context is neither removed nor deprecated by this decision.
- **Alternatives rejected:** Retaining the application context as runtime authority conflicts with the approved canonical engine path. Maintaining two equal runtime contexts preserves undefined conversion. Replacing the application context without an adapter is unsafe.
- **Consequences:** Runtime lifecycle and serialization authority are explicit. Learning/Decision stages are not added as engine runtime states. Timeout remains an error/retry/failure/cancellation reason unless a future ADR changes the state vocabulary.
- **Migration strategy:** Define contract fixtures and a request-to-engine-context adapter, compare serialization/lifecycle behavior, migrate the dispatcher after parity passes, then retain the application context through transition.
- **Compatibility strategy:** Preserve existing API response shapes and application service signatures while mapping transition statuses at an approved boundary.
- **Rollback strategy:** Revert future dispatcher migration to the application context path; keep both classes in place.
- **Removal gates:** State/serialization parity; canonical dispatcher/runtime use; no remaining runtime consumers of application context; explicit deprecation approval.
- **Affected components:** Application/engine contexts, engine enums, dispatcher, workflow engine, engine execution service, API status schemas, handlers, and execution tests.
- **Next action:** PHASE 1L — EXECUTION CONTRACTS AND CONTEXT ADAPTER IMPLEMENTATION PLAN.

### ADR-018 — Workflow and Runtime Dispatch Contract

- **Date:** 2026-08-06
- **Status:** Accepted
- **Context:** WorkflowDispatcher awaits `dispatch/get_status/get_result`, but canonical WorkflowEngine currently provides planning-only methods. ExecutionOrchestrator exists but is not on the dispatcher path. Status/result ownership was undefined.
- **Decision:** The canonical runtime entry flow is WorkflowDispatcher → `WorkflowEngine.dispatch` → ExecutionOrchestrator → capability execution → Execution Result. WorkflowEngine is the canonical planner plus asynchronous execution-entry coordinator. Its approved but not yet implemented public contracts are `async dispatch(WorkflowDispatchRequest) -> WorkflowDispatchResult`, `async get_execution_status(UUID) -> ExecutionStatusSnapshot`, and `async get_execution_result(UUID) -> ExecutionResultEnvelope`.
- **Responsibility boundaries:** WorkflowEngine plans, validates dependencies, initializes canonical runtime context, delegates runtime work to ExecutionOrchestrator, and exposes approved status/result retrieval. It must not construct API responses, define routes, access API request objects, generate Learning/Decision/Artifact output, manage database sessions directly, or execute capability business logic itself. ExecutionOrchestrator remains the runtime execution owner. The public ExecutionService facade does not coordinate runtime.
- **Alternatives rejected:** Dispatcher direct orchestration weakens layer separation. A dedicated runtime facade is not an approved canonical component. Public ExecutionService runtime coordination conflicts with ADR-011. Retaining the current mismatch leaves the dispatcher path nonfunctional.
- **Consequences:** Runtime entry, execution ID/status/result contracts, and durable retrieval ownership are explicit. Live status/progress/retry/worker/checkpoint ownership belongs to engine runtime components. Durable final result, execution record, metrics, errors, and persisted snapshots belong to the execution repository boundary.
- **Migration strategy:** Add contracts/adapters, integrate planning/runtime behind canonical WorkflowEngine, add durable status/result persistence, then migrate consumers only after parity verification.
- **Compatibility strategy:** Retain legacy orchestration and application-context paths until canonical dispatch/status/result contracts pass controlled and integration parity tests.
- **Rollback strategy:** Revert future changes per implementation batch; do not remove transition components.
- **Removal gates:** Dispatch/status/result contract tests; runtime context/state parity; durable retrieval tests; no transition consumers; ADR-013 compatibility resolution; explicit deprecation approval.
- **Affected components:** Dispatcher, canonical workflow engine, orchestrator, engine execution service/context, execution repositories/models, application execution service/facade, handlers, and V2 execution endpoints.
- **Next action:** PHASE 1L — EXECUTION CONTRACTS AND CONTEXT ADAPTER IMPLEMENTATION PLAN.

### ADR-019 — Execution Contract Field, Stage, Identity and Time Standard

- **Date:** 2026-08-06
- **Status:** Accepted
- **Context:** ADR-012 and ADR-018 establish the canonical runtime context and dispatch boundary, but the execution identity, state/stage vocabulary, timestamp standard, and serializable cross-boundary contracts were not yet defined.
- **Decision:** `app/engine/execution_context.py::ExecutionContext` remains the mutable canonical runtime context. WorkflowDispatcher generates `execution_id` before planning, with API visibility only after runtime acceptance. WorkflowEngine resolves and validates the workflow, creates the canonical context, and delegates acceptance to ExecutionOrchestrator. `ExecutionState` remains the runtime lifecycle authority; processing stage is a separate concept with only `validation`, `planning`, `forecast`, `safety_stock`, `supplier`, `simulation`, `backtest`, and `completed`. New execution contracts use frozen dataclasses, timezone-aware UTC timestamps, initial contract/result version `1.0.0`, and JSON-safe serialization.
- **Alternatives rejected:** Keeping lifecycle state and processing stage merged; placing identity/trace/version fields in generic metadata; retaining naive timestamps for new contracts; and using mutable boundary contract objects.
- **Consequences:** Learning, Decision Intelligence, and Artifact remain downstream pipeline stages, not engine states or stages. Existing runtime/context consumers remain unchanged until explicit adapter and consumer-alignment phases.
- **Migration strategy:** Introduce additive contracts first, then align the engine context and add a request-to-context adapter before migrating dispatcher, engine, orchestrator, or consumers.
- **Compatibility strategy:** Existing contexts, status models, routes, schemas, persistence, and public APIs remain intact. Older contract versions require explicit adapters.
- **Rollback strategy:** Remove the additive contract module and its governance implementation status if its isolated contract validation fails; retain all existing runtime paths.
- **Removal gates:** Contract construction/serialization validation; context-adapter parity; canonical dispatcher and engine integration; consumer migration verification; no transition consumers; and explicit deprecation approval.
- **Affected components:** `app/engine/contracts.py`, engine ExecutionContext/ExecutionState, WorkflowDispatcher, WorkflowEngine, ExecutionOrchestrator, application execution services, execution APIs, repositories, and future adapters.
- **Next action:** PHASE 1P — EXECUTION CONTRACTS BATCH 1.

## Unresolved decisions

### ADR-013 — WorkflowEngine legacy compatibility strategy

- **Status:** Unresolved — ADR required
- **Context:** Registered V2 decision routes directly use `app.orchestration.WorkflowEngine`.
- **Decision:** Not selected.
- **Consequences:** The orchestration engine remains in place.
- **Affected components:** `app/orchestration/*`, V2 decision route, dispatcher.
- **Next action:** Compare objective, graph, status, and failure behavior.

### ADR-014 — Decision Intelligence persistence ownership

- **Status:** Unresolved — ADR required
- **Context:** DecisionIntelligenceEngine directly uses SessionLocal and ArtifactRepository.
- **Decision:** Not selected.
- **Consequences:** No persistence movement is authorized.
- **Affected components:** DI engine, artifact service/handler, repositories, timeline/advisor persistence.
- **Next action:** Define owner and artifact lifecycle transaction boundary.

### ADR-015 — Event publication authority

- **Status:** Unresolved — ADR required
- **Context:** EventBus and engine EventPublisher are separate mechanisms.
- **Decision:** Not selected.
- **Consequences:** No event publisher consolidation is authorized.
- **Affected components:** Events package, engine execution events, subscribers, integration.
- **Next action:** Compare publication, retry, delivery, and audit contracts.

### ADR-016 — V2 route ownership and registration strategy

- **Status:** Unresolved — ADR required
- **Context:** Registered V2 routes bypass application boundaries while application-service V2 endpoint modules are unregistered.
- **Decision:** Not selected.
- **Consequences:** No route registration, unregistration, or replacement is authorized.
- **Affected components:** V2 router, endpoint packages, application services, schemas.
- **Next action:** Define route-by-route compatibility plan.

### ADR-017 — Missing ExportPipeline

- **Status:** Unresolved — ADR required
- **Context:** ExportPipeline is referenced by architecture/package expectations but no implementation file exists.
- **Decision:** Not selected.
- **Consequences:** No missing component may be created by assumption.
- **Affected components:** Integration package and future export contract.
- **Next action:** Establish exact producer, consumer, and contract evidence.

## Revision — Product Architecture Phase 1

### Approved Product Levels

#### Level 1 — Standalone Analysis

- **Purpose:** Allow users to run one analysis independently.
- **Supported analyses:** Forecast, Safety Stock, Simulation, Backtest, Supplier.
- **Learning:** Enabled.
- **Decision Intelligence:** Disabled.
- **AI output:** Analysis explanation only, delivered as an AI Artifact.

#### Level 2 — Business Workflow

- **Purpose:** Produce an operational business plan.
- A Business Workflow is not an analysis; it orchestrates multiple analyses.
- **Decision Intelligence:** Enabled.
- **Final output:** Dynamic Operational Plan.

### Approved Business Workflow Products

#### Forecast Business Workflow

Validation → Forecast → Simulation → Backtest → Learning → Decision Intelligence → Dynamic Demand Plan → AI Artifact

Outputs include Demand Plan, Expected Sales, Risk Periods, Forecast Confidence, and Recommended Actions.

#### Safety Stock Business Workflow

Validation → Forecast → Safety Stock → Simulation → Backtest → Learning → Decision Intelligence → Dynamic Inventory Plan → AI Artifact

Outputs include Expected End-of-Month Inventory, Order Week, Order Quantity, Expected Service Level, and Stockout Risk. If supplier data exists, Supplier Allocation is performed after the Dynamic Inventory Plan.

### Learning

- Learning never changes deterministic calculation results.
- Learning improves Forecast accuracy, Backtest accuracy, Simulation behaviour, Supplier performance evaluation, and Pattern recognition.
- Future ERP/API feedback may contribute to Company Learning.
- Learning never requires mandatory user input.

### Decision Intelligence

Decision Intelligence never performs deterministic analysis. It evaluates Forecast, Safety Stock, Simulation, Backtest, and Learning, then produces operational decisions.

### Dynamic Operational Plan

Dynamic Operational Plan represents the final output of every Business Workflow.

### External Intelligence

External Intelligence is automatically collected external information, including Inflation, Exchange Rates, Interest Rates, Calendar, Public Holidays, Weather, Google Trends, and Sector Data.

External Intelligence → Company Learning → Pattern Intelligence → AI Parameter Optimizer → Deterministic Analysis

### AI Philosophy and Core Principle

- Deterministic engines perform calculations.
- AI optimizes parameters, learns, supports decisions, and explains results.
- AI never replaces deterministic calculations.
- The more data available, the more valuable the operational output.

### ADR-020 — Product Levels, Workflow Intent Types and Dynamic Operational Plan Outputs

- **Date:** 2026-08-06
- **Status:** ACCEPTED
- **Context:** The approved product architecture distinguishes an independently requested analytical capability from a business outcome that requires an ordered set of analyses and an operational decision. The existing documents define both Single Analysis Workflow and Business Objective Workflow concepts, while the prior INV-001 wording did not express their separate execution-intent identities.
- **Accepted decision:** Stokonomi has two product levels. Level 1, Standalone Analysis, accepts exactly one capability intent—Forecast, Safety Stock, Simulation, Backtest, or Supplier—runs only that analytical capability, runs Learning afterward, excludes Decision Intelligence, and produces an analysis-level AI Artifact. Level 2, Business Workflow, accepts exactly one Business Objective intent, orchestrates its ordered analytical capabilities, runs Learning and Decision Intelligence, produces a Dynamic Operational Plan, and then produces a final AI Artifact. `objective_type XOR analysis_type` is binding; the two intent domains must not be silently converted into one another. Forecast Business Workflow is Validation → Forecast → Simulation → Backtest → Learning → Decision Intelligence → Dynamic Demand Plan → AI Artifact. Safety Stock Business Workflow is Validation → Forecast → Safety Stock → Simulation → Backtest → Learning → Decision Intelligence → Dynamic Inventory Plan → AI Artifact. Simulation and Backtest are mandatory in both approved Business Workflows. Supplier allocation is conditional enrichment after the Dynamic Inventory Plan and missing supplier data does not block the core plan. Learning cannot retroactively alter a completed deterministic result; it improves future parameter, model, confidence, pattern, supplier, and Decision Intelligence behavior. External Intelligence affects deterministic analysis only through Company Learning, Pattern Intelligence, and AI Parameter Optimizer boundaries. Missing optional data invokes graceful degradation. Deterministic engines calculate; AI learns, optimizes, evaluates, supports decisions, and explains, but never replaces deterministic calculation.
- **Alternatives rejected:** Treating a Standalone Analysis as a Business Objective; automatically expanding a selected capability into hidden analytical prerequisites; allowing Decision Intelligence for Level 1; omitting mandatory Simulation or Backtest from the approved Level 2 workflows; allowing AI or External Intelligence to replace or overwrite deterministic analytical results; and failing a valid capability solely because optional enrichment data is absent.
- **Consequences:** Workflow intent must be explicit at every future boundary. Dynamic Demand Plan and Dynamic Inventory Plan are approved named Dynamic Operational Plan outputs. ERP/API actual-action feedback is a V2/future Company Learning capability unless separately evidenced as implemented.
- **Compatibility strategy:** This is a documentation and governance decision only. Existing runtime paths, public APIs, routes, schemas, models, repositories, execution behavior, and legacy components remain unchanged until separately aligned with behavioral-equivalence evidence.
- **Migration strategy:** Future alignment introduces the approved intent contract and workflow behavior incrementally, preserving public behavior and compatibility. WorkflowDispatcher, WorkflowEngine, capability execution, result collection, routes, and schemas are not migrated by this ADR record.
- **Rollback strategy:** Revert this appended ADR-020 entry and its associated revision append sections as one documentation-only change set if the approved product decision is withdrawn. No runtime rollback is required because this decision makes no runtime change.
- **Removal gates:** No transition or legacy execution path may be removed until the approved intent semantics, ordered workflow behavior, result/error behavior, public API compatibility, persistence/event effects, and rollback evidence are verified and an explicit removal approval is recorded.
- **Affected components:** Product architecture governance; WorkflowDispatcher; WorkflowEngine; ExecutionOrchestrator; Capability Registry; Learning; Decision Intelligence; AI Artifact; Application and API boundaries; future Company Learning and External Intelligence boundaries.

## Phase 2 accepted decisions

### ADR-033 — Database Migration Authority and Schema Ownership

- **Date:** 2026-08-06
- **Status:** Accepted
- **Context:** The configured remote Neon PostgreSQL schema has no migration-history table. Repository evidence confirms competing writers: automatic `Base.metadata.create_all()` at application startup, `migrate.py`, manual index SQL, and an Alembic-style migration file. Live and ORM schemas are not equivalent.
- **Decision:** Alembic is the sole authoritative mechanism for managed PostgreSQL schema changes. Every PostgreSQL schema mutation requires an ordered migration revision. The migration-history table is authoritative evidence of schema version. `Base.metadata.create_all()` must not run automatically against managed PostgreSQL environments; it may remain only for explicitly configured disposable local/test databases. `migrate.py` and manual schema scripts are transition/legacy tools and must not introduce new PostgreSQL schema changes. Direct manual production DDL is prohibited except through an explicitly approved emergency procedure. Application startup verifies schema readiness but does not mutate managed schema. Database environment classification must be explicit.
- **Environment rules:** `local`, `test`, `development`, `staging`, and `production` must be explicitly configured. Unknown environments fail closed for schema mutation. Remote PostgreSQL, including Neon, must never run implicit `create_all`. Staging and production require migration history before startup continues.
- **Startup behavior:** Managed deployment/release performs Alembic upgrade and version verification before application start; normal application startup performs no schema mutation.
- **Local/test compatibility:** Explicit disposable local/test configuration may permit `create_all`; database URL alone never selects destructive or schema-mutating behavior.
- **Migration-history ownership:** Alembic's version table, in the controlled application schema, is the authoritative applied-revision record.
- **Legacy-script policy:** Existing `migrate.py`, `add_indexes.py`, and `migrations/create_ai_artifacts_table.py` are retained as transition evidence only until a controlled baseline establishes their disposition. They are prohibited for new managed-PostgreSQL DDL.
- **Emergency-DDL policy:** Emergency direct DDL requires explicit approval, recorded command evidence, immediate follow-up revision, and reconciliation with migration history.
- **Alternatives rejected:** Retaining `create_all` for managed PostgreSQL lacks ordered alteration, rollback, and history semantics. Retaining `migrate.py` lacks proven ordered upgrade/downgrade/history control. A custom manager adds unsupported authority while Alembic-compatible evidence already exists.
- **Consequences:** Phase 2C runtime-table implementation cannot begin until migration bootstrap, a legacy schema baseline, and startup schema-control implementation are separately approved and verified.
- **Migration strategy:** Establish Alembic tooling, baseline the existing live schema without executing destructive DDL, prevent managed-startup `create_all`, then introduce only additive runtime revisions.
- **Compatibility strategy:** Leave legacy tables and scripts intact during the transition; no existing table is recreated, deleted, or repurposed by the baseline.
- **Rollback:** Tooling changes are file-scoped. Before any consumer migration, remove the new tooling configuration and restore preceding startup behavior; do not rollback live schema without an approved migration.
- **Removal gates:** Verified Alembic baseline/history, deployment guard, environment classification, startup non-mutation verification, schema-drift review, and explicit legacy-tool retirement approval.
- **Affected components:** `app/database.py`, `app/main.py`, migration tooling, deployment configuration, `migrate.py`, `add_indexes.py`, `migrations/`, and all future PostgreSQL schema changes.
- **Next phase:** PHASE 2C-M0 — ALEMBIC BASELINE AND STARTUP SCHEMA CONTROL.

### ADR-021 — Capability Execution Boundary

- **Date:** 2026-08-06
- **Status:** Accepted
- **Decision:** A dedicated `CapabilityExecutor` is the canonical invocation boundary between runtime workers and deterministic analytical implementations: ExecutionOrchestrator → TaskScheduler → Worker → CapabilityExecutor → capability implementation. It owns request validation, input-provider invocation, implementation resolution, timeout boundary, deterministic invocation, exception conversion, result-contract construction, and execution metrics. It does not own workflow planning, scheduling, worker assignment, retry policy, durable lifecycle, Learning, Decision Intelligence, Dynamic Operational Plans, AI Artifacts, or API responses. Internal HTTP endpoints remain transition adapters.

### ADR-022 — Durable Runtime Store

- **Date:** 2026-08-06
- **Status:** Accepted
- **Decision:** PostgreSQL is the durable source of truth for execution/workflow/task identity and state, stages, progress, attempts, retries, errors, timestamps, checkpoints, result references, metrics, and trace/correlation identity. Queue/cache systems may be transient only. Store implementation and schema migration are deferred to Phase 2C.

### ADR-023 — Queue and Worker Strategy

- **Date:** 2026-08-06
- **Status:** Accepted
- **Decision:** The target uses an external queue, dedicated capability workers, PostgreSQL durable state, heartbeat/lost-worker recovery, and process isolation for CPU-heavy work. The transition uses local process-based execution with common CapabilityExecutor contracts and PostgreSQL durable state. In-process asyncio alone is not the production target. No queue technology is selected.

### ADR-024 — Capability Result and Data-Passing Contract

- **Date:** 2026-08-06
- **Status:** Accepted
- **Decision:** Workflow tasks communicate through versioned `CapabilityExecutionRequest` and `CapabilityExecutionResult`. Upstream transfer is explicit; dependency alone never implies data input. Each edge is classified as required data, execution-order only, optional enrichment, unsupported, or adapter-required. No implicit previous-result guessing is permitted.

### ADR-025 — Execution Group, SKU Task and Merge Model

- **Date:** 2026-08-06
- **Status:** Accepted
- **Decision:** The future hierarchy is Execution → Execution Group → Task Group → SKU Task → Capability execution, with deterministic partitioning and merge, stable SKU ordering, execution progress, scoped retry, no unnecessary re-run, partial-failure evidence, and one-SKU telemetry. Runtime implementation is deferred to Phase 2G.

### ADR-026 — Downstream Product Pipeline Handoff

- **Date:** 2026-08-06
- **Status:** Accepted
- **Decision:** Deterministic analytical completion and downstream product completion are separate lifecycle domains. Standalone flows hand analytical results to Learning then an AI Explanation Artifact; Business Workflows hand analytical bundles to Learning, Decision Intelligence, Dynamic Operational Plan, and AI Artifact. A downstream failure must not erase or rewrite analytical results. Durable retryable handoff is deferred to Phase 2F.

### ADR-027 — Capability Execution Failure and Error Result Policy

- **Date:** 2026-08-06
- **Status:** Accepted
- **Decision:** Pre-start system/configuration failures propagate as explicit executor exceptions. Started operational failures, including timeouts and invalid output, return a failed `CapabilityExecutionResult`. The executor records retryable metadata but never schedules retries. Technical errors carry stable code, category, retryability, aware UTC occurrence time, and JSON-safe non-sensitive details.

### ADR-028 — User-Facing Execution Error Language and Notification Contract

- **Date:** 2026-08-06
- **Status:** Accepted
- **Context:** Runtime diagnosis and user communication require separate contracts.
- **Decision:** Runtime owns technical classification; the application layer owns user-facing wording. Normal user messages answer what happened, preserved work, system action, user action, and retry status; they exclude motor, engine, executor, worker, adapter, protocol, implementation, JSON-safe, queue, traceback, and internal exception-class terminology. Technical codes are optional support references only. Notification contracts never select HTTP status and invalid analysis output is never a success.
- **Initial notice categories:** unable to start; missing/invalid data; unable to complete; longer than expected; invalid result; temporarily unavailable data.
- **Mapping ownership:** a pure application mapping translates technical metadata into notices.
- **Alternatives rejected:** exposing runtime errors directly; producing user messages in the engine; treating invalid output as success.
- **Consequences:** API wiring remains deferred; engine-to-application message dependencies are prohibited.
- **Compatibility strategy:** additive, not an API response change.
- **Migration strategy:** wire notices at an approved application/API boundary only after compatibility tests.
- **Rollback:** remove the additive mapper/contracts; no route or data rollback is required.
- **Removal gates:** approved API contract, mapping coverage, observability, and explicit deprecation approval.
- **Affected components:** engine capability contracts/executor; application error mapping; future API execution surfaces.
- **Next phase:** PHASE 2C — DURABLE RUNTIME STORE DESIGN AND MIGRATION PLAN.
- **Next phase:** PHASE 1AI — SINGLE ANALYSIS CONTRACT IMPLEMENTATION PLAN.

### ADR-029 — Canonical Runtime Entity and State Persistence Model

- **Date:** 2026-08-07
- **Status:** Accepted
- **Context:** Process-local `ExecutionContext`, lifecycle, and worker structures are not a recoverable runtime authority. Existing `workflow_*` and `execution_*` tables have conflicting legacy identity/live-schema contracts and lack durable attempts, leases, heartbeats, checkpoints, optimistic locking, idempotency evidence, and versioned result references.
- **Decision:** Introduce additive canonical entities `RuntimeExecution`, `RuntimeTask`, `RuntimeTaskAttempt`, `RuntimeCheckpoint`, and `RuntimeResultReference` in `runtime_executions`, `runtime_tasks`, `runtime_task_attempts`, `runtime_checkpoints`, and `runtime_result_references`. Existing workflow/execution tables remain transition/legacy and are not canonical authority. Runtime execution state uses `app.engine.enums.ExecutionState`; task/attempt state uses compatible task vocabulary and the capability-result contract. RuntimeStore validates all transitions, records timestamps and row versions, rejects stale writes and terminal-to-non-terminal transitions, and never allows downstream stages to overwrite completed deterministic results.
- **Data and tenancy rules:** Every tenant-owned entity carries `company_id`; cross-company reads/writes are prohibited. Runtime persistence excludes raw dataset rows, decrypted inputs, credentials, secrets, personal information, and raw tracebacks. Long calculation never runs in an open database transaction.
- **Alternatives rejected:** Extending legacy tables, process-only state, and queue-state authority do not provide compatible recoverable lifecycle evidence.
- **Consequences and compatibility:** An additive schema is required in Phase 2C-M2 and a repository/facade in Phase 2C-M3. No consumer changes now; process-local context remains a temporary non-authoritative cache after durable implementation.
- **Rollback and removal gates:** Before consumers connect, additive tables may be removed via reviewed downgrade. Legacy models require active canonical records, RuntimeStore status/result reads, no legacy-route dependency, compatibility evidence, and explicit deprecation approval before retirement.

### ADR-030 — RuntimeStore Ownership and Persistence Boundary

- **Date:** 2026-08-07
- **Status:** Accepted
- **Context:** Direct ORM/repository writes from dispatch, workflow, or analytical components would violate ownership boundaries.
- **Decision:** RuntimeStore is the canonical engine-facing durable facade: `ExecutionOrchestrator → RuntimeStore interface → runtime repositories → PostgreSQL`. It owns atomic execution/task creation, idempotency, validated transitions, claims/leases, attempts, checkpoints, result references, progress, cancellation, terminal completion/failure, durable reads, and optimistic concurrency. It may coordinate the five runtime repositories.
- **Boundary:** RuntimeStore does not own planning, analytical calculation, queue technology, worker execution, retry-policy selection, Learning, Decision Intelligence, downstream products, API response construction, or user-facing wording. Application/API layers do not query runtime repositories directly; their approved read path reaches RuntimeStore. Durable state wins over divergent in-memory cache without silent merging.
- **Transaction policy:** Operations use short transactions; capability, external API, LLM, and simulation work occurs outside them.
- **Alternatives rejected:** Orchestrator-owned repositories, Application ExecutionService persistence, API repository queries, and uncoordinated repository calls violate separation or atomicity.
- **Compatibility, rollback, and removal gates:** Introduce the facade alongside in-memory context; migrate acceptance writes, then status/result reads. Per-consumer rollback is allowed only without ignoring/duplicating durable evidence. In-memory authority may be removed only after durable writes/reads, restart and multi-instance evidence, and explicit approval.

### ADR-031 — Worker Claim, Lease, Concurrency and Idempotency Model

- **Date:** 2026-08-07
- **Status:** Accepted
- **Context:** Duplicate delivery, worker loss, stale completion, and concurrent claims require durable evidence beyond queue acknowledgement.
- **Decision:** Runtime tasks use atomic claim-and-lease. A claim validates claimable state, dependencies, cancellation, lease absence/expiry, and expected state/row version; it persists a unique lease token and creates an attempt. Heartbeat, completion, and failure require that active token. Calculation occurs outside the transaction; stale/duplicate completion is deterministically rejected.
- **Concurrency and idempotency:** Use integer `row_version`, expected-state conditional updates, lease-token verification, unique `(execution_id, task_id)`, unique `(runtime_task_id, attempt_number)`, company-scoped execution idempotency, and unique result-reference/version constraints. `SELECT FOR UPDATE SKIP LOCKED` may select ready claims, but locks never span calculation. Repeated delivery cannot create duplicate executions, active claims, or valid-attempt results.
- **Failure policy:** Expired leases may be reclaimed only after durable validation. Cancellation prevents claims and invalidates stale completion. CapabilityExecutor records retryability only; Orchestrator/Scheduler selects retry policy, and every retry is a new attempt.
- **Alternatives rejected:** Visibility timeout only, worker identity without a token, `updated_at` only, and long transactions are insufficient.
- **Compatibility, rollback, and removal gates:** Initial local execution uses the same contract without selecting queue technology. Before durable-worker consumption, additive work is removable; thereafter reconciliation is required. No simplified claim path may bypass lease validation once durable workers are active.

### ADR-032 — Runtime Result Storage and Reference Policy

- **Date:** 2026-08-07
- **Status:** Accepted
- **Context:** Large, SKU-heavy, versioned results are unsuitable for mutable execution/task rows, and legacy result tables are not canonical runtime reference authority.
- **Decision:** Runtime rows store references by default. `RuntimeResultReference` owns company/execution and optional task/attempt identity, type/version/contract, storage kind/location, optional bounded inline JSONB, checksum, byte size, approved compression/encryption metadata, creation time, validation status, and metadata. Small validated results may be inline; large/SKU-heavy and final bundles use reference contracts. Storage technology and a byte threshold remain later configurable implementation decisions.
- **Integrity and boundaries:** Register only validated results; invalid results never become successful or Learning/Decision Intelligence input. Company scope is mandatory; raw dataset rows and decrypted inputs are prohibited. Dynamic Operational Plans and AI Artifacts remain separate products.
- **Alternatives rejected:** Storing all results in execution/task JSONB, external references only, and reusing `execution_results` as authority are rejected.
- **Compatibility, rollback, and removal gates:** Existing result tables remain untouched. Before consumers, the additive schema is removable; after references exist, referenced data must be preserved or migrated. No backend may be removed until active references migrate or expire.
