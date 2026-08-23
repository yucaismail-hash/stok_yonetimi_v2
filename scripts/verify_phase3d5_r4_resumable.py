"""R4 bounded post-completion Decision failure/recovery proof."""
import asyncio, hashlib, json, sys
from pathlib import Path
from time import perf_counter
from uuid import UUID
from unittest.mock import patch
from uuid_extensions import uuid7
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.business_workflow_acceptance import BusinessWorkflowAcceptanceService
from app.application.business_decision_plan import BusinessDecisionPlanService
import app.application.business_decision_plan as plan_module
from app.database import SessionLocal
from app.engine.business_workflow_scheduler import BusinessWorkflowScheduler
from app.models.actuals import ActualWeeklyObservation,ActualWeeklyRevision
from app.models.company import Company,User
from app.models.dataset import Dataset
from app.models.decision_snapshot import DecisionSnapshot,DecisionSnapshotCandidate
from app.models.forecast_vintage import ForecastVintage,ForecastVintagePoint
from app.models.runtime import RuntimeExecution,RuntimeResultReference,RuntimeTask,RuntimeTaskAttempt
from app.models.security import CompanyEncryptionKey
from app.services.security import EncryptionService

def mp(k):return Path(__file__).with_name(f'.phase3d5_r4_{k}.json')
def load(k):return json.loads(mp(k).read_text())
def write(k,v):mp(k).write_text(json.dumps(v,sort_keys=True,indent=2))
def fp(v):return hashlib.sha256(json.dumps(v,sort_keys=True,default=str,separators=(',',':')).encode()).hexdigest()
def plan_value(p):return {'execution_id':str(p.execution_id),'company_id':str(p.company_id),'cutoff':p.decision_cutoff_period,'demand':p.demand_type,'context':p.decision_context,'items':list(p.items),'limitations':list(p.limitations)}
def state(s,cid,eid):
 refs=s.query(RuntimeResultReference).filter_by(execution_id=eid).all();tasks=s.query(RuntimeTask).filter_by(execution_id=eid).order_by(RuntimeTask.task_order).all()
 return {'execution':tuple((str(eid),s.query(RuntimeExecution).filter_by(execution_id=eid).one().state,float(s.query(RuntimeExecution).filter_by(execution_id=eid).one().progress))),'tasks':tuple((t.task_id,t.state,tuple(t.dependencies)) for t in tasks),'refs':{r.result_type:(str(r.id),fp(r.inline_result)) for r in refs},'snapshots':s.query(DecisionSnapshot).filter_by(company_id=cid).count(),'candidates':s.query(DecisionSnapshotCandidate).join(DecisionSnapshot).filter(DecisionSnapshot.company_id==cid).count(),'actuals':s.query(ActualWeeklyObservation).filter_by(company_id=cid).count()}

