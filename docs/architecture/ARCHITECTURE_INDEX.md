# Stokonomi Architecture Index

## Governance status

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

## Phase 2B implementation status

## DOCUMENT_05 Capability Design Principles Revision

**COMPLETED — BINDING**

Scientific Foundation; Deterministic First; Capability Continuity; Multi-Method Selection; Explainability; LLM Boundary; and Capability Continuity Gate are binding capability-design references.

| Component | Status |
|---|---|
| Capability technical contracts | IMPLEMENTED — NOT YET CONSUMED |
| User-facing execution notice contract | IMPLEMENTED — APPLICATION MAPPING ONLY — API WIRING PENDING |
| CapabilityExecutor | IMPLEMENTED — CONTROLLED-DOUBLE VERIFIED — PRODUCTION WIRING PENDING |
