from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.support.decision_policy_pg_support import build,evaluate,types,cleanup
from app.models.company_learning_memory_v2 import CompanyLearningMemoryV2
from app.database import SessionLocal
from time import perf_counter
def main():
 started=perf_counter()
 try:
  stable=build('core_stable');e,r=evaluate(stable);assert types(r)==('HOLD_POLICY',)
  missing=build('core_missing',safety=False);em,rm=evaluate(missing);assert em.status=='INSUFFICIENT_REQUIRED_EVIDENCE' and rm.status=='INSUFFICIENT'
  low=build('core_low',maturity='low');_,rl=evaluate(low);assert types(rl)==types(r) and rl.confidence<r.confidence
  first=build('core_first');s=SessionLocal();s.query(CompanyLearningMemoryV2).filter_by(company_id=first['company_id']).delete();s.commit();s.close();ef,rf=evaluate(first);assert rf.status=='READY' and rf.confidence<r.confidence
  assert evaluate(stable)==(e,r);print('3D3A CORE PASS',round((perf_counter()-started)*1000,3),flush=True)
 finally:cleanup()
if __name__=='__main__':main()
