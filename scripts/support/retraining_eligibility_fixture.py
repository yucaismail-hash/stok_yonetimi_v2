"""Test-only canonical eligibility evidence wrapper around Champion evidence."""
from dataclasses import dataclass
from scripts.support.champion_evidence_fixture import create_finished_good_sales,reconstruct,cleanup

# Generalized tier evidence uses the verified AA5 durable Runtime/Vintage/Evaluation boundary.
async def create_tier_shape(shape, points=8, material_code='SKU', demand_type='sales', product_level='finished_good', context=None, cutoff_week=24, target_start_week=None):
 from datetime import timedelta
 from decimal import Decimal
 from uuid_extensions import uuid7
 from app.database import SessionLocal
 from app.models.company import Company,User
 from app.models.dataset import Dataset
 from app.models.runtime import RuntimeExecution,RuntimeResultReference
 from app.models.forecast_vintage import ForecastVintage,ForecastVintagePoint
 from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
 from app.application.forecast_evaluation_service import ForecastEvaluationService
 from app.application.effective_forecast_timeline import target_period_start
 from app.services.security import EncryptionService
 import hashlib
 s=SessionLocal();cid=uid=did=None
 try:
  tag='eligibility_tier_'+shape+'_'+str(uuid7())
  if context is None:
   c=Company(id=uuid7(),name=tag,tax_id=tag);u=User(id=uuid7(),company_id=c.id,email=tag+'@x.invalid',hashed_password='x');s.add_all((c,u));s.flush();cid,uid=c.id,u.id;d=Dataset(id=uuid7(),company_id=cid,user_id=uid,uploaded_by=uid,dataset_hash=hashlib.sha256(tag.encode()).hexdigest(),source_type=tag,encrypted_data=EncryptionService(s).encrypt_dataset(uid,{'items':[{'sku_code':material_code,'demand_history':[100+w for w in range(cutoff_week)],'lead_time_days':7}]}),is_active=True);s.add(d);s.commit();did=d.id
  else:
   cid,uid,did=context['company_id'],context['user_id'],context['dataset_id']
  target_start_week=target_start_week or cutoff_week+1
  targets=[f'2026-W{w:02d}' for w in range(target_start_week,target_start_week+points)];actuals=[100]*points if shape!='tier3' else [100]*(points-3)+[150]*3;forecasts=[100]*points
  if shape=='tier2': forecasts[-3:]=[80,120,80]
  if shape=='tier3': forecasts[-3:]=[100,100,100]
  rows=[{'material_code':material_code,'period':f'2026-W{w:02d}','quantity':100,'product_level':product_level,'product_group':'G','product_class':'C'} for w in range(1,cutoff_week+1)]+[{'material_code':material_code,'period':p,'quantity':a,'product_level':product_level,'product_group':'G','product_class':'C'} for p,a in zip(targets,actuals)];ActualWeeklyLedgerService().ingest_dataset_actuals(cid,uid,did,rows,demand_type)
  cutoff_period=f'2026-W{cutoff_week:02d}';e=RuntimeExecution(execution_id=uuid7(),company_id=cid,user_id=uid,dataset_id=did,workflow_id=tag,analysis_type='forecast',state='completed');s.add(e);s.flush();r=RuntimeResultReference(company_id=cid,execution_id=e.execution_id,result_type='forecast',result_version='1',contract_version='1',storage_kind='inline_jsonb',inline_result={'fixture':shape},validation_status='validated');s.add(r);s.flush();available=target_period_start(cutoff_period)+timedelta(hours=1);v=ForecastVintage(company_id=cid,execution_id=e.execution_id,runtime_result_reference_id=r.id,dataset_id=did,forecast_available_at=available,forecast_origin_period=cutoff_period,input_cutoff_period=cutoff_period,demand_type=demand_type,result_version='1',contract_version='1');s.add(v);s.flush()
  for i,(p,f) in enumerate(zip(targets,forecasts),1):s.add(ForecastVintagePoint(forecast_vintage_id=v.id,material_code=material_code,target_period=p,forecast_value=Decimal(str(f)),lower_interval=Decimal(str(f-1)),upper_interval=Decimal(str(f+1)),model_used='fixture',product_level=product_level,product_group='G',product_class='C',horizon_index=i))
  s.flush();ev=ForecastEvaluationService(s).evaluate(cid,demand_type,targets[0],targets[-1]);s.commit();return {'company_id':cid,'user_id':uid,'dataset_id':did,'execution_id':e.execution_id,'runtime_result_reference_id':r.id,'forecast_vintage_id':v.id,'evaluation_id':ev.evaluation.id,'material_code':material_code,'demand_type':demand_type,'product_level':product_level,'start_period':targets[0],'end_period':targets[-1],'latest_evaluation_id':ev.evaluation.id}
 except:
  s.rollback();raise
 finally:s.close()

@dataclass(frozen=True)
class RetrainingEligibilityFixtureIds:
 company_id:object; user_id:object; dataset_id:object; execution_id:object; runtime_result_reference_id:object; forecast_vintage_id:object; evaluation_id:object; material_code:str; demand_type:str; start_period:str; end_period:str

async def create_stable_finished_good_sales():
 ids,evidence,tag=await create_finished_good_sales()
 periods=evidence.target_periods
 return RetrainingEligibilityFixtureIds(ids.company_id,ids.user_id,ids.dataset_id,ids.execution_id,ids.runtime_result_reference_id,ids.forecast_vintage_id,ids.evaluation_id,ids.material_code,ids.demand_type,periods[0],periods[-1]),evidence,tag

def cleanup_fixture(session,ids):
 from scripts.support.champion_evidence_fixture import ChampionFixtureIds
 cleanup(session,ChampionFixtureIds(ids.company_id,ids.user_id,ids.dataset_id,ids.execution_id,ids.runtime_result_reference_id,ids.forecast_vintage_id,ids.evaluation_id,ids.material_code,ids.demand_type))
