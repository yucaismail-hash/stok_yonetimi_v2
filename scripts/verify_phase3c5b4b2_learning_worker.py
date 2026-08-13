"""Focused PostgreSQL proof for bounded durable Learning refresh workers."""
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.learning_evidence import LearningEvidenceService
from app.application.learning_refresh_delivery import LearningRefreshDeliveryService
from app.application.learning_refresh_orchestrator import LearningRefreshOrchestrator
from app.application.learning_refresh_worker import LearningRefreshWorker
from app.application.retraining_eligibility import RetrainingEligibilityService
from app.application.retraining_jobs import RetrainingJobRequest, RetrainingJobService
from app.database import SessionLocal
from app.models.actuals import ActualWeeklyObservation, ActualWeeklyRevision
from app.models.champion_registry import ChampionRegistryCurrent, ChampionRegistryEntry, ChampionRegistryTransition
from app.models.company import Company
from app.models.company_learning_memory_v2 import CompanyLearningMemoryV2
from app.models.forecast_evaluation import ForecastEvaluation
from app.models.forecast_vintage import ForecastVintage
from app.models.learning_evidence import LearningEvidence
from app.models.learning_refresh_delivery import LearningRefreshDelivery
from app.models.model_artifact import ModelArtifact
from app.models.pattern_learning_memory import PatternLearningMemory
from app.models.retraining_job import RetrainingJob
from app.models.runtime import RuntimeExecution, RuntimeResultReference, RuntimeTask, RuntimeTaskAttempt
from scripts.support.retraining_eligibility_fixture import cleanup_fixture, create_tier_shape
from scripts.support.rollback_xgboost_fixture import create as create_rollback_fixture, cleanup as cleanup_rollback_fixture


def _observation(root, material, demand, period):
    s = SessionLocal()
    try:
        return s.query(ActualWeeklyObservation).filter_by(company_id=root['company_id'], material_code=material,
            demand_type=demand, period=period).one().id
    finally:
        s.close()


def _correction(root, quantity, accepted=True):
    created = ActualWeeklyLedgerService().ingest_dataset_actuals(root['company_id'], root['user_id'], root['dataset_id'], [{
        'material_code': root['material_code'], 'period': root['end_period'], 'quantity': quantity,
        'product_level': root['product_level'], 'product_group': 'G', 'product_class': 'C',
    }], root['demand_type'])
    revision_id = created['revision_ids'][0]
    (ActualWeeklyLedgerService().approve_revision if accepted else ActualWeeklyLedgerService().reject_revision)(
        root['company_id'], revision_id, root['user_id'])
    return revision_id


def _terminal_job(root):
    s = SessionLocal()
    try:
        eligibility = next(row for row in RetrainingEligibilityService(s).evaluate(
            root['company_id'], root['demand_type'], root['start_period'], root['end_period'])
            if row.material_code == root['material_code'])
    finally:
        s.close()
    result = RetrainingJobService().accept_candidate(RetrainingJobRequest(
        root['company_id'], root['material_code'], root['demand_type'], root['start_period'], root['end_period'],
        '2026-W24', eligibility))
    assert result.status == 'CREATED'
    s = SessionLocal()
    try:
        job = s.query(RetrainingJob).filter_by(id=result.job_id, company_id=root['company_id']).one()
        job.state = 'not_trainable'; job.completed_at = datetime.now(timezone.utc); s.commit()
        return job.id
    finally:
        s.close()


def _delivery(company_id, evidence_id):
    s = SessionLocal()
    try:
        return s.query(LearningRefreshDelivery).filter_by(company_id=company_id, learning_evidence_id=evidence_id).one()
    finally:
        s.close()


def _expire(company_id, delivery_id):
    s = SessionLocal()
    try:
        row = s.query(LearningRefreshDelivery).filter_by(company_id=company_id, id=delivery_id).one()
        row.lease_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1); s.commit()
    finally:
        s.close()


def _projection(company_id):
    s = SessionLocal()
    try:
        company = s.query(CompanyLearningMemoryV2).filter_by(company_id=company_id).one_or_none()
        patterns = tuple((x.material_code, x.demand_type, x.row_version, x.source_pattern_fingerprint)
                         for x in s.query(PatternLearningMemory).filter_by(company_id=company_id)
                         .order_by(PatternLearningMemory.material_code, PatternLearningMemory.demand_type))
        return (None if company is None else (company.row_version, company.source_summary_fingerprint,
                                               company.evidence_maturity_score), patterns)
    finally:
        s.close()


