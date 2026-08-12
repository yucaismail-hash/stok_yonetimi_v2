import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.database import SessionLocal
from app.application.pattern_intelligence import PatternIntelligenceService,MIN_HISTORY
from scripts.support.pattern_intelligence_fixture import create,cleanup
def result(f):
 s=SessionLocal()
 try:return PatternIntelligenceService(s).calculate(f.company_id,f.material_code,f.demand_type,f.periods[-1])
 finally:s.close()
def main():
 fs=[]
 try:
  stable=create('stable');fs.append(stable);trend=create('trend');fs.append(trend);volatile=create('volatile');fs.append(volatile);inter=create('intermittent');fs.append(inter);lumpy=create('lumpy');fs.append(lumpy);missing=create('missing');fs.append(missing);short=create('insufficient');fs.append(short)
  a,b,c,d,e,g,h=map(result,(stable,trend,volatile,inter,lumpy,missing,short))
  assert a.coefficient_of_variation<.03 and abs(a.trend_slope)<.2
  assert b.trend_slope>0 and b.trend_strength>=.2
  assert c.coefficient_of_variation>=.5 and c.zero_demand_ratio==0
  assert d.zero_demand_ratio>.5 and d.adi>1.32
  assert e.zero_demand_ratio>.5 and e.adi>1.32 and e.squared_coefficient_of_variation>.49
  assert g.missing_periods and g.coverage_ratio<1 and h.status=='INSUFFICIENT_HISTORY' and h.sample_count<MIN_HISTORY
  print('PATTERN FIXTURES PASS',{'stable_cv':a.coefficient_of_variation,'trend_slope':b.trend_slope,'volatile_cv':c.coefficient_of_variation,'intermittent_adi':d.adi,'lumpy_cv2':e.squared_coefficient_of_variation,'missing':len(g.missing_periods)})
 finally:
  for f in reversed(fs):cleanup(f)
if __name__=='__main__':main()
