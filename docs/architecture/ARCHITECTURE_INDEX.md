# Stokonomi Architecture Index

## Governance status

- **Production Champion Forecast:** Phase 3C3B3B1 development verified: current-canonical and replay-snapshot scope, trusted XGBoost Champion inference, explicit demand type, and immutable Forecast provenance are durable. Controlled rollback remains pending; PHASE 3C1 PostgreSQL verification is complete.
- **Controlled Champion Rollback:** Phase 3C3B3B2 development verified: explicit PostgreSQL-atomic rollback affects future Forecasts only; historical Forecast/Vintage evidence is immutable and runtime fallback never mutates the registry.

- **Architecture version:** v2.0
- **Authority:** Documents 01–07 are the current single source of truth.
- **Current milestone:** Phase 1C — Architecture Governance Baseline
- **Current migration phase:** Phase 1 — Canonical Alignment (governance complete)
- **Next approved phase:** PHASE 1D — EXECUTIONSERVICE ADR
- **Code authority rule:** If repository code conflicts with Documents 01–07, code must be aligned to the documents. A document change requires explicit approval and an ADR.

## Architecture specification documents

| Document | Title | Status | Primary dependencies |
|---|---|---|---|
| 01 | Foundation & Architecture Principles | Authoritative | Governs all documents |
| 02 | Domain Model | Authoritative | 01 |
| 03 | Workflow & Execution Planning | Authoritative | 01, 02 |
| 04 | Execution Engine | Authoritative | 01, 03 |
| 05 | AI Intelligence Architecture | Authoritative | 01, 02, 03, 04 |
| 06 | Data Architecture | Authoritative | 01, 02, 05 |
| 07 | System Architecture | Authoritative baseline | 01–06 |

## Canonical component registry

| Component | Official path | Status |
|---|---|---|
| WorkflowDispatcher | `app/application/workflow_dispatcher.py` | Canonical |
| WorkflowEngine | `app/engine/workflow_engine.py` | Canonical workflow planning and asynchronous execution entry; **APPROVED — NOT YET IMPLEMENTED** dispatch contract |
| ExecutionOrchestrator | `app/engine/orchestrator.py` | Runtime execution coordinator; **IMPLEMENTATION PRESENT — ASYNC RUNTIME ALIGNMENT PENDING** |
| ExecutionContext | `app/engine/execution_context.py` | **APPROVED — BATCHED IMPLEMENTATION IN PROGRESS**; runtime context alignment pending |
| ExecutionState | `app/engine/enums.py` | **ACCEPTED — IMPLEMENTATION PRESENT, MAPPING PENDING** |
| WorkflowDispatchRequest | `app/engine/contracts.py` | **IMPLEMENTED — NOT YET CONSUMED** |
| WorkflowDispatchResult | `app/engine/contracts.py` | **IMPLEMENTED — NOT YET CONSUMED** |
| ExecutionStatusSnapshot | `app/engine/contracts.py` | **IMPLEMENTED — NOT YET CONSUMED** |
| ExecutionResultEnvelope | `app/engine/contracts.py` | **IMPLEMENTED — NOT YET CONSUMED** |
| LearningEngine | `app/learning/learning_engine.py` | Canonical |
| DecisionIntelligenceEngine | `app/decision_intelligence/decision_intelligence_engine.py` | Canonical |
| Repository Layer | `app/repositories/*` | Canonical |
| Application Layer | `app/application/*` | Canonical |
| ExecutionService | `app/services/execution/execution_service.py` | **APPROVED — NOT YET IMPLEMENTED**; public execution facade |

## Transition component registry

| Responsibility | Transition component | Reason |
|---|---|---|
| Workflow engine | `app/orchestration/workflow_engine.py` | Duplicate implementation; registered V2 decision route consumes it. |
| Workflow support | `app/orchestration/workflow_registry.py`, `dependency_manager.py`, `objectives.py` | Parallel workflow ownership surface. |
| Execution service | `app/application/services/execution/execution_service.py` | Active delegated application use-case implementation. |
| Engine execution service | `app/engine/execution_service.py` | Active delegated runtime lifecycle implementation. |
| Execution context | `app/application/execution/execution_context.py` | Dispatcher currently uses this duplicate context. |
| Dataset service | `app/services/dataset/dataset_service.py` | Registered V2 dataset route consumes legacy service path. |
| Learning | `app/services/learning/*`, `app/services/learning_engine.py` | Parallel learning implementations. |
| AI decision | `app/services/ai/ai_decision_engine.py` | Parallel decision surface used by API paths. |
| Event publication | `app/engine/execution_events.py` | Separate publisher from `app/events.EventBus`. |

