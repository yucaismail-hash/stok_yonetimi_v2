"""Persisted Resolver -> Policy integration matrix (no Decision writes)."""
from pathlib import Path
import sys
from decimal import Decimal
from hashlib import sha256
from time import perf_counter
from uuid_extensions import uuid7
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.application.decision_evidence_resolver import DecisionEvidenceResolver
from app.application.decision_policy import DecisionPolicy
from app.database import SessionLocal
from app.models.company import Company, User, Supplier
from app.models.dataset import Dataset
from app.models.company_learning_memory_v2 import CompanyLearningMemoryV2
from app.models.pattern_learning_memory import PatternLearningMemory
from app.models.supplier_learning_memory import SupplierLearningMemory
from app.models.event_intelligence_memory import EventIntelligenceMemory
from scripts import verify_phase3d2_decision_evidence_matrix as d2

T1=d2.T1; roots=[]
def progress(label, started=None):
 elapsed='' if started is None else f' elapsed_ms={round((perf_counter()-started)*1000,3)}'
 print(f'[3D3A] {label}{elapsed}',flush=True)
def context(tag):
 s=SessionLocal()
 try:
  c=Company(name=tag,tax_id=tag);s.add(c);s.flush();u=User(company_id=c.id,email=tag+'@invalid.test',hashed_password='x');s.add(u);s.flush()
  d=Dataset(company_id=c.id,user_id=u.id,uploaded_by=u.id,dataset_hash=sha256(tag.encode()).hexdigest(),source_type='phase3d3a',encrypted_data=b'fixture',is_active=True);s.add(d);s.commit();return {'company_id':c.id,'user_id':u.id,'dataset_id':d.id}
 finally:s.close()
def build(label, *, pattern=None, supplier=None, event=False, backtest=None, simulation=None, maturity='mature', safety=True, company_learning=True):
 started=perf_counter();progress('fixture '+label+' start')
 ids=context('phase3d3a_pg_'+label+'_'+str(uuid7()));roots.append(ids);s=SessionLocal()
 try:
  d2._forecast(s,ids,'SKU','sales',T1,'finished_good')
  if safety:d2._runtime(s,ids,'SKU','sales',T1,'safety_stock')
  if backtest:d2._runtime(s,ids,'SKU','sales',T1,'backtest',backtest)
  if simulation:d2._runtime(s,ids,'SKU','sales',T1,'simulation',simulation)
  if pattern:s.add(d2._pattern(ids,'SKU','sales',T1,'p'*64));s.flush();s.query(PatternLearningMemory).filter_by(company_id=ids['company_id'],material_code='SKU',demand_type='sales').update({'pattern_classification':pattern})
  if company_learning:s.add(CompanyLearningMemoryV2(company_id=ids['company_id'],company_learning_policy_version='v1',learning_score_policy_version='v1',evidence_count=1,evidence_type_counts={},evidence_source_diversity=1,material_scope_count=1,demand_scope_count=1,pattern_memory_scope_count=0,forecast_evaluated_scope_count=0,forecast_evaluation_sample_count=0,pattern_distribution={},accepted_correction_evidence_count=0,retraining_summary={},champion_summary={},evidence_maturity_score=Decimal('20' if maturity=='low' else '80'),evidence_maturity_level=maturity,source_summary_fingerprint='m'*64,row_version=1))
  if supplier:
   x=Supplier(company_id=ids['company_id'],code='S',name='S');s.add(x);s.flush();mem=d2._supplier_memory(ids,x,'SKU');mem.classification=supplier;s.add(mem)
  if event:s.add(d2._event(ids,'EVENT',T1,event if isinstance(event,str) else 'POSITIVE','SKU','sales'))
  s.commit();progress('fixture '+label+' end',started);return ids
 finally:s.close()
def evaluate(ids, context='REPLENISHMENT'):
 e=DecisionEvidenceResolver().resolve(ids['company_id'],'SKU','sales',T1,context);return e,DecisionPolicy().evaluate(e)
def types(result):return tuple(x.candidate_type for x in result.candidates)
def main():
 try:
  total=perf_counter();progress('[1] fixture/setup start')
  stable=build('stable');e,r=evaluate(stable);assert types(r)==('HOLD_POLICY',)
  missing=build('missing',safety=False);e0,r0=evaluate(missing);assert e0.status=='INSUFFICIENT_REQUIRED_EVIDENCE' and r0.status=='INSUFFICIENT'
  weak=build('weak',backtest='weak_validation');_,rw=evaluate(weak);assert 'REVIEW_FORECAST' in types(rw) and rw.agreement_status=='ALIGNED'
  structural=build('pattern',pattern='STRUCTURAL_CHANGE');_,rp=evaluate(structural);assert 'REVIEW_FORECAST' in types(rp)
  late=build('late',supplier='LATE_PRONE');_,rl=evaluate(late);assert 'REVIEW_SUPPLIER' in types(rl)
  mixed=build('mixed',supplier='MIXED_RISK');_,rm=evaluate(mixed);assert 'REVIEW_SUPPLIER' in types(rm)
  event=build('event',event=True);_,re=evaluate(event);assert 'MONITOR_EVENT_RISK' in types(re)
  stock=build('stock',simulation='stockout_risk');_,rs=evaluate(stock);assert 'REVIEW_SAFETY_STOCK' in types(rs)
  excess=build('excess',simulation='excess_risk');_,rx=evaluate(excess);assert 'REVIEW_SAFETY_STOCK' in types(rx)
  multi=build('multi',supplier='LATE_PRONE',event=True,backtest='weak_validation',simulation='stockout_risk');em,rr=evaluate(multi);assert types(rr)==('REVIEW_SAFETY_STOCK','REVIEW_FORECAST','REVIEW_SUPPLIER','MONITOR_EVENT_RISK')
  low=build('low',maturity='low');_,rlo=evaluate(low);assert types(rlo)==types(r) and rlo.confidence<r.confidence
  first=build('first');s=SessionLocal();s.query(CompanyLearningMemoryV2).filter_by(company_id=first['company_id']).delete();s.commit();s.close();_,rf=evaluate(first);assert rf.status=='READY' and rf.confidence<r.confidence
  progress('[1-4] fixture/resolver/policy matrix end',total)
  progress('[5] deterministic repeat start')
  warm=evaluate(stable);times=[]
  for _ in range(3):
   a=perf_counter();env=DecisionEvidenceResolver().resolve(stable['company_id'],'SKU','sales',T1,'REPLENISHMENT');b=perf_counter();pol=DecisionPolicy().evaluate(env);c=perf_counter();times.append(((b-a)*1000,(c-b)*1000,(c-a)*1000));assert pol==r
  progress('[8] performance measurement end',total)
  print('PHASE 3D3A POSTGRES PASS',{'total_ms':round((perf_counter()-total)*1000,3),'resolver_ms':[round(x[0],3) for x in times],'policy_ms':[round(x[1],3) for x in times],'combined_ms':[round(x[2],3) for x in times],'candidate_count':len(rr.candidates),'writes':0},flush=True)
 finally:
  cleanup=perf_counter();progress('[9] cleanup start')
  for ids in reversed(roots):d2._cleanup([ids],[])
  progress('[9] cleanup end',cleanup)
if __name__=='__main__':main()
