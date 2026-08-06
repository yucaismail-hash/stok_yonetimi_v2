# Stokonomi Architecture Glossary

| Term | Established meaning | Status |
|---|---|---|
| Business Objective | A business-facing requested outcome that determines workflow selection rather than directly selecting analytical engines. | Established |
| Capability | A registered analytical ability available to the execution flow. | Established |
| Workflow | An ordered/dependency-aware plan of work for a business objective or analysis. | Established |
| Workflow Dispatcher | The application-to-workflow dispatch boundary. It forwards validated execution requests and does not own runtime execution. | Established |
| Workflow Engine | The canonical workflow planner and asynchronous execution-entry coordinator at `app/engine/workflow_engine.py`. Its dispatch contract is APPROVED — NOT YET IMPLEMENTED. | Established |
| Execution Orchestrator | The runtime coordinator responsible for executing the accepted workflow plan, including scheduler, workers, and result collection. | Established |
| Execution Context | The authoritative engine-owned runtime context at `app/engine/execution_context.py`. The application context remains transition request-context representation only. | Accepted; consumer migration pending |
| Execution State | The authoritative engine runtime-state vocabulary at `app/engine/enums.py`. | Accepted; API/application mapping pending |
| Execution Service | The official public execution facade at `app/services/execution/execution_service.py`. It delegates execution use cases to the Application Layer and does not own runtime lifecycle, capability execution, persistence, Learning, Decision Intelligence, or Artifact responsibilities. | APPROVED — NOT YET IMPLEMENTED |
| Execution Group | A grouped execution construct required by execution architecture. | CONCEPTUAL / FUTURE COMPONENT |
| Task Group | A grouped task construct required by execution architecture. | CONCEPTUAL / FUTURE COMPONENT |
| SKU Task | A SKU-scoped execution task construct. | CONCEPTUAL / FUTURE COMPONENT |
| Learning Engine | The canonical learning orchestrator at `app/learning/learning_engine.py`. | Established |
| Company Memory | Company-scoped institutional memory; it is isolated between companies. | Established |
| Pattern Memory | SKU-scoped behavior memory, independent from Company Memory. | Established |
| Decision Intelligence | The layer that produces business decisions from validated inputs and intelligence context. | Established |
| Recommendation | A proposed business action communicated as part of a decision output; it does not independently create a decision. | Established |
| Explainability | Decision explanation content that must not alter the decision. | Established |
| Narrative | Business communication derived from decision output; it must not change business logic. | Established |
| AI Artifact | The standardized deliverable created only after a completed Decision. | Established |
| Repository | The data-access layer; it does not own workflow or AI calculation. | Established |
| Application Service | Application-layer use-case coordinator for validation, handlers, workflows, transactions, and responses. | Established |
| Canonical Component | A component at an official architecture path designated by Documents 01–07 or accepted architecture decisions. | Established |
| Transition Component | A currently retained parallel, duplicate, or compatibility component pending proven alignment. | Established |
| Legacy Component | A retained earlier implementation not selected as the canonical target. | Established |
| Architecture Exception | A confirmed deviation from the official architecture that is tracked until resolved by an ADR and alignment phase. | Established |
| ADR | Architecture Decision Record: a dated decision with context, consequences, status, and affected components. | Established |
| Removal Gate | The evidence threshold required before a transition or legacy component can be deprecated or removed. | Established |
| Behavioral Equivalence | Evidence that canonical and transition paths have equivalent observable contracts, outputs, errors, side effects, and relevant persistence/event behavior. | Established |
| Graceful Degradation | A controlled failure or reduced-service behavior that preserves defined contracts and does not bypass architectural boundaries. | Established |
| Runtime Store | Live, non-durable execution state used for progress, worker, retry, and checkpoint tracking. | Established ownership model |
| Runtime State | The execution lifecycle vocabulary governed by `app.engine.enums.ExecutionState`: created, queued, running, waiting, retrying, completed, failed, or cancelled. | Accepted |
| Processing Stage | The current engine processing step, separate from Runtime State: validation, planning, forecast, safety_stock, supplier, simulation, backtest, or completed. | Accepted |
| Downstream Pipeline | Learning, Decision Intelligence, and Artifact processing that follows engine execution; it is not an engine runtime state or processing stage. | Accepted |
| Timezone-aware UTC | The timestamp standard for new execution contracts: aware UTC datetimes internally and ISO-8601 values normalized with `Z` at public boundaries. | Accepted |
| First-class Field | A contract field represented explicitly rather than hidden within generic metadata. | Accepted |
| Contract Version | The explicit compatibility version carried by execution boundary contracts; initial value is `1.0.0`. | Accepted |
| WorkflowDispatchRequest | Frozen versioned request contract forwarded from WorkflowDispatcher to WorkflowEngine. | APPROVED — NOT YET IMPLEMENTED |
| WorkflowDispatchResult | Frozen acceptance contract returned after workflow runtime acceptance. | APPROVED — NOT YET IMPLEMENTED |
| ExecutionStatusSnapshot | Frozen runtime status retrieval contract. | APPROVED — NOT YET IMPLEMENTED |
| ExecutionResultEnvelope | Frozen completed execution result retrieval contract. | APPROVED — NOT YET IMPLEMENTED |