def _unrelated_counts(company_id):
    s = SessionLocal()
    try:
        return (
            s.query(RuntimeExecution).filter_by(company_id=company_id).count(),
            s.query(RuntimeTask).filter_by(company_id=company_id).count(),
            s.query(RuntimeTaskAttempt).filter_by(company_id=company_id).count(),
            s.query(RuntimeResultReference).filter_by(company_id=company_id).count(),
            s.query(ForecastVintage).filter_by(company_id=company_id).count(),
            s.query(ForecastEvaluation).filter_by(company_id=company_id).count(),
            s.query(RetrainingJob).filter_by(company_id=company_id).count(),
            s.query(ModelArtifact).filter_by(company_id=company_id).count(),
            s.query(ChampionRegistryEntry).filter_by(company_id=company_id).count(),
            s.query(ChampionRegistryCurrent).filter_by(company_id=company_id).count(),
            s.query(ChampionRegistryTransition).filter_by(company_id=company_id).count(),
        )
    finally:
        s.close()


def _clear(root):
    s = SessionLocal()
    try:
        s.query(CompanyLearningMemoryV2).filter_by(company_id=root['company_id']).delete(synchronize_session=False)
        s.query(PatternLearningMemory).filter_by(company_id=root['company_id']).delete(synchronize_session=False)
        s.query(LearningRefreshDelivery).filter_by(company_id=root['company_id']).delete(synchronize_session=False)
        for evidence in s.query(LearningEvidence).filter_by(company_id=root['company_id']).order_by(
                LearningEvidence.recorded_at.desc(), LearningEvidence.id.desc()).all():
            s.delete(evidence); s.flush()
        s.query(RetrainingJob).filter_by(company_id=root['company_id']).delete(synchronize_session=False)
        s.commit(); cleanup_fixture(s, type('FixtureIds', (), root)())
    finally:
        s.close()


class _FailOnceOrchestrator:
    remaining = 1

    def orchestrate(self, company_id, evidence_id):
        if _FailOnceOrchestrator.remaining:
            _FailOnceOrchestrator.remaining -= 1
            raise RuntimeError('INJECTED_RETRYABLE_ORCHESTRATOR_FAILURE')
        return LearningRefreshOrchestrator().orchestrate(company_id, evidence_id)