async def setup(k):
 assert not mp(k).exists();materials=['SKU'] if k=='single' else ['SKU-A','SKU-B'];s=SessionLocal()
 try:
  started=perf_counter();tag='d5r4_'+k+'_'+str(uuid7()).replace('-','');c=Company(id=uuid7(),name=tag,tax_id=tag);u=User(id=uuid7(),company_id=c.id,email=tag+'@x.invalid',hashed_password='x');s.add_all((c,u));s.flush();items=[{'sku_code':m,'demand_history':list(range(100,132)),'lead_time_days':14,'initial_stock':500,'eoq':100,'product_level':'finished_good'} for m in materials];d=Dataset(id=uuid7(),company_id=c.id,user_id=u.id,uploaded_by=u.id,dataset_hash=hashlib.sha256(tag.encode()).hexdigest(),source_type=tag,encrypted_data=EncryptionService(s).encrypt_dataset(u.id,{'items':items}),is_active=True);s.add(d);s.commit();ActualWeeklyLedgerService().ingest_dataset_actuals(c.id,u.id,d.id,[{'material_code':m,'period':f'2026-W{w:02d}','quantity':100+w,'product_level':'finished_good'} for m in materials for w in range(1,33)],'sales');fixture=(perf_counter()-started)*1000;a=BusinessWorkflowAcceptanceService().accept_or_resolve(c.id,u.id,d.id,request_metadata={'params':{'forecast_vintage':{'demand_type':'sales','product_metadata':{m:{'product_level':'finished_good'} for m in materials}}}});run=perf_counter()
  for _ in range(5):
   s.close();s=SessionLocal()
   if await BusinessWorkflowScheduler(s).run_next_ready(a.execution_id,c.id) is None:break
  e=s.query(RuntimeExecution).filter_by(execution_id=a.execution_id,company_id=c.id).one();ts=s.query(RuntimeTask).filter_by(execution_id=e.execution_id).order_by(RuntimeTask.task_order).all();assert e.state=='completed' and float(e.progress)==100 and [x.task_id for x in ts]==['forecast','safety_stock','simulation','backtest'];params=e.metadata_['request_metadata']['params'];attempts=s.query(RuntimeTaskAttempt).filter_by(execution_id=e.execution_id).all();dur={t.task_id:float(next((x.duration_ms for x in attempts if x.runtime_task_id==t.id and x.duration_ms is not None),0)or 0) for t in ts};write(k,{'company_id':str(c.id),'user_id':str(u.id),'dataset_id':str(d.id),'execution_id':str(e.execution_id),'materials':materials,'cutoff':params['forecast_cutoff_period'],'demand_type':'sales'});print('R4 '+k.upper()+' WORKFLOW PASS',{'fixture_ms':round(fixture,3),'analytics_ms':round((perf_counter()-run)*1000,3),'execution_id':str(e.execution_id),'task_duration_ms':dur,'materials':materials},flush=True)
 finally:s.close()

class InjectedPolicyError(RuntimeError):pass
class InjectedAfterSnapshotError(RuntimeError):pass
def inject_before():
 class FailingPolicy:
  def evaluate(self,envelope):raise InjectedPolicyError('probe injected policy failure')
 return FailingPolicy
def inject_selective():
 original=plan_module.DecisionPolicy
 class Selective:
  def evaluate(self,envelope):
   if envelope.material_code=='SKU-B':raise InjectedPolicyError('probe injected SKU-B policy failure')
   return original().evaluate(envelope)
 return Selective
def inject_after():
 original=plan_module.DecisionSnapshotService
 class After:
  def materialize(self,envelope,policy):
   original().materialize(envelope,policy);raise InjectedAfterSnapshotError('probe injected after snapshot')
 return After

def before_failure():
 m=load('single');cid,eid=UUID(m['company_id']),UUID(m['execution_id']);s=SessionLocal();pre=state(s,cid,eid);s.close()
 with patch.object(plan_module,'DecisionPolicy',inject_before()):out=BusinessDecisionPlanService().materialize(cid,eid)
 s=SessionLocal();post=state(s,cid,eid);s.close();assert not out.items and len(out.limitations)==1 and out.limitations[0]['failure_stage']=='policy' and out.limitations[0]['error_class']=='InjectedPolicyError' and pre['execution']==post['execution'] and pre['tasks']==post['tasks'] and pre['refs']==post['refs'] and post['snapshots']==0;print('R4 SINGLE BEFORE-SNAPSHOT FAILURE PASS',{'limitation':out.limitations[0],'workflow':post['execution'],'snapshot_count':post['snapshots']},flush=True)
def recover(k):
 m=load(k);cid,eid=UUID(m['company_id']),UUID(m['execution_id']);s=SessionLocal();pre=state(s,cid,eid);s.close();t=perf_counter();out=BusinessDecisionPlanService().materialize(cid,eid);elapsed=(perf_counter()-t)*1000;s=SessionLocal();post=state(s,cid,eid);snaps=s.query(DecisionSnapshot).filter_by(company_id=cid).order_by(DecisionSnapshot.id).all();s.close();assert not out.limitations and len(out.items)==len(m['materials']) and pre['execution']==post['execution'] and pre['tasks']==post['tasks'] and pre['refs']==post['refs'];m.update({'snapshot_ids':[str(x.id) for x in snaps],'plan_fp':fp(plan_value(out)),'candidate_count':post['candidates']});write(k,m);print('R4 '+k.upper()+' RECOVERY PASS',{'snapshot_ids':m['snapshot_ids'],'plan_fingerprint':m['plan_fp'],'decision_ms':round(elapsed,3),'items':list(out.items)},flush=True)
