"""Development-only proof for the durable real standalone Safety Stock slice."""
import asyncio, hashlib, json, sys
from pathlib import Path
from time import perf_counter
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from uuid_extensions import uuid7
from sqlalchemy.orm import configure_mappers
from app.application.workflow_dispatcher import WorkflowDispatcher
from app.database import SessionLocal
from app.engine.adapters.safety_stock_adapter import safety_stock_adapter
from app.engine.capability_contracts import CapabilityExecutionRequest
from app.engine.capability_executor import CapabilityExecutor
from app.engine.capability_registry import Capability
from app.engine.dataset_runtime_provider import DatasetRuntimeProvider
from app.engine.local_forecast_runner import LocalForecastRunner
from app.models.company import Company, User
from app.models.dataset import Dataset
from app.models.runtime import RuntimeExecution, RuntimeResultReference, RuntimeTask, RuntimeTaskAttempt
from app.models.security import CompanyEncryptionKey
from app.services.security import EncryptionService
from app.analysis.safety_stock import ComprehensiveSafetyStockOptimizer

async def main():
    s=SessionLocal(); probe='phase2e_fast_'+str(uuid7()).replace('-',''); company=user=dataset=None
    try:
        configure_mappers(); company=Company(id=uuid7(),name=probe,tax_id=probe); user=User(id=uuid7(),company_id=company.id,email=probe+'@example.invalid',hashed_password='probe'); s.add_all((company,user)); s.flush()
        payload={'items':[{'sku_code':'SKU_A','demand_history':[10,11,12,11,13,12,14,13,12,14,15,14,16,15,14,16],'lead_time_days':14},{'sku_code':'SKU_B','demand_history':[0,0,8,0,0,0,12,0,0,7,0,0,0,15,0,0],'lead_time_days':21}]}
        encrypted=EncryptionService(s).encrypt_dataset(user.id,payload); dataset=Dataset(id=uuid7(),company_id=company.id,user_id=user.id,uploaded_by=user.id,dataset_hash=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest(),source_type=probe,encrypted_data=encrypted,is_active=True); s.add(dataset); s.commit()
        # Controlled real executor proof, with supplier data deliberately absent.
        request=CapabilityExecutionRequest(uuid7(),'safety_probe','safety_stock',Capability.SAFETY_STOCK,company.id,user.id,dataset.id,60,params={'service_level':{'mode':'automatic'}})
        executor=CapabilityExecutor(lambda c: ComprehensiveSafetyStockOptimizer if c is Capability.SAFETY_STOCK else None,DatasetRuntimeProvider(s),safety_stock_adapter,lambda invoke,timeout:invoke())
        direct=await executor.execute(request); assert direct.state.value=='completed' and len(direct.result['items'])==2 and all(len(x['candidate_methods'])==6 and x['supplier_enrichment']['status']=='unavailable' and x['lead_time_source']=='dataset_manual' for x in direct.result['items'])
        assert direct.result['items'][0]['safety_stock'] != direct.result['items'][1]['safety_stock']
        # Executor boundary failure proofs: real-engine exception conversion and non-JSON result rejection.
        bad_engine=CapabilityExecutor(lambda c: ComprehensiveSafetyStockOptimizer,lambda r:{'items':[{'material_code':'X','demand_history':[1]*8,'lead_time_days':7,'supplier_enrichment':'unavailable_unused'}]},lambda *args: (_ for _ in ()).throw(RuntimeError('controlled engine exception')),lambda invoke,timeout:invoke())
        assert (await bad_engine.execute(request)).state.value=='failed'
        bad_json=CapabilityExecutor(lambda c: ComprehensiveSafetyStockOptimizer,lambda r:{'items':[{'material_code':'X','demand_history':[1]*8,'lead_time_days':7,'supplier_enrichment':'unavailable_unused'}]},lambda *args:{'bad':set()},lambda invoke,timeout:invoke())
        assert (await bad_json.execute(request)).state.value=='failed'
        dispatcher=WorkflowDispatcher(); started=perf_counter(); accepted=await dispatcher.dispatch_single_analysis(company.id,user.id,dataset.id,'safety_stock',params={'service_level':{'mode':'manual','value':.95}}); acceptance_ms=(perf_counter()-started)*1000; execution_id=accepted['execution_id']
        durable=s.query(RuntimeExecution).filter_by(execution_id=execution_id).one(); tasks=s.query(RuntimeTask).filter_by(execution_id=execution_id).all(); assert durable.state=='queued' and float(durable.progress)==0 and len(tasks)==1 and tasks[0].capability=='safety_stock' and tasks[0].required and not tasks[0].skippable and tasks[0].dependencies==[]
        t=perf_counter(); await LocalForecastRunner().run(execution_id); execution_ms=(perf_counter()-t)*1000
        fresh=WorkflowDispatcher(); status=await fresh.get_execution_status(execution_id); result=await fresh.get_execution_result(execution_id); s.expire_all(); durable=s.query(RuntimeExecution).filter_by(execution_id=execution_id).one(); task=s.query(RuntimeTask).filter_by(execution_id=execution_id).one(); attempts=s.query(RuntimeTaskAttempt).filter_by(execution_id=execution_id).all(); refs=s.query(RuntimeResultReference).filter_by(execution_id=execution_id).all()
        assert status['state']=='completed' and status['progress']==100 and durable.state=='completed' and task.state=='completed' and len(attempts)==1 and len(refs)==1 and refs[0].validation_status=='validated' and result['result']==refs[0].inline_result
        # Controlled durable input failures: invalid service level and missing lead time/insufficient history each must never persist a result.
        for suffix, items, params in [('bad_service',payload['items'],{'service_level':{'mode':'manual','value':1.2}}),('missing_lead',[{'sku_code':'M','demand_history':[1]*8}],{}),('short_history',[{'sku_code':'S','demand_history':[1,2,3],'lead_time_days':7}],{})]:
            enc=EncryptionService(s).encrypt_dataset(user.id,{'items':items}); d=Dataset(id=uuid7(),company_id=company.id,user_id=user.id,uploaded_by=user.id,dataset_hash=probe+suffix,source_type=probe+suffix,encrypted_data=enc,is_active=True); s.add(d); s.commit(); bad=await dispatcher.dispatch_single_analysis(company.id,user.id,d.id,'safety_stock',params=params); await LocalForecastRunner().run(bad['execution_id']); s.expire_all(); e=s.query(RuntimeExecution).filter_by(execution_id=bad['execution_id']).one(); a=s.query(RuntimeTaskAttempt).filter_by(execution_id=bad['execution_id']).one(); assert e.state=='failed' and a.state=='failed' and s.query(RuntimeResultReference).filter_by(execution_id=bad['execution_id']).count()==0
        print('PHASE2E FAST PASS',json.dumps({'acceptance_latency_ms':round(acceptance_ms,3),'claim_delay_ms':0.0,'safety_stock_execution_duration_ms':round(execution_ms,3),'capability_duration_ms':round(direct.duration_ms,3),'total_duration_ms':round((perf_counter()-started)*1000,3),'sku_count':2,'candidate_method_count':6,'attempt_count':len(attempts),'execution_id':str(execution_id)}),flush=True)
    finally:
        s.rollback()
        if company is not None:
            ids=[x[0] for x in s.query(RuntimeExecution.execution_id).filter_by(company_id=company.id).all()]
            if ids:
                s.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(ids)).delete(synchronize_session=False); s.query(RuntimeTaskAttempt).filter(RuntimeTaskAttempt.execution_id.in_(ids)).delete(synchronize_session=False); s.query(RuntimeTask).filter(RuntimeTask.execution_id.in_(ids)).delete(synchronize_session=False); s.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(ids)).delete(synchronize_session=False)
            s.query(Dataset).filter(Dataset.source_type.like(probe+'%')).delete(synchronize_session=False); s.query(CompanyEncryptionKey).filter_by(user_id=user.id).delete(synchronize_session=False); s.query(User).filter_by(email=probe+'@example.invalid').delete(synchronize_session=False); s.query(Company).filter_by(tax_id=probe).delete(synchronize_session=False); s.commit()
        s.close()
if __name__=='__main__': asyncio.run(main())
