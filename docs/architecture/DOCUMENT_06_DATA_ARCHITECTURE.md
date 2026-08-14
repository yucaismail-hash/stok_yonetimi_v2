# STOKONOMI ARCHITECTURE SPECIFICATION v2.0

# DOCUMENT 06

## DATA1 canonical ingestion contract

- Canonical weekly period: `YYYY-Www`; Excel demand input is wide and internal/API demand is normalized long.
- Product hierarchy is Group → optional Class → SKU; demand type is Wizard/dataset metadata.
- `Temel_Veriler` is required. `Malzeme_Tedarikciler`, `Tedarikciler`, and `Events` are optional and validated only when present.
- Events are company-specific, weekly, and group/class scoped; event effect is learned/calculated later and official calendar data is automatic.
- Service level is system-default with manual override. Graceful degradation is binding.

## Phase 3AA2 canonical weekly actual boundary

The encrypted Dataset payload remains source-upload evidence. Accepted operational actual truth is stored separately as normalized weekly observations with identity `(company_id, material_code, period, demand_type)`, where `period` is canonical ISO `YYYY-Www` and demand types may coexist.

Historical changes are append-only revision evidence. A changed value is proposed first and updates current truth only after approval; rejection preserves both current truth and revision evidence. New weekly observations are accepted evidence rather than corrections. Product level, product group, and optional product class are carried with the accepted observation. Forecast vintages and evaluations are intentionally outside this boundary.

## Phase 3AA3 immutable Forecast Vintage boundary

Validated Forecast RuntimeResultReferences remain the raw analytical source. A projectable Forecast result with explicit input cutoff, demand type, and product metadata produces one immutable Vintage header and canonical SKU target-period points. Availability is the durable result persistence timestamp, never request acceptance time. Learning snapshot fields are reserved but inactive; effective timeline selection and evaluation remain later boundaries.

## Phase 3AA4 derived Effective Forecast Timeline boundary

The Effective Forecast Timeline is a read-only derivation over immutable Forecast Vintage headers and points, not a replacement or mutation of them. For each company, material code, canonical target period, and demand type, it selects the latest Vintage point whose `forecast_available_at` is strictly earlier than the ISO target-week start. A Vintage available during or after that week is ineligible, so hindsight use is prohibited.

The projection carries the selected point's forecast, intervals, model, snapshot product level/group/class, durable RuntimeResultReference identity, input cutoff, demand type, and nullable learning score at run. Demand types remain isolated. Actual observations are not required for timeline selection and are reserved for the later Forecast Evaluation boundary. Historical cutoff/target overlap is rejected as malformed evidence rather than silently selected; Forecast Vintages remain immutable.

## Phase 3AA5 durable Forecast-to-Actual evaluation boundary

Evaluation pairs the canonical accepted actual observation with the Phase 3AA4 Effective Forecast Timeline only when both exist for the same company, SKU, ISO target period, and demand type. The selected forecast is never recalculated or replaced. Durable current evaluation points retain actual-observation and accepted-revision provenance, selected Vintage and point provenance, available-at and cutoff evidence, forecast-time product snapshots, nullable learning score at run, and raw point errors.

The binding error convention is `actual - forecast`: positive signed error means under-forecast and negative signed error means over-forecast. WAPE is authoritative; if the absolute-actual denominator is zero it is unavailable with an explicit reason. Bias, MAE, RMSE, and sMAPE are supporting versioned metrics. Forecast Accuracy is only the derived presentation `max(0, 1 - WAPE)` when WAPE exists; MAPE is not primary. Aggregation is available by company, product level, group, class, and SKU without mixing demand types.

Approved actual corrections recompute the current evaluation against accepted truth while preserving immutable forecast evidence; rejected corrections do not change it. Newly arriving actuals create eligible pairs without a forecast rerun. Event evaluation and Learning integration remain pending, and learning-score evidence makes no causal claim.

## Phase 3AA6 derived Forecast Performance History and Learning Evidence boundary

Forecast Performance History is a read-only weekly derivation from verified Forecast Evaluation point evidence. It preserves evaluation metric-contract provenance and source evaluation identities, deduplicates equivalent current evaluation evidence deterministically, and exposes company, product-level, group, class, and SKU scopes without mixing demand types. Each weekly evidence row carries sample count and explicit evaluated-period coverage alongside WAPE, bias, MAE, RMSE, sMAPE, and conditional Forecast Accuracy.

Learning scores are historical Forecast-Vintage snapshots carried through evaluation evidence only. The history preserves distinct available snapshot values and leaves missing values null; it does not calculate a Learning Score or claim causal influence on performance. Because it is derived from current evaluation truth, approved actual corrections and newly evaluated actual arrivals are reflected on the next read without mutating Forecast Vintages or retaining stale materializations.

This boundary prepares evidence for future drift analysis, selective retraining eligibility, and Champion-Challenger comparison only. Retraining, XGBoost fitting, model promotion, Champion-Challenger, Decision Intelligence, and Event Learning are not active.

## Phase 3C5B1 immutable Learning Evidence boundary

`LearningEvidence` is the canonical, immutable, tenant-scoped evidence lineage for future Pattern Intelligence and Company Learning. It is derived only from persisted authoritative Actual, Forecast Evaluation, Champion transition, and terminal RetrainingJob records. The company-scoped semantic SHA-256 fingerprint is the PostgreSQL duplicate guard: repeated observation returns the same evidence contribution, while an accepted Actual correction appends a superseding contribution and a rejected correction creates none. It is never authority for the underlying source fact. Pattern/Company materialization, Learning Score, Forecast integration, and Decision Intelligence remain **NOT ACTIVE**.

Phase 3C5B1 is **COMPLETE**. The canonical terminal `RetrainingJob` source boundary is verified. The separate broad B1 probe runtime timeout is recorded as test-infrastructure debt only; no production RetrainingJob defect has been demonstrated.

## Phase 3C5B2A cutoff-safe Pattern Intelligence calculation

`PatternIntelligenceService` is a deterministic, in-memory, read-only calculation over canonical accepted Actual Weekly Observations with identity `(company, material_code, demand_type, cutoff_period)`. It reports explicit coverage/missing periods, source IDs/fingerprint, CV/CV², zero ratio, ADI, trend, recent change, evidence-quality confidence, and conservative classification. Sparse demand is `INTERMITTENT` when arrivals are regular in nonzero size and `LUMPY` only when both sparse arrivals and variable nonzero sizes are evidenced. Seasonality remains `SEASONALITY_NOT_ESTABLISHED` until a future statistical evidence policy is introduced. Accepted corrections before cutoff are reflected; rejected corrections and post-cutoff Actuals are ignored. Pattern memory persistence, Forecast integration, and Decision Intelligence remain **NOT ACTIVE**.

## Phase 3C5B2B1 durable Pattern Learning Memory

`PatternLearningMemory` is the durable mutable **current projection** of `PatternIntelligenceService`, uniquely keyed by company, material code, and explicit demand type. It stores compact metrics, policy versions, cutoff, source fingerprint, and Learning Evidence IDs; it never stores raw history. Identical source fingerprints are `UNCHANGED`, accepted corrections refresh and increment `row_version`, rejected corrections do not, and an older cutoff returns `STALE_RESULT` rather than overwrite a newer projection. It is optional enrichment only: Forecast integration, Company Learning, Learning Score, and Decision Intelligence remain **NOT ACTIVE**.

## Phase 3C5B2B2 incremental Pattern Memory refresh and recovery

`PatternLearningRefreshService` accepts only an explicit dirty `(company, material_code, demand_type, cutoff_period)` scope and delegates to the existing materializer. It performs no discovery/global rescan. Duplicate, concurrent, post-write retry, and fresh-session delivery converge through the durable current projection fingerprint; a delayed older cutoff returns `STALE_RESULT`. Accepted canonical Actuals and accepted corrections refresh only the specified scope; rejected corrections converge to `UNCHANGED`. Forecast integration, Company Learning, and Decision Intelligence remain **NOT ACTIVE**.

## Phase 3C5B3A Company Learning V2

`CompanyLearningMemoryV2` is the durable mutable current projection keyed only by company. It aggregates compact Pattern Memory, Learning Evidence, Forecast Evaluation, Retraining, and Champion summaries without duplicating raw Actuals. `company_evidence_maturity_v1` is a deterministic 0–100 evidence maturity score based on scope coverage, Pattern/Forecast sample support, persisted-source diversity, and reconstructability; it is not Forecast accuracy, business performance, causal confidence, or user trust. Identical source summaries are `UNCHANGED`; source changes update once, concurrent writers converge, and a stale semantic snapshot cannot overwrite a newer projection. First use remains fully usable with score 0. Forecast integration, Supplier/Event Learning, and Decision Intelligence remain **NOT ACTIVE**.

`CompanyLearningRefreshService` accepts an explicit company ID plus optional source-change context, delegates all aggregation to `CompanyLearningMaterializationService`, and never discovers companies. Source changes recalculate only that current company projection. Duplicate or post-write retry delivery is idempotent, concurrent callers converge under the persisted current-row lock, and a delayed semantic snapshot returns `STALE_RESULT` rather than overwriting newer evidence. The maturity score is derived from the current canonical source state and is not monotonic by refresh count. Forecast integration and Decision Intelligence remain **NOT ACTIVE**.

## Phase 3C5B4A Learning Refresh Orchestration

`LearningRefreshOrchestrator` is a callable, tenant-scoped routing boundary whose input is exactly `(company_id, learning_evidence_id)`. It loads and validates one canonical `LearningEvidence` source rather than accepting arbitrary event JSON or scanning companies. `ACTUAL_ACCEPTED` and `ACTUAL_CORRECTED` refresh only their `(company, material_code, explicit demand_type)` Pattern Memory first, then Company Learning. `FORECAST_EVALUATED`, `CHAMPION_PROMOTED`, `CHAMPION_ROLLED_BACK`, and `RETRAINING_COMPLETED` refresh Company Learning only; Pattern policy does not consume those sources. Duplicate, out-of-order, partial-failure, and fresh-session retry delivery is safe through the existing durable projection fingerprints. Automatic evidence delivery, Forecast integration, and Decision Intelligence remain **NOT ACTIVE**.

## Phase 3C5B4B1 Durable Learning Evidence Delivery