## Architecture exceptions and removal gates

Current exceptions are recorded in `DECISION_LOG.md` as unresolved ADRs. Transition components remain supported until all of the following are evidenced:

1. No registered route or static consumer depends on the component.
2. Canonical replacement has behavioral-equivalence coverage.
3. Import/public API compatibility has been verified or explicitly versioned.
4. Persistence, event, and error behavior are verified where applicable.
5. The relevant ADR has an accepted deprecation/removal decision.

## Accepted ADR items

- ADR-011 — Official ExecutionService public facade and layer ownership.
- ADR-012 — Engine ExecutionContext and ExecutionState authority. The application context remains a transition request-context representation.
- ADR-018 — Workflow and runtime dispatch contract. WorkflowEngine dispatch is approved but not yet implemented; ExecutionOrchestrator remains the runtime owner.
- ADR-019 — Execution contract field, stage, identity and time standard. Runtime state and processing stage are separate; contract implementation is batched.
- ADR-020 — Product Levels, Workflow Intent Types and Dynamic Operational Plan Outputs. Runtime/code alignment pending.

## Unresolved ADR items

- ADR-013 — Legacy WorkflowEngine compatibility strategy.
- ADR-014 — Decision Intelligence persistence ownership.
- ADR-015 — Event publication authority.
- ADR-016 — V2 route ownership and registration strategy.
- ADR-017 — Missing ExportPipeline decision.

## Revision — Product Architecture Phase 1

| Conceptual component | Product architecture role |
|---|---|
| Standalone Analysis | Level 1 product flow for one independently requested analysis. |
| Business Workflow | Level 2 product flow that orchestrates multiple analyses into an operational plan. |
| Forecast Business Workflow | Business Workflow that produces a Dynamic Demand Plan. |
| Safety Stock Business Workflow | Business Workflow that produces a Dynamic Inventory Plan. |
| Dynamic Operational Plan | Final operational output of every Business Workflow. |
| External Intelligence | Automatically collected external information feeding learning and parameter optimization. |
| AI Parameter Optimizer | AI component that optimizes deterministic-analysis parameters without replacing deterministic calculation. |
| AI Artifact | AI-produced explanation artifact; for Standalone Analysis it is the only AI output. |

## ADR-020 product architecture registration

| Component or concept | Approved role | Alignment status |
|---|---|---|
| Level 1 — Standalone Analysis | Free / Entry Level experience for one selected analytical capability, followed by Learning and an AI Explanation Artifact. | Runtime/code alignment pending |
| Level 2 — Business Workflow | Operational-plan experience that orchestrates ordered capabilities, Learning, Decision Intelligence, a Dynamic Operational Plan, and a final AI Artifact. | Runtime/code alignment pending |
| Capability Intent | Execution intent identifying exactly one selected standalone analytical capability. | Runtime/code alignment pending |
| Business Objective Intent | Execution intent identifying exactly one Business Workflow objective. | Runtime/code alignment pending |
| Forecast Business Workflow | Validation → Forecast → Simulation → Backtest → Learning → Decision Intelligence → Dynamic Demand Plan → AI Artifact. | Runtime/code alignment pending |
| Safety Stock Business Workflow | Validation → Forecast → Safety Stock → Simulation → Backtest → Learning → Decision Intelligence → Dynamic Inventory Plan → AI Artifact. | Runtime/code alignment pending |
| Dynamic Demand Plan | Approved named Dynamic Operational Plan for Forecast Business Workflow. | Runtime/code alignment pending |
| Dynamic Inventory Plan | Approved named Dynamic Operational Plan for Safety Stock Business Workflow. | Runtime/code alignment pending |

## Documents 01–07 Product Architecture Phase 1 revisions

**COMPLETED — BINDING**

Each authoritative architecture specification document now contains its bounded Product Architecture Phase 1 revision with ADR-020 reference. Runtime/code alignment remains pending.

## Phase 2 capability-execution governance

## Phase 3A3 cross-process Business Workflow recovery

| Recovery evidence | Status |
|---|---|
| Business Workflow Cross-Process Recovery | DEVELOPMENT VERIFIED |
| PostgreSQL Authoritative Recovery | VERIFIED |
| Recovery after Forecast | VERIFIED |
| Recovery after Safety Stock | VERIFIED |
| Recovery after Simulation | VERIFIED |
| Completed Workflow Re-entry Protection | VERIFIED |
| Duplicate Result Protection | VERIFIED |
| Expired Lease Recovery | DOCUMENTED GAP — Business Workflow tasks are accepted with `max_attempts=1`; a retry-policy phase is required before reclaim can occur. |
| Failure Propagation | PENDING 3A4 |
| Workflow Aggregation | PENDING 3A5 |

