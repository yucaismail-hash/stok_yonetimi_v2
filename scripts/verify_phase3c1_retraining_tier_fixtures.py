import asyncio,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.application.retraining_eligibility import RetrainingEligibilityService
from app.database import SessionLocal
from scripts.support.retraining_eligibility_fixture import create_tier_shape,cleanup_fixture
async def main():
 fixtures=[]
 try:
  for shape,n in (('stable',4),('tier2',8),('tier3',8)):
   x=await create_tier_shape(shape,n);fixtures.append(x);s=SessionLocal();r=RetrainingEligibilityService(s).evaluate(x['company_id'],x['demand_type'],x['start_period'],x['end_period'])[0];print('TIER_FIXTURE',shape,r.tier,r.sample_count,r.performance_drift,r.demand_drift,r.mean_signed_error);s.close()
 finally:
  for x in fixtures:
   s=SessionLocal();cleanup_fixture(s,type('Ids',(),x)())
if __name__=='__main__':asyncio.run(main())
