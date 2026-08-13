"""Pure capability input assembly for validated Business Workflow evidence."""
from statistics import mean, pstdev
from math import sqrt
from app.engine.runtime_store import RuntimeStoreUpstreamResultError

class CapabilityDataflowError(ValueError): pass

def resolve_business_upstream(store, execution_id, company_id, required=('forecast','safety_stock')):
    resolved={}
    for result_type in required:
        resolved[result_type]=store.get_validated_upstream_result(execution_id,result_type,company_id)
    return resolved

def _items(result):
    values=result.get('items',[]) if isinstance(result,dict) else []
    return {item.get('material_code'):item for item in values if isinstance(item,dict) and isinstance(item.get('material_code'),str)}

def supplier_lead_time_evidence(supplier, material_code):
    """Derive only truthful mapped lead-time evidence from a persisted Supplier result."""
    if not isinstance(supplier,dict) or not isinstance(supplier.get('result'),dict): return {'status':'unavailable','lead_time_source':'dataset_manual','supplier_result_reference_ids':[]}
    matches=[]
    for item in supplier['result'].get('suppliers',[]):
        if not isinstance(item,dict): continue
        for mapping in item.get('material_mappings',[]):
            if isinstance(mapping,dict) and mapping.get('material_code')==material_code:
                share=mapping.get('share'); mean_days=item.get('lead_time_mean'); std_days=item.get('lead_time_std')
                if isinstance(mean_days,(int,float)) and mean_days>0 and isinstance(std_days,(int,float)) and std_days>=0: matches.append((item.get('supplier_id'),share,float(mean_days),float(std_days)))
    ref=[supplier.get('provenance',{}).get('result_reference_id')]
    ref=[value for value in ref if value]
    if len(matches)==1:
        sid,_,avg,std=matches[0]; return {'status':'used','lead_time_source':'supplier_single','lead_time_mean_days':avg,'lead_time_std_days':std,'supplier_ids':[sid],'supplier_result_reference_ids':ref}
    if len(matches)>1 and all(isinstance(row[1],(int,float)) and not isinstance(row[1],bool) and row[1]>0 for row in matches):
        total=sum(row[1] for row in matches); weights=[row[1]/total for row in matches]; avg=sum(weight*row[2] for weight,row in zip(weights,matches)); std=sqrt(sum(weight*(row[3]**2+(row[2]-avg)**2) for weight,row in zip(weights,matches)))
        return {'status':'used','lead_time_source':'supplier_weighted','lead_time_mean_days':avg,'lead_time_std_days':std,'supplier_ids':[row[0] for row in matches],'supplier_result_reference_ids':ref}
    return {'status':'insufficient','lead_time_source':'dataset_manual','supplier_result_reference_ids':ref}

def attach_supplier_learning_context(operational_evidence, resolution):
    """Metadata-only B5 enrichment; it must never affect operational lead time."""
    result = dict(operational_evidence)
    result['supplier_learning'] = resolution.evidence if resolution and resolution.status == 'AVAILABLE' else {
        'supplier_learning_available': False, 'status': resolution.status if resolution else 'NO_LEARNED_SUPPLIER_EVIDENCE'}
    return result

def supplier_learning_context_for_scope(resolver, company_id, supplier_id, material_code, *, cutoff_date=None):
    """Explicit canonical-scope helper for optional Supplier/Safety Stock explainability.

    Callers retain responsibility for establishing the canonical supplier UUID;
    dataset supplier labels are not silently treated as that authority.
    """
    return resolver.resolve(company_id, supplier_id, material_code, cutoff_date=cutoff_date)

def assemble_safety_stock_business_input(primary_input, supplier):
    rows=[]
    for item in primary_input.get('items',[]):
        evidence=supplier_lead_time_evidence(supplier,item['material_code'])
        lead=max(1, int(round(evidence.get('lead_time_mean_days',item['lead_time_days']))))
        rows.append({**item,'lead_time_days':lead,'supplier_enrichment':evidence})
    return {'items':rows,'warnings':[]}

def assemble_simulation_business_input(primary_input, upstream_results):
    """Use validated Forecast + Safety Stock evidence; does not invoke analytical engines."""
    if not isinstance(primary_input,dict) or not isinstance(upstream_results,dict): raise CapabilityDataflowError('inputs must be mappings')
    forecast=upstream_results.get('forecast'); safety=upstream_results.get('safety_stock')
    if not isinstance(forecast,dict) or not isinstance(safety,dict): raise CapabilityDataflowError('business simulation requires forecast and safety_stock upstream evidence')
    forecast_items=_items(forecast['result']); safety_items=_items(safety['result']); rows=[]
    for code,fc in forecast_items.items():
        ss=safety_items.get(code)
        if not ss: raise CapabilityDataflowError(f'missing upstream safety stock for {code}')
        values=fc.get('forecast',[])
        if not isinstance(values,list) or not values or not all(isinstance(v,(int,float)) and not isinstance(v,bool) for v in values): raise CapabilityDataflowError(f'invalid upstream forecast for {code}')
        demand_mean=float(mean(values)); demand_std=float(pstdev(values))
        policy=primary_input.get('policies',{}).get(code,{})
        supplier=upstream_results.get('supplier'); evidence=supplier_lead_time_evidence(supplier,code) if supplier else {'status':'unavailable','lead_time_source':'dataset_manual','supplier_result_reference_ids':[]}
        lead=float(evidence.get('lead_time_mean_days',ss['effective_lead_time_used']))
        rows.append({'material_code':code,'demand_mean':demand_mean,'demand_std':demand_std,'rop':float(ss['safety_stock']) + demand_mean * lead / 7,'safety_stock':ss['safety_stock'],'lead_time_days':lead,'lead_time_std_days':evidence.get('lead_time_std_days'),'initial_stock':policy.get('initial_stock'),'eoq':policy.get('eoq'),'forecast_source':'upstream','safety_stock_source':'upstream','supplier_enrichment':evidence,'provenance':{'forecast':forecast['provenance'],'safety_stock':safety['provenance'],'supplier':supplier.get('provenance') if supplier else None}})
    return {'items':rows,'forecast_source':'upstream','safety_stock_source':'upstream'}

def assemble_simulation_standalone_input(primary_input):
    """Approved fallback only; no hidden Forecast or Safety Stock capability execution."""
    items=[]
    for item in primary_input.get('items',[]):
        history=item.get('demand_history',[])
        if not isinstance(history,list) or not history: raise CapabilityDataflowError('historical demand is required for standalone fallback')
        policy=item.get('existing_policy',{})
        if not isinstance(policy,dict) or policy.get('rop') is None: raise CapabilityDataflowError('existing policy ROP is required for standalone simulation')
        items.append({'material_code':item.get('material_code'),'demand_mean':float(mean(history)),'demand_std':float(pstdev(history)),'rop':policy['rop'],'safety_stock':policy.get('safety_stock'),'forecast_source':'historical_fallback','safety_stock_source':'user_existing_policy'})
    return {'items':items,'forecast_source':'historical_fallback','safety_stock_source':'user_existing_policy'}

def selected_backtest_strategy(safety_stock_upstream):
    item=(safety_stock_upstream['result'].get('items') or [{}])[0]; selected=item.get('selected_method')
    mapping={'classic_ss':'classic','croston_ss':'croston','syntetos_boylan_ss':'syntetos_boylan','ml_ss':'ml','hybrid_ss':'hybrid'}
    if selected not in mapping: raise CapabilityDataflowError('upstream selected Safety Stock method is unsupported for backtest')
    return mapping[selected]