## Phase 3A4 Business Workflow failure propagation

| Failure evidence | Status |
|---|---|
| Business Workflow Failure Propagation | DEVELOPMENT VERIFIED |
| Forecast Failure Downstream Blocking | VERIFIED |
| Safety Stock Failure Downstream Blocking | VERIFIED |
| Simulation Required-Task Failure | VERIFIED |
| Backtest Failure | VERIFIED |
| Terminal Failed Re-entry Protection | VERIFIED |
| Automatic Retry | NOT IMPLEMENTED |
| Expired Lease Retry Policy | OPEN GAP |
| Workflow Aggregation | PENDING 3A5 |

## Phase 3A5 Business Workflow result aggregation

| Aggregation evidence | Status |
|---|---|
| Business Workflow Result Aggregation | DEVELOPMENT VERIFIED |
| Four Task-Level Results | PRESERVED / IMMUTABLE |
| Execution-Level Aggregate Result | VERIFIED |
| Aggregate Idempotency | VERIFIED |
| Fresh-Process Aggregate Retrieval | VERIFIED |
| Failed/Partial Workflow Aggregation | PROHIBITED / VERIFIED |
| Learning | NOT INVOKED |
| Decision Intelligence | NOT INVOKED |
| Next | PHASE 3AA — ACTUALS + FORECAST VINTAGE + EVALUATION ARCHITECTURE |

## Phase 3AA2 canonical actual weekly observation and revision ledger

| Actual-data evidence | Status |
|---|---|
| Canonical Weekly Actual | BINDING / DEVELOPMENT VERIFIED |
| Current Actual Identity | `(company, material_code, period, demand_type)` |
| Actual Revision Ledger | APPEND-ONLY / VERIFIED |
| Identical Reupload | IDEMPOTENT |
| Historical Correction | APPROVAL REQUIRED |
| Dataset Blob | PRESERVED AS SOURCE EVIDENCE |
| Forecast Vintage | PENDING 3AA3 |
| Evaluation | PENDING |

## Phase 3AA3 Forecast Vintage and target-period persistence

