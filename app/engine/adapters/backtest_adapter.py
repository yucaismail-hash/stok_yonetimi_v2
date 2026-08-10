"""Adapter for the real rolling Safety Stock BacktestEngine."""
from app.engine.capability_executor import CapabilityInputValidationError
from app.engine.capability_dataflow import selected_backtest_strategy, CapabilityDataflowError
def backtest_adapter(implementation, prepared, request):
 p=request.params; mode=p.get('mode','COMPARE_CANDIDATES'); window=p.get('test_window',12)
 if isinstance(window,bool) or not isinstance(window,int) or window<1: raise CapabilityInputValidationError('invalid test_window')
 strategies=p.get('strategies')
 if mode=='VALIDATE_SELECTED':
  try: strategy=selected_backtest_strategy(request.upstream_results['safety_stock'])
  except (KeyError,CapabilityDataflowError) as exc: raise CapabilityInputValidationError('valid upstream selected method is required') from exc
 elif mode!='COMPARE_CANDIDATES': raise CapabilityInputValidationError('invalid backtest mode')
 rows=[]
 for item in prepared['items']:
  r=implementation().run_backtest(item['demand_history'],int(item['lead_time_days']),test_window=window,strategies=strategies,mode=mode,selected_strategy=strategy if mode=='VALIDATE_SELECTED' else None)
  if 'error' in r: raise CapabilityInputValidationError(r['error'])
  rows.append({'material_code':item['material_code'],'backtest_mode':mode,'validated_strategy':strategy if mode=='VALIDATE_SELECTED' else None,'strategies_tested':list(r['metrics']),'metrics':r['metrics'],'comparison':r['comparison'],'recommendation':r['recommendation'],'test_window':window,'provenance':request.upstream_results.get('safety_stock',{}).get('provenance')})
 return {'items':rows,'warnings':[]}
