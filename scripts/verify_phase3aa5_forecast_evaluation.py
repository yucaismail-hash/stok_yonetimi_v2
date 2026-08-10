"""PostgreSQL proof for durable Forecast-to-Actual evaluation."""
import hashlib, json, sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from uuid_extensions import uuid7
from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.effective_forecast_timeline import target_period_start
from app.application.forecast_evaluation_service import ForecastEvaluationService
from app.database import SessionLocal
from app.models.actuals import ActualWeeklyObservation, ActualWeeklyRevision
from app.models.company import Company, User
from app.models.dataset import Dataset
from app.models.forecast_evaluation import ForecastEvaluation, ForecastEvaluationPoint
from app.models.forecast_vintage import ForecastVintage, ForecastVintagePoint
from app.models.runtime import RuntimeExecution, RuntimeResultReference, RuntimeTask, RuntimeTaskAttempt
from app.models.security import CompanyEncryptionKey
from app.services.security import EncryptionService

def at(period, hour=0): return target_period_start(period)+timedelta(hours=hour)
def row(code, period, quantity, level='Mamul', group='actual-group', klass='actual-class'): return {'material_code':code,'period':period,'quantity':quantity,'product_level':level,'product_group':group,'product_class':klass}

def vintage(s,cid,uid,did,label,available,cutoff,code,period,value,demand='sales',level='finished_good',group='forecast-group',klass='forecast-class',learning=None):
 e=RuntimeExecution(execution_id=uuid7(),company_id=cid,user_id=uid,dataset_id=did,workflow_id='phase3aa5_'+label,analysis_type='forecast',state='completed');s.add(e);s.flush()
 r=RuntimeResultReference(company_id=cid,execution_id=e.execution_id,result_type='forecast',result_version='1.0.0',contract_version='1.0.0',storage_kind='inline_jsonb',inline_result={'fixture':label},validation_status='validated',created_at=available);s.add(r);s.flush()
 v=ForecastVintage(company_id=cid,execution_id=e.execution_id,runtime_result_reference_id=r.id,dataset_id=did,forecast_available_at=available,forecast_origin_period=cutoff,input_cutoff_period=cutoff,demand_type=demand,learning_score_at_run=learning,result_version='1.0.0',contract_version='1.0.0');s.add(v);s.flush()
 p=ForecastVintagePoint(forecast_vintage_id=v.id,material_code=code,target_period=period,forecast_value=Decimal(str(value)),lower_interval=Decimal(str(value-1)),upper_interval=Decimal(str(value+1)),model_used='model-'+label,product_level=level,product_group=group,product_class=klass,horizon_index=1);s.add(p);s.flush();return v

def cleanup(s,cid,uid):
 ids=[x for x, in s.query(RuntimeExecution.execution_id).filter_by(company_id=cid)]; vids=[x for x, in s.query(ForecastVintage.id).filter_by(company_id=cid)]; eids=[x for x, in s.query(ForecastEvaluation.id).filter_by(company_id=cid)]
 s.query(ForecastEvaluationPoint).filter(ForecastEvaluationPoint.evaluation_id.in_(eids)).delete(synchronize_session=False);s.query(ForecastEvaluation).filter_by(company_id=cid).delete(synchronize_session=False);s.query(ForecastVintagePoint).filter(ForecastVintagePoint.forecast_vintage_id.in_(vids)).delete(synchronize_session=False);s.query(ForecastVintage).filter_by(company_id=cid).delete(synchronize_session=False);s.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeTaskAttempt).filter(RuntimeTaskAttempt.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeTask).filter(RuntimeTask.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(ids)).delete(synchronize_session=False);s.query(ActualWeeklyRevision).filter_by(company_id=cid).delete(synchronize_session=False);s.query(ActualWeeklyObservation).filter_by(company_id=cid).delete(synchronize_session=False);s.query(Dataset).filter_by(company_id=cid).delete(synchronize_session=False);s.query(CompanyEncryptionKey).filter_by(user_id=uid).delete(synchronize_session=False);s.query(User).filter_by(id=uid).delete(synchronize_session=False);s.query(Company).filter_by(id=cid).delete(synchronize_session=False);s.commit()

