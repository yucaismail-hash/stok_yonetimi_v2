"""Bounded CORE micro-shards; invoke with stable|missing|maturity|first_use|repeat."""
from pathlib import Path
import sys
from time import perf_counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.database import SessionLocal
from app.models.company_learning_memory_v2 import CompanyLearningMemoryV2
from scripts.support.decision_policy_pg_support import build,evaluate,types,cleanup
def run(label):
 start=perf_counter();ids=build('core_maturity_high') if label=='maturity' else (build('core_missing',safety=False) if label=='missing' else (build('core_first_use',safety=False,company_learning=False) if label=='first_use' else build('core_'+label)));fixture=perf_counter()
 try:
  e0=perf_counter();e,r=evaluate(ids,'FORECAST_REVIEW') if label=='first_use' else evaluate(ids);e1=perf_counter()
  if label=='stable':assert types(r)==('HOLD_POLICY',)
  elif label=='missing':assert e.status=='INSUFFICIENT_REQUIRED_EVIDENCE' and r.status=='INSUFFICIENT'
  elif label=='first_use':
   optional=dict(e.optional);assert r.status=='READY' and types(r)==('HOLD_POLICY',) and all(optional[name]['status']=='ABSENT' for name in ('pattern','company_learning','supplier_learning','event','simulation','backtest','supplier_operational','retraining'))
  elif label=='repeat':assert evaluate(ids)==(e,r)
  elif label=='maturity':
   rh=r; s=SessionLocal();row=s.query(CompanyLearningMemoryV2).filter_by(company_id=ids['company_id']).one();row.evidence_maturity_level='low';row.evidence_maturity_score=20;row.source_summary_fingerprint='l'*64;s.commit();s.close();u=perf_counter();_,rl=evaluate(ids);assert types(rh)==types(rl) and rl.confidence<rh.confidence;print('3D3A CORE-MATURITY UPDATE_MS',round((perf_counter()-u)*1000,3),flush=True)
  print('3D3A CORE-'+label.upper()+' PASS',{'fixture_ms':round((fixture-start)*1000,3),'resolver_policy_ms':round((e1-e0)*1000,3)},flush=True)
 finally:
  c=perf_counter();cleanup();print('3D3A CORE-'+label.upper()+' CLEANUP PASS',round((perf_counter()-c)*1000,3),flush=True)
if __name__=='__main__':run(sys.argv[1])