| Vintage evidence | Status |
|---|---|
| Forecast Vintage | IMMUTABLE / DEVELOPMENT VERIFIED |
| Target Period Identity | CANONICAL YYYY-Www / VERIFIED |
| Forecast Availability | VALIDATED RESULT PERSISTENCE TIME |
| Input Cutoff Period | IMMUTABLE PROVENANCE |
| RuntimeResultReference | PRESERVED AS RAW FORECAST RESULT |
| Learning Score Snapshot | SCHEMA READY / NOT YET ACTIVATED |
| Effective Forecast Timeline | DERIVED / DEVELOPMENT VERIFIED |
| Timeline Selection | LATEST ELIGIBLE VINTAGE |
| Timeline Eligibility | `forecast_available_at < target_period_start` |
| Hindsight Use | PROHIBITED |
| Timeline Actual Data | NOT REQUIRED |
| Forecast Evaluation | DEVELOPMENT VERIFIED |
| Forecast Selection Authority | EFFECTIVE FORECAST TIMELINE |
| Evaluation Actual Authority | CANONICAL ACCEPTED ACTUAL |
| Primary Error Metric | WAPE |
| Bias Convention | `actual - forecast` |
| Supporting Metrics | MAE / RMSE / sMAPE |
| MAPE | NOT PRIMARY |
| Learning Score | SNAPSHOT CARRIED / NO CAUSAL CLAIM |
| Actual Correction | REEVALUATION SUPPORTED |
| Product-Level Evaluation | Mamul / Yari Mamul / Hammadde |
| Event Evaluation | PENDING |
| Learning Integration | PENDING |
| Forecast Performance History | DERIVED / DEVELOPMENT VERIFIED |
| Learning Evidence Boundary | COMPLETE / IMMUTABLE / IDEMPOTENT |
| Canonical Learning Evidence | IMMUTABLE / IDEMPOTENT / TENANT-SCOPED |
| Pattern Intelligence Calculation | POSTGRESQL VERIFIED / READ-ONLY |
| Pattern Learning Memory | DURABLE CURRENT PROJECTION / POSTGRESQL VERIFIED |
| Pattern Memory Refresh | INCREMENTAL / SCOPE-BASED / POSTGRESQL VERIFIED |
| Company Learning Memory V2 | DURABLE COMPANY CURRENT PROJECTION / POSTGRESQL VERIFIED |
| Company Learning Refresh | INCREMENTAL / COMPANY-SCOPED / POSTGRESQL VERIFIED |
| Learning Refresh Orchestrator | CALLABLE / EVIDENCE-ROUTED / POSTGRESQL VERIFIED |
| Learning Evidence Delivery | DURABLE / LEASED / POSTGRESQL VERIFIED |
| Learning Delivery Worker | LEASED / BOUNDED / POSTGRESQL VERIFIED |
| Performance Source Authority | FORECAST EVALUATION |
| Sample Strength | EXPLICIT SAMPLE / PERIOD COVERAGE |
| Historical Learning Score | SNAPSHOT ONLY / NO CAUSAL CLAIM |
| Retraining | NOT ACTIVE |
| Champion-Challenger | NOT ACTIVE |
| Event Learning | PENDING |
| Optional Supplier Business Branch | DEVELOPMENT VERIFIED |
| Supplier Absent | GRACEFUL DEGRADATION VERIFIED |
| Supplier Present | REAL EXECUTION VERIFIED |
| Supplier Product Level | NOT RAW-MATERIAL-ONLY |
| Four-Task Business Workflow | PRESERVED |
| Five-Task Business Workflow | VERIFIED |
| Supplier Branch Learning | NOT INVOKED |
| Supplier Delivery Observation Ledger | CANONICAL OBSERVED AUTHORITY / POSTGRESQL VERIFIED |
| Supplier Learning Calculation | DETERMINISTIC / READ-ONLY / POSTGRESQL VERIFIED |
| Supplier Learning Memory | DURABLE CURRENT PROJECTION / POSTGRESQL VERIFIED |
| Supplier Learning Refresh / Delivery | INCREMENTAL EXACT-SCOPE / POSTGRESQL VERIFIED |
| Supplier Learning Enrichment | READ-ONLY / OPTIONAL / SAFETY-STOCK-NON-IMPACT VERIFIED |
| Canonical Event Observation Ledger | EVENT AUTHORITY / POSTGRESQL VERIFIED |
| Event Intelligence Association Calculation | DETERMINISTIC / READ-ONLY / CUTOFF-SAFE / POSTGRESQL VERIFIED |
| Event Intelligence Memory | DURABLE CURRENT PROJECTION / POSTGRESQL VERIFIED |
| Event LearningEvidence Delivery | ATOMIC / BOUNDED EVENT-ONLY ROUTING / POSTGRESQL VERIFIED |
| Event Forecast / Simulation Enrichment | READ-ONLY / OPTIONAL / NUMERICAL-NON-IMPACT VERIFIED |

## Phase 3C1 Retraining Eligibility

| Eligibility evidence | Status |
|---|---|
| Retraining Eligibility | POSTGRESQL VERIFIED / READ-ONLY |
| Tier 0 | Stable performance + no new evaluation watermark / VERIFIED |
| Tier 1 | Stable performance + new evaluation watermark / VERIFIED |
| Tier 2 | Drift analysis / VERIFIED |
| Tier 3 | Retrain eligible only / VERIFIED |
| Tier-3 Training Bridge | Explicit Challenger Training only / VERIFIED |
| Lower-tier Training | BLOCKED / ZERO FIT |
| Watermark Ownership | Caller / future Learning scheduler |
| Company / Material / Demand Isolation | VERIFIED |
| Historical Window | LEAKAGE-SAFE / VERIFIED |
| Accepted Actual Correction | REFLECTED THROUGH FORECAST EVALUATION |
| Rejected Actual Correction | IGNORED |
| Automatic Retraining / Promotion | NOT ACTIVE |

## Phase 3C4B1 Durable Retraining Job

| Retraining-job evidence | Status |
|---|---|
| Retraining Job | DURABLE / POSTGRESQL VERIFIED |
| Candidate Fingerprint | CORRECTION-SAFE / VERIFIED |
| Duplicate Guard | PostgreSQL unique company/candidate fingerprint / VERIFIED |
| Processed Evidence Ownership | Retraining Job |
| Tier 3 | MAY CREATE PENDING JOB |
| Tier 0 / 1 / 2 | NO JOB |
| Runtime Execution Link | DEFERRED TO 3C4B2 |
| Training / Artifact Persistence | NOT ACTIVE |
| Automatic Comparison / Promotion | NOT ACTIVE |

## Phase 3C4B2 Explicit Retraining Job Execution