def main():
 s=SessionLocal();cid=uid=None
 try:
  tag='phase3aa5_'+str(uuid7()).replace('-','');c=Company(id=uuid7(),name=tag,tax_id=tag);u=User(id=uuid7(),company_id=c.id,email=tag+'@x.invalid',hashed_password='x');s.add_all((c,u));s.flush();cid,uid=c.id,u.id
  payload={'items':[{'sku_code':'SKU-F','demand_history':[1,2]}]};d=Dataset(id=uuid7(),company_id=cid,user_id=uid,uploaded_by=uid,dataset_hash=hashlib.sha256(tag.encode()).hexdigest(),source_type=tag,encrypted_data=EncryptionService(s).encrypt_dataset(uid,payload),is_active=True);s.add(d);s.commit();did=d.id
  ledger=ActualWeeklyLedgerService(); sales=[row('SKU-F',f'2026-W{w:02d}',q) for w,q in ((10,100),(11,100),(12,100),(13,0),(14,50),(15,100),(16,100),(17,70))]+[row('SKU-S','2026-W10',40,'semi_finished_good','semi-actual','S'),row('SKU-R','2026-W10',20,'raw_material','raw-actual','R')]
  ledger.ingest_dataset_actuals(cid,uid,did,sales,'sales');ledger.ingest_dataset_actuals(cid,uid,did,[row('SKU-F','2026-W10',55)],'shipment');ledger.ingest_dataset_actuals(cid,uid,did,[row('SKU-Z','2026-W10',0)],'order')
  s.close();s=SessionLocal()
  for w,value in ((10,100),(11,90),(12,110),(13,0),(14,0),(15,80)): vintage(s,cid,uid,did,'A'+str(w),at('2026-W09'),'2026-W09','SKU-F',f'2026-W{w:02d}',value)
  a15=s.query(ForecastVintage).filter_by(company_id=cid,input_cutoff_period='2026-W09').first();b15=vintage(s,cid,uid,did,'B',at('2026-W12'),'2026-W12','SKU-F','2026-W15',90,group='overlap-snapshot',klass='B',learning=Decimal('0.700'))
  vintage(s,cid,uid,did,'future',at('2026-W16',1),'2026-W15','SKU-F','2026-W16',95);vintage(s,cid,uid,did,'awaiting',at('2026-W17'),'2026-W17','SKU-F','2026-W18',10);vintage(s,cid,uid,did,'arrival',at('2026-W18'),'2026-W18','SKU-F','2026-W19',90)
  vintage(s,cid,uid,did,'semi',at('2026-W09'),'2026-W09','SKU-S','2026-W10',30,level='semi_finished_good',group='semi-forecast',klass='S');vintage(s,cid,uid,did,'raw',at('2026-W09'),'2026-W09','SKU-R','2026-W10',25,level='raw_material',group='raw-forecast',klass='R');vintage(s,cid,uid,did,'ship',at('2026-W09'),'2026-W09','SKU-F','2026-W10',50,demand='shipment');vintage(s,cid,uid,did,'zero',at('2026-W09'),'2026-W09','SKU-Z','2026-W10',0,demand='order');s.commit()
  service=ForecastEvaluationService(s);first=service.evaluate(cid,'sales','2026-W10','2026-W19');header=first.evaluation;assert header and first.evaluated_point_count==8 and ('SKU-F','2026-W18') in first.awaiting_actual and ('SKU-F','2026-W19') in first.awaiting_actual and {('SKU-F','2026-W16'),('SKU-F','2026-W17')}.issubset(set(first.no_eligible_forecast));assert header.wape==Decimal('95')/Decimal('510') and header.forecast_accuracy==Decimal('1')-header.wape
  points={(p.material_code,p.target_period):p for p in s.query(ForecastEvaluationPoint).filter_by(evaluation_id=header.id)};assert points[('SKU-F','2026-W10')].error==0 and points[('SKU-F','2026-W11')].error==10 and points[('SKU-F','2026-W12')].error==-10 and points[('SKU-F','2026-W13')].accepted_actual_quantity==0 and points[('SKU-F','2026-W14')].forecast_value==0 and points[('SKU-F','2026-W15')].forecast_vintage_id==b15.id and points[('SKU-F','2026-W15')].product_group=='overlap-snapshot' and points[('SKU-F','2026-W15')].learning_score_at_run==Decimal('0.700')
  assert service.aggregate(header.id,cid,product_level='finished_good').point_count==6 and service.aggregate(header.id,cid,product_level='semi_finished_good').point_count==1 and service.aggregate(header.id,cid,product_level='raw_material').point_count==1 and service.aggregate(header.id,cid,product_group='overlap-snapshot').point_count==1 and service.aggregate(header.id,cid,product_class='B').point_count==1 and service.aggregate(header.id,cid,material_code='SKU-F').point_count==6
  shipment=service.evaluate(cid,'shipment','2026-W10','2026-W10');zero=service.evaluate(cid,'order','2026-W10','2026-W10');assert shipment.evaluated_point_count==1 and shipment.evaluation.wape==Decimal('5')/Decimal('55') and zero.evaluation.wape is None and zero.evaluation.wape_unavailable_reason=='zero_actual_denominator';s.commit()
  before=(s.query(ForecastEvaluation).filter_by(company_id=cid).count(),s.query(ForecastEvaluationPoint).join(ForecastEvaluation).filter(ForecastEvaluation.company_id==cid).count());again=service.evaluate(cid,'sales','2026-W10','2026-W19');s.commit();assert again.evaluation.id==header.id and (s.query(ForecastEvaluation).filter_by(company_id=cid).count(),s.query(ForecastEvaluationPoint).join(ForecastEvaluation).filter(ForecastEvaluation.company_id==cid).count())==before
  ledger.ingest_dataset_actuals(cid,uid,did,[row('SKU-F','2026-W19',100)],'sales');arrival=service.evaluate(cid,'sales','2026-W10','2026-W19');s.commit();assert arrival.evaluated_point_count==9 and ('SKU-F','2026-W19') not in arrival.awaiting_actual
  proposed=ledger.ingest_dataset_actuals(cid,uid,did,[row('SKU-F','2026-W11',120)],'sales');ledger.approve_revision(cid,proposed['revision_ids'][0],uid);corrected=service.evaluate(cid,'sales','2026-W10','2026-W19');s.commit();corrected_point=s.query(ForecastEvaluationPoint).filter_by(evaluation_id=header.id,material_code='SKU-F',target_period='2026-W11').one();assert corrected_point.accepted_actual_quantity==120 and corrected_point.error==30 and corrected_point.actual_revision_id is not None
  rejected=ledger.ingest_dataset_actuals(cid,uid,did,[row('SKU-F','2026-W12',120)],'sales');ledger.reject_revision(cid,rejected['revision_ids'][0],uid);unchanged=service.evaluate(cid,'sales','2026-W10','2026-W19');s.commit();assert s.query(ForecastEvaluationPoint).filter_by(evaluation_id=header.id,material_code='SKU-F',target_period='2026-W12').one().accepted_actual_quantity==100
  expected=[(p.material_code,p.target_period,str(p.accepted_actual_quantity),str(p.forecast_value),str(p.forecast_vintage_id)) for p in s.query(ForecastEvaluationPoint).filter_by(evaluation_id=header.id).order_by(ForecastEvaluationPoint.material_code,ForecastEvaluationPoint.target_period)];s.close();s=SessionLocal();fresh=ForecastEvaluationService(s).evaluate(cid,'sales','2026-W10','2026-W19');s.commit();observed=[(p.material_code,p.target_period,str(p.accepted_actual_quantity),str(p.forecast_value),str(p.forecast_vintage_id)) for p in s.query(ForecastEvaluationPoint).filter_by(evaluation_id=fresh.evaluation.id).order_by(ForecastEvaluationPoint.material_code,ForecastEvaluationPoint.target_period)];assert observed==expected
  print('PHASE3AA5 PASS',json.dumps({'points':len(observed),'wape_contract':'1.0.0','overlap':'effective timeline','correction':'100->120','zero_actual_wape':'unavailable'}),flush=True)
 finally:
  if s and cid: cleanup(s,cid,uid)
  elif s: s.close()
if __name__=='__main__': main()