## Revision — Product Architecture Phase 1

| Term | Definition | Status |
|---|---|---|
| Standalone Analysis | A Level 1 user-requested execution of exactly one analysis: Forecast, Safety Stock, Simulation, Backtest, or Supplier. Learning is enabled, Decision Intelligence is disabled, and AI produces an analysis explanation as an AI Artifact. | Approved product concept |
| Business Workflow | A Level 2 operational flow that orchestrates multiple analyses and produces a Dynamic Operational Plan; it is not itself an analysis. | Approved product concept |
| Dynamic Operational Plan | The final operational output of every Business Workflow. | Approved product concept |
| Forecast Business Workflow | The Business Workflow product flow Validation → Forecast → Simulation → Backtest → Learning → Decision Intelligence → Dynamic Demand Plan → AI Artifact. | Approved product concept |
| Safety Stock Business Workflow | The Business Workflow product flow Validation → Forecast → Safety Stock → Simulation → Backtest → Learning → Decision Intelligence → Dynamic Inventory Plan → AI Artifact; Supplier Allocation follows the Dynamic Inventory Plan when supplier data exists. | Approved product concept |
| AI Artifact | An AI-produced explanation artifact. It is the analysis explanation for a Standalone Analysis and follows the operational plan in a Business Workflow. | Approved product concept |
| External Intelligence | Automatically collected information such as macroeconomic, calendar, weather, trend, and sector data that flows through Company Learning and Pattern Intelligence to the AI Parameter Optimizer. | Approved product concept |
| AI Parameter Optimizer | AI function that optimizes parameters for deterministic analysis without replacing deterministic calculations. | Approved product concept |

## Phase 2 capability-execution terms

| Term | Definition | Status |
|---|---|---|
| Capability Execution Request | Frozen, versioned engine contract that carries one validated capability-attempt input. | Accepted — ADR-024 |
| Capability Execution Result | Frozen, versioned engine contract describing a completed or failed capability attempt. | Accepted — ADR-024, ADR-027 |
| Capability Execution Error | Structured, non-sensitive technical failure metadata with code, category, retryability, timestamp, and details. | Accepted — ADR-027 |
| Capability Executor | Canonical deterministic-capability invocation boundary, independent of planning, queues, persistence, and downstream processing. | Accepted — ADR-021 |
| User Execution Notice | Pure application-owned, non-HTTP user notification derived from technical error metadata. | Accepted — ADR-028 |
| Durable Runtime Store | PostgreSQL authority for durable execution and task lifecycle evidence; implementation deferred. | Accepted — ADR-022 |

## ADR-020 glossary additions

## Phase 2C migration-governance terms

| Term | Definition | Status |
|---|---|---|
| Migration Authority | The sole approved mechanism permitted to mutate managed PostgreSQL schema. | Accepted — ADR-033 |
| Managed PostgreSQL | A non-disposable PostgreSQL environment, including remote Neon, where startup may not implicitly mutate schema. | Accepted — ADR-033 |
| Schema Baseline | A controlled migration-history marker representing the existing live schema without recreating or deleting legacy tables. | Accepted — ADR-033 |
| Disposable Local/Test Database | An explicitly classified local or test database where controlled `create_all` may be permitted. | Accepted — ADR-033 |

| Term | Definition | Status |
|---|---|---|
| Product Level | The approved user-visible product experience level: Level 1 Standalone Analysis or Level 2 Business Workflow. | Accepted — ADR-020 |
| Single Analysis Workflow | A workflow belonging to one Capability Intent that runs exactly one selected analytical capability, may run Learning afterward, excludes Decision Intelligence, and produces an AI Explanation Artifact. | Accepted — ADR-020 |
| Business Objective Workflow | A workflow belonging to one Business Objective Intent that orchestrates its approved ordered capabilities, Learning, Decision Intelligence, a Dynamic Operational Plan, and a final AI Artifact. | Accepted — ADR-020 |
| Execution Intent | The exclusive workflow identity domain expressed by `objective_type XOR analysis_type`. | Accepted — ADR-020 |
| Capability Intent | An Execution Intent identifying exactly one standalone analytical capability. | Accepted — ADR-020 |
| Business Objective Intent | An Execution Intent identifying exactly one Business Workflow objective. | Accepted — ADR-020 |
| Dynamic Demand Plan | The approved Dynamic Operational Plan output of Forecast Business Workflow. | Accepted — ADR-020 |
| Dynamic Inventory Plan | The approved Dynamic Operational Plan output of Safety Stock Business Workflow. | Accepted — ADR-020 |
| AI Explanation Artifact | The analysis-level AI Artifact that explains a Standalone Analysis result without producing an operational decision. | Accepted — ADR-020 |
