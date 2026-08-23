"""Focused PostgreSQL proof for immutable Decision Snapshot vintages."""
from pathlib import Path
import sys
from threading import Barrier, Thread
from time import perf_counter
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.decision_snapshot import DecisionSnapshotService
from app.application.decision_evidence_resolver import DecisionEvidenceResolver
from app.application.decision_policy import DecisionPolicy
from app.database import SessionLocal
from app.models.company_learning_memory_v2 import CompanyLearningMemoryV2
from app.models.decision_snapshot import DecisionSnapshot, DecisionSnapshotCandidate
from app.models.event_intelligence_memory import EventIntelligenceMemory
from app.models.pattern_learning_memory import PatternLearningMemory
from app.models.supplier_learning_memory import SupplierLearningMemory
from scripts import verify_phase3d2_decision_evidence_matrix as d2
from scripts.verify_phase3d3a_decision_policy_postgres import T1, build, roots


def resolve(ids):
    envelope=DecisionEvidenceResolver().resolve(ids["company_id"],"SKU","sales",T1,"REPLENISHMENT")
    return envelope,DecisionPolicy().evaluate(envelope)


def entry(provenance,name): return dict(provenance["optional"])[name]


def cleanup(ids):
    session=SessionLocal()
    try:
        snapshot_ids=[row[0] for row in session.query(DecisionSnapshot.id).filter_by(company_id=ids["company_id"]).all()]
        session.query(DecisionSnapshotCandidate).filter(DecisionSnapshotCandidate.decision_snapshot_id.in_(snapshot_ids)).delete(synchronize_session=False)
        session.query(DecisionSnapshot).filter_by(company_id=ids["company_id"]).delete(synchronize_session=False);session.commit()
    finally: session.close()
    d2._cleanup([ids],[])


def main():
    started=perf_counter(); ids=build("decision_snapshot",pattern="stable",supplier="LATE_PRONE",event="POSITIVE_ASSOCIATION",backtest="weak_validation",simulation="stockout_risk")
    try:
        envelope,policy=resolve(ids); service=DecisionSnapshotService(); first=service.materialize(envelope,policy); duplicate=service.materialize(envelope,policy)
        assert first.status=="CREATED" and duplicate.status=="ALREADY_EXISTS" and first.snapshot_id==duplicate.snapshot_id
        session=SessionLocal()
        try:
            s1=session.query(DecisionSnapshot).filter_by(id=first.snapshot_id,company_id=ids["company_id"]).one(); frozen=s1.source_provenance
            candidates=session.query(DecisionSnapshotCandidate).filter_by(decision_snapshot_id=first.snapshot_id).order_by(DecisionSnapshotCandidate.ordinal).all()
            assert [row.candidate_type for row in candidates]==[candidate.candidate_type for candidate in policy.candidates]
            pattern=session.query(PatternLearningMemory).filter_by(company_id=ids["company_id"],material_code="SKU",demand_type="sales").one(); pattern.pattern_classification="STRUCTURAL_CHANGE";pattern.source_pattern_fingerprint="2"*64;pattern.cutoff_period="2026-W24"
            supplier=session.query(SupplierLearningMemory).filter_by(company_id=ids["company_id"],material_code="SKU").one();supplier.classification="DETERIORATING";supplier.source_fingerprint="d"*64
            event=session.query(EventIntelligenceMemory).filter_by(company_id=ids["company_id"],material_code="SKU",demand_type="sales").one();event.classification="NO_CLEAR_EFFECT";event.source_fingerprint="e"*64;event.cutoff_period="2026-W24"
            company=session.query(CompanyLearningMemoryV2).filter_by(company_id=ids["company_id"]).one();company.evidence_maturity_level="low";company.evidence_maturity_score=20;company.source_summary_fingerprint="c"*64
            session.commit()
        finally: session.close()
        e2,p2=resolve(ids); assert e2.fingerprint!=envelope.fingerprint
        try:
            service.materialize(envelope,p2)
            raise AssertionError("mismatched envelope/policy result unexpectedly accepted")
        except ValueError:
            pass
        barrier=Barrier(2); outcomes=[]
        def worker():
            barrier.wait(); outcomes.append(DecisionSnapshotService().materialize(e2,p2))
        threads=[Thread(target=worker),Thread(target=worker)];[thread.start() for thread in threads];[thread.join() for thread in threads]
        assert sorted(item.status for item in outcomes)==["ALREADY_EXISTS","CREATED"] and outcomes[0].snapshot_id==outcomes[1].snapshot_id
        session=SessionLocal()
        try:
            old=session.query(DecisionSnapshot).filter_by(id=first.snapshot_id,company_id=ids["company_id"]).one()
            assert entry(old.source_provenance,"pattern")["classification"]=="stable" and entry(old.source_provenance,"pattern")["fingerprint"]!="2"*64
            assert entry(old.source_provenance,"supplier_learning")["entries"][0]["classification"]=="LATE_PRONE"
            assert entry(old.source_provenance,"event")["entries"][0]["classification"]=="POSITIVE_ASSOCIATION"
            assert entry(old.source_provenance,"company_learning")["maturity_level"]=="mature"
            assert service.get(uuid4(),first.snapshot_id) is None and not service.list_for_scope(ids["company_id"],"SKU","consumption","REPLENISHMENT")
            try:
                old.agreement_status="MIXED";session.commit();raise AssertionError("snapshot update unexpectedly succeeded")
            except Exception: session.rollback()
        finally: session.close()
        print("PHASE 3D4 SNAPSHOT PASS",{"snapshot_1":str(first.snapshot_id),"snapshot_2":str(outcomes[0].snapshot_id),"first_ms":round(first.elapsed_ms,3),"duplicate_ms":round(duplicate.elapsed_ms,3),"candidate_count":len(candidates),"fixture_plus_proof_ms":round((perf_counter()-started)*1000,3)},flush=True)
    finally:
        cleanup(ids);print("PHASE 3D4 SNAPSHOT CLEANUP PASS",{"residue":0},flush=True)


if __name__=="__main__": main()
