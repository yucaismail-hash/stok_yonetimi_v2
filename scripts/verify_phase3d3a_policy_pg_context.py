from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.support.decision_policy_pg_support import build,evaluate,types,cleanup
def main():
 try:
  for risk in ('LATE_PRONE','VARIABLE','FULFILLMENT_RISK','DETERIORATING'):
   _,r=evaluate(build('context_'+risk,supplier=risk));assert 'REVIEW_SUPPLIER' in types(r)
  _,e=evaluate(build('context_event',event=True));assert 'MONITOR_EVENT_RISK' in types(e)
  print('3D3A CONTEXT PASS',flush=True)
 finally:cleanup()
if __name__=='__main__':main()