| Retraining execution evidence | Status |
|---|---|
| Retraining Job Execution | EXPLICIT / DEVELOPMENT VERIFIED |
| Training Runtime | LEASED / PostgreSQL VERIFIED |
| Duplicate Start Guard | PostgreSQL row lock / VERIFIED |
| Worker Claim | EXCLUSIVE / VERIFIED |
| Retry Policy | BOUNDED / 2 attempts |
| Tier-3 Job | MAY TRAIN |
| Trained Job | Immutable ModelArtifact linked / VERIFIED |
| Automatic Scan | NOT ACTIVE |
| Automatic Comparison / Promotion | NOT ACTIVE |
| Production Forecast | UNCHANGED |

## Phase 3C4B3 Retraining Artifact Race Recovery

| Retraining recovery evidence | Status |
|---|---|
| Retraining Retry | BOUNDED / VERIFIED |
| Lease Expiry Recovery | VERIFIED |
| Stale Worker Completion | REJECTED / VERIFIED |
| Artifact Race | IDEMPOTENT / VERIFIED |
| Artifact Post-Persist Recovery | VERIFIED |
| Terminal Re-entry | IDEMPOTENT / VERIFIED |
| Automatic Scan / Enqueue | NOT ACTIVE |
| Automatic Comparison / Promotion | NOT ACTIVE |
| Production Forecast | UNCHANGED |

## Phase 3C4B4 Retraining Cooldown, Priority, and Admission

| Retraining scheduling control | Status |
|---|---|
| Retraining Cooldown | VERSIONED / DURABLE |
| New Evidence During Cooldown | PRESERVED / DEFERRED |
| Retraining Priority | DETERMINISTIC / VERSIONED |
| Retraining Resource Admission | POSTGRESQL-BACKED / VERIFIED |
| Global Retraining Capacity | CONFIGURABLE |
| Production Analysis | NOT BLOCKED BY RETRAINING GUARD |
| Automatic Scanner | NOT ACTIVE |
| Automatic Comparison / Promotion | NOT ACTIVE |

## Phase 3C4B5A Retraining Scanner Discovery

| Scanner discovery control | Status |
|---|---|
| Retraining Scanner Discovery | DEVELOPMENT VERIFIED |
| Scanner Scope | COMPANY + PERIOD BOUNDED |
| Tier 0 / 1 / 2 | NO JOB |
| Tier 3 | DURABLE JOB ACCEPTANCE ONLY |
| Repeated Scan | IDEMPOTENT |
| Concurrent Scan | POSTGRESQL SAFE |
| Training | NOT STARTED BY SCANNER |
| Resource Admission | NOT ACQUIRED IN DISCOVERY |
| Periodic Activation | NOT ACTIVE |
| Automatic Promotion | NOT ACTIVE |

## Phase 3C4B5B Controlled Scanner Activation

| Scanner activation control | Status |
|---|---|
| Scanner Discovery | READ-ONLY FOR RUNTIME |
| Controlled Scanner Activation | EXPLICIT / VERIFIED |
| Cooldown | ENFORCED |
| Priority | ENFORCED |
| Resource Admission | ENFORCED |
| Capacity Block | NO TRAINING |
| Repeated Activation | IDEMPOTENT |
| Periodic Scheduler | NOT ACTIVE |
| Automatic Promotion | NOT ACTIVE |

## Phase 3C4B5C1 Periodic Scanner Tick Safety

| Scheduler tick control | Status |
|---|---|
| Periodic Tick Owner | POSTGRESQL DURABLE / VERIFIED |
| Tick Identity | COMPANY + WINDOW + POLICY + CADENCE BUCKET |
| Duplicate / Concurrent Tick | IDEMPOTENT / POSTGRESQL SAFE |
| Failed Tick | AUDITED / NEXT BUCKET AVAILABLE |
| Scheduler Loop / Cron | NOT ACTIVE |
| Automatic Promotion | NOT ACTIVE |

## Phase 3C4 Selective Retraining Orchestration Closeout

| Selective retraining orchestration | Status |
|---|---|
| Orchestration | DEVELOPMENT VERIFIED |
| Periodic Scheduler Logic | DURABLE / IDEMPOTENT |
| New Evidence | CORRECTION-SAFE |
| Cooldown / Priority / Capacity | ENFORCED |
| Leased Worker | VERIFIED |
| Model Artifact | IMMUTABLE / IDEMPOTENT |
| Business Workflow | NOT BLOCKED |
| Deployment Timer | NOT CONFIGURED IN REPOSITORY |
| Automatic Champion Comparison / Promotion | NOT ACTIVE |

## Phase 3C2B1 XGBoost weekly feature builder