async def main():
    roots = []; rollback_ids = rollback_refs = None
    try:
        root = await create_tier_shape('tier3', 8, 'SKU', 'sales'); roots.append(root)
        other = await create_tier_shape('tier3', 8, 'SKU', 'sales'); roots.append(other)
        evidence = LearningEvidenceService()
        delivery_service = LearningRefreshDeliveryService(lease_seconds=30, max_attempts=3)
        worker = LearningRefreshWorker('worker-main', delivery_service)

        # A/B: one pending actual item claims, refreshes Pattern before Company, and completes.
        accepted = evidence.record_actual_accepted(root['company_id'], _observation(root, 'SKU', 'sales', '2026-W28'))
        actual_delivery = _delivery(root['company_id'], accepted.evidence_id)
        before_actual = _projection(root['company_id']); unrelated_before = _unrelated_counts(root['company_id'])
        actual_result = worker.process_next(root['company_id'])
        assert actual_result.status == 'COMPLETED' and actual_result.delivery_id == actual_delivery.id
        after_actual = _projection(root['company_id']); persisted = _delivery(root['company_id'], accepted.evidence_id)
        assert before_actual[0] is None and after_actual[1] and persisted.state == 'completed' and persisted.worker_id == 'worker-main'
        assert persisted.last_outcome['event_type'] == 'ACTUAL_ACCEPTED' and persisted.last_outcome['pattern_status'] == 'CREATED' and persisted.last_outcome['company_status'] == 'CREATED'
        assert _unrelated_counts(root['company_id']) == unrelated_before

        # F: true competing worker acquisition on one delivery has one effective owner.
        concurrent_event = evidence.record_actual_accepted(root['company_id'], _observation(root, 'SKU', 'sales', '2026-W27'))
        barrier = threading.Barrier(2)
        def compete(worker_id):
            barrier.wait(); return LearningRefreshWorker(worker_id, LearningRefreshDeliveryService(lease_seconds=30)).process_next(root['company_id'])
        with ThreadPoolExecutor(max_workers=2) as pool:
            competition = list(pool.map(compete, ('worker-a', 'worker-b')))
        assert sorted(x.status for x in competition) == ['COMPLETED', 'NO_WORK']
        assert _delivery(root['company_id'], concurrent_event.evidence_id).state == 'completed'

        # C/E/G: company-only routes remain Pattern-free and a bounded batch consumes at most its limit.
        forecast = evidence.record_forecast_evaluated(root['company_id'], root['evaluation_id'])
        job = evidence.record_retraining_completed(root['company_id'], _terminal_job(root))
        patterns_before_company_only = _projection(root['company_id'])[1]
        batch = worker.process_batch(root['company_id'], limit=2)
        assert len(batch) == 2 and all(x.status == 'COMPLETED' for x in batch)
        assert _delivery(root['company_id'], forecast.evidence_id).state == 'completed'
        assert _delivery(root['company_id'], job.evidence_id).state == 'completed'
        assert _projection(root['company_id'])[1] == patterns_before_company_only
        assert worker.process_batch(root['company_id'], limit=2) == ()

        # H: failure is delivery-policy retryable; fresh worker succeeds without corrupting projections.
        retry_event = evidence.record_actual_accepted(root['company_id'], _observation(root, 'SKU', 'sales', '2026-W26'))
        retry_delivery = _delivery(root['company_id'], retry_event.evidence_id)
        failed = LearningRefreshWorker('flaky-worker', LearningRefreshDeliveryService(
            lease_seconds=30, orchestrator_factory=_FailOnceOrchestrator)).process_next(root['company_id'])
        assert failed.status == 'RETRY_PENDING' and _delivery(root['company_id'], retry_event.evidence_id).state == 'pending'
        retry = LearningRefreshWorker('retry-worker', LearningRefreshDeliveryService(lease_seconds=30)).process_next(root['company_id'])
        assert retry.status == 'COMPLETED' and _delivery(root['company_id'], retry_event.evidence_id).attempt_count == 2

        # I: deterministic missing source terminalizes; no infinite retry exists.
        bad_rows = [{'material_code': 'BAD', 'period': f'2026-W{week:02d}', 'quantity': 50,
                     'product_level': 'finished_good', 'product_group': 'G', 'product_class': 'C'} for week in range(1, 9)]
        ActualWeeklyLedgerService().ingest_dataset_actuals(root['company_id'], root['user_id'], root['dataset_id'], bad_rows, 'sales')
        bad_event = evidence.record_actual_accepted(root['company_id'], _observation(root, 'BAD', 'sales', '2026-W08'))
        s = SessionLocal()
        try:
            oid = _observation(root, 'BAD', 'sales', '2026-W08')
            s.query(ActualWeeklyRevision).filter_by(company_id=root['company_id'], observation_id=oid).delete(synchronize_session=False)
            s.query(ActualWeeklyObservation).filter_by(id=oid, company_id=root['company_id']).delete(synchronize_session=False); s.commit()
        finally:
            s.close()
        bad_result = worker.process_next(root['company_id'])
        assert bad_result.status == 'FAILED_TERMINAL' and _delivery(root['company_id'], bad_event.evidence_id).state == 'failed'
        assert worker.process_next(root['company_id']).status == 'NO_WORK'

        # J/K/L: healthy heartbeat blocks reclaim; expired lease lets a fresh worker finish and stale token is rejected.
        lease_event = evidence.record_actual_accepted(root['company_id'], _observation(root, 'SKU', 'sales', '2026-W25'))
        lease_delivery = _delivery(root['company_id'], lease_event.evidence_id)
        claim_a = delivery_service.claim(root['company_id'], lease_delivery.id, 'worker-lease-a'); assert claim_a.status == 'CLAIMED'
        assert delivery_service.heartbeat(root['company_id'], lease_delivery.id, claim_a.claim_token).status == 'HEARTBEAT'
        assert LearningRefreshWorker('worker-lease-b', LearningRefreshDeliveryService(lease_seconds=30)).process_next(root['company_id']).status == 'NO_WORK'
        _expire(root['company_id'], lease_delivery.id)
        reclaim = LearningRefreshWorker('worker-lease-b', LearningRefreshDeliveryService(lease_seconds=30)).process_next(root['company_id'])
        assert reclaim.status == 'COMPLETED'
        for stale in (lambda: delivery_service.heartbeat(root['company_id'], lease_delivery.id, claim_a.claim_token),
                      lambda: delivery_service.complete(root['company_id'], lease_delivery.id, claim_a.claim_token, {})):
            try: stale(); raise AssertionError('stale worker mutated current delivery')
            except Exception as exc: assert type(exc).__name__ == 'LearningRefreshDeliveryLeaseError'

        # M: crash after successful orchestration but before complete: lease expiry re-runs idempotently and completes.
        crash_event = evidence.record_actual_accepted(root['company_id'], _observation(root, 'SKU', 'sales', '2026-W24'))
        crash_delivery = _delivery(root['company_id'], crash_event.evidence_id)
        crash_claim = delivery_service.claim(root['company_id'], crash_delivery.id, 'crash-worker'); assert crash_claim.status == 'CLAIMED'
        assert LearningRefreshOrchestrator().orchestrate(root['company_id'], crash_event.evidence_id).outcome == 'COMPLETED'
        projection_after_crash = _projection(root['company_id']); _expire(root['company_id'], crash_delivery.id)
        crash_retry = LearningRefreshWorker('crash-recovery', LearningRefreshDeliveryService(lease_seconds=30)).process_next(root['company_id'])
        assert crash_retry.status == 'COMPLETED' and _projection(root['company_id']) == projection_after_crash

        # N/O/P: non-ideal delivery order is safe; accepted correction processes, rejected creates no work.
        older = evidence.record_actual_corrected(root['company_id'], _correction(root, 121, True))
        newer = evidence.record_actual_corrected(root['company_id'], _correction(root, 131, True))
        for event, name in ((newer, 'newer-worker'), (older, 'older-worker')):
            item = _delivery(root['company_id'], event.evidence_id)
            claim = delivery_service.claim(root['company_id'], item.id, name); assert claim.status == 'CLAIMED'
            assert LearningRefreshWorker(name, delivery_service).process_claimed(root['company_id'], item.id, claim.claim_token).status == 'COMPLETED'
        accepted_correction = evidence.record_actual_corrected(root['company_id'], _correction(root, 141, True))
        assert worker.process_next(root['company_id']).status == 'COMPLETED' and _delivery(root['company_id'], accepted_correction.evidence_id).state == 'completed'
        rejected = _correction(root, 151, False); delivery_count = len([x for x in (evidence.list_scope(root['company_id']) if True else ())])
        try: evidence.record_actual_corrected(root['company_id'], rejected); raise AssertionError('rejected correction created LearningEvidence')
        except ValueError: pass
        assert len(evidence.list_scope(root['company_id'])) == delivery_count and worker.process_next(root['company_id']).status == 'NO_WORK'

        # D: Champion promotion delivery is company-only and is consumed by the same worker.
        rollback_ids, rollback_refs = create_rollback_fixture(); s = SessionLocal()
        try: promotion_id = s.query(ChampionRegistryTransition).filter_by(company_id=rollback_ids.company_id, transition_type='PROMOTION').first().id
        finally: s.close()
        promoted = evidence.record_champion_promotion(rollback_ids.company_id, promotion_id)
        champion_result = LearningRefreshWorker('champion-worker').process_next(rollback_ids.company_id)
        assert champion_result.status == 'COMPLETED' and _delivery(rollback_ids.company_id, promoted.evidence_id).last_outcome['pattern_status'] is None

        # Q/R/S/T: tenant scope is hard, fresh process rebuilds from delivery, and delivery is the only work authority.
        other_event = evidence.record_actual_accepted(other['company_id'], _observation(other, 'SKU', 'sales', '2026-W28'))
        assert LearningRefreshWorker('tenant-a').process_next(root['company_id']).status == 'NO_WORK'
        fresh = LearningRefreshWorker('fresh-other-worker').process_next(other['company_id']); assert fresh.status == 'COMPLETED'
        delivered = _delivery(other['company_id'], other_event.evidence_id)
        assert delivered.company_id == other['company_id'] and delivered.learning_evidence_id == other_event.evidence_id and delivered.state == 'completed'
        assert _unrelated_counts(root['company_id'])[:6] == unrelated_before[:6]
        print('PHASE 3C5B4B2 PROBE PASS', {
            'actual': actual_result.status, 'batch': len(batch), 'retry': retry.status, 'terminal': bad_result.status,
            'reclaim': reclaim.status, 'crash_retry': crash_retry.status, 'promotion': champion_result.status,
            'tenant': fresh.status,
        }, flush=True)
    finally:
        if rollback_ids:
            s = SessionLocal()
            try:
                s.query(CompanyLearningMemoryV2).filter_by(company_id=rollback_ids.company_id).delete(synchronize_session=False)
                s.query(LearningRefreshDelivery).filter_by(company_id=rollback_ids.company_id).delete(synchronize_session=False)
                s.query(LearningEvidence).filter_by(company_id=rollback_ids.company_id).delete(synchronize_session=False); s.commit()
            finally: s.close()
            cleanup_rollback_fixture(rollback_ids, rollback_refs)
        for root in reversed(roots): _clear(root)
        s = SessionLocal()
        try: assert all(s.query(Company).filter_by(id=root['company_id']).count() == 0 for root in roots)
        finally: s.close()


if __name__ == '__main__':
    asyncio.run(main())
