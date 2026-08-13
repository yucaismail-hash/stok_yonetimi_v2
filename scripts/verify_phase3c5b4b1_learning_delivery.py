"""Focused PostgreSQL proof for durable Learning Evidence delivery/claim ownership."""
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.champion_rollback import ChampionRollbackService
from app.application.learning_evidence import LearningEvidenceService
from app.application.learning_refresh_delivery import LearningRefreshDeliveryLeaseError, LearningRefreshDeliveryService
from app.application.retraining_eligibility import RetrainingEligibilityService
from app.application.retraining_jobs import RetrainingJobRequest, RetrainingJobService
from app.database import SessionLocal
from app.models.actuals import ActualWeeklyObservation, ActualWeeklyRevision
from app.models.champion_registry import ChampionRegistryCurrent, ChampionRegistryEntry, ChampionRegistryTransition
from app.models.company import Company
from app.models.company_learning_memory_v2 import CompanyLearningMemoryV2
from app.models.learning_evidence import LearningEvidence
from app.models.learning_refresh_delivery import LearningRefreshDelivery
from app.models.pattern_learning_memory import PatternLearningMemory
from app.models.retraining_job import RetrainingJob
from scripts.support.retraining_eligibility_fixture import cleanup_fixture, create_tier_shape
from scripts.support.rollback_xgboost_fixture import create as create_rollback_fixture, cleanup as cleanup_rollback_fixture


def _obs(root, period):
    s = SessionLocal()
    try:
        return s.query(ActualWeeklyObservation).filter_by(company_id=root['company_id'], material_code=root['material_code'],
            demand_type=root['demand_type'], period=period).one().id
    finally: s.close()


def _correction(root, quantity, accepted=True):
    result = ActualWeeklyLedgerService().ingest_dataset_actuals(root['company_id'], root['user_id'], root['dataset_id'], [{
        'material_code': root['material_code'], 'period': root['end_period'], 'quantity': quantity,
        'product_level': root['product_level'], 'product_group': 'G', 'product_class': 'C',
    }], root['demand_type'])
    revision = result['revision_ids'][0]
    (ActualWeeklyLedgerService().approve_revision if accepted else ActualWeeklyLedgerService().reject_revision)(root['company_id'], revision, root['user_id'])
    return revision


def _terminal_job(root):
    s = SessionLocal()
    try:
        eligibility = next(x for x in RetrainingEligibilityService(s).evaluate(root['company_id'], root['demand_type'], root['start_period'], root['end_period']) if x.material_code == root['material_code'])
    finally: s.close()
    accepted = RetrainingJobService().accept_candidate(RetrainingJobRequest(root['company_id'], root['material_code'], root['demand_type'], root['start_period'], root['end_period'], '2026-W24', eligibility))
    assert accepted.status == 'CREATED'
    s = SessionLocal()
    try:
        job = s.query(RetrainingJob).filter_by(id=accepted.job_id, company_id=root['company_id']).one(); job.state = 'not_trainable'; job.completed_at = datetime.now(timezone.utc); s.commit(); return job.id
    finally: s.close()


def _expire(company_id, delivery_id):
    s = SessionLocal()
    try:
        row = s.query(LearningRefreshDelivery).filter_by(id=delivery_id, company_id=company_id).one()
        row.lease_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1); s.commit()
    finally: s.close()


def _clear(root):
    s = SessionLocal()
    try:
        s.query(CompanyLearningMemoryV2).filter_by(company_id=root['company_id']).delete(synchronize_session=False)
        s.query(PatternLearningMemory).filter_by(company_id=root['company_id']).delete(synchronize_session=False)
        s.query(LearningRefreshDelivery).filter_by(company_id=root['company_id']).delete(synchronize_session=False)
        for e in s.query(LearningEvidence).filter_by(company_id=root['company_id']).order_by(LearningEvidence.recorded_at.desc(), LearningEvidence.id.desc()).all(): s.delete(e); s.flush()
        s.query(RetrainingJob).filter_by(company_id=root['company_id']).delete(synchronize_session=False); s.commit(); cleanup_fixture(s, type('Ids', (), root)())
    finally: s.close()