def after_failure():
 m=load('single');cid,eid=UUID(m['company_id']),UUID(m['execution_id']);s=SessionLocal();pre=state(s,cid,eid);s.close()
 with patch.object(plan_module,'DecisionSnapshotService',inject_after()):out=BusinessDecisionPlanService().materialize(cid,eid)
 s=SessionLocal();post=state(s,cid,eid);s.close();assert not out.items and out.limitations[0]['failure_stage']=='snapshot' and out.limitations[0]['error_class']=='InjectedAfterSnapshotError' and pre['snapshots']==post['snapshots']==1 and pre['refs']==post['refs'];normal=BusinessDecisionPlanService().materialize(cid,eid);assert fp(plan_value(normal))==m['plan_fp'];print('R4 SINGLE AFTER-SNAPSHOT FAILURE PASS',{'limitation':out.limitations[0],'snapshot_count':post['snapshots'],'retry_fingerprint':m['plan_fp']},flush=True)
def partial():
 m=load('multi');cid,eid=UUID(m['company_id']),UUID(m['execution_id']);s=SessionLocal();pre=state(s,cid,eid);s.close()
 with patch.object(plan_module,'DecisionPolicy',inject_selective()):out=BusinessDecisionPlanService().materialize(cid,eid)
 s=SessionLocal();post=state(s,cid,eid);s.close();assert [x['material_code'] for x in out.items]==['SKU-A'] and out.limitations[0]['material_code']=='SKU-B' and out.limitations[0]['failure_stage']=='policy' and post['snapshots']==1 and pre['refs']==post['refs'] and pre['execution']==post['execution'];print('R4 MULTI PARTIAL PASS',{'items':list(out.items),'limitations':list(out.limitations),'snapshot_count':post['snapshots']},flush=True)
def cleanup(k):
 m=load(k);cid=UUID(m['company_id']);s=SessionLocal()
 try:
  eids=[x[0] for x in s.query(RuntimeExecution.execution_id).filter_by(company_id=cid)];vids=[x[0] for x in s.query(ForecastVintage.id).filter_by(company_id=cid)];sids=[x[0] for x in s.query(DecisionSnapshot.id).filter_by(company_id=cid)];s.query(DecisionSnapshotCandidate).filter(DecisionSnapshotCandidate.decision_snapshot_id.in_(sids)).delete(synchronize_session=False);s.query(DecisionSnapshot).filter_by(company_id=cid).delete(synchronize_session=False);s.query(ForecastVintagePoint).filter(ForecastVintagePoint.forecast_vintage_id.in_(vids)).delete(synchronize_session=False);s.query(ForecastVintage).filter_by(company_id=cid).delete(synchronize_session=False);s.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(eids)).delete(synchronize_session=False);s.query(RuntimeTaskAttempt).filter(RuntimeTaskAttempt.execution_id.in_(eids)).delete(synchronize_session=False);s.query(RuntimeTask).filter(RuntimeTask.execution_id.in_(eids)).delete(synchronize_session=False);s.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(eids)).delete(synchronize_session=False);s.query(ActualWeeklyRevision).filter_by(company_id=cid).delete(synchronize_session=False);s.query(ActualWeeklyObservation).filter_by(company_id=cid).delete(synchronize_session=False);s.query(Dataset).filter_by(id=UUID(m['dataset_id'])).delete(synchronize_session=False);s.query(CompanyEncryptionKey).filter_by(user_id=UUID(m['user_id'])).delete(synchronize_session=False);s.query(User).filter_by(id=UUID(m['user_id'])).delete(synchronize_session=False);s.query(Company).filter_by(id=cid).delete(synchronize_session=False);s.commit();assert s.query(Company).filter_by(id=cid).count()==0;print('R4 '+k.upper()+' CLEANUP PASS',{'residue':0},flush=True)
 finally:s.close()
 mp(k).unlink()
if __name__=='__main__':
 k,stage=sys.argv[1:3]
 if stage=='a':asyncio.run(setup(k))
 elif k=='single' and stage=='before':before_failure()
 elif stage=='recover':recover(k)
 elif k=='single' and stage=='after':after_failure()
 elif k=='multi' and stage=='partial':partial()
 elif stage=='d':cleanup(k)
 else:raise ValueError('invalid stage')
