"""Bounded persisted Supplier-Learning context proof; one classification/run."""
from pathlib import Path
import sys
from time import perf_counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.verify_phase3d3a_decision_policy_postgres import build,evaluate,types,roots
from scripts import verify_phase3d2_decision_evidence_matrix as d2
def main(risk):
 t=perf_counter();ids=build('context_'+risk,supplier=risk);a=perf_counter()
 try:
  e,p=evaluate(ids);b=perf_counter();supplier=dict(e.optional)['supplier_learning'];print('CONTEXT SUPPLIER DIAGNOSTIC',{'risk':risk,'envelope_status':e.status,'context':e.decision_context,'supplier_learning':supplier,'candidates':[(c.candidate_type,c.severity,c.priority,c.reason_codes,c.supporting_evidence,c.conflicting_evidence) for c in p.candidates],'policy_status':p.status,'agreement':p.agreement_status,'confidence':p.confidence,'fingerprint':p.fingerprint},flush=True);assert supplier['status']=='AVAILABLE' and 'REVIEW_SUPPLIER' in types(p);assert evaluate(ids)==(e,p);print('CONTEXT SUPPLIER '+risk+' PASS',{'fixture_ms':round((a-t)*1000,3),'combined_ms':round((b-a)*1000,3),'reason_codes':[c.reason_codes for c in p.candidates if c.candidate_type=='REVIEW_SUPPLIER']},flush=True)
 finally:
  c=perf_counter();d2._cleanup([roots.pop()],[]);print('CONTEXT SUPPLIER '+risk+' CLEANUP PASS',round((perf_counter()-c)*1000,3),flush=True)
if __name__=='__main__':main(sys.argv[1])
