"""Three-process durable first-use proof: setup | assert | cleanup."""
from pathlib import Path
import json,sys
from time import perf_counter_ns
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.verify_phase3d3a_decision_policy_postgres import build,roots
from scripts import verify_phase3d2_decision_evidence_matrix as d2
from app.application.decision_evidence_resolver import DecisionEvidenceResolver
from app.application.decision_policy import DecisionPolicy
from app.database import SessionLocal
from app.models.forecast_vintage import ForecastVintage
M=Path(__file__).resolve().parent/'.phase3d3a_core_d_fixture.json'
def setup():
 t=perf_counter_ns();ids=build('core_d_first_use',safety=False,company_learning=False);s=SessionLocal()
 try:
  v=s.query(ForecastVintage).filter_by(company_id=ids['company_id'],demand_type='sales').one();data={**{k:str(vv) for k,vv in ids.items()},'runtime_execution_id':str(v.execution_id),'forecast_result_reference_id':str(v.runtime_result_reference_id),'forecast_vintage_id':str(v.id),'material_code':'SKU','demand_type':'sales','decision_cutoff_period':'2026-W20','decision_context':'FORECAST_REVIEW'};M.write_text(json.dumps(data));print('CORE-D SETUP PASS',{'setup_ms':round((perf_counter_ns()-t)/1e6,3),'manifest_fields':sorted(data)},flush=True)
 finally:s.close()
def assertion():
 d=json.loads(M.read_text());t=perf_counter_ns();e=DecisionEvidenceResolver().resolve(d['company_id'],d['material_code'],d['demand_type'],d['decision_cutoff_period'],d['decision_context']);a=perf_counter_ns();r=DecisionPolicy().evaluate(e);b=perf_counter_ns();o=dict(e.optional);assert e.status=='READY' and dict(e.required)['forecast']['status']=='AVAILABLE' and r.status=='READY' and r.candidates[0].candidate_type=='HOLD_POLICY';assert all(o[x]['status']=='ABSENT' for x in ('safety_stock','supplier_operational','simulation','backtest','pattern','company_learning','supplier_learning','event','champion','retraining'));print('CORE-D ASSERTIONS PASS',{'resolver_ms':round((a-t)/1e6,3),'policy_ms':round((b-a)/1e6,3),'combined_ms':round((b-t)/1e6,3),'confidence':r.confidence},flush=True)
def cleanup():
 d=json.loads(M.read_text());t=perf_counter_ns();d2._cleanup([{'company_id':d['company_id'],'user_id':d['user_id'],'dataset_id':d['dataset_id']}],[]);M.unlink();print('CORE-D CLEANUP PASS',round((perf_counter_ns()-t)/1e6,3),flush=True)
if __name__=='__main__':{'setup':setup,'assert':assertion,'cleanup':cleanup}[sys.argv[1]]()
