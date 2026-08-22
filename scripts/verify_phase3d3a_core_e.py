"""Three-process persisted determinism/fresh-session proof."""
from pathlib import Path
import json,sys
from time import perf_counter_ns
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.verify_phase3d3a_decision_policy_postgres import build
from scripts import verify_phase3d2_decision_evidence_matrix as d2
from app.application.decision_evidence_resolver import DecisionEvidenceResolver
from app.application.decision_policy import DecisionPolicy
from app.database import SessionLocal
from app.models.forecast_vintage import ForecastVintage
M=Path(__file__).resolve().parent/'.phase3d3a_core_e_fixture.json'
def setup():
 t=perf_counter_ns();ids=build('core_e',safety=False,company_learning=False);s=SessionLocal()
 try:
  v=s.query(ForecastVintage).filter_by(company_id=ids['company_id']).one();d={**{k:str(x) for k,x in ids.items()},'material_code':'SKU','demand_type':'sales','decision_cutoff_period':'2026-W20','decision_context':'FORECAST_REVIEW','forecast_vintage_id':str(v.id),'forecast_result_reference_id':str(v.runtime_result_reference_id),'runtime_execution_id':str(v.execution_id)};M.write_text(json.dumps(d));print('CORE-E SETUP PASS',round((perf_counter_ns()-t)/1e6,3),flush=True)
 finally:s.close()
def run(d):
 t=perf_counter_ns();e=DecisionEvidenceResolver().resolve(d['company_id'],d['material_code'],d['demand_type'],d['decision_cutoff_period'],d['decision_context']);a=perf_counter_ns();p=DecisionPolicy().evaluate(e);b=perf_counter_ns();return e,p,round((a-t)/1e6,3),round((b-a)/1e6,3),round((b-t)/1e6,3)
def assertion():
 d=json.loads(M.read_text());e1,p1,*t1=run(d);e2,p2,*t2=run(d);assert e1==e2 and p1==p2;print('CORE-E ASSERTIONS PASS',{'r1_ms':t1,'r2_ms':t2,'envelope':e1.fingerprint,'policy':p1.fingerprint,'candidates':[x.candidate_type for x in p1.candidates]},flush=True)
def cleanup():
 d=json.loads(M.read_text());t=perf_counter_ns();d2._cleanup([{'company_id':d['company_id'],'user_id':d['user_id'],'dataset_id':d['dataset_id']}],[]);M.unlink();print('CORE-E CLEANUP PASS',round((perf_counter_ns()-t)/1e6,3),flush=True)
if __name__=='__main__':{'setup':setup,'assert':assertion,'cleanup':cleanup}[sys.argv[1]]()