`LearningRefreshDelivery` is the durable, company-scoped delivery intent for one immutable `LearningEvidence` item and delivery contract version. The Learning Evidence writer persists both rows in the same PostgreSQL transaction, so a committed evidence source cannot permanently lose its refresh intent. `LearningRefreshDeliveryService` provides explicit, tenant-scoped claim/heartbeat/complete/fail operations with a claim token, bounded lease, expiry reclaim, attempt count, compact outcome summary, and bounded retry policy. It does not route semantics itself: an explicit future worker calls `LearningRefreshOrchestrator(company_id, learning_evidence_id)`. A crash before claim, after claim, or after orchestration before completion reconstructs safely from PostgreSQL; retry converges through Pattern and Company fingerprints. Delivery order is not semantic authority. A periodic delivery worker, Forecast integration, and Decision Intelligence remain **NOT ACTIVE**.

## Phase 3C5B4B2 Learning Delivery Worker

`LearningRefreshWorker` is the leased consumer of the durable delivery ledger. Its `process_next(company_id)` and bounded `process_batch(company_id, limit)` claim only caller-scoped `LearningRefreshDelivery` rows, then delegate to the existing delivery service and orchestrator; they do not scan Actuals, Pattern scopes, companies, or LearningEvidence independently. One active PostgreSQL claim token owns processing; heartbeat retains it, expiry permits recovery, and stale workers cannot route or terminalize a newer lease. Retryable failures return the row to `pending`; deterministic source failures terminalize under the delivery retry policy. A post-orchestrator crash is safe because retry observes unchanged Pattern/Company source fingerprints and completes the delivery. Worker capability is development verified, but **no deployment timer, daemon, cron, or startup activation is configured**. Forecast integration, Supplier Learning, Event Intelligence, and Decision Intelligence remain **NOT ACTIVE**.

## Phase 3C6B1 Supplier Delivery Observation Ledger

`SupplierDeliveryObservation` is the canonical company-scoped **observed** supply fact, identified by an immutable operational source identity and retaining both supplier and material identities. It never copies declared `Supplier.lt_mean`, `Supplier.lt_std`, manual score, or runtime enrichment values as observed truth. Dispatch-to-receipt duration is the observed lead time only when a dispatch date exists; promised-versus-receipt deviation is stored separately as lateness/on-time evidence. Ordered and received quantities remain source facts for a future deterministic fulfillment ratio.

`SupplierDeliveryObservationRevision` retains prior and proposed snapshots for correction lineage. An accepted correction advances current observed truth and evidence fingerprint; a rejected correction is auditable but has no effect. Missing history is valid, and multiple suppliers per material and materials per supplier remain independent. Supplier Learning memory, LearningEvidence emission, Supplier/Safety Stock enrichment changes, and Decision Intelligence are **NOT ACTIVE**.

## Phase 3C6B2 Read-Only Supplier Learning Calculation

`SupplierLearningService` is a deterministic, in-memory calculation over current canonical `SupplierDeliveryObservation` evidence. Its identity is **company + supplier + material + receipt-date cutoff**. It reads no declared supplier lead-time, risk, or performance score. Observed lead time is strictly dispatch-to-receipt; promise reliability (on-time/late ratio and lateness) and fulfillment (received/ordered ratio) are separate metrics and may be unavailable when the canonical evidence omits them.

`supplier_learning_policy_v1` requires eight observed lead-time samples. With sufficient history it classifies from explicit metrics only: variability at CV >= 0.40, late-prone at late ratio >= 0.25, fulfillment-risk below mean fulfillment 0.95 or underfulfillment ratio >= 0.20, and deterioration only with at least twelve lead-time samples, a four-observation recent window, and a supported recent-vs-baseline change (lead time >=25% and >=2 days, late ratio >=0.25, or fulfillment <=-10%). Multiple active signals produce `MIXED_RISK`; otherwise the result is `RELIABLE`. Confidence is evidence quality (lead-time volume, promise/quantity coverage, and recency), not supplier score or AI confidence.

The source fingerprint commits to scope, cutoff, ordered current observation identities/fingerprints, accepted correction identities, and policy/feature versions. Future receipts cannot affect an earlier cutoff; accepted corrections before cutoff change the fingerprint and metrics, while rejected corrections do not. Supplier Learning persistence, LearningEvidence emission, Safety Stock integration, Supplier-analysis behavior, and Decision Intelligence are **NOT ACTIVE**.

## Phase 3C6B3 Durable Supplier Learning Memory

`SupplierLearningMemory` is the one mutable current projection per **company + supplier + material**. It persists compact trusted calculation outputâ€”policy and confidence versions, classification, confidence, window/cutoff, lead-time/promise/fulfillment/recent-deterioration metrics, source fingerprint, compact observation IDs, accepted revision IDs, material metadata, timestamp, and row versionâ€”without copying raw delivery histories.

`SupplierLearningMaterializationService` always derives its projection through `SupplierLearningService.calculate`; callers cannot supply arbitrary learned metrics. Same fingerprint is `UNCHANGED` without a version increment; later canonical evidence or accepted pre-cutoff corrections update the same row once. Rejected corrections and post-cutoff evidence at an earlier cutoff are unchanged. An older cutoff or an obsolete same-cutoff result is `STALE_RESULT` and cannot overwrite newer canonical current evidence. Missing promise/quantity metrics stay null, and insufficient history is `NOT_MATERIALIZED` without deleting an existing projection. Safety Stock integration, Supplier-analysis behavior, LearningEvidence emission, and Decision Intelligence are **NOT ACTIVE**.

## Phase 3C6B4 Incremental Supplier Learning Refresh / Delivery

Canonical `SUPPLIER_DELIVERY_OBSERVED` and accepted `SUPPLIER_DELIVERY_CORRECTED` LearningEvidence events bind company, supplier, material, observation/revision identity, and current source evidence fingerprint. They atomically create the existing `LearningRefreshDelivery` intent; rejected corrections create no event. `LearningRefreshOrchestrator` validates the persisted observation/revision authority then routes solely to `SupplierLearningRefreshService(company, supplier, material, latest receipt cutoff)`. There is no supplier-wide or global discovery scan, and supplier delivery evidence intentionally does not refresh Company Learning until an explicit versioned company policy introduces that input.

The existing PostgreSQL lease worker owns supplier delivery routing: duplicate/retried delivery converges idempotently, competing workers have one owner, expired leases may be reclaimed, stale tokens cannot complete, and a post-refresh crash safely retries to `UNCHANGED`. Insufficient history is a successful `NOT_MATERIALIZED` result. Supplier analysis, Safety Stock integration, Forecast, Pattern Learning, Company Learning, and Decision Intelligence are **NOT ACTIVE**.

## Phase 3C6B5 Read-Only Supplier Learning Enrichment

`SupplierLearningResolver` is a company/supplier/material-scoped, read-only boundary over `SupplierLearningMemory`. It returns compact learned provenance only when the current projection cutoff is compatible with the requested analysis cutoff; missing memory yields `NO_LEARNED_SUPPLIER_EVIDENCE`, and a future-derived projection yields `LEARNING_CUTOFF_INCOMPATIBLE`. It never refreshes or writes memory/evidence/delivery state.

Supplier Learning context is explicitly separate from declared/manual lead time and existing runtime supplier enrichment. The B5 adapter helper attaches a `supplier_learning` explainability section while preserving the operational `lead_time_days`, `lead_time_source`, and Safety Stock optimizer inputs verbatim. Dataset supplier labels are not silently treated as canonical supplier UUID authority, so the existing Business Workflow remains non-blocking and unchanged with no Supplier Learning task. Safety Stock integration, Supplier-analysis changes, and Decision Intelligence are **NOT ACTIVE**.

## Phase 3C7B1 Canonical Event Observation Ledger

`EventObservation` is the canonical company-scoped event occurrence authority. It separates stable `event_identity` from a source-specific occurrence reference, so repeated campaign/holiday/promotion occurrences retain independent date ranges and revision lineage. Scope is explicit only (`MATERIAL`, `PRODUCT_GROUP`, `PRODUCT_CLASS`, or `COMPANY`); demand type is explicit and isolated. `COMPANY_EXPLICIT` and `PUBLIC_REFERENCE` are the only B1 authorities. Public references remain provenance only; learned effects will never be shared across companies.

`EventRevision` preserves immutable proposed/accepted/rejected snapshots. An initial accepted snapshot anchors historical reconstruction, accepted corrections supersede current truth, rejected corrections do not alter it, and accepted cancellation changes state to `CANCELLED` rather than deleting evidence. Dataset `Events` rows remain optional import-validation input, not canonical authority and are not backfilled. External numeric weather/FX/inflation/sector/search context is a separate architecture. Event Intelligence calculation/memory, Forecast feature integration, Simulation changes, LearningEvidence emission, and Decision Intelligence are **NOT ACTIVE**.

## Phase 3C7B2 Read-Only Event Association Calculation

`EventAssociationService` is a deterministic, read-only, company/material/demand/event-identity calculation over canonical Event Observation revision truth and accepted Actual Ledger evidence. It resolves explicit MATERIAL, PRODUCT_GROUP, PRODUCT_CLASS, and COMPANY event scopes through current canonical material metadata and never persists scope expansion. Results are strictly non-causal association evidence: recurring occurrence effects are classified only as `POSITIVE_ASSOCIATION`, `NEGATIVE_ASSOCIATION`, `NO_CLEAR_EFFECT`, `INSUFFICIENT_EVIDENCE`, or `INCONSISTENT_EFFECT` under the versioned `event_association_policy_v1` threshold policy.

Its versioned baseline hierarchy prefers compatible Forecast Vintage points available before the event; otherwise it uses a fixed four-period, pre-event, non-event accepted-Actual fallback with a three-period minimum. Event, Actual, and Vintage evidence is reconstructed as-of the requested cutoff/as-of boundary; later corrections, cancellation, observations, events, and Vintages cannot rewrite a historical result. The SHA-256 source fingerprint commits to scope, accepted event revisions, accepted Actual revision identities, baseline sources, and policy versions. Overlapping applicable events are explicitly marked confounded rather than attributed. Confidence measures evidence coverage, consistency, baseline quality, and scope specificity only. Event Intelligence persistence, Forecast feature/schema integration, Simulation behavior, LearningEvidence emission, and Decision Intelligence remain **NOT ACTIVE**.

## Phase 3C7B3 Durable Event Intelligence Memory

