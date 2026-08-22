from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.support.decision_policy_pg_support import build,evaluate,types,cleanup
def main():
 try:
  weak=build('forecast_weak',backtest='weak_validation');_,rw=evaluate(weak);assert 'REVIEW_FORECAST' in types(rw) and rw.agreement_status=='CONFLICTED'
  structural=build('forecast_pattern',pattern='STRUCTURAL_CHANGE');_,rp=evaluate(structural);assert 'REVIEW_FORECAST' in types(rp)
  assert evaluate(weak)==evaluate(weak);print('3D3A FORECAST PASS',flush=True)
 finally:cleanup()
if __name__=='__main__':main()
