import asyncio,hashlib,json,sys
from pathlib import Path
from time import perf_counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from uuid_extensions import uuid7
from app.database import SessionLocal
from app.models.company import Company,User
from app.models.dataset import Dataset
from app.models.runtime import RuntimeExecution,RuntimeTask,RuntimeTaskAttempt,RuntimeResultReference
from app.models.security import CompanyEncryptionKey
from app.services.security import EncryptionService
from app.application.workflow_dispatcher import WorkflowDispatcher
from app.engine.local_forecast_runner import LocalForecastRunner
from app.engine.adapters.backtest_adapter import backtest_adapter
from app.analysis.backtest import BacktestEngine
from types import SimpleNamespace
async def main():
 s=SessionLocal();p='phase2g_'+str(uuid7()).replace('-','');c=u=d=None
 try:
  c=Company(id=uuid7(),name=p,tax_id=p);u=User(id=uuid7(),company_id=c.id,email=p+'@x.invalid',hashed_password='x');s.add_all((c,u));s.flush();hist=[3,5,2,6,4,7,3,8,4,9,5,10,6,11,7,12]
  data={'items':[{'sku_code':'A','demand_history':hist,'lead_time_days':14},{'sku_code':'B','demand_history':[x*2 for x in hist],'lead_time_days':21}]};d=Dataset(id=uuid7(),company_id=c.id,user_id=u.id,uploaded_by=u.id,dataset_hash=hashlib.sha256(json.dumps(data).encode()).hexdigest(),source_type=p,encrypted_data=EncryptionService(s).encrypt_dataset(u.id,data),is_active=True);s.add(d);s.commit()
  t=perf_counter();r=await WorkflowDispatcher().dispatch_single_analysis(c.id,u.id,d.id,'backtest',params={'test_window':12,'strategies':['classic','hybrid']});accept=(perf_counter()-t)*1000;eid=r['execution_id'];tasks=s.query(RuntimeTask).filter_by(execution_id=eid).all();assert len(tasks)==1 and tasks[0].capability=='backtest';t=perf_counter();await LocalForecastRunner().run(eid);dur=(perf_counter()-t)*1000
  fresh=WorkflowDispatcher();status=await fresh.get_execution_status(eid);result=await fresh.get_execution_result(eid);s.expire_all();e=s.query(RuntimeExecution).filter_by(execution_id=eid).one();a=s.query(RuntimeTaskAttempt).filter_by(execution_id=eid).one();refs=s.query(RuntimeResultReference).filter_by(execution_id=eid).all();assert status['state']=='completed' and status['progress']==100 and e.state=='completed' and a.state=='completed' and len(refs)==1 and result['result']==refs[0].inline_result;row=result['result']['items'][0];assert set(row['strategies_tested'])=={'classic','hybrid'} and row['comparison'] and row['recommendation']
  upstream={'safety_stock':{'result':{'items':[{'selected_method':'syntetos_boylan_ss'}]},'provenance':{'result_reference_id':'ss-ref'}}};selected=backtest_adapter(BacktestEngine,{'items':[{'material_code':'A','demand_history':hist,'lead_time_days':14}]},SimpleNamespace(params={'mode':'VALIDATE_SELECTED','test_window':12},upstream_results=upstream));assert selected['items'][0]['strategies_tested']==['syntetos_boylan'] and selected['items'][0]['provenance']['result_reference_id']=='ss-ref'
  try: backtest_adapter(BacktestEngine,{'items':[{'material_code':'A','demand_history':hist,'lead_time_days':14}]},SimpleNamespace(params={'mode':'VALIDATE_SELECTED'},upstream_results={'safety_stock':{'result':{'items':[{'selected_method':'bootstrapping_ss'}]}}}));raise AssertionError()
  except Exception: pass
  print('PHASE2G PASS',json.dumps({'acceptance_ms':round(accept,3),'backtest_ms':round(dur,3),'skus':2,'test_window':12,'strategies':2,'attempts':1}),flush=True)
 finally:
  s.rollback()
  if c:
   ids=[x[0] for x in s.query(RuntimeExecution.execution_id).filter_by(company_id=c.id).all()];s.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeTaskAttempt).filter(RuntimeTaskAttempt.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeTask).filter(RuntimeTask.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(ids)).delete(synchronize_session=False);s.query(Dataset).filter_by(source_type=p).delete(synchronize_session=False);s.query(CompanyEncryptionKey).filter_by(user_id=u.id).delete(synchronize_session=False);s.query(User).filter_by(email=p+'@x.invalid').delete(synchronize_session=False);s.query(Company).filter_by(tax_id=p).delete(synchronize_session=False);s.commit();s.close()
if __name__=='__main__':asyncio.run(main())