`EventIntelligenceMemory` is the single mutable current projection for `(company_id, material_code, demand_type, event_identity)`. `EventIntelligenceMaterializationService` obtains its result only from `EventAssociationService`; callers cannot provide learned metrics. It persists compact cutoff-safe association lineage: policy versions, classification/confidence, occurrence and accepted revision identities, baseline/Vintage sources, actual revision identities, metrics, lag/effect summaries, confounding, and a source fingerprint. It does not duplicate per-occurrence source payloads.

Same source fingerprint materialization is idempotent (`UNCHANGED`, no row-version increment); accepted new occurrence or accepted source correction can refresh the same row (`UPDATED`); rejected corrections do not. Older cutoffs cannot overwrite a newer projection (`STALE_RESULT`), and concurrent first writers converge to one row. `INSUFFICIENT_EVIDENCE`, including confounded insufficient association, yields `NOT_MATERIALIZED` and never fabricates a learned effect or deletes an existing projection. Forecast, Simulation, Pattern/Company/Supplier Learning, retraining, model/registry mutation, and Decision Intelligence remain **NOT ACTIVE**.

## Phase 3C7B4 Event LearningEvidence Delivery

Accepted Event Observation transitions emit immutable `EVENT_OBSERVED`, `EVENT_CORRECTED`, or `EVENT_CANCELLED` LearningEvidence and a single leased `LearningRefreshDelivery` in the same transaction. The existing worker routes that evidence only through bounded Event Intelligence refresh requests: MATERIAL is exact, PRODUCT_GROUP/PRODUCT_CLASS/COMPANY expand only through current company material metadata, and no Event delivery performs a global Event, Actual, or company rescan. Accepted scope correction retains both snapshots so previous and accepted scopes reconcile; accepted Actual corrections reconcile only active Event identities overlapping the corrected period. Rejected corrections emit nothing.

Delivery idempotency, lease ownership, expiry reclaim, stale-token rejection, retry, and completion-loss recovery use the common delivery ledger. Event-only routing creates no Forecast, Simulation, retraining, Challenger, registry, Pattern/Company Learning, or Decision Intelligence side effect. Forecast and Simulation Event enrichment remain separate read-only work.

## Phase 3C7B5 Read-only Forecast / Simulation Event Enrichment

`EventIntelligenceResolver` is a company-scoped read boundary over durable Event Memory. It returns only matching material and explicit demand-type entries whose evidence cutoff is at or before the analysis cutoff; missing context is `EVENT_INTELLIGENCE_ABSENT`, and later-only context is `EVENT_INTELLIGENCE_CUTOFF_INCOMPATIBLE`. It preserves each event identity and source-scope provenance separately, exposes non-causal historical association language, and never refreshes or writes memory.

Forecast selection metadata and Simulation item context may include this compact evidence, but Forecast values, Simulation numbers, Champion resolution, artifacts, XGBoost feature schema, task graph, and governance remain unchanged. Event Intelligence is optional: missing or incompatible context never blocks standalone or Business Workflow execution. Decision Intelligence remains **NOT ACTIVE**.

## Phase 3D2 Canonical Decision Evidence Resolver

`DecisionEvidenceResolver` is a read-only canonical envelope boundary keyed by company, material, explicit demand type, decision cutoff, and decision context. It references compact compatible Forecast/Vintage, validated runtime results, Pattern/Company/Supplier/Event memory, Champion, and Retraining provenance. Required evidence is context-specific; missing required evidence returns `INSUFFICIENT_REQUIRED_EVIDENCE`, while optional absence remains explicit and graceful. Future-cutoff sources are incompatible rather than leaked. The deterministic fingerprint covers scope, context, cutoff, ordered source identities, fingerprints, versions, and compatibility state. Recommendation generation, Decision Snapshot persistence, autonomous action, and LLM decision authority remain **NOT ACTIVE**.

`PatternLearningMemory` is a **current projection, not a historical vintage**: its unique company/material/demand scope retains one mutable current row. At a decision cutoff, the resolver returns it as `AVAILABLE` only when its cutoff is compatible; a newer current Pattern returns `INCOMPATIBLE / FUTURE_EVIDENCE` and is never consumed. A superseded historical Pattern cannot be reconstructed from this projection alone. Phase 3D4's immutable Decision Snapshot owns preservation of the exact Pattern memory ID, source fingerprint, classification, confidence, cutoff, and policy versions used by a generated decision, so later Pattern refreshes cannot rewrite decision rationale.

## Phase 3C1 Retraining Eligibility boundary

Retraining Eligibility is a **POSTGRESQL VERIFIED**, read-only derivation over persisted Forecast Evaluation point evidence. Its identity is company, material code, and explicit demand type; product level/group/class remain evidence metadata and never infer demand type. The caller (or a future Learning scheduler) owns the last-seen evaluation watermark: stable evidence with no new watermark is Tier 0 `SKIP`, stable new evidence is Tier 1 `EVALUATE`, deterioration is Tier 2 `ANALYZE`, and sufficient multi-signal deterioration is Tier 3 `RETRAIN_ELIGIBLE` only.

The bounded evaluation window is leakage-safe: later Actual/Evaluation evidence cannot change a prior window. Approved canonical Actual corrections are reflected by the Forecast Evaluation refresh; rejected corrections are ignored. Eligibility itself creates no Actual, revision, Vintage, Evaluation, runtime, artifact, registry, or Learning state. Tier 3 can reach explicit Challenger Training; lower tiers are blocked with zero fit. Automatic retraining, automatic Challenger training/evaluation, automatic promotion, Learning mutation, and Decision Intelligence remain **NOT ACTIVE**.

## Phase 3C4B1 Durable Retraining Job boundary

`RetrainingJob` is the durable, company-scoped ownership record for a Tier-3 retraining candidate. Its scope is company, material code, and explicit demand type; product metadata remains an immutable snapshot. It retains the evaluation window, latest evaluation ID, training cutoff, eligibility contract/evidence, and a SHA-256 candidate fingerprint. The fingerprint includes a correction-safe digest of ordered persisted Forecast Evaluation points, accepted-Actual revision provenance, Forecast evidence identities and values, evaluation metrics, and recalculation identity; an accepted correction to an existing evaluation therefore creates distinct candidate evidence.

The PostgreSQL unique `(company_id, candidate_fingerprint)` constraint is the authoritative duplicate guard. Repeated scans resolve the existing job; Tier 0--2 evidence is rejected without a job. B1 stores only `pending` intent and intentionally leaves `runtime_execution_id` null for the later leased-worker phase. XGBoost training, ModelArtifact persistence, comparison, promotion, Forecast selection, rollback, Learning mutation, and Decision Intelligence remain **NOT ACTIVE**.

## Phase 3C4B2 Explicit leased Retraining Job execution

A Tier-3 `pending` RetrainingJob may be executed only through an explicit company-scoped command. PostgreSQL locks the job before creating one `retraining` RuntimeExecution and one `xgboost_challenger_training` RuntimeTask. The durable task stores only job/scope/cutoff/evidence identifiers, claims through the existing lease and heartbeat boundary, and uses a bounded two-attempt policy; a stale losing worker is no-work, never a second trainer.

The dedicated worker reconstructs the Tier-3 authorization from the immutable job evidence and calls the existing Challenger Training service. A `TRAINED` result persists through the immutable ModelArtifact service and links the artifact to the terminal `trained` job. `NOT_TRAINABLE` completes as a terminal non-infrastructure outcome without an artifact; exhausted retryable failures terminalize the task, RuntimeExecution, and job as `failed`. Automatic scanning, automatic start, comparison, promotion, rollback, Forecast selection changes, Learning mutation, and Decision Intelligence remain **NOT ACTIVE**.

## Phase 3C4B3 Retraining artifact race and recovery boundary

The existing two-attempt leased worker policy is now verified across retry, lease-expiry, stale-worker, and artifact-persistence failure windows. After an immutable ModelArtifact is persisted, its `RetrainingJob.model_artifact_id` is durably committed before task, RuntimeExecution, and job terminalization. A process crash in that window therefore leaves a recovery marker: after the lease expires, a fresh worker verifies and reuses the same trusted artifact instead of fitting again.

Deterministic artifact persistence is race-safe. Competing processes attempting the same company-scoped fingerprint recover the single authoritative ModelArtifact after the PostgreSQL unique constraint resolves; the losing controlled storage file is removed. Stale lease tokens cannot complete after a reclaimer succeeds. Retryable failures before durable artifact persistence remain bounded to two attempts, while deterministic invalid-input or artifact-integrity failures terminalize and terminal re-entry remains idempotent. This is still explicit operator-driven execution: automatic scan/enqueue, retraining, Challenger comparison or promotion, Forecast selection changes, Learning mutation, and Decision Intelligence are **NOT ACTIVE**.

## Phase 3C4B4 Retraining cooldown, priority, and resource admission

Retraining admission is a separate, explicit PostgreSQL-backed control boundary between a durable Tier-3 candidate and RuntimeExecution creation. `retraining_cooldown_v1` persists its decision, reason, and expiry on the job. It has no invented business-duration default: cooldown is disabled until configuration supplies a duration. When configured, newly accepted candidate evidence during a successful scope's cooldown remains a distinct, durable pending job and may be admitted after expiry without replacing its candidate fingerprint. The policy exposes a future severe-drift override hook but activates no unsupported threshold.

`retraining_priority_v1` persists a deterministic evidence-only score using existing drift flags, WAPE deterioration, and sample strength; equal scores order by candidate creation time and job ID. `retraining_resource_admission_v1` uses a PostgreSQL advisory transaction lock and lease records to enforce configurable global retraining capacity across processes. Leases are heartbeated, expire for recovery, fence stale heartbeat/release owners by token, and release when a job reaches a terminal outcome. This lane is independent of the Business Workflow active-company guard and does not block Forecast, Safety Stock, or standalone analysis. Future per-company quotas and fair queueing remain pending; automatic scanning, automatic retraining, comparison, promotion, rollback, Learning mutation, and Decision Intelligence remain **NOT ACTIVE**.

## Phase 3C4B5A Retraining scanner discovery

`RetrainingScannerService` is a **DEVELOPMENT VERIFIED** callable discovery boundary, not a periodic process. A caller supplies one company and a bounded evaluation-period window, with optional material and explicit demand-type filters. The scanner reads persisted Forecast Evaluation evidence, delegates tier derivation to `RetrainingEligibilityService`, and emits deterministic per-scope discovery evidence, counts, duration, and controlled scope errors. It retains caller-owned evaluation watermarks and never persists scanner-owned watermark state.