| Feature evidence | Status |
|---|---|
| XGBoost Weekly Feature Builder | DEVELOPMENT VERIFIED |
| Feature Schema | `xgboost_weekly_v1` |
| Training Evidence Authority | Canonical accepted Actual Weekly Observations only |
| Cutoff Leakage Protection | VERIFIED |
| Product Levels | `finished_good` / `semi_finished_good` / `raw_material` VERIFIED |
| Demand Types | ISOLATED / VERIFIED |
| ISO W53 and Year Boundary | VERIFIED |
| XGBoost Training | NOT YET ACTIVE |

## Phase 3C2B2 XGBoost Challenger training

| Challenger evidence | Status |
|---|---|
| XGBoost Challenger Training | DEVELOPMENT VERIFIED |
| Production Forecast | UNCHANGED |
| Feature Schema | `xgboost_weekly_v1` |
| Split Policy | TIME ORDERED / `time_ordered_holdout_v1` |
| Future Leakage | PROHIBITED / VERIFIED |
| Automatic Retraining | NOT ACTIVE |
| Artifact Persistence | PENDING |
| Champion-Challenger Governance | PENDING 3C3 |
| Tier-3 Full PostgreSQL Trigger | VERIFIED / EXPLICIT TRAINING ONLY |

## Phase 3C2B3 immutable Challenger model artifacts

| Artifact evidence | Status |
|---|---|
| XGBoost Challenger Training | VERIFIED |
| Immutable Model Artifact | VERIFIED |
| Artifact Checksum | SHA-256 VERIFIED |
| Tenant Isolation | VERIFIED |
| Artifact History | APPEND-ONLY / IMMUTABLE |
| Production Forecast | UNCHANGED |
| Automatic Retraining | NOT ACTIVE |
| Champion-Challenger Governance | PENDING 3C3 |
| Tier-3 Full PostgreSQL Trigger | VERIFIED / EXPLICIT TRAINING ONLY |

## Phase 3C3A Champion--Challenger decision evidence

| Decision evidence | Status |
|---|---|
| Champion--Challenger Evaluation | DEVELOPMENT VERIFIED |
| Comparison Window | SAME OUT-OF-SAMPLE WINDOW / VERIFIED |
| Policy | `champion_challenger_policy_v1` |
| Primary Metric | WAPE |
| Guardrails | Bias / MAE / RMSE / sample strength VERIFIED |
| Decisions | IMMUTABLE / APPEND-ONLY / IDEMPOTENT |
| Artifact Integrity and Tenant Isolation | VERIFIED |
| Promotion Execution | NOT ACTIVE |
| XGBoost Fit During Comparison | ZERO |
| Production Forecast | UNCHANGED |
| Full Tier-3 Trigger | VERIFIED / EXPLICIT TRAINING ONLY |

## Phase 3C3B1A Champion Registry foundation

| Registry evidence | Status |
|---|---|
| Champion Registry | DEVELOPMENT VERIFIED |
| Registry Identity | company + material + demand type |
| Initial Champion | `classical_existing` / `demand_forecaster_auto_v1` |
| Registry History | IMMUTABLE |
| Current Pointer | MUTABLE / PostgreSQL protected |
| Promotion / Rollback / Forecast Resolution | NOT ACTIVE |
| Automatic Retraining / Promotion | NOT ACTIVE; PHASE 3C1 verified |
| Controlled Challenger Promotion | DEVELOPMENT VERIFIED / PROMOTE_CHALLENGER authority only |
| Promotion Safety | PostgreSQL atomicity, stale protection, same/competing concurrency, integrity, tenant and demand isolation VERIFIED |
| Forecast / Business Workflow Activation | NOT ACTIVE / unchanged |
| Rollback | PENDING 3C3B3 |

## Phase 3C3B3A Champion Resolver

| Resolver evidence | Status |
|---|---|
| Champion Resolver | DEVELOPMENT VERIFIED / READ-ONLY |
| Classical and XGBoost Resolution | VERIFIED |
| Integrity, Missing, and Compatibility Fallback | VERIFIED |
| No Classical Fallback | CONTROLLED FAILURE VERIFIED |
| Tenant and Demand-Type Isolation | VERIFIED |
| Registry Mutation During Fallback | PROHIBITED / VERIFIED |
| Production Forecast Integration | NOT ACTIVE |
| Rollback | PENDING 3C3B3B |
| Automatic Retraining / Promotion | NOT ACTIVE; PHASE 3C1 verified |

## Phase 3C2B4 Business Workflow execution safety

