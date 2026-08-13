"""Focused durable-delivery proof for incremental Supplier Learning refresh."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import sys, threading

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.learning_evidence import LearningEvidenceService
from app.application.learning_refresh_delivery import LearningRefreshDeliveryService, LearningRefreshDeliveryLeaseError
from app.application.learning_refresh_orchestrator import LearningRefreshOrchestrator
from app.application.learning_refresh_worker import LearningRefreshWorker
from app.application.supplier_delivery_observations import SupplierDeliveryObservationService
from app.application.supplier_learning_materialization import SupplierLearningMaterializationService
from app.database import SessionLocal
from app.models.learning_evidence import LearningEvidence
from app.models.learning_refresh_delivery import LearningRefreshDelivery
from app.models.supplier_learning_memory import SupplierLearningMemory
from scripts.verify_phase3c6b2_supplier_learning import fixture, cleanup, cleanup_interrupted_fixtures, add_series, side_counts


def cleanup_delivery(root):
    s=SessionLocal()
    try:
        evidence=[row.id for row in s.query(LearningEvidence).filter_by(company_id=root['company_id']).all()]
        if evidence: s.query(LearningRefreshDelivery).filter(LearningRefreshDelivery.learning_evidence_id.in_(evidence)).delete(synchronize_session=False)
        s.query(LearningEvidence).filter_by(company_id=root['company_id']).delete(synchronize_session=False)
        s.query(SupplierLearningMemory).filter_by(company_id=root['company_id']).delete(synchronize_session=False)
        s.commit()
    finally: s.close()
    cleanup(root)


def current(root,supplier,material):
    return SupplierLearningMaterializationService().get_current(root['company_id'],root['suppliers'][supplier],material)


def main():
    roots=[]
    try:
        cleanup_interrupted_fixtures(); root=fixture('refresh_a'); roots.append(root); other=fixture('refresh_b'); roots.append(other)
        # Three dirty scopes plus a never-delivered control scope.
        ax=add_series(root,'A','X',[5]*8,prefix='ax'); add_series(root,'A','Y',[5]*8,prefix='ay')
        bx=add_series(root,'B','X',[2,10]*4,prefix='bx'); add_series(root,'C','Y',[5]*8,prefix='control')
        evidence=LearningEvidenceService(); delivery=LearningRefreshDeliveryService(); worker=LearningRefreshWorker('supplier-worker',delivery)
        # A/B/F/K/O: one observed delivery creates atomic evidence+intent, refreshes only AX, and retry converges.
        observed=evidence.record_supplier_delivery_observed(root['company_id'],ax[-1]); assert observed.status=='CREATED'
        duplicate=evidence.record_supplier_delivery_observed(root['company_id'],ax[-1]); assert duplicate.status=='ALREADY_EXISTS' and duplicate.evidence_id==observed.evidence_id
        d=delivery.get_by_evidence(root['company_id'],observed.evidence_id); assert d is not None and d.state=='pending'
        done=worker.process_next(root['company_id']); assert done.status=='COMPLETED'
        ax_memory=current(root,'A','X'); assert ax_memory and ax_memory.row_version==1
        assert current(root,'A','Y') is None and current(root,'B','X') is None and current(root,'C','Y') is None
        assert worker.process_next(root['company_id']).status=='NO_WORK'
        # C/D/E: accepted corrections generate superseding evidence; rejected creates none and refresh is unchanged.
        writer=SupplierDeliveryObservationService()
        dr=writer.propose_correction(root['company_id'],ax[0],root['user_id'],actual_receipt_date=date(2026,1,4)); writer.accept_correction(root['company_id'],dr.revision_id,root['user_id'])
        corrected=evidence.record_supplier_delivery_corrected(root['company_id'],dr.revision_id); assert corrected.status=='CREATED'
        assert worker.process_next(root['company_id']).status=='COMPLETED'; after_date=current(root,'A','X'); assert after_date.row_version==2
        qr=writer.propose_correction(root['company_id'],ax[1],root['user_id'],received_quantity=80); writer.accept_correction(root['company_id'],qr.revision_id,root['user_id'])
        evidence.record_supplier_delivery_corrected(root['company_id'],qr.revision_id); assert worker.process_next(root['company_id']).status=='COMPLETED'; assert current(root,'A','X').row_version==3
        rr=writer.propose_correction(root['company_id'],ax[2],root['user_id'],received_quantity=50); writer.reject_correction(root['company_id'],rr.revision_id,root['user_id'])
        assert SupplierLearningMaterializationService().materialize(root['company_id'],root['suppliers']['A'],'X',current(root,'A','X').cutoff_date).status=='UNCHANGED'
        # G/H: independent refresh calls converge and old cutoff cannot overwrite later projection.
        add_series(root,'A','X',[7],start=date(2026,8,1),prefix='newer')
        newer=SupplierLearningMaterializationService().materialize(root['company_id'],root['suppliers']['A'],'X',date(2026,12,31)); assert newer.status=='UPDATED'
        stale=SupplierLearningMaterializationService().materialize(root['company_id'],root['suppliers']['A'],'X',date(2026,6,30)); assert stale.status=='STALE_RESULT'
        barrier=threading.Barrier(2)
        add_series(root,'F','Y',[5]*8,prefix='race')
        def race(): barrier.wait(); return SupplierLearningMaterializationService().materialize(root['company_id'],root['suppliers']['F'],'Y',date(2026,12,31))
        with ThreadPoolExecutor(max_workers=2) as pool: raced=list(pool.map(lambda _:race(),range(2)))
        assert sorted(x.status for x in raced)==['CREATED','UNCHANGED']
        # I/J/M/Q: failure before route is retryable; post-write lost response retries unchanged; lease reclaim rejects stale token.
        by=evidence.record_supplier_delivery_observed(root['company_id'],bx[-1])
        claim=delivery.claim_next(root['company_id'],'manual-fail'); assert claim.status=='CLAIMED'
        assert delivery.fail(root['company_id'],claim.delivery_id,claim.claim_token,RuntimeError('before-write')).status=='RETRY_PENDING'
        assert worker.process_next(root['company_id']).status=='COMPLETED'
        replay=LearningRefreshOrchestrator().orchestrate(root['company_id'],by.evidence_id); assert replay.supplier_status=='UNCHANGED'
        clock=[datetime(2026,1,1,tzinfo=timezone.utc)]; leased=LearningRefreshDeliveryService(lease_seconds=1,now_factory=lambda:clock[0])
        # Create a distinct valid insufficiency event: it may complete with NOT_MATERIALIZED.
        small=add_series(other,'A','X',[5]*3,prefix='small')
        small_ev=evidence.record_supplier_delivery_observed(other['company_id'],small[-1]); first=leased.claim_next(other['company_id'],'w1'); clock[0]+=timedelta(seconds=2); second=leased.claim_next(other['company_id'],'w2')
        assert second.status=='CLAIMED'
        try: leased.complete(other['company_id'],first.delivery_id,first.claim_token,{}) ; raise AssertionError('stale lease completed')
        except LearningRefreshDeliveryLeaseError: pass
        assert leased.process_claimed(other['company_id'],second.delivery_id,second.claim_token).status=='COMPLETED'
        assert current(other,'A','X') is None
        # L/N/P/R/S/U: explicit three scope delivery, tenant isolation, no global routing, and no downstream state.
        for supplier,material,oid in (('A','Y',add_series(root,'A','Y',[6],start=date(2026,8,1),prefix='aynew')[-1]),):
            evidence.record_supplier_delivery_observed(root['company_id'],oid)
        batch=worker.process_batch(root['company_id'],limit=3); assert len(batch)==1 and all(row.status=='COMPLETED' for row in batch)
        assert current(root,'A','Y') and current(root,'B','X') and current(root,'C','Y') is None
        assert current(other,'A','X') is None
        # Evidence/delivery are the intended durable routing boundary; all
        # operational downstream tables remain untouched.
        counts=side_counts(root['company_id']); assert counts[2:7]==(0,0,0,0,0) and counts[7] >= 4 and counts[8] >= 4 and counts[9] == 0
        print('PHASE 3C6B4 PROBE PASS',{'observed':observed.status,'correction':corrected.status,'race':[x.status for x in raced],'batch':len(batch),'ax_version':current(root,'A','X').row_version},flush=True)
    finally:
        for root in reversed(roots): cleanup_delivery(root)

if __name__=='__main__': main()