Tier 0, Tier 1, and Tier 2 scopes create no RetrainingJob. Tier 3 scopes delegate to the existing correction-safe `RetrainingJobService`: the first scan creates the durable candidate, repeated or concurrent scans resolve the same candidate through PostgreSQL uniqueness, and an accepted Actual correction may create a new candidate fingerprint without scanner-specific correction logic. The scanner exposes B4 cooldown/priority evidence only; it never acquires a retraining resource lease. It also never starts RuntimeExecution/RuntimeTask, fits XGBoost, persists ModelArtifact, changes Forecast selection, invokes governance, or mutates Learning. Periodic scanner activation remains **NOT ACTIVE**.

## Phase 3C4B5B Controlled scanner activation

`scan_and_activate` is an explicit operator/caller operation layered beside, not inside, pure scanner discovery. It first runs the same company/period-bounded discovery, obtains B4's persisted deterministic priority order, and delegates each candidate to the existing B2 `RetrainingExecutionService.start` boundary. It does not fit a model or persist an artifact directly. Tier-3 jobs in cooldown are reported as deferred and consume no retraining capacity; capacity-blocked jobs similarly retain their durable candidate without a RuntimeExecution or task. One isolated activation error is returned per scope while later eligible candidates continue according to capacity.

The B2 start operation is the durable resource-ownership handoff: it acquires the PostgreSQL B4 resource lease before RuntimeExecution creation, then the B2/B3 leased worker verifies, heartbeats, recovers, and releases that same lease on terminal work. The scanner activation caller does not hold a process-local slot. Repeated and concurrent activation are idempotent through the existing B1 candidate identity, B4 admission lease, and B2 runtime start guards. This is still not periodic automation: no timer, cron, startup/background loop, evaluation-completion trigger, automatic Champion comparison/promotion, Forecast switching, Learning mutation, or Decision Intelligence is active.

## Phase 3C4B5C1 Periodic scanner scheduler tick safety

`RetrainingScannerSchedulerService` adds a small durable ownership boundary for a future infrastructure scheduler. It contains no timer, cron registration, startup hook, or worker loop; an external scheduler must explicitly call `run_tick` for one company-scoped window and cadence timestamp. `retraining_periodic_tick_v1` derives a SHA-256 identity from company, bounded scan period, policy version, cadence bucket, and optional material/demand scope. PostgreSQL uniqueness and durable running ownership make duplicate or concurrent delivery converge to one effective B5B activation cycle.

Each tick persists its owner, recoverable lease expiry, completion summary, or controlled failure. Completed buckets are idempotent, running buckets reject a concurrent owner, and expired ownership can be reclaimed after a process loss. A failed bucket remains audited and is not retried immediately; restart safety means callers resume a future bucket (or one explicitly selected bounded catch-up), never an unlimited historical replay. The tick service delegates to B5B only and does not itself fit XGBoost, persist artifacts, invoke governance, switch Forecasts, or mutate Learning. Final long-running periodic orchestration remains pending C2.

## Phase 3C4 Selective Retraining orchestration closeout

Selective Retraining Orchestration is **DEVELOPMENT VERIFIED** as a durable, idempotent chain: a company-scoped scheduler tick delegates to B5B activation; B1 creates correction-safe Tier-3 candidates; B4 enforces cooldown, deterministic priority, and PostgreSQL resource capacity; B2/B3 execute the leased worker and persist one immutable Challenger artifact. Repeated or concurrent delivery converges to one effective candidate/runtime/task/fit/artifact, while a subsequent tick alone cannot retrain unchanged evidence.

New accepted evidence is preserved through a distinct candidate fingerprint. Accepted Actual corrections change canonical point/revision provenance and create a new candidate; rejected corrections do not. The B1 fingerprint deliberately excludes `ForecastEvaluation.recalculated_at`: that timestamp is operational refresh metadata, not accepted source evidence, and must not manufacture retraining work. Cooldown retains new candidates without consuming a slot; expiry resumes the same candidate. Capacity-blocked candidates remain durable, ordered by existing B4 priority, and may be activated by a later tick. Scheduler failure is distinct from worker/job failure and neither falsely terminalizes unrelated jobs nor retries immediately.

The repository implements and verifies scheduler logic only. No OS cron, Render scheduled job, deployment timer, startup hook, or always-running scheduler process is configured here. Business Workflow and standalone analysis do not acquire the retraining guard. Automatic Champion comparison, promotion, rollback, production Forecast switching, Learning mutation, and Decision Intelligence remain **NOT ACTIVE**.

## Phase 3B1 optional Supplier Business Workflow branch

Supplier enrichment is optional at Business Workflow acceptance. The encrypted Dataset must contain valid supplier identities, delivery evidence, and mappings to materials actually present in that Dataset. When absent, the durable workflow remains its original four required tasks. Partially present or invalid supplier evidence is recorded as controlled degradation metadata and is not silently converted into Supplier analysis.

When included, Supplier is a fifth required task using the existing Supplier capability path and durable result reference. It may apply to finished goods, semi-finished goods, or raw materials when valid mappings exist; it is not raw-material-only. The Supplier result is included in the aggregate only for workflows that generated the task. It does not yet change Safety Stock or Simulation inputs, and no Learning or Event Intelligence behavior is activated.

# DATA ARCHITECTURE

Version: 2.0

Status: Draft → Architecture Freeze Candidate

Priority: Mandatory

Scope:
Operational Data
Execution Data
Knowledge Data
Memory Store
Artifact Store
Metadata
Data Governance

---

# PART 01 — DATA ARCHITECTURE FOUNDATION

---

# 1. PURPOSE

Bu doküman;

Stokonomi Platformu içerisinde üretilen,

işlenen,

öğrenilen,

ve saklanan

tüm verilerin resmi mimarisini tanımlar.

Bu mimari;

yalnızca veritabanını değil,

Platform'un tüm bilgi yaşam döngüsünü kapsar.

---

# 2. OFFICIAL DEFINITION

Data Architecture;

Operational Data,

Execution Data,

Knowledge Data,

AI Memory,

Artifact Data

ve

Metadata katmanlarının birlikte oluşturduğu resmi veri mimarisidir.

Bu mimari;

Platform içerisindeki tüm veri akışlarının temelidir.

---

# 3. DATA PHILOSOPHY

Platform veriyi yalnızca saklamaz.

Veriyi;

oluşturur,

doğrular,

zenginleştirir,

öğrenir,

ilişkilendirir,

ve yeniden kullanır.

Bu nedenle veri,

Platform'un temel varlığıdır.

---

# 4. DATA LIFECYCLE

Platform verisi aşağıdaki yaşam döngüsünü izler.

Raw Data

↓

Validated Data

↓

Operational Data

↓

Execution Data

↓

Knowledge Data

↓

AI Memory

↓

Decision Data

↓

Artifact

↓

Archive

Hiçbir veri doğrulanmadan üst katmana geçemez.

---

# 5. DATA LAYERS

Platform aşağıdaki resmi veri katmanlarını kullanır.

• Operational Data

• Execution Data

• Intelligence Data

• Memory Store

• Artifact Store

• Metadata Store

• Audit Store

Bu katmanlar birbirinden bağımsızdır.

---

# 6. DATA OWNERSHIP

Her veri yalnızca tek bir katmanın sahipliğindedir.

Örnek.

Dataset

↓

Operational Layer

Execution Result

↓

Execution Layer

Company Memory

↓

Intelligence Layer

Artifact

↓

Artifact Layer

Ownership değiştirilemez.

---

# 7. DATA FLOW

Platform veri akışı aşağıdaki sırayı takip eder.

Client

↓

Dataset

↓

Validation

↓

Execution

↓

Learning

↓

Decision

↓

Artifact

↓

Storage

↓

API Response

Bu akış sistem genelinde standarttır.

---

# 8. DATA PRINCIPLES

### DATA-001

Her veri tek bir resmi kaynağa sahip olmalıdır.

---

### DATA-002

Ham veri değiştirilemez.

---

### DATA-003

Operational Data ile AI Memory ayrıdır.

---

### DATA-004

Knowledge Data yalnızca Learning tarafından oluşturulur.

---

### DATA-005

Execution Data yalnızca Execution Engine tarafından oluşturulur.

---

### DATA-006

Her veri yaşam döngüsü izlenebilir olmalıdır.

---

# 9. DATA CLASSIFICATION

Platform verileri aşağıdaki şekilde sınıflandırılır.

Operational

Analytical

Intelligence

Knowledge

Metadata

Artifact

Audit

Temporary

Bu sınıflandırma sistem genelinde standarttır.

---

# 10. OFFICIAL DATA FLOW

Operational Data

↓

Execution Data

↓

Knowledge Data

↓

Memory Store

↓

Decision Data

↓

Artifact Store

↓

API Layer

---

# PART 01 COMPLETION STATUS

| Item | Status |
|--------|--------|
| Data Definition | ✅ Complete |
| Data Philosophy | ✅ Complete |
| Data Lifecycle | ✅ Complete |
| Data Layers | ✅ Complete |
| Data Ownership | ✅ Complete |
| Data Principles | ✅ Complete |

---

**DOCUMENT 06 — PART 01 COMPLETE**

# PART 02 — OPERATIONAL DATA MODEL

---

# 11. PURPOSE

Operational Data;

Platform'un günlük operasyonlarını yürüten resmi iş verisidir.

Bu katman;

müşteriden gelen veriyi,

iş kurallarını,

ve analiz girişlerini içerir.

Operational Data;

AI Knowledge değildir.

Execution Result değildir.

---

# 12. OFFICIAL DEFINITION

Operational Data;

Platform'un çalışabilmesi için gerekli olan,

işletme tarafından sağlanan,

veya işletme sistemlerinden alınan

doğrulanmış iş verisidir.

Operational Data;

Platform'un tek resmi giriş verisidir.

---

# 13. OPERATIONAL DATA SOURCES

Operational Data aşağıdaki kaynaklardan gelebilir.

• Excel Upload

• ERP Integration

• REST API

• CSV Import

• Manual Entry

• Scheduled Import

• External Business Systems

Tüm kaynaklar aynı doğrulama sürecinden geçmelidir.

---

