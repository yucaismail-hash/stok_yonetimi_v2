import asyncio,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.application.retraining_eligibility import RetrainingEligibilityService
from app.database import SessionLocal
from app.models.company import Company
from scripts.support.retraining_eligibility_fixture import create_stable_finished_good_sales,cleanup_fixture
async def main():
 ids=evidence=None;s=None
 try:
  ids,evidence,_=await create_stable_finished_good_sales();s=SessionLocal();before=(s.query(__import__('app.models.actuals',fromlist=['ActualWeeklyObservation']).ActualWeeklyObservation).filter_by(company_id=ids.company_id).count(),s.query(__import__('app.models.forecast_evaluation',fromlist=['ForecastEvaluation']).ForecastEvaluation).filter_by(company_id=ids.company_id).count());result=RetrainingEligibilityService(s).evaluate(ids.company_id,ids.demand_type,ids.start_period,ids.end_period);print('ELIGIBILITY_SMOKE',result);assert len(result)==1,'result count';assert result[0].material_code==ids.material_code,'material';assert result[0].latest_evaluation_id==ids.evaluation_id,'watermark';assert before==(s.query(__import__('app.models.actuals',fromlist=['ActualWeeklyObservation']).ActualWeeklyObservation).filter_by(company_id=ids.company_id).count(),s.query(__import__('app.models.forecast_evaluation',fromlist=['ForecastEvaluation']).ForecastEvaluation).filter_by(company_id=ids.company_id).count()),'read-only';expected=result[0];s.close();s=SessionLocal();fresh=RetrainingEligibilityService(s).evaluate(ids.company_id,ids.demand_type,ids.start_period,ids.end_period)[0];assert fresh==expected,'fresh reconstruction';print('PHASE3C1 FIXTURE PASS',{'tier':fresh.tier,'evaluation_id':str(fresh.latest_evaluation_id),'sample_count':fresh.sample_count})
 finally:
  if s:
   if ids:cleanup_fixture(s,ids);assert s.query(Company).filter_by(id=ids.company_id).count()==0
   else:s.close()
if __name__=='__main__':asyncio.run(main())
