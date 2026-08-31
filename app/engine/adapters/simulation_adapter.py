"""Adapter for real Monte Carlo simulation; never invokes Forecast or Safety Stock."""
from time import perf_counter
from statistics import mean, pstdev
from app.engine.capability_executor import CapabilityInputValidationError
from app.application.event_intelligence_resolver import EventIntelligenceResolver

def simulation_adapter(implementation, prepared, request, event_resolver_factory=EventIntelligenceResolver):
    p=request.params; n=p.get('n_simulations',1000); weeks=p.get('weeks',26)
    if isinstance(n,bool) or not isinstance(n,int) or not 1<=n<=10000 or isinstance(weeks,bool) or not isinstance(weeks,int) or not 1<=weeks<=260: raise CapabilityInputValidationError('invalid simulation config')
    sim=implementation(n_simulations=n); started=perf_counter(); rows=[]; cutoff=p.get('forecast_cutoff_period'); demand=p.get('demand_type'); resolver=event_resolver_factory() if isinstance(cutoff,str) and isinstance(demand,str) else None
    for item in prepared['items']:
        initial=item['initial_stock']; eoq=item['eoq']
        if not all(isinstance(x,(int,float)) and not isinstance(x,bool) and x>=0 for x in (initial,eoq)): raise CapabilityInputValidationError(f'initial_stock and eoq are required for {item["material_code"]}')
        if item.get('forecast_source') == 'upstream' and item.get('safety_stock_source') == 'upstream':
            demand_mean=float(item['demand_mean']); demand_std=float(item['demand_std']); rop=float(item['rop']); ss=float(item['safety_stock']); lead=float(item['lead_time_days'])
            forecast_source='upstream'; safety_stock_source='upstream'; rop_source='persisted_upstream'
        else:
            history=item['demand_history']; lead=item['lead_time_days']; demand_mean=float(mean(history)); demand_std=float(pstdev(history)); ss=item['existing_safety_stock']; rop=item['existing_rop']
            if rop is None: rop=demand_mean*lead/7+(float(ss) if isinstance(ss,(int,float)) else demand_mean*.3); rop_source='derived_fallback'
            else: rop_source='existing_policy'
            forecast_source='historical_fallback'; safety_stock_source='user_existing_policy' if ss is not None else 'derived_fallback'
        lead_std=float(item.get('lead_time_std_days') if isinstance(item.get('lead_time_std_days'),(int,float)) else max(1,lead*.2))
        incoming_supply=item.get('incoming_supply') if isinstance(item.get('incoming_supply'),dict) else {}
        output=sim.simulate(float(initial),lead,lead_std,demand_mean,demand_std,float(eoq),float(rop),weeks=weeks,use_regime=bool(p.get('use_regime',False)),historical_demand=None,use_copula=bool(p.get('use_copula',False)),use_adaptive_ss=bool(p.get('use_adaptive_ss',False)),incoming_supply_schedule=incoming_supply.get('incoming_supply_schedule'))
        event_context=resolver.resolve(request.company_id,item['material_code'],demand,cutoff) if resolver else {'status':'EVENT_INTELLIGENCE_ABSENT','memories':[]}
        incoming_used=float(incoming_supply.get('incoming_supply_qty_used') or 0)
        rows.append({'material_code':item['material_code'],'service_level':output['service_level'],'stockout_probability':output['stockout_probability'],'avg_stock':output['avg_stock'],'cvar_95':output['cvar_95'],'weeks':weeks,'n_simulations':n,'regime_used':output['regime_used'],'copula_used':output['copula_used'],'adaptive_ss_used':output['adaptive_ss_used'],'initial_stock':initial,'lead_time_days':lead,'lead_time_std_days':lead_std,'eoq':eoq,'rop':rop,'incoming_supply_qty_used':incoming_used,'incoming_supply_delivery_date':incoming_supply.get('incoming_supply_delivery_date'),'incoming_supply_delivery_dates':incoming_supply.get('incoming_supply_delivery_dates',[]),'incoming_supply_status':incoming_supply.get('incoming_supply_status','OPEN_ORDER_SNAPSHOT_UNAVAILABLE'),'open_order_snapshot_state':incoming_supply.get('open_order_snapshot_state','CALCULATION_FALLBACK_ZERO'),'incoming_supply_warnings':incoming_supply.get('warnings',[]),'replenishment_horizon_days':incoming_supply.get('replenishment_horizon_days'),'net_requirement_after_incoming_supply':max(0.0, float(rop)-float(initial)-incoming_used),'forecast_source':forecast_source,'safety_stock_source':safety_stock_source,'rop_source':rop_source,'supplier_enrichment':item.get('supplier_enrichment'),'provenance':item.get('provenance'),'event_intelligence':event_context})
    return {'items':rows,'metrics':{'processed_skus':len(rows),'adapter_duration_ms':(perf_counter()-started)*1000},'warnings':[]}
