from pathlib import Path
import sys
from time import perf_counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.verify_phase3d3a_decision_policy_postgres import build,evaluate,roots
from scripts import verify_phase3d2_decision_evidence_matrix as d2
def main(classification='POSITIVE_ASSOCIATION'):
 t=perf_counter();ids=build('context_event_'+classification.lower(),event=classification);a=perf_counter()
 try:
  e,p=evaluate(ids);b=perf_counter();event=dict(e.optional)['event'];monitor=any(x.candidate_type=='MONITOR_EVENT_RISK' for x in p.candidates);print('CONTEXT EVENT DIAGNOSTIC',{'classification':classification,'envelope':e.status,'scope':(e.material_code,e.demand_type,e.decision_cutoff_period),'event':event,'candidates':[(x.candidate_type,x.reason_codes,x.supporting_evidence) for x in p.candidates],'agreement':p.agreement_status,'confidence':p.confidence},flush=True);assert event['status']=='AVAILABLE' and event['entries'][0]['classification']==classification and (monitor if classification in {'POSITIVE_ASSOCIATION','NEGATIVE_ASSOCIATION'} else not monitor) and evaluate(ids)==(e,p);print('CONTEXT EVENT '+classification+' PASS',{'fixture_ms':round((a-t)*1000,3),'combined_ms':round((b-a)*1000,3)},flush=True)
 finally:
  c=perf_counter();d2._cleanup([roots.pop()],[]);print('CONTEXT EVENT '+classification+' CLEANUP PASS',round((perf_counter()-c)*1000,3),flush=True)
if __name__=='__main__':main(sys.argv[1] if len(sys.argv)>1 else 'POSITIVE_ASSOCIATION')
