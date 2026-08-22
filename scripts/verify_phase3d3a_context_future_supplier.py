from pathlib import Path
import sys
from datetime import date
from time import perf_counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.verify_phase3d3a_decision_policy_postgres import build,evaluate,roots
from scripts import verify_phase3d2_decision_evidence_matrix as d2
from app.database import SessionLocal
from app.models.supplier_learning_memory import SupplierLearningMemory
def main():
 t=perf_counter();ids=build('context_future_supplier',supplier='LATE_PRONE');s=SessionLocal();s.query(SupplierLearningMemory).filter_by(company_id=ids['company_id'],material_code='SKU').update({'cutoff_date':date(2026,6,14)});s.commit();s.close();a=perf_counter()
 try:
  e,p=evaluate(ids);b=perf_counter();sl=dict(e.optional)['supplier_learning'];print('CONTEXT FUTURE SUPPLIER DIAGNOSTIC',{'envelope':e.status,'supplier':sl,'candidates':[(x.candidate_type,x.reason_codes) for x in p.candidates]},flush=True);assert sl['status']=='INCOMPATIBLE' and sl['reason']=='FUTURE_EVIDENCE' and all(x.candidate_type!='REVIEW_SUPPLIER' for x in p.candidates) and evaluate(ids)==(e,p);print('CONTEXT FUTURE SUPPLIER PASS',{'fixture_ms':round((a-t)*1000,3),'combined_ms':round((b-a)*1000,3)},flush=True)
 finally:
  c=perf_counter();d2._cleanup([roots.pop()],[]);print('CONTEXT FUTURE SUPPLIER CLEANUP PASS',round((perf_counter()-c)*1000,3),flush=True)
if __name__=='__main__':main()
