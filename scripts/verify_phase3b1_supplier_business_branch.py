"""PostgreSQL proof for optional Supplier Business Workflow enrichment."""
import asyncio, hashlib, json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from uuid_extensions import uuid7
from app.application.business_workflow_acceptance import BusinessWorkflowAcceptanceService
from app.application.business_workflow_aggregation import BusinessWorkflowAggregationService
from app.database import SessionLocal
from app.engine.business_workflow_scheduler import BusinessWorkflowScheduler
from app.engine.runtime_store import RuntimeStore
from app.models.company import Company,User
from app.models.dataset import Dataset
from app.models.learning import CompanyLearningMemory
from app.models.runtime import RuntimeExecution,RuntimeResultReference,RuntimeTask,RuntimeTaskAttempt
from app.models.security import CompanyEncryptionKey
from app.services.security import EncryptionService

def make(name,payload):
 s=SessionLocal();tag='phase3b1_'+name+'_'+str(uuid7()).replace('-','')
 try:
  c=Company(id=uuid7(),name=tag,tax_id=tag);u=User(id=uuid7(),company_id=c.id,email=tag+'@x.invalid',hashed_password='x');s.add_all((c,u));s.flush();d=Dataset(id=uuid7(),company_id=c.id,user_id=u.id,uploaded_by=u.id,dataset_hash=hashlib.sha256((tag+json.dumps(payload)).encode()).hexdigest(),source_type=tag,encrypted_data=EncryptionService(s).encrypt_dataset(u.id,payload),is_active=True);s.add(d);s.commit();eid=BusinessWorkflowAcceptanceService().accept(c.id,u.id,d.id,request_metadata={'params':{'n_simulations':2,'weeks':1,'test_window':4}});return tag,c.id,u.id,eid
 finally:s.close()
def clean(f):
 tag,cid,uid,_=f;s=SessionLocal()
 try:
  ids=[x for x, in s.query(RuntimeExecution.execution_id).filter_by(company_id=cid)];s.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeTaskAttempt).filter(RuntimeTaskAttempt.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeTask).filter(RuntimeTask.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(ids)).delete(synchronize_session=False);s.query(Dataset).filter_by(source_type=tag).delete(synchronize_session=False);s.query(CompanyEncryptionKey).filter_by(user_id=uid).delete(synchronize_session=False);s.query(User).filter_by(id=uid).delete(synchronize_session=False);s.query(Company).filter_by(id=cid).delete(synchronize_session=False);s.commit()
 finally:s.close()
async def run_all(eid,cid):
 progress=[]
 for _ in range(5):
  s=SessionLocal()
  try:
   ref=await BusinessWorkflowScheduler(s).run_next_ready(eid,cid)
   if not ref:break
   s.expire_all();progress.append(int(RuntimeStore(s).get_execution(eid,cid).progress))
  finally:s.close()
 return progress
async def main():
 fixtures=[];mode=sys.argv[1] if len(sys.argv)>1 else 'all';history=[3,5,2,6,4,7,3,8,4,9,5,10,6,11,7,12,8,13]
 items=[{'sku_code':'FG-1','product_level':'finished_good','demand_history':history,'lead_time_days':14,'initial_stock':80,'eoq':25},{'sku_code':'RAW-1','product_level':'raw_material','demand_history':history,'lead_time_days':21,'initial_stock':60,'eoq':20}]
 try:
  if mode != 'present':
   absent=make('absent',{'items':items});fixtures.append(absent);s=SessionLocal();tasks=RuntimeStore(s).get_tasks(absent[3],absent[1]);assert len(tasks)==4 and 'supplier' not in {x.task_id for x in tasks} and (RuntimeStore(s).get_execution(absent[3],absent[1]).metadata_ or {})['supplier_enrichment']['status']=='absent';s.close();progress_a=await run_all(absent[3],absent[1]);assert progress_a==[25,50,75,100];aggregate_a=BusinessWorkflowAggregationService().aggregate(absent[1],absent[3]);assert set(aggregate_a)-{'execution_id','workflow_type','workflow_version','dataset_id','company_id','provenance'}=={'forecast','safety_stock','simulation','backtest'}
   if mode == 'absent':
    print('PHASE3B1 ABSENT PASS',json.dumps({'progress':progress_a,'tasks':4}),flush=True);return
  supplier_payload={'items':items,'suppliers':{'SUP-1':{'name':'Supplier 1','delivery_records':[{'planned_days_ago':12,'actual_days_ago':11,'planned_qty':100,'actual_qty':100}]},'SUP-2':{'name':'Supplier 2','delivery_records':[{'planned_days_ago':20,'actual_days_ago':8,'planned_qty':100,'actual_qty':80,'defects':2}]}},'supplier_mapping':{'FG-1':{'supplier_id':'SUP-1','share':.7},'RAW-1':{'supplier_id':'SUP-2','share':.3}}}
  present=make('present',supplier_payload);fixtures.append(present);s=SessionLocal();tasks=RuntimeStore(s).get_tasks(present[3],present[1]);assert len(tasks)==5 and {x.task_id for x in tasks}=={'forecast','safety_stock','supplier','simulation','backtest'} and (RuntimeStore(s).get_execution(present[3],present[1]).metadata_ or {})['supplier_enrichment']['status']=='available';s.close();progress_b=await run_all(present[3],present[1]);assert progress_b==[20,40,60,80,100]
  aggregate_b=BusinessWorkflowAggregationService().aggregate(present[1],present[3]);assert 'supplier' in aggregate_b and len(aggregate_b['supplier']['suppliers'])==2 and aggregate_b['supplier']['mapping_count']==2
  s=SessionLocal();store=RuntimeStore(s);execution=store.get_execution(present[3],present[1]);tasks={x.task_id:x for x in store.get_tasks(present[3],present[1])};refs={x.result_type:x for x in store.get_execution_result_references(present[3],present[1])};assert execution.state=='completed' and all(x.state=='completed' for x in tasks.values()) and s.query(RuntimeTaskAttempt).filter_by(execution_id=present[3],state='completed').count()==5 and set(refs)=={'forecast','safety_stock','supplier','simulation','backtest','business_workflow'} and refs['supplier'].inline_result==aggregate_b['supplier'] and s.query(CompanyLearningMemory).filter_by(company_id=present[1]).count()==0;s.close()
  invalid=make('invalid',{'items':items,'suppliers':{'SUP-1':{'delivery_records':[]}},'supplier_mapping':{'MISSING':{'supplier_id':'SUP-1'}}});fixtures.append(invalid);s=SessionLocal();e=RuntimeStore(s).get_execution(invalid[3],invalid[1]);assert len(RuntimeStore(s).get_tasks(invalid[3],invalid[1]))==4 and e.metadata_['supplier_enrichment']['status']=='invalid';s.close()
  print('PHASE3B1 PASS',json.dumps({'absent_progress':progress_a if mode != 'present' else None,'present_progress':progress_b,'supplier_attempts':5,'supplier_results':1,'product_levels':['finished_good','raw_material'],'learning_side_effects':0}),flush=True)
 finally:
  for f in fixtures:clean(f)
if __name__=='__main__':asyncio.run(main())
