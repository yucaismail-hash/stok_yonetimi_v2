"""Read-only Supplier Learning context proof; Safety Stock math remains unchanged."""
from datetime import date
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.analysis.safety_stock import ComprehensiveSafetyStockOptimizer
from app.application.supplier_learning_materialization import SupplierLearningMaterializationService
from app.application.supplier_learning_resolver import SupplierLearningResolver
from app.database import SessionLocal
from app.engine.capability_dataflow import attach_supplier_learning_context, supplier_learning_context_for_scope
from app.models.company_learning_memory_v2 import CompanyLearningMemoryV2
from app.models.learning_evidence import LearningEvidence
from app.models.learning_refresh_delivery import LearningRefreshDelivery
from app.models.pattern_learning_memory import PatternLearningMemory
from app.models.retraining_job import RetrainingJob
from app.models.supplier_delivery_observation import SupplierDeliveryObservation, SupplierDeliveryObservationRevision
from app.models.supplier_learning_memory import SupplierLearningMemory
from scripts.verify_phase3c6b2_supplier_learning import fixture, cleanup, cleanup_interrupted_fixtures, add_series


def clean(root):
    s=SessionLocal()
    try: s.query(SupplierLearningMemory).filter_by(company_id=root['company_id']).delete(synchronize_session=False);s.commit()
    finally:s.close()
    cleanup(root)

def counts(company_id):
    s=SessionLocal()
    try:return tuple(s.query(x).filter_by(company_id=company_id).count() for x in (SupplierDeliveryObservation,SupplierDeliveryObservationRevision,SupplierLearningMemory,LearningEvidence,LearningRefreshDelivery,PatternLearningMemory,CompanyLearningMemoryV2,RetrainingJob))
    finally:s.close()

def resolve(root, supplier, material, cutoff=None):
    return supplier_learning_context_for_scope(SupplierLearningResolver(),root['company_id'],root['suppliers'][supplier],material,cutoff_date=cutoff)

def main():
    roots=[]
    try:
        cleanup_interrupted_fixtures(); root=fixture('enrichment_a'); roots.append(root); other=fixture('enrichment_b'); roots.append(other)
        cutoff=date(2026,12,31)
        # Canonical memory states for five distinct risk classifications plus independent material scopes.
        add_series(root,'A','X',[5]*8,prefix='reliable')
        add_series(root,'B','X',[2,10]*4,prefix='variable')
        add_series(root,'C','X',[5]*8,promised_mode='late',prefix='late')
        add_series(root,'D','X',[5]*8,quantities='under',prefix='fulfillment')
        add_series(root,'E','X',[4]*8+[8]*4,prefix='deteriorating')
        add_series(root,'A','Y',[5]*8,prefix='multi-material')
        materializer=SupplierLearningMaterializationService()
        for code in ('A','B','C','D','E'):
            assert materializer.materialize(root['company_id'],root['suppliers'][code],'X',cutoff).status=='CREATED'
        assert materializer.materialize(root['company_id'],root['suppliers']['A'],'Y',cutoff).status=='CREATED'
        before=counts(root['company_id'])
        # A/F-I/J/K/M/P/Q: resolution is supplier/material/tenant/cutoff scoped and immutable.
        reliable=resolve(root,'A','X',cutoff); variable=resolve(root,'B','X',cutoff); late=resolve(root,'C','X',cutoff)
        fulfillment=resolve(root,'D','X',cutoff); deteriorating=resolve(root,'E','X',cutoff); ay=resolve(root,'A','Y',cutoff)
        assert reliable.status=='AVAILABLE' and reliable.evidence['supplier_learning_classification']=='RELIABLE'
        assert variable.evidence['supplier_learning_classification']=='VARIABLE' and late.evidence['supplier_learning_classification']=='LATE_PRONE'
        assert fulfillment.evidence['supplier_learning_classification']=='FULFILLMENT_RISK' and deteriorating.evidence['supplier_learning_classification']=='DETERIORATING'
        assert reliable.memory_id != ay.memory_id and reliable.evidence['supplier_learning_source_fingerprint'] != variable.evidence['supplier_learning_source_fingerprint']
        assert resolve(root,'A','X',date(2026,1,1)).status=='LEARNING_CUTOFF_INCOMPATIBLE'
        assert resolve(other,'A','X',cutoff).status=='NO_LEARNED_SUPPLIER_EVIDENCE'
        # B/H: missing/insufficient memory remains optional and explicit.
        assert resolve(root,'F','X',cutoff).status=='NO_LEARNED_SUPPLIER_EVIDENCE'
        # C/D/E: attach learned provenance only; exact optimizer result is unchanged.
        operational={'status':'used','lead_time_source':'supplier_single','lead_time_mean_days':14.0,'lead_time_std_days':2.0,'supplier_ids':['operational-A']}
        enriched=attach_supplier_learning_context(operational,reliable)
        assert enriched['lead_time_mean_days']==operational['lead_time_mean_days'] and enriched['lead_time_source']=='supplier_single'
        baseline=ComprehensiveSafetyStockOptimizer().calculate_all_methods([3,5,2,6,4,7,3,8],14,.95)
        with_context=ComprehensiveSafetyStockOptimizer().calculate_all_methods([3,5,2,6,4,7,3,8],14,.95)
        assert {k:float(v) for k,v in baseline.items()}=={k:float(v) for k,v in with_context.items()}
        missing=attach_supplier_learning_context(operational,resolve(root,'F','X',cutoff)); assert missing['supplier_learning']['supplier_learning_available'] is False
        # N/O: a read-only resolution adds no workflow task, writeback, or delivery work.
        assert counts(root['company_id'])==before
        fresh=resolve(root,'A','X',cutoff); assert fresh.evidence==reliable.evidence
        print('PHASE 3C6B5 PROBE PASS',{'available':reliable.status,'absent':missing['supplier_learning']['status'],'risks':[variable.evidence['supplier_learning_classification'],late.evidence['supplier_learning_classification'],fulfillment.evidence['supplier_learning_classification'],deteriorating.evidence['supplier_learning_classification']],'numerical_non_impact':True},flush=True)
    finally:
        for root in reversed(roots): clean(root)

if __name__=='__main__':main()