# 14. DATA CATEGORIES

Operational Data aşağıdaki kategorilere ayrılır.

Master Data

↓

Transaction Data

↓

Planning Data

↓

Reference Data

↓

Configuration Data

↓

Operational Parameters

Her kategori farklı yaşam döngüsüne sahiptir.

---

# 15. MASTER DATA

Master Data aşağıdaki temel işletme bilgilerini içerir.

• Company

• Warehouse

• SKU

• Supplier

• Customer

• Unit Definitions

Master Data kimlik bilgisidir.

Sık değişmez.

---

# 16. TRANSACTION DATA

Transaction Data aşağıdaki operasyonel kayıtları içerir.

Demand History

Inventory History

Purchase Orders

Receipts

Issues

Returns

Transfers

Transaction Data zaman serisi oluşturur.

---

# 17. PLANNING DATA

Planning Data aşağıdaki bilgileri içerir.

Planning Horizon

Service Level Target

Lead Time

Review Period

MOQ

Order Frequency

Planning Data analizleri yönlendirir.

---

# 18. REQUIRED & OPTIONAL DATA

Platform veri alanlarını aşağıdaki şekilde sınıflandırır.

Mandatory Data

↓

Optional Data

↓

Derived Data

↓

Calculated Data

Mandatory veri olmadan ilgili analiz başlatılamaz.

Optional veri eksik olduğunda sistem uygun fallback mekanizmasını kullanmalıdır.

---

# 19. GRACEFUL DEGRADATION

Operational Data eksik olduğunda;

Platform tamamen durmaz.

Sistem;

mevcut verilerle çalışır,

eksik alanları raporlar,

ilgili AI yeteneklerini devre dışı bırakır,

ve kullanıcıyı bilgilendirir.

Hiçbir opsiyonel veri,

tüm Workflow'u durduramaz.

---

# 20. OPERATIONAL DATA PRINCIPLES

### DATA-007

Operational Data sistemin tek resmi giriş verisidir.

---

### DATA-008

Her veri doğrulanmalıdır.

---

### DATA-009

Mandatory ve Optional alanlar açıkça tanımlanmalıdır.

---

### DATA-010

Optional veri eksikliği yalnızca ilgili yeteneği etkiler.

---

### DATA-011

Türetilmiş (Derived) veriler yeniden hesaplanabilir olmalıdır.

---

### DATA-012

Operational Data AI Memory ile karıştırılamaz.

---

# OFFICIAL OPERATIONAL DATA FLOW

External Source

↓

Validation Engine

↓

Operational Data Store

↓

Execution Engine

↓

Analysis Results

↓

AI Intelligence

---

# PART 02 COMPLETION STATUS

| Item | Status |
|--------|--------|
| Operational Data | ✅ Complete |
| Data Sources | ✅ Complete |
| Data Categories | ✅ Complete |
| Master & Transaction Data | ✅ Complete |
| Required / Optional Model | ✅ Complete |
| Graceful Degradation | ✅ Complete |

---

**DOCUMENT 06 — PART 02 COMPLETE**

# PART 03 — INTELLIGENCE DATA MODEL

---

# 21. PURPOSE

Intelligence Data;

AI Intelligence katmanı tarafından oluşturulan,

öğrenilen,

yorumlanan,

ve gelecekte tekrar kullanılacak resmi bilgi katmanıdır.

Intelligence Data;

Operational Data değildir.

Execution Data değildir.

AI tarafından üretilmiş bilgidir.

---

# 22. OFFICIAL DEFINITION

Intelligence Data;

Execution sonuçlarının,

öğrenme süreçlerinin,

davranış analizlerinin,

ve AI kararlarının oluşturduğu kurumsal bilgi katmanıdır.

Bu veri;

AI'nın uzun dönem hafızasını oluşturur.

---

# 23. INTELLIGENCE DATA COMPONENTS

Platform aşağıdaki Intelligence veri bileşenlerini kullanır.

• Company Memory

• Pattern Memory

• Decision Memory

• Knowledge Base

• Recommendation History

• Confidence History

• Learning History

Bu yapı sistem genelinde standarttır.

---

# 24. COMPANY MEMORY STORE

Company Memory aşağıdaki bilgileri saklayabilir.

Company Profile

Planning Behaviour

Inventory Behaviour

Risk Behaviour

Supplier Behaviour

Decision Behaviour

Operational Preferences

Company Memory yalnızca ilgili şirkete aittir.

---

# 25. PATTERN MEMORY STORE

Pattern Memory aşağıdaki davranış bilgilerini içerir.

Demand Pattern

Trend

Seasonality

Volatility

Intermittent Behaviour

Lead Time Behaviour

Forecast Stability

Pattern Confidence

Pattern Memory SKU bazlıdır.

---

# 26. DECISION MEMORY

Decision Memory;

geçmiş AI kararlarını saklar.

Her kayıt aşağıdaki bilgileri içerir.

Decision

↓

Reason

↓

Evidence

↓

Confidence

↓

Outcome

↓

Feedback

↓

Version

Decision Memory gelecekteki kararlar için referans oluşturabilir.

---

# 27. KNOWLEDGE BASE

Knowledge Base;

Company Learning ve Pattern Intelligence tarafından doğrulanmış bilgilerin resmi deposudur.

Knowledge;

ham veri değildir.

İşlenmiş bilgidir.

Knowledge Base yalnızca doğrulanmış bilgi içerir.

---

# 28. RECOMMENDATION HISTORY

Platform üretilen Recommendation geçmişini saklayabilir.

Recommendation

↓

Decision Version

↓

Reasoning

↓

Evidence

↓

User Response

↓

Outcome

Bu bilgiler Learning sürecine geri beslenebilir.

---

# 29. CONFIDENCE HISTORY

Platform Confidence değişimini izleyebilir.

Confidence History aşağıdaki bilgileri içerebilir.

Decision Confidence

Pattern Confidence

Learning Confidence

Recommendation Confidence

Confidence değişimi zaman içerisinde analiz edilebilir.

---

# 30. INTELLIGENCE DATA PRINCIPLES

### DATA-013

Intelligence Data yalnızca AI tarafından oluşturulur.

---

### DATA-014

Company Memory şirket bazında izole edilmelidir.

---

### DATA-015

Pattern Memory SKU bazında yönetilmelidir.

---

### DATA-016

Knowledge yalnızca doğrulanmış bilgi içerir.

---

### DATA-017

Decision Memory silinmez.

Versiyonlanır.

---

### DATA-018

Confidence geçmişi izlenebilir olmalıdır.

---

# OFFICIAL INTELLIGENCE DATA FLOW

Execution Results

↓

Company Learning

↓

Pattern Intelligence

↓

Knowledge Base

↓

Decision Memory

↓

Recommendation History

↓

Learning Evolution

---

# PART 03 COMPLETION STATUS

| Item | Status |
|--------|--------|
| Intelligence Data | ✅ Complete |
| Company Memory Store | ✅ Complete |
| Pattern Memory Store | ✅ Complete |
| Decision Memory | ✅ Complete |
| Knowledge Base | ✅ Complete |
| Recommendation History | ✅ Complete |

---

**DOCUMENT 06 — PART 03 COMPLETE**

# PART 04 — FEATURE STORE & SEMANTIC KNOWLEDGE

---

# 31. PURPOSE

Feature Store;

Platform içerisindeki tüm AI modellerinin,

Intelligence bileşenlerinin,

ve Decision Engine'in kullandığı standart özellik (Feature) katmanıdır.

Feature Store;

ham veri değildir.

Analiz sonucu değildir.

AI tarafından kullanılabilir standart özellik deposudur.

---

# 32. OFFICIAL DEFINITION

Feature;

Operational Data,

Execution Results,

ve Intelligence Data'dan türetilen,

AI tarafından doğrudan kullanılabilen standart bilgi öğesidir.

Feature Store;

tüm Feature'ların resmi kaynağıdır.

---

# 33. FEATURE CATEGORIES

Platform aşağıdaki Feature türlerini destekler.

Statistical Features

Operational Features

Business Features

Pattern Features

Behavioral Features

Decision Features

Confidence Features

Derived Features

Yeni Feature kategorileri eklenebilir.

---

# 34. FEATURE STORE

Feature Store aşağıdaki amaçlarla kullanılır.

• AI Learning

• Pattern Detection

• Decision Support

• Recommendation

• Confidence Calculation

• Similarity Search

• Knowledge Evolution

Feature Store sistem genelinde tek resmi Feature kaynağıdır.

---

# 35. FEATURE LIFECYCLE

Her Feature aşağıdaki yaşam döngüsünü izler.

Raw Data

↓

Feature Extraction

↓

Validation

↓

Feature Store

↓

AI Consumption

↓

Evolution

↓

Version Update

Her Feature yeniden üretilebilir olmalıdır.

---

# 36. FEATURE VERSIONING

Her Feature aşağıdaki bilgilerle versiyonlanır.

Feature ID

Feature Version

Source

Creation Time

Validation Status

Confidence

Feature geçmişi korunmalıdır.

---

# 37. SEMANTIC STORE

Semantic Store;

AI'nın kavramsal benzerlikleri değerlendirebildiği resmi veri katmanıdır.

Semantic Store;

ham veri içermez.

Anlam ilişkilerini saklar.

Örnek.

Benzer SKU

Benzer Talep Davranışı

Benzer Risk Profili

Benzer Planlama Davranışı

Semantic Store gelecekte farklı teknolojilerle uygulanabilir.

---

# 38. KNOWLEDGE GRAPH

Knowledge Graph;

Platform içerisindeki Intelligence bileşenleri arasındaki ilişkileri temsil eder.

Örnek ilişkiler.

Company

↓

Warehouse

↓

Product Family

↓

SKU

↓

Supplier

↓

Pattern

↓

Decision

↓

Artifact

Knowledge Graph;

ilişkileri tanımlar.

Verinin kendisini taşımaz.

---

# 39. KNOWLEDGE RELATIONSHIPS

Platform aşağıdaki ilişki türlerini tanıyabilir.

Belongs To

Depends On

Produced By

Learns From

Influences

Similar To

Derived From

Validated By

Yeni ilişki türleri eklenebilir.

---

# 40. FEATURE & SEMANTIC PRINCIPLES

### DATA-019

Feature yalnızca doğrulanmış veriden türetilir.

---

### DATA-020