| Execution safety decision | Status |
|---|---|
| One active Business Workflow per company | POSTGRESQL VERIFIED |
| Authoritative guard | PostgreSQL partial unique active-workflow index / VERIFIED |
| Duplicate behavior | Resolve existing active execution as `ALREADY_RUNNING` / VERIFIED |
| Standalone analyses | UNCHANGED / OUT OF SCOPE |
| PostgreSQL concurrency proof | VERIFIED |
| Optional Supplier Business Branch | DEVELOPMENT VERIFIED |
| Supplier Absent | GRACEFUL DEGRADATION VERIFIED |
| Supplier Present | REAL EXECUTION VERIFIED |
| Supplier Product Level | NOT RAW-MATERIAL-ONLY |
| Four-Task Business Workflow | PRESERVED |
| Five-Task Business Workflow | VERIFIED |
| Supplier Branch Learning | NOT INVOKED |

| ADR | Decision | Status |
|---|---|---|
| ADR-021 | Dedicated CapabilityExecutor boundary | Accepted |
| ADR-022 | PostgreSQL Durable Runtime Store authority | Accepted; implementation deferred to Phase 2C |
| ADR-023 | Queue and worker target/transition strategy | Accepted; technology and runtime deferred |
| ADR-024 | Versioned capability request/result and explicit data passing | Accepted |
| ADR-025 | Execution Group / Task Group / SKU Task merge model | Accepted; implementation deferred to Phase 2G |
| ADR-026 | Separate downstream product-pipeline handoff | Accepted; implementation deferred to Phase 2F |
| ADR-027 | Capability failure and error-result policy | Accepted |
| ADR-028 | User-facing execution notice language | Accepted |
| ADR-033 | Alembic migration authority and managed-schema ownership | Accepted |

## Phase 2C migration governance

## Phase 2C-M0 implementation status

| Component | Status |
|---|---|
| Alembic tooling | IMPLEMENTED — BASELINE STAMPED AT `20260806_01` ON THE DEVELOPMENT NEON DATABASE |
| Managed PostgreSQL startup schema mutation | DISABLED |
| Schema readiness | IMPLEMENTED |
| Legacy schema baseline | ACTIVE — `20260806_01` STAMPED WITHOUT BASELINE DDL OR DML |
| Unversioned managed-schema transition flag | INACTIVE — RETAINED TRANSITION COMPATIBILITY; NOT ENABLED FOR THE BASELINE STAMP |

| Component | Approved status |
|---|---|
| Managed PostgreSQL schema authority | Alembic only — bootstrap pending |
| Startup schema mutation | Prohibited for managed PostgreSQL — implementation pending |
| Existing schema baseline | Required before additive runtime migration |
| Legacy schema scripts | Retained transition evidence; prohibited for new managed PostgreSQL DDL |

## Phase 2C-M1 durable runtime governance

| Decision / state | Status |
|---|---|
| ADR-029 — Canonical runtime entity model | ACCEPTED — IMPLEMENTATION PENDING |
| ADR-030 — RuntimeStore ownership | ACCEPTED — IMPLEMENTATION PENDING |
| ADR-031 — Claim / lease / idempotency model | ACCEPTED — IMPLEMENTATION PENDING |
| ADR-032 — Result reference policy | ACCEPTED — IMPLEMENTATION PENDING |
| Alembic development Neon baseline | CURRENT — `20260806_01` |
| Runtime tables | NOT YET CREATED |
| Runtime ORM models | IMPLEMENTED — NOT YET CONSUMED |
| Runtime migration | AUTHORED — HEAD `20260807_01` — STRUCTURALLY VERIFIED; LIVE/ISOLATED APPLY TEST PENDING |
| Development Neon | CURRENT REVISION `20260806_01` — MIGRATION NOT YET APPLIED |

## Phase 2C durable runtime verification

| Component | Status |
|---|---|
| Phase 2C Durable Runtime | COMPLETE |
| PostgreSQL RuntimeStore | VERIFIED |
| Fresh-Session Recovery | VERIFIED |
| Claim / Lease / Attempt | VERIFIED |
| Completion / Failure | VERIFIED |
| Checkpoint / Progress | VERIFIED |
| Optimistic Concurrency | VERIFIED |
| Cancellation / Terminal Protection | VERIFIED |
| Tenant Isolation | VERIFIED |
| Runtime Result Scope | VERIFIED |
| Development Probe Cleanup | VERIFIED — ZERO RESIDUE |
| Distributed Queue/Worker | NOT YET IMPLEMENTED |
| Real Capability Execution | NEXT |

## Phase 2E Safety Stock vertical slice

