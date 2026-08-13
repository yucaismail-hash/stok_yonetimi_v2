"""Focused PostgreSQL proof for Company Learning V2 current projection."""
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.application.learning_evidence import LearningEvidenceService
from app.application.pattern_learning_materialization import PatternLearningMaterializationService
from app.application.company_learning_materialization import CompanyLearningMaterializationService
from app.database import SessionLocal
from app.models.actuals import ActualWeeklyObservation
from app.models.company import Company
from app.models.company_learning_memory_v2 import CompanyLearningMemoryV2
from app.models.pattern_learning_memory import PatternLearningMemory
from app.models.learning_evidence import LearningEvidence
from app.models.runtime import RuntimeExecution
from scripts.support.pattern_intelligence_fixture import create,cleanup
def clear(f):
 s=SessionLocal()
 try:s.query(CompanyLearningMemoryV2).filter_by(company_id=f.company_id).delete(synchronize_session=False);s.query(PatternLearningMemory).filter_by(company_id=f.company_id).delete(synchronize_session=False);s.query(LearningEvidence).filter_by(company_id=f.company_id).delete(synchronize_session=False);s.commit()
 finally:s.close()
def main():
 roots=[]
 try:
  zero=create('insufficient');roots.append(zero);ctx={'company_id':zero.company_id,'user_id':zero.user_id,'dataset_id':zero.dataset_id}
  stable=create('stable','STABLE','sales','finished_good',ctx);trend=create('trend','TREND','sales','semi_finished_good',ctx);sparse=create('intermittent','SPARSE','consumption','raw_material',ctx);other=create('stable');roots.append(other)
  c=CompanyLearningMaterializationService();z=c.materialize(other.company_id);assert z.status=='CREATED' and c.get_current(other.company_id).evidence_maturity_score==0
  pm=PatternLearningMaterializationService()
  for f in (stable,trend,sparse):assert pm.materialize(f.company_id,f.material_code,f.demand_type,f.periods[-1]).status=='CREATED'
  s=SessionLocal();oid=s.query(ActualWeeklyObservation).filter_by(company_id=stable.company_id,material_code='STABLE',demand_type='sales',period=stable.periods[-1]).one().id;s.close();LearningEvidenceService().record_actual_accepted(stable.company_id,oid)
  first=c.materialize(stable.company_id);same=c.materialize(stable.company_id);row=c.get_current(stable.company_id);assert (first.status,same.status)==('CREATED','UNCHANGED') and row.pattern_distribution=={'STABLE':1,'STRUCTURAL_CHANGE':1,'INTERMITTENT':1} and row.evidence_maturity_score>0
  old=CompanyLearningMaterializationService()._snapshot(SessionLocal(),stable.company_id)
  s=SessionLocal();oid=s.query(ActualWeeklyObservation).filter_by(company_id=stable.company_id,material_code='TREND',demand_type='sales',period=trend.periods[-1]).one().id;s.close();LearningEvidenceService().record_actual_accepted(stable.company_id,oid)
  updated=c.materialize(stable.company_id);assert updated.status=='UPDATED' and updated.row_version==2 and c.persist_snapshot(old).status=='STALE_RESULT'
  barrier=threading.Barrier(2)
  def run():barrier.wait();return CompanyLearningMaterializationService().materialize(stable.company_id)
  with ThreadPoolExecutor(max_workers=2) as pool:out=list(pool.map(lambda _:run(),range(2)))
  assert all(x.status=='UNCHANGED' for x in out) and c.get_current(other.company_id) is not None and c.get_current(stable.company_id).company_id!=other.company_id
  assert RuntimeExecution is not None
  print('PHASE3C5B3A PASS',{'zero':z.status,'first':first.status,'unchanged':same.status,'updated':updated.status,'stale':'STALE_RESULT','patterns':row.pattern_distribution,'score':float(row.evidence_maturity_score)},flush=True)
 finally:
  for f in reversed(roots):clear(f);cleanup(f)
  s=SessionLocal()
  try:assert all(s.query(Company).filter_by(id=f.company_id).count()==0 for f in roots)
  finally:s.close()
if __name__=='__main__':main()
