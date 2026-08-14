"""Focused PostgreSQL proof: Event context is optional, cutoff-safe metadata only."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from types import SimpleNamespace
from app.application.event_intelligence_materialization import EventIntelligenceMaterializationService
from app.application.event_intelligence_resolver import EventIntelligenceResolver
from app.engine.adapters.forecast_adapter import forecast_adapter
from app.engine.adapters.simulation_adapter import simulation_adapter
from app.analysis.forecast import DemandForecaster
from scripts.verify_phase3c7b3_event_intelligence_memory import fixture, clean as clean_base
from scripts.verify_phase3c7b2_event_association import make_context

def main():
 roots=[]
 try:
  root=make_context(); roots.append(root); other=make_context(); roots.append(other); fixture(root); fixture(other)
  cid=root['company_id']; cutoff='2026-W25'; materializer=EventIntelligenceMaterializationService()
  for identity in ('POS','NEG','CLEAR','MIX'):
   assert materializer.materialize(cid,'SKU','sales',identity,cutoff).status in {'CREATED','UNCHANGED'}
  resolver=EventIntelligenceResolver(); context=resolver.resolve(cid,'SKU','sales',cutoff)
  assert context['status']=='EVENT_INTELLIGENCE_AVAILABLE' and [x['event_identity'] for x in context['memories']]==['CLEAR','MIX','NEG','POS']
  by={x['event_identity']:x for x in context['memories']}; assert by['POS']['classification']=='POSITIVE_ASSOCIATION'; assert by['NEG']['classification']=='NEGATIVE_ASSOCIATION'; assert by['CLEAR']['classification']=='NO_CLEAR_EFFECT'; assert by['MIX']['classification']=='INCONSISTENT_EFFECT'
  assert resolver.resolve(cid,'SKU','sales','2026-W04')['status']=='EVENT_INTELLIGENCE_CUTOFF_INCOMPATIBLE'
  assert resolver.resolve(cid,'SKU','consumption',cutoff)['status']=='EVENT_INTELLIGENCE_ABSENT'; assert resolver.resolve(other['company_id'],'SKU','sales',cutoff)['status']=='EVENT_INTELLIGENCE_ABSENT'
  req=SimpleNamespace(company_id=cid,params={'horizon':4,'model_type':'auto','demand_type':'sales','forecast_cutoff_period':cutoff})
  prepared={'items':[{'material_code':'SKU','demand_history':[100,102,101,103,100,102,101,103]}],'warnings':[]}
  enriched=forecast_adapter(DemandForecaster,prepared,req); absent=forecast_adapter(DemandForecaster,prepared,req,event_resolver_factory=lambda:SimpleNamespace(resolve=lambda *a:{'status':'EVENT_INTELLIGENCE_ABSENT','memories':[]}))
  assert enriched['items'][0]['forecast']==absent['items'][0]['forecast']; assert enriched['items'][0]['selection_info']['event_intelligence']['status']=='EVENT_INTELLIGENCE_AVAILABLE'
  simreq=SimpleNamespace(company_id=cid,params={'n_simulations':3,'weeks':2,'demand_type':'sales','forecast_cutoff_period':cutoff})
  prepared_sim={'items':[{'material_code':'SKU','demand_history':[10,12,11,13], 'lead_time_days':7,'initial_stock':50,'eoq':20,'existing_rop':30,'existing_safety_stock':5}]}
  class DeterministicSim:
   def __init__(self,**_): pass
   def simulate(self,*_args,**_kw): return {'service_level':.9,'stockout_probability':.1,'avg_stock':20,'cvar_95':5,'regime_used':False,'copula_used':False,'adaptive_ss_used':False}
  sim_enriched=simulation_adapter(DeterministicSim,prepared_sim,simreq); sim_absent=simulation_adapter(DeterministicSim,prepared_sim,simreq,event_resolver_factory=lambda:SimpleNamespace(resolve=lambda *a:{'status':'EVENT_INTELLIGENCE_ABSENT','memories':[]}))
  a,b=sim_enriched['items'][0],sim_absent['items'][0]; assert {k:v for k,v in a.items() if k!='event_intelligence'}=={k:v for k,v in b.items() if k!='event_intelligence'}; assert a['event_intelligence']['status']=='EVENT_INTELLIGENCE_AVAILABLE'
  print('PHASE 3C7B5 PROBE PASS',{'event_memories':len(context['memories']),'forecast_non_impact':True,'simulation_non_impact':True},flush=True)
 finally:
  for root in reversed(roots): clean_base(root)
if __name__=='__main__': main()