| Component | Status |
|---|---|
| Standalone Safety Stock Durable Execution | DEVELOPMENT VERIFIED |
| Real Safety Stock Engine | CONNECTED |
| Safety Stock Multi-Method Behavior | PRESERVED â€” classic, Croston, Syntetos-Boylan, bootstrapping, ML-based, hybrid |
| Automatic Method Selection | GAP â€” existing endpoint path selects `hybrid_ss`; no dynamic winner selector exists |
| Service Level | SYSTEM DEFAULT WITH MANUAL OVERRIDE |
| Supplier Dependency | OPTIONAL ENRICHMENT |
| Fresh-Process Status/Result | VERIFIED |
| Learning | NOT INVOKED |
| Decision Intelligence | NOT INVOKED |

## Phase 3D5 Business Decision Plan

| Contract | Status |
|---|---|
| Analytical Business Workflow authority | VERIFIED — completion precedes Decision support |
| Dynamic Operational Plan | DERIVED / READ-ONLY |
| DecisionSnapshot | DURABLE PER-SKU AUTHORITY |
| Decision failure isolation | VERIFIED — completed analytics remain unchanged |
| Per-SKU limitation and retry | VERIFIED — no global Decision transaction |
| Autonomous action / ERP / LLM | NOT ACTIVE |

## Phase 3D6 User Explanation and Feedback

| Boundary | Contract |
|---|---|
| DecisionSnapshot | Historical decision authority. |
| Structured explanation | Deterministic, read-only presentation context reconstructed only from immutable Snapshot/Candidate/frozen provenance. |
| LLM | Optional narrative translator only; it has no decision, metric, confidence, causality, or action authority. |
| Feedback | Immutable user-opinion audit evidence, not correctness truth and not approval. |
| Learning from feedback | Deferred to a future explicitly versioned policy. Execution/ERP actions remain inactive. |

## FU-F6A-R1 Post-analytics Decision finalization

| Boundary | Contract |
|---|---|
| Analytical completion | `RuntimeExecution.completed` and its validated `business_workflow` aggregate remain the analytical authority. |
| Decision finalization | `BusinessWorkflowDecisionFinalization` is mutable, leased advisory lifecycle state created only after the analytical commit. |
| Failure/retry | A Decision failure cannot invalidate analytics; pending, failed, partial, and expired work is recoverable from PostgreSQL without rerunning analytical tasks. |
| Task graph | Decision finalization is not a RuntimeTask. |
| Historical provenance | `DecisionSnapshot` remains immutable authority; execution-to-Snapshot association is explicitly deferred to FU-F6A-R2. |

## Phase 3D7 Production Authority Hardening

| Boundary | Contract |
|---|---|
| Canonical Decision authority | Exclusive: Resolver → Policy → immutable Snapshot. |
| Legacy v2 Decision route | Retired from mounted API routing; dormant legacy code is not canonical authority. |
| Feedback retries | PostgreSQL-enforced per-company non-null semantic key; concurrent retries converge. |
| Feedback changes | Immutable superseding events; feedback remains non-authoritative and cannot trigger Learning or actions. |

## Phase 3D Decision Intelligence Closeout

| Boundary | Final contract |
|---|---|
| Authority chain | Analytical results and mutable learned projections feed the cutoff-safe Resolver, deterministic Policy, immutable Snapshot, derived Plan, and Snapshot-only Explanation. |
| Historical boundary | Mutable Pattern/Company/Supplier/Event projections are not historical authority; admitted provenance is frozen in DecisionSnapshot. |
| Feedback | Immutable user opinion/audit evidence; it is database-idempotent, does not express correctness/approval, and does not feed Learning automatically. |
| Operations | LLM has no Decision authority. ERP/action execution is inactive. Decision-stage failures are isolated after analytics completion. |
| Scale | 1-SKU functional proof is verified. 10/50/100/250-SKU benchmarks and any 22,000-SKU claim remain deferred. |

| Phase 2E Capability Dataflow | BINDING â€” validated same-tenant upstream evidence, Simulation no-recompute, and Backtest no-reselection |
| Standalone Simulation Durable Execution | DEVELOPMENT VERIFIED â€” real Monte Carlo, one task, fresh-process retrieval |

## Phase 2B implementation status

## DOCUMENT_05 Capability Design Principles Revision

**COMPLETED — BINDING**

Scientific Foundation; Deterministic First; Capability Continuity; Multi-Method Selection; Explainability; LLM Boundary; and Capability Continuity Gate are binding capability-design references.

| Component | Status |
|---|---|
| Capability technical contracts | IMPLEMENTED — NOT YET CONSUMED |
| User-facing execution notice contract | IMPLEMENTED — APPLICATION MAPPING ONLY — API WIRING PENDING |
| CapabilityExecutor | IMPLEMENTED — CONTROLLED-DOUBLE VERIFIED — PRODUCTION WIRING PENDING |
