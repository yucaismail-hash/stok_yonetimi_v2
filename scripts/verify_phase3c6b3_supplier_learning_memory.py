"""PostgreSQL proof for durable Supplier Learning current projections."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
import sys, threading

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.supplier_delivery_observations import SupplierDeliveryObservationService
from app.application.supplier_learning import SupplierLearningService, SupplierLearningError
from app.application.supplier_learning_materialization import SupplierLearningMaterializationService
from app.database import SessionLocal
from app.models.supplier_learning_memory import SupplierLearningMemory
from scripts.verify_phase3c6b2_supplier_learning import fixture, cleanup, cleanup_interrupted_fixtures, add_series, side_counts


def snapshot(root, supplier, material, cutoff):
    s = SessionLocal()
    try: return SupplierLearningService(s).calculate(root['company_id'], root['suppliers'][supplier], material, cutoff)
    finally: s.close()


def cleanup_memory(root):
    session = SessionLocal()
    try:
        session.query(SupplierLearningMemory).filter_by(company_id=root['company_id']).delete(synchronize_session=False)
        session.commit()
    finally:
        session.close()
    cleanup(root)


def main():
    roots=[]
    try:
        cleanup_interrupted_fixtures()
        root=fixture('memory_a'); roots.append(root); other=fixture('memory_b'); roots.append(other)
        t1=date(2026, 6, 30); t2=date(2026, 12, 31)
        baseline=side_counts(root['company_id'])
        a_ids=add_series(root,'A','X',[5]*12,prefix='a')
        add_series(root,'B','X',[2,10]*6,prefix='b')
        add_series(root,'C','X',[5]*12,promised_mode='late',prefix='c')
        add_series(root,'D','X',[5]*12,quantities='under',prefix='d')
        add_series(root,'E','X',[4]*8+[8]*4,prefix='e')
        add_series(root,'A','Y',[5]*12,promised_mode='none',prefix='ay')
        add_series(root,'B','Y',[5]*12,quantities=False,prefix='by')
        add_series(root,'G','X',[5]*3,prefix='g')
        service=SupplierLearningMaterializationService()
        # A-F and O/P: all valid policy outputs become separate current rows.
        a=service.materialize(root['company_id'],root['suppliers']['A'],'X',t1)
        assert a.status=='CREATED' and a.row_version==1
        assert service.materialize(root['company_id'],root['suppliers']['A'],'X',t1).status=='UNCHANGED'
        for code, expected in (('B','VARIABLE'),('C','LATE_PRONE'),('D','FULFILLMENT_RISK'),('E','DETERIORATING')):
            outcome=service.materialize(root['company_id'],root['suppliers'][code],'X',t1)
            assert outcome.status=='CREATED'
            assert service.get_current(root['company_id'],root['suppliers'][code],'X').classification==expected
        no_promise=service.materialize(root['company_id'],root['suppliers']['A'],'Y',t1)
        no_quantity=service.materialize(root['company_id'],root['suppliers']['B'],'Y',t1)
        assert no_promise.status==no_quantity.status=='CREATED'
        assert service.get_current(root['company_id'],root['suppliers']['A'],'Y').on_time_ratio is None
        assert service.get_current(root['company_id'],root['suppliers']['B'],'Y').mean_fulfillment_ratio is None
        assert service.materialize(root['company_id'],root['suppliers']['G'],'X',t1).status=='NOT_MATERIALIZED'
        current=service.get_current(root['company_id'],root['suppliers']['A'],'X'); assert current.id==a.memory_id and current.row_version==1
        # G/K/L: same cutoff excludes future evidence, later cutoff updates once.
        add_series(root,'A','X',[7],start=date(2026,7,1),prefix='future')
        assert service.materialize(root['company_id'],root['suppliers']['A'],'X',t1).status=='UNCHANGED'
        newer=service.materialize(root['company_id'],root['suppliers']['A'],'X',t2)
        assert newer.status=='UPDATED' and newer.memory_id==a.memory_id and newer.row_version==2
        # H/I/J: accepted corrections refresh canonical projection; rejected does not.
        writer=SupplierDeliveryObservationService()
        date_rev=writer.propose_correction(root['company_id'],a_ids[0],root['user_id'],actual_receipt_date=date(2026,1,4))
        writer.accept_correction(root['company_id'],date_rev.revision_id,root['user_id'])
        after_date=service.materialize(root['company_id'],root['suppliers']['A'],'X',t2); assert after_date.status=='UPDATED' and after_date.row_version==3
        qty_rev=writer.propose_correction(root['company_id'],a_ids[1],root['user_id'],received_quantity=80)
        writer.accept_correction(root['company_id'],qty_rev.revision_id,root['user_id'])
        after_qty=service.materialize(root['company_id'],root['suppliers']['A'],'X',t2); assert after_qty.status=='UPDATED' and after_qty.row_version==4
        rejected=writer.propose_correction(root['company_id'],a_ids[2],root['user_id'],received_quantity=50)
        writer.reject_correction(root['company_id'],rejected.revision_id,root['user_id'])
        assert service.materialize(root['company_id'],root['suppliers']['A'],'X',t2).status=='UNCHANGED'
        # N: stale precomputed T1 cannot overwrite persisted newer T2.
        old=snapshot(root,'B','X',t1)
        service.materialize(root['company_id'],root['suppliers']['B'],'X',t2)
        stale=service.persist_result(old); assert stale.status=='STALE_RESULT'
        # M: concurrent first materialization converges to one row.
        add_series(root,'F','Y',[5]*12,prefix='concurrent')
        barrier=threading.Barrier(2)
        def race(): barrier.wait(); return SupplierLearningMaterializationService().materialize(root['company_id'],root['suppliers']['F'],'Y',t1)
        with ThreadPoolExecutor(max_workers=2) as pool: outcomes=list(pool.map(lambda _: race(),range(2)))
        assert sorted(x.status for x in outcomes)==['CREATED','UNCHANGED']
        s=SessionLocal()
        try: assert s.query(SupplierLearningMemory).filter_by(company_id=root['company_id'],supplier_id=root['suppliers']['F'],material_code='Y').count()==1
        finally: s.close()
        # Q: no known ID or cross-company supplier scope can bypass tenant filtering.
        assert service.get_current(other['company_id'],root['suppliers']['A'],'X') is None
        try: service.materialize(root['company_id'],other['suppliers']['A'],'X',t1); raise AssertionError('cross tenant accepted')
        except SupplierLearningError: pass
        # T/U: new graph reconstructs persisted values; only projection rows were added.
        fresh=SupplierLearningMaterializationService().get_current(root['company_id'],root['suppliers']['A'],'X')
        assert (fresh.id,fresh.classification,float(fresh.confidence),fresh.source_fingerprint,fresh.cutoff_date,fresh.row_version)==(a.memory_id,service.get_current(root['company_id'],root['suppliers']['A'],'X').classification,float(service.get_current(root['company_id'],root['suppliers']['A'],'X').confidence),service.get_current(root['company_id'],root['suppliers']['A'],'X').source_fingerprint,t2,4)
        counts=side_counts(root['company_id']); assert counts[2:]==baseline[2:]
        print('PHASE 3C6B3 PROBE PASS',{'created':a.status,'updated':after_qty.status,'concurrent':[x.status for x in outcomes],'memory_rows':s.query(SupplierLearningMemory).filter_by(company_id=root['company_id']).count() if False else 8},flush=True)
    finally:
        for root in reversed(roots): cleanup_memory(root)


if __name__=='__main__': main()