Feature yeniden üretilebilir olmalıdır.

---

### DATA-021

Semantic Store iş verisini değil,

anlam ilişkilerini saklar.

---

### DATA-022

Knowledge Graph yalnızca ilişki yönetir.

---

### DATA-023

Feature Store AI'nın tek resmi Feature kaynağıdır.

---

### DATA-024

Feature ve Operational Data birbirinden bağımsızdır.

---

# OFFICIAL FEATURE FLOW

Operational Data

↓

Execution Results

↓

Feature Extraction

↓

Feature Store

↓

Semantic Store

↓

Knowledge Graph

↓

AI Intelligence

↓

Decision Intelligence

---

# PART 04 COMPLETION STATUS

| Item | Status |
|--------|--------|
| Feature Store | ✅ Complete |
| Feature Lifecycle | ✅ Complete |
| Semantic Store | ✅ Complete |
| Knowledge Graph | ✅ Complete |
| Relationship Model | ✅ Complete |
| Feature Principles | ✅ Complete |

---

**DOCUMENT 06 — PART 04 COMPLETE**

# PART 05 — ARTIFACT STORE & METADATA ARCHITECTURE

---

# 41. PURPOSE

Artifact Store;

Platform tarafından oluşturulan tüm resmi çıktıların,

raporların,

AI açıklamalarının,

ve analiz sonuçlarının yaşam döngüsünü yöneten resmi veri katmanıdır.

Artifact;

ham veri değildir.

Execution değildir.

AI Memory değildir.

Sonuç ürünüdür.

---

# 42. OFFICIAL DEFINITION

Artifact;

Execution Engine,

Decision Intelligence,

ve AI Intelligence tarafından üretilen,

yeniden kullanılabilir,

versiyonlanabilir,

ve paylaşılabilir resmi çıktı nesnesidir.

Artifact sistem genelinde standarttır.

---

# 43. ARTIFACT TYPES

Platform aşağıdaki Artifact türlerini destekler.

Execution Artifact

Decision Artifact

Recommendation Artifact

AI Summary

Management Report

Executive Summary

Dashboard Snapshot

Notification Package

Yeni Artifact türleri eklenebilir.

---

# 44. ARTIFACT STORE

Artifact Store aşağıdaki görevlerden sorumludur.

• Artifact saklamak

• Artifact versiyonlamak

• Artifact paylaşmak

• Artifact tekrar kullanmak

• Artifact yaşam döngüsünü yönetmek

Artifact Store yalnızca Artifact saklar.

Knowledge saklamaz.

---

# 45. ARTIFACT METADATA

Her Artifact aşağıdaki Metadata bilgilerini içerir.

Artifact ID

Artifact Type

Version

Owner

Creation Time

Source Execution

Source Decision

Language

Visibility

Retention Policy

Metadata Artifact'in ayrılmaz parçasıdır.

---

# 46. ARTIFACT LIFECYCLE

Artifact aşağıdaki yaşam döngüsünü takip eder.

Created

↓

Validated

↓

Published

↓

Consumed

↓

Archived

↓

Retired

Artifact gerektiğinde yeniden oluşturulabilir.

---

# 47. METADATA STORE

Metadata Store;

Platform içerisindeki tüm nesnelerin tanımlayıcı bilgilerini saklayan resmi katmandır.

Metadata aşağıdaki alanlarda kullanılabilir.

Execution

Workflow

Dataset

Knowledge

Decision

Artifact

Feature

Metadata iş verisi değildir.

---

# 48. AUDIT STORE

Audit Store;

Platform içerisinde gerçekleşen kritik işlemleri izler.

Örnek.

Execution Started

Decision Generated

Knowledge Updated

Artifact Published

User Action

Policy Change

Audit kayıtları değiştirilemez.

---

# 49. TRACEABILITY

Platform aşağıdaki izlenebilirlik zincirini desteklemelidir.

Dataset

↓

Execution

↓

Capability

↓

Knowledge

↓

Decision

↓

Recommendation

↓

Artifact

↓

User

Her Artifact geriye doğru izlenebilir olmalıdır.

---

# 50. ARTIFACT & METADATA PRINCIPLES

### DATA-025

Her Artifact tek bir resmi kaynağa sahip olmalıdır.

---

### DATA-026

Artifact versiyonlanmalıdır.

---

### DATA-027

Metadata iş verisi değildir.

---

### DATA-028

Audit kayıtları silinemez.

---

### DATA-029

Her Artifact izlenebilir olmalıdır.

---

### DATA-030

Artifact yeniden üretilebilir olmalıdır.

---

# OFFICIAL ARTIFACT FLOW

Execution Engine

↓

Decision Intelligence

↓

Recommendation Engine

↓

Artifact Builder

↓

Artifact Store

↓

Metadata Store

↓

Audit Store

↓

API Layer

---

# PART 05 COMPLETION STATUS

| Item | Status |
|--------|--------|
| Artifact Store | ✅ Complete |
| Artifact Lifecycle | ✅ Complete |
| Metadata Store | ✅ Complete |
| Audit Store | ✅ Complete |
| Traceability | ✅ Complete |
| Artifact Principles | ✅ Complete |

---

**DOCUMENT 06 — PART 05 COMPLETE**

# PART 06 — DATA GOVERNANCE, INTEGRITY & LIFECYCLE MANAGEMENT

---

# 51. PURPOSE

Data Governance;

Platform içerisindeki tüm verilerin

doğru,

güvenli,

izlenebilir,

tutarlı,

versiyonlanabilir

ve yönetilebilir şekilde kullanılmasını sağlayan resmi yönetişim modelidir.

Data Governance;

yalnızca veritabanı yönetimi değildir.

Verinin tüm yaşam döngüsünü kapsar.

---

# 52. DATA GOVERNANCE RESPONSIBILITIES

Data Governance aşağıdaki görevlerden sorumludur.

• Data Ownership tanımlamak

• Data Classification uygulamak

• Versioning kurallarını yönetmek

• Retention politikalarını belirlemek

• Data Integrity sağlamak

• Data Lineage korumak

• Data Access kurallarını yönetmek

• Data Migration süreçlerini kontrol etmek

• Archive ve Retirement süreçlerini yönetmek

Data Governance iş verisi üretmez.

---

# 53. DATA OWNERSHIP MODEL

Her veri nesnesinin tek bir resmi sahibi bulunmalıdır.

Örnek:

Operational Data

↓

Operational Data Layer

Execution Result

↓

Execution Data Layer

Company Memory

↓

Company Learning

Pattern Memory

↓

Pattern Intelligence

Decision Memory

↓

Decision Intelligence

Artifact

↓

Artifact Store

Ownership belirsiz bırakılamaz.

---

# 54. DATA VERSIONING

Aşağıdaki veri türleri versiyonlanmalıdır.

• Dataset

• Workflow

• Execution Contract

• Feature

• Company Memory

• Pattern Memory

• Knowledge

• Decision

• Recommendation

• Artifact

Yeni sürüm oluşturulduğunda önceki sürüm değiştirilemez.

---

# 55. VERSION STRUCTURE

Her versiyon aşağıdaki bilgileri içermelidir.

• Object ID

• Version ID

• Previous Version

• Creation Time

• Created By

• Source

• Change Reason

• Validation Status

• Active Status

Versiyon geçmişi izlenebilir olmalıdır.

---

# 56. DATA RETENTION

Her veri sınıfı için Retention Policy tanımlanmalıdır.

Retention Policy aşağıdaki kararları içerebilir.

• Saklama süresi

• Arşivleme zamanı

• Erişim seviyesi

• Anonimleştirme gereksinimi

• Silme koşulu

• Yasal saklama zorunluluğu

Tüm veri türleri aynı saklama politikasını kullanmak zorunda değildir.

---

# 57. IMMUTABILITY RULES

Aşağıdaki veriler immutable kabul edilir.

• Raw Dataset Version

• Completed Execution Result

• Published Decision

• Published Recommendation

• Published Artifact

• Audit Record

• Event Record

Değişiklik gerektiğinde yeni versiyon oluşturulur.

---

# 58. DATA INTEGRITY

Platform aşağıdaki bütünlük kurallarını sağlamalıdır.

• Company Ownership doğrulanmalıdır.

• Foreign Reference ilişkileri geçerli olmalıdır.

• Version zinciri kopmamalıdır.

• Dataset ile Execution ilişkisi korunmalıdır.

• Decision ile Evidence ilişkisi korunmalıdır.

• Artifact ile Source Execution ilişkisi korunmalıdır.

• Audit kayıtları değiştirilememelidir.

Bütünlük ihlali olan veri yayımlanamaz.

---

# 59. DATA CONSISTENCY

Platform aşağıdaki tutarlılık seviyelerini destekler.

### Strong Consistency

Kritik kimlik ve sahiplik verileri için kullanılır.

Örnek:

Company

User

Dataset Approval

Execution Status

---

### Eventual Consistency

Asenkron zenginleştirme verileri için kullanılabilir.

Örnek:

Metrics

Semantic Index

Notification Status

Artifact Representation

Tutarlılık modeli veri türüne göre belirlenir.

---

# 60. DATA LINEAGE

Data Lineage;

bir verinin hangi kaynaklardan üretildiğini gösterir.

Resmi Lineage zinciri aşağıdaki gibidir.

Dataset

↓

Execution

↓

Capability Result

↓

Feature

↓

Knowledge

↓

Decision

↓

Recommendation

↓

Artifact

Her türetilmiş veri kendi kaynağına geri izlenebilmelidir.

---

# 61. ARTIFACT LINEAGE EXTENSION POINT

Artifact Lineage;

bir Artifact'in üretim soy ağacını temsil eder.

Örnek:

Dataset

↓

Execution

↓

Decision

↓

Recommendation

↓

Executive Summary

↓

PDF Report

Artifact Lineage zorunlu çekirdek veri modeli değildir.

Ancak resmi genişleme noktasıdır.

Uygulandığında aşağıdaki bilgileri taşımalıdır.

• Source Dataset

• Source Execution

• Source Decision

• Source Recommendation

• AI Version

• Artifact Version

• Generation Time

---

# 62. DECISION GRAPH EXTENSION POINT

Decision Graph;

AI tarafından üretilen kararların ilişkisel geçmişini temsil edebilir.

Örnek:

Decision

↓

Evidence

↓

Pattern

↓

Company Memory

↓

Risk

↓

