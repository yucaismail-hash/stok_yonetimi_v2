"""Focused no-runtime dataflow contract proof."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.engine.capability_dataflow import assemble_simulation_business_input, assemble_simulation_standalone_input, selected_backtest_strategy, CapabilityDataflowError
from app.analysis.backtest import BacktestEngine
from app.engine.runtime_store import RuntimeStore, RuntimeStoreUpstreamResultError
from types import SimpleNamespace

forecast={'result':{'items':[{'material_code':'SKU_A','forecast':[10,12,14,16],'model_used':'auto','selection_info':{}}]},'provenance':{'result_reference_id':'forecast-ref','result_type':'forecast','result_version':'1.0.0','contract_version':'1.0.0','upstream_execution_id':'execution'}}
safety={'result':{'items':[{'material_code':'SKU_A','selected_method':'syntetos_boylan_ss','safety_stock':9.0,'candidate_methods':{},'effective_lead_time_used':14,'effective_unit':'days'}]},'provenance':{'result_reference_id':'safety-ref','result_type':'safety_stock','result_version':'1.0.0','contract_version':'1.0.0','upstream_execution_id':'execution'}}
def main():
    company_a='company-a'; company_b='company-b'; execution='execution-a'
    ref=SimpleNamespace(execution_id=execution,company_id=company_a,runtime_task_id='task',id='ref',result_type='forecast',result_version='1.0.0',contract_version='1.0.0',inline_result=forecast['result'])
    class Query:
        def __init__(self, value): self.value=value
        def filter_by(self, **kwargs): self.kwargs=kwargs; return self
        def one_or_none(self): return self.value if self.kwargs.get('company_id')==company_a and self.kwargs.get('validation_status')=='validated' else None
    class Session:
        def __init__(self, value): self.value=value
        def query(self, model): return Query(self.value)
    store=object.__new__(RuntimeStore); store.session=Session(ref); store.get_execution=lambda e,c: object() if (e,c)==(execution,company_a) else None
    assert store.get_validated_upstream_result(execution,'forecast',company_a)['provenance']['result_reference_id']=='ref'
    for bad_company in (company_b,):
        try: store.get_validated_upstream_result(execution,'forecast',bad_company); raise AssertionError('cross tenant accepted')
        except RuntimeStoreUpstreamResultError: pass
    store.session=Session(SimpleNamespace(**{**ref.__dict__,'result_version':'9.0.0'}))
    try: store.get_validated_upstream_result(execution,'forecast',company_a); raise AssertionError('incompatible version accepted')
    except RuntimeStoreUpstreamResultError: pass
    store.session=Session(None)
    try: store.get_validated_upstream_result(execution,'forecast',company_a); raise AssertionError('invalid/missing evidence accepted')
    except RuntimeStoreUpstreamResultError: pass
    business=assemble_simulation_business_input({'policies':{'SKU_A':{'initial_stock':30,'eoq':20}}},{'forecast':forecast,'safety_stock':safety})
    assert business['items'][0]['forecast_source']=='upstream' and business['items'][0]['safety_stock_source']=='upstream' and business['items'][0]['demand_mean']==13
    standalone=assemble_simulation_standalone_input({'items':[{'material_code':'SKU_B','demand_history':[1,3,5],'existing_policy':{'rop':12,'safety_stock':4}}]})
    assert standalone['forecast_source']=='historical_fallback' and standalone['safety_stock_source']=='user_existing_policy'
    strategy=selected_backtest_strategy(safety); assert strategy=='syntetos_boylan'
    demand=[3,5,2,6,4,7,3,8,4,9,5,10,6,11,7,12]
    validated=BacktestEngine().run_backtest(demand,14,test_window=12,mode='VALIDATE_SELECTED',selected_strategy=strategy)
    assert validated['mode']=='VALIDATE_SELECTED' and list(validated['metrics'])==[strategy] and validated['recommendation']['best_strategy']==strategy
    compared=BacktestEngine().run_backtest(demand,14,test_window=12,strategies=['classic','hybrid'])
    assert compared['mode']=='COMPARE_CANDIDATES' and set(compared['metrics'])=={'classic','hybrid'}
    try: assemble_simulation_business_input({}, {'forecast':forecast}); raise AssertionError('missing safety evidence accepted')
    except CapabilityDataflowError: pass
    print('CAPABILITY DATAFLOW PROOF PASS',flush=True)
if __name__=='__main__': main()