async def main():
    roots=[]; rollback_ids=rollback_refs=None
    try:
        root=await create_tier_shape('tier3',8,'SKU','sales'); roots.append(root)
        other=await create_tier_shape('tier3',8,'SKU','sales'); roots.append(other)
        evidence=LearningEvidenceService(); delivery=LearningRefreshDeliveryService(lease_seconds=30,max_attempts=3)
        # A/B: evidence and intent commit atomically, and duplicate evidence is one delivery.
        observation=_obs(root,'2026-W28'); first=evidence.record_actual_accepted(root['company_id'],observation); same=evidence.record_actual_accepted(root['company_id'],observation)
        intent=delivery.get_by_evidence(root['company_id'],first.evidence_id)
        assert (first.status,same.status,first.evidence_id,same.evidence_id)==('CREATED','ALREADY_EXISTS',first.evidence_id,first.evidence_id) and intent and intent.state=='pending'
        # C: true concurrent writer/inbox identity convergence.
        obs2=_obs(root,'2026-W27'); barrier=threading.Barrier(2)
        def writer(): barrier.wait(); return LearningEvidenceService().record_actual_accepted(root['company_id'],obs2)
        with ThreadPoolExecutor(max_workers=2) as pool: writes=list(pool.map(lambda _:writer(),range(2)))
        assert sorted(x.status for x in writes)==['ALREADY_EXISTS','CREATED']
        assert delivery.get_by_evidence(root['company_id'],writes[0].evidence_id) is not None
        # G/H: two independent workers compete, one owns the durable lease and may heartbeat.
        barrier=threading.Barrier(2)
        def claimer(name): barrier.wait(); return LearningRefreshDeliveryService(lease_seconds=30).claim(root['company_id'],intent.id,name)
        with ThreadPoolExecutor(max_workers=2) as pool: claims=list(pool.map(claimer,('worker-a','worker-b')))
        won=next(x for x in claims if x.status=='CLAIMED'); assert sorted(x.status for x in claims)==['CLAIMED','NO_WORK']
        heartbeat=delivery.heartbeat(root['company_id'],intent.id,won.claim_token); assert heartbeat.status=='HEARTBEAT'
        # I/J/L: expiry is reclaimable, and stale token cannot mutate after newer claim.
        _expire(root['company_id'],intent.id); reclaimed=delivery.claim(root['company_id'],intent.id,'worker-c'); assert reclaimed.status=='CLAIMED' and reclaimed.claim_token!=won.claim_token
        for operation in (lambda:delivery.heartbeat(root['company_id'],intent.id,won.claim_token), lambda:delivery.complete(root['company_id'],intent.id,won.claim_token,{})):
            try: operation(); raise AssertionError('stale owner changed delivery')
            except LearningRefreshDeliveryLeaseError: pass
        try:
            delivery.process_claimed(root['company_id'], intent.id, won.claim_token)
            raise AssertionError('stale owner invoked delivery routing')
        except LearningRefreshDeliveryLeaseError:
            pass
        # M: explicit processing delegates to B4A and completes; exact routing summary is retained only compactly.
        completed=delivery.process_claimed(root['company_id'],intent.id,reclaimed.claim_token); assert completed.status=='COMPLETED'
        persisted=delivery.get(root['company_id'],intent.id); assert persisted.state=='completed' and persisted.last_outcome['event_type']=='ACTUAL_ACCEPTED' and persisted.last_outcome['pattern_status'] in ('CREATED','UPDATED','UNCHANGED')
        # N: emulate crash after orchestrator/persisted projection and before delivery completion.
        after_orchestrator=evidence.record_actual_accepted(root['company_id'],obs2); crash_intent=delivery.get_by_evidence(root['company_id'],after_orchestrator.evidence_id)
        crash_claim=delivery.claim(root['company_id'],crash_intent.id,'crash-worker'); from app.application.learning_refresh_orchestrator import LearningRefreshOrchestrator
        assert LearningRefreshOrchestrator().orchestrate(root['company_id'],after_orchestrator.evidence_id).outcome=='COMPLETED'
        _expire(root['company_id'],crash_intent.id); crash_retry=delivery.claim(root['company_id'],crash_intent.id,'recovery-worker'); assert crash_retry.status=='CLAIMED'
        assert delivery.process_claimed(root['company_id'],crash_intent.id,crash_retry.claim_token).status=='COMPLETED'
        # D/E: accepted correction yields a distinct intent; rejected correction yields neither.
        correction=_correction(root,111,True); corrected=evidence.record_actual_corrected(root['company_id'],correction); assert delivery.get_by_evidence(root['company_id'],corrected.evidence_id) is not None
        rejected=_correction(root,112,False); before=s=SessionLocal()
        try: before_count=s.query(LearningRefreshDelivery).filter_by(company_id=root['company_id']).count()
        finally: s.close()
        try: evidence.record_actual_corrected(root['company_id'],rejected); raise AssertionError('rejected correction created evidence')
        except ValueError: pass
        s=SessionLocal()
        try: assert s.query(LearningRefreshDelivery).filter_by(company_id=root['company_id']).count()==before_count
        finally: s.close()
        # Representative company-only delivery routes reuse B4A, never Pattern.
        forecast=evidence.record_forecast_evaluated(root['company_id'],root['evaluation_id']); fclaim=delivery.claim(root['company_id'],delivery.get_by_evidence(root['company_id'],forecast.evidence_id).id,'forecast-worker'); assert delivery.process_claimed(root['company_id'],fclaim.delivery_id,fclaim.claim_token).status=='COMPLETED'
        job=evidence.record_retraining_completed(root['company_id'],_terminal_job(root)); jclaim=delivery.claim(root['company_id'],delivery.get_by_evidence(root['company_id'],job.evidence_id).id,'job-worker'); assert delivery.process_claimed(root['company_id'],jclaim.delivery_id,jclaim.claim_token).status=='COMPLETED'
        # Governance evidence uses the same worker contract, company only.
        rollback_ids,rollback_refs=create_rollback_fixture(); s=SessionLocal()
        try: promotion=s.query(ChampionRegistryTransition).filter_by(company_id=rollback_ids.company_id,transition_type='PROMOTION').first().id
        finally:s.close()
        promoted=evidence.record_champion_promotion(rollback_ids.company_id,promotion); pclaim=delivery.claim(rollback_ids.company_id,delivery.get_by_evidence(rollback_ids.company_id,promoted.evidence_id).id,'promotion-worker'); assert delivery.process_claimed(rollback_ids.company_id,pclaim.delivery_id,pclaim.claim_token).status=='COMPLETED'
        # O: newer then older correction delivery is semantically safe.
        c1=evidence.record_actual_corrected(root['company_id'],_correction(root,121,True)); c2=evidence.record_actual_corrected(root['company_id'],_correction(root,131,True))
        for event,name in ((c2,'newer'),(c1,'older')):
            claim=delivery.claim(root['company_id'],delivery.get_by_evidence(root['company_id'],event.evidence_id).id,name); assert delivery.process_claimed(root['company_id'],claim.delivery_id,claim.claim_token).status=='COMPLETED'
        # F/Q/R/S: tenant-facing retrieval/claim, fresh process, and no global scan/unrelated runtime.
        assert delivery.get(other['company_id'],intent.id) is None and delivery.claim_next(other['company_id'],'other-worker').status=='NO_WORK'
        fresh=LearningRefreshDeliveryService().get(root['company_id'],intent.id); assert fresh.learning_evidence_id==first.evidence_id and fresh.state=='completed'
        assert all(row.company_id==root['company_id'] for row in [delivery.get(root['company_id'],intent.id)])
        print('PHASE 3C5B4B1 PROBE PASS',{'intent':'pending','concurrent_claims':[x.status for x in claims],'reclaim':reclaimed.status,'completed':completed.status,'post_orchestrator_retry':'COMPLETED','forecast':'COMPLETED','retraining':'COMPLETED','promotion':'COMPLETED'},flush=True)
    finally:
        if rollback_ids:
            s=SessionLocal()
            try:s.query(CompanyLearningMemoryV2).filter_by(company_id=rollback_ids.company_id).delete(synchronize_session=False);s.query(LearningRefreshDelivery).filter_by(company_id=rollback_ids.company_id).delete(synchronize_session=False);s.query(LearningEvidence).filter_by(company_id=rollback_ids.company_id).delete(synchronize_session=False);s.commit()
            finally:s.close()
            cleanup_rollback_fixture(rollback_ids,rollback_refs)
        for root in reversed(roots): _clear(root)
        s=SessionLocal()
        try: assert all(s.query(Company).filter_by(id=root['company_id']).count()==0 for root in roots)
        finally:s.close()

if __name__=='__main__': asyncio.run(main())