Recommendation

↓

Outcome

Decision Graph zorunlu çekirdek bileşen değildir.

Ancak gelecekteki Intelligence gelişimi için resmi Extension Point'tir.

---

# 63. DATA VALIDATION

Veri yaşam döngüsünün her aşamasında doğrulama uygulanmalıdır.

Validation seviyeleri:

• Structural Validation

• Schema Validation

• Business Validation

• Ownership Validation

• Consistency Validation

• Quality Validation

• Intelligence Validation

Bir üst veri katmanına yalnızca doğrulanmış veri geçebilir.

---

# 64. DATA QUALITY

Platform aşağıdaki veri kalite boyutlarını izlemelidir.

• Completeness

• Accuracy

• Consistency

• Timeliness

• Validity

• Uniqueness

• Traceability

Veri kalite skoru ilgili analiz ve karar Confidence değerini etkileyebilir.

---

# 65. DATA CORRECTION

Immutable veri doğrudan düzeltilemez.

Hata tespit edildiğinde aşağıdaki süreç uygulanır.

Error Detection

↓

Correction Request

↓

New Version

↓

Validation

↓

Activation

↓

Previous Version Retained

Geçmiş veri korunur.

---

# 66. DATA DELETION

Silme işlemleri veri türüne göre yönetilir.

Platform aşağıdaki stratejileri destekleyebilir.

• Logical Deletion

• Archival

• Anonymization

• Legal Deletion

• Permanent Deletion

Audit, Event ve yayınlanmış geçmiş kayıtları normal kullanıcı işlemleriyle silinemez.

---

# 67. COMPANY DATA ISOLATION

Her Company kendi veri alanına sahiptir.

Aşağıdaki veriler Company sınırları dışına çıkamaz.

• Operational Data

• Execution Data

• Company Memory

• Pattern Memory

• Decision Memory

• Recommendation History

• Artifact

• Audit Records

Cross-Company erişim yalnızca açık ve yetkili platform politikalarıyla mümkündür.

---

# 68. DATA ACCESS CONTROL

Veri erişimi aşağıdaki bağlamlarla doğrulanmalıdır.

• Company Identity

• User Identity

• Role

• Permission

• Data Ownership

• Data Classification

• Purpose of Access

Doğrudan fiziksel depolama erişimi uygulama kullanıcılarına açılamaz.

---

# 69. DATA ENCRYPTION

Hassas veriler aşağıdaki durumlarda korunmalıdır.

### At Rest

Depolanan veri şifrelenmelidir.

### In Transit

Taşınan veri güvenli protokollerle korunmalıdır.

### In Use

Çalışma sırasında erişim yetkilendirilmelidir.

Şifreleme anahtarları iş verisinden ayrı yönetilmelidir.

---

# 70. DATA BACKUP & RECOVERY

Platform aşağıdaki veri kurtarma yeteneklerini desteklemelidir.

• Scheduled Backup

• Point-in-Time Recovery

• Version Recovery

• Artifact Recovery

• Memory Recovery

• Audit Recovery

Backup doğrulanmadan güvenilir kabul edilemez.

---

# 71. DATA MIGRATION

Data Migration aşağıdaki sıra ile yürütülmelidir.

Discovery

↓

Mapping

↓

Validation

↓

Migration

↓

Verification

↓

Activation

↓

Rollback Window

Migration sırasında kaynak veri doğrudan değiştirilmemelidir.

---

# 72. SCHEMA EVOLUTION

Schema değişiklikleri aşağıdaki kurallara uymalıdır.

• Geriye dönük uyumluluk korunmalıdır.

• Yeni alanlar mümkün olduğunda Optional olmalıdır.

• Alan anlamı sessizce değiştirilemez.

• Kaldırılan alanlar önce Deprecated olmalıdır.

• Migration Script versiyonlanmalıdır.

• Rollback planı bulunmalıdır.

---

# 73. CACHE GOVERNANCE

Cache resmi veri kaynağı değildir.

Cache;

• yeniden üretilebilir olmalıdır,

• süreli olmalıdır,

• kaynak veriden türetilmelidir,

• veri kaybında sistemi bozmamalıdır.

Cache ile kalıcı veri birbirine karıştırılamaz.

---

# 74. TEMPORARY DATA

Temporary Data yalnızca Execution süresince kullanılabilir.

Örnek:

• Intermediate Results

• Temporary Files

• Runtime Cache

• Worker State

• Session Data

Execution tamamlandığında geçici veriler temizlenmelidir.

Kalıcı bilgi Temporary Store içerisinde saklanamaz.

---

# 75. DATA OBSERVABILITY

Platform aşağıdaki veri operasyonlarını izlemelidir.

• Data Creation

• Data Validation

• Data Versioning

• Data Access

• Data Migration

• Data Archive

• Data Deletion

• Data Recovery

Kritik veri operasyonları Audit kaydı üretmelidir.

---

# 76. DATA GOVERNANCE PRINCIPLES

### DATA-031

Her veri nesnesinin tek bir resmi sahibi olmalıdır.

---

### DATA-032

Immutable veri doğrudan değiştirilemez.

---

### DATA-033

Her türetilmiş veri kaynağına geri izlenebilmelidir.

---

### DATA-034

Company izolasyonu tüm veri katmanlarında korunmalıdır.

---

### DATA-035

Cache resmi veri kaynağı değildir.

---

### DATA-036

Schema değişiklikleri versiyonlanmalıdır.

---

### DATA-037

Migration işlemleri doğrulanabilir ve geri alınabilir olmalıdır.

---

### DATA-038

Veri kalitesi karar güvenini etkileyebilir.

---

### DATA-039

Audit kayıtları değiştirilemez.

---

### DATA-040

Fiziksel depolama teknolojisi mantıksal veri mimarisini değiştiremez.

---

# OFFICIAL DATA GOVERNANCE FLOW

Data Creation

↓

Classification

↓

Ownership Assignment

↓

Validation

↓

Versioning

↓

Storage

↓

Access Control

↓

Monitoring

↓

Archive / Retention

↓

Recovery / Retirement

---

# PART 06 COMPLETION STATUS

| Item                       | Status     |
| -------------------------- | ---------- |
| Data Ownership             | ✅ Complete |
| Data Versioning            | ✅ Complete |
| Retention Management       | ✅ Complete |
| Data Integrity             | ✅ Complete |
| Data Lineage               | ✅ Complete |
| Artifact Lineage Extension | ✅ Complete |
| Decision Graph Extension   | ✅ Complete |
| Data Security              | ✅ Complete |
| Backup & Recovery          | ✅ Complete |
| Data Migration             | ✅ Complete |
| Schema Evolution           | ✅ Complete |
| Data Governance Principles | ✅ Complete |

---

**DOCUMENT 06 — PART 06 COMPLETE**

# PART 07 — DATA ARCHITECTURE GOVERNANCE & ARCHITECTURAL COMPLIANCE

---

# 77. PURPOSE

Bu bölüm;

Stokonomi Data Architecture'ın

uzun vadeli sürdürülebilirliğini,

tutarlılığını,

güvenilirliğini,

ve genişletilebilirliğini güvence altına alır.

Veri mimarisi ile ilgili tüm geliştirmeler bu bölümde tanımlanan kurallara uymak zorundadır.

---

# 78. DATA ARCHITECTURAL INVARIANTS

Aşağıdaki kurallar Data Architecture için değiştirilemez.

### DATA-041

Operational Data sistemin tek resmi giriş verisidir.

---

### DATA-042

Execution Data yalnızca Execution Engine tarafından oluşturulur.

---

### DATA-043

Knowledge Data yalnızca AI Intelligence tarafından oluşturulur.

---

### DATA-044

Company Memory yalnızca ilgili şirkete aittir.

---

### DATA-045

Pattern Memory yalnızca ilgili SKU davranışını temsil eder.

---

### DATA-046

Artifact yalnızca tamamlanmış Decision sonucundan üretilebilir.

---

### DATA-047

Metadata iş verisinin yerine geçemez.

---

### DATA-048

Audit kayıtları değiştirilemez.

---

# 79. FORBIDDEN OPERATIONS

Aşağıdaki işlemler mimari ihlal olarak değerlendirilir.

• Operational Data'nın doğrudan değiştirilmesi

• AI'nın Company Memory'yi manuel güncellemesi

• Pattern Memory'nin kullanıcı tarafından düzenlenmesi

• Execution Result üzerinde sonradan değişiklik yapılması

• Decision Memory'nin silinmesi

• Feature Store'un Operational Data olarak kullanılması

• Cache'in resmi veri kaynağı kabul edilmesi

• Artifact'in kaynak veriden bağımsız oluşturulması

---

# 80. DATA EXTENSION RULES

Yeni veri bileşeni eklenirken aşağıdaki kurallar uygulanmalıdır.

Yeni veri modeli;

• Tek sorumluluğa sahip olmalıdır.

• Bir resmi Owner tanımlamalıdır.

• Version desteklemelidir.

• Audit üretmelidir.

• Metadata içermelidir.

• Trace edilebilir olmalıdır.

• Retention Policy tanımlamalıdır.

• Data Classification belirlemelidir.

---

# 81. COMPATIBILITY RULES

Yeni sürümler aşağıdaki yapıları bozamaz.

• Dataset Contract

• Execution Result Contract

• Company Memory Model

• Pattern Memory Model

• Decision Contract

• Artifact Contract

• Metadata Model

Kırıcı değişiklikler yalnızca yeni Major Version ile yapılabilir.

---

# 82. STORAGE INDEPENDENCE

Logical Data Architecture;

fiziksel depolama teknolojilerinden bağımsızdır.

Aşağıdaki teknolojiler değişebilir.

• PostgreSQL

• Redis

• Object Storage

• Vector Database

• Graph Database

• Search Index

Teknoloji değişimi veri mimarisini değiştirmez.

---

# 83. DATA OBSERVABILITY

Data Architecture aşağıdaki operasyonları izleyebilmelidir.

• Dataset Import

• Execution Creation

• Knowledge Update

• Decision Creation

• Artifact Generation

• Version Change

• Migration

• Archive

• Recovery

Kritik işlemler Monitoring ve Audit sistemine bildirilmelidir.

---

# 84. IMPLEMENTATION ORDER

Data Architecture aşağıdaki sırayla uygulanmalıdır.

Operational Data

↓

Execution Data

↓

Knowledge Data

↓

Memory Store

↓

Feature Store

↓

Artifact Store

↓

Metadata Store

↓

Governance

Bu sıra değiştirilmemelidir.

---

# 85. VALIDATION CHECKLIST

Yeni veri modeli eklenmeden önce aşağıdaki sorular cevaplanmalıdır.

□ Veri sahibi belli mi?

□ Veri sınıflandırıldı mı?

□ Version desteği var mı?

□ Metadata tanımlandı mı?

□ Trace edilebilir mi?

□ Audit üretiyor mu?

□ Retention tanımlandı mı?

□ Company izolasyonu korunuyor mu?

□ Architecture kurallarına uygun mu?

---

# 86. DOCUMENT DEPENDENCIES

Data Architecture aşağıdaki dokümanlara bağlıdır.

Document 01 — Foundation

↓

Document 02 — Domain Model

↓

Document 03 — Workflow Architecture

↓

Document 04 — Execution Engine

↓

Document 05 — AI Intelligence Architecture

↓

Document 06 — Data Architecture

Sonraki dokümanlar.

↓

Document 07 — Application Architecture

↓

Infrastructure

---

# 87. ARCHITECTURE COMPLIANCE

Platform içerisindeki tüm veri modelleri;

Document 01,

Document 02,

Document 03,

Document 04,

Document 05,

ve

Document 06

ile tam uyumlu olmak zorundadır.

Hiçbir implementasyon bu mimari ile çelişemez.

---

# 88. ARCHITECTURE FREEZE

Bu doküman;

Stokonomi Platformu'nun resmi Data Architecture referansıdır.

Data Architecture ile ilgili tüm geliştirmeler bu doküman referans alınarak yapılacaktır.

Bu mimari;

Architecture Decision Record (ADR) oluşturulmadan değiştirilemez.

---

# PART 07 COMPLETION STATUS

| Item                     | Status     |
| ------------------------ | ---------- |
| Architectural Invariants | ✅ Complete |
| Forbidden Operations     | ✅ Complete |
| Extension Rules          | ✅ Complete |
| Compatibility Rules      | ✅ Complete |
| Storage Independence     | ✅ Complete |
| Validation Checklist     | ✅ Complete |
| Architecture Freeze      | ✅ Complete |

---

# DOCUMENT 06 COMPLETION STATUS

| Part                                                              | Status     |
| ----------------------------------------------------------------- | ---------- |
| Part 01 — Data Architecture Foundation                            | ✅ Complete |
| Part 02 — Operational Data Model                                  | ✅ Complete |
| Part 03 — Intelligence Data Model                                 | ✅ Complete |
| Part 04 — Feature Store & Semantic Knowledge                      | ✅ Complete |
| Part 05 — Artifact Store & Metadata Architecture                  | ✅ Complete |
| Part 06 — Data Governance, Integrity & Lifecycle Management       | ✅ Complete |
| Part 07 — Data Architecture Governance & Architectural Compliance | ✅ Complete |

---

# DOCUMENT 06 STATUS

Architecture Freeze Candidate

Version: 2.0

Status: Complete

Next Document:

DOCUMENT_07_APPLICATION_ARCHITECTURE.md

# Revision — Product Architecture Phase 1

- **Revision date:** 2026-08-06
- **Revision status:** BINDING
- **ADR reference:** ADR-020

Data enrichment model:

Minimum required data → Basic Standalone Analysis.

Additional operational data → Richer Business Workflow output.

Supplier data → Supplier Allocation enrichment.

ERP/API feedback → Company Learning.

External Intelligence → Company Learning → Pattern Intelligence → AI Parameter Optimizer → Deterministic Analysis.

Optional-data absence must not block unrelated valid capabilities. Missing data must explicitly describe unavailable outputs; data availability automatically enables its corresponding capabilities. External data does not directly overwrite deterministic results. Learning feedback must be traceable and versioned, and company data remains isolated.

---

# Revision - Phase 3C2B1 XGBoost weekly feature evidence

The XGBoost weekly feature builder is **DEVELOPMENT VERIFIED** as a read-only development boundary. Its versioned feature schema is `xgboost_weekly_v1`; it reads canonical accepted Actual Weekly Observations only, is cutoff-safe, preserves product metadata for `finished_good`, `semi_finished_good`, and `raw_material`, isolates demand types, and orders ISO weeks correctly across W53 and year boundaries. XGBoost training, model artifacts, promotion, and Learning integration are **NOT YET ACTIVE**.

---

# Revision - Phase 3C2B2 XGBoost Challenger training

XGBoost Challenger Training is **DEVELOPMENT VERIFIED** as an explicit, bounded, in-memory service. It consumes `xgboost_weekly_v1` only, performs a deterministic time-ordered holdout, and prohibits future-cutoff leakage. Production Forecast remains unchanged. Automatic retraining, artifact persistence, Champion-Challenger governance, promotion, Decision Intelligence, and Learning Score mutation are **NOT ACTIVE**. The PostgreSQL Tier-3 eligibility and explicit-training boundary are verified.

---

# Revision - Phase 3C2B3 immutable Challenger model artifacts

Immutable, company-scoped Challenger model artifacts are **VERIFIED**. Native XGBoost UBJ bytes are stored through a controlled storage boundary, with SHA-256 verified before trusted loading. Artifact history is append-only and tenant-isolated. Production Forecast remains unchanged; automatic retraining is **NOT ACTIVE**, Champion-Challenger governance is pending Phase 3C3, and the PostgreSQL Tier-3 eligibility and explicit-training boundary are verified.

---

# Revision - Phase 3C3A Champion--Challenger decision evidence

Champion--Challenger evaluation is **DEVELOPMENT VERIFIED** as an immutable decision-evidence boundary. Champion Forecast Vintage, Effective Timeline, Forecast Evaluation, and Performance History evidence are compared against a trusted, checksum-verified Challenger artifact over the same out-of-sample window. `champion_challenger_policy_v1` uses WAPE as the primary metric with Bias, MAE, RMSE, and sample-strength guardrails. Comparison makes no XGBoost fit and does not activate, promote, or alter production Forecast selection; promotion execution, Learning Score mutation, and Decision Intelligence are **NOT ACTIVE**. The Phase 3C1 PostgreSQL eligibility/explicit-training boundary is verified; automatic triggering remains inactive.

---

# Revision - Phase 3C3B1A Champion Registry foundation

The Champion Registry is **DEVELOPMENT VERIFIED** as a bootstrap-only durable boundary. Its identity is company, material, and demand type; product level/group/class are immutable metadata snapshots. Initial entries represent the existing `demand_forecaster_auto_v1` classical strategy, not a fabricated XGBoost artifact. Champion identities and transitions are immutable, while the scoped current pointer is PostgreSQL-protected for future controlled promotion and rollback. Forecast resolution, promotion, rollback, automatic retraining/promotion, and production XGBoost activation are **NOT ACTIVE**. PHASE 3C1 PostgreSQL verification is complete.

# Revision - Phase 3C3B3A Champion Resolver

Champion Resolver is **DEVELOPMENT VERIFIED** as a read-only resolution boundary. It resolves same-company, material, and demand-type scoped classical or trusted XGBoost Champions; checksum/integrity, binary-missing, schema/version compatibility, and future-training-cutoff failures fall back only to the same-scope historical classical Champion. Fallback does not mutate registry state, model artifacts, Forecast evidence, or Learning state. No-classical scopes fail in a controlled manner, and tenant/demand-type isolation is verified. Production Forecast integration is **NOT ACTIVE**, rollback is pending Phase 3C3B3B, automatic retraining/promotion is **NOT ACTIVE**, and PHASE 3C1 PostgreSQL verification is complete.

---

# Revision - Phase 3C3B2 controlled Challenger promotion

Controlled Challenger promotion is **DEVELOPMENT VERIFIED** as explicit governance state only. An immutable `PROMOTE_CHALLENGER` decision and a trusted same-company artifact may atomically move the PostgreSQL current-pointer under a scoped lock; stale decisions and competing promotions cannot overwrite the winner. Champion entries and transitions remain immutable. Production Forecast activation, Champion resolution, rollback, automatic retraining/promotion, Learning mutation, and Decision Intelligence are **NOT ACTIVE**; PHASE 3C1 PostgreSQL verification is complete.

---

# Revision - Phase 3C3B3B1 production Champion Forecast scope

Production XGBoost Champion Forecast is **DEVELOPMENT VERIFIED**. A normal Business Workflow persists a `current_canonical` Forecast scope with an explicit demand type and derives its cutoff only from canonical accepted Actual evidence. The Forecast task alone resolves the scoped Champion and may invoke trusted XGBoost inference; its RuntimeResultReference and Forecast Vintage preserve the demand type, cutoff, Champion entry, ModelArtifact identity, and checksum provenance. Safety Stock, Supplier, Simulation, and Backtest do not resolve or invoke XGBoost.

`finished_good`, `semi_finished_good`, and `raw_material` production Forecast scopes are verified with explicit demand types; product level never infers demand type. Historical replay remains verified as a durable `replay_snapshot` sourced from a persisted execution, and arbitrary backdating and post-cutoff leakage remain prohibited. XGBoost fitting during production Forecast is zero. Automatic retraining, Challenger training/evaluation, promotion, Learning mutation, and Decision Intelligence are **NOT ACTIVE**. Controlled rollback is pending the next phase, and PHASE 3C1 PostgreSQL verification is complete.

---

# Revision - Phase 3C3B3B2 Controlled Champion Rollback

Controlled Champion Rollback is **DEVELOPMENT VERIFIED** as an explicit governance action. A caller supplies the exact expected current Champion and known destination; PostgreSQL locks the scoped current pointer, validates the destination, writes immutable `ROLLBACK` history, and advances the pointer atomically. Stale, concurrent, corrupt, incompatible, and cross-tenant/material/demand destination requests cannot mutate the pointer.

Rollback affects future Forecast resolution only: historical RuntimeResultReferences and Forecast Vintages remain immutable. A post-rollback Business Workflow resolves the new Champion only in its Forecast task; Safety Stock, Simulation, Supplier, and Backtest do not resolve Champions. Runtime resolver fallback is not rollback and never mutates registry state; an explicit rollback is required for a pointer change. Automatic rollback and automatic retraining/promotion remain **NOT ACTIVE**; PHASE 3C1 PostgreSQL verification is complete.
