from datetime import datetime,timedelta
from app.engine.capability_executor import CapabilityInputValidationError
def supplier_adapter(implementation,prepared,request):
 analyzer=implementation(); rows=[]
 for material,mapping in prepared['supplier_mapping'].items():
  entries=mapping if isinstance(mapping,list) else [mapping]
  if not entries or any(not isinstance(entry,dict) or entry.get('supplier_id') not in prepared['suppliers'] for entry in entries): raise CapabilityInputValidationError(f'unknown supplier mapping for {material}')
 for sid,info in prepared['suppliers'].items():
  if not isinstance(info,dict): raise CapabilityInputValidationError('invalid supplier evidence')
  for record in info.get('delivery_records',[]):
   analyzer.add_delivery_record(str(sid),datetime.now()-timedelta(days=record.get('planned_days_ago',10)),datetime.now()-timedelta(days=record.get('actual_days_ago',8)),record.get('planned_qty',1),record.get('actual_qty',1),record.get('defects',0))
  dist=analyzer.get_supplier_lead_time_distribution(str(sid)); linked=[{'material_code':m,'share':entry.get('share')} for m,x in prepared['supplier_mapping'].items() for entry in (x if isinstance(x,list) else [x]) if isinstance(entry,dict) and entry.get('supplier_id')==sid]
  rows.append({'supplier_id':sid,'name':info.get('name',sid),'risk_score':float(dist['risk_score']),'performance_score':float(dist['perf_score']),'lead_time_mean':float(dist['mean']),'lead_time_std':float(dist['std']),'supplier_factor':float(dist['supplier_factor']),'material_mappings':linked})
 return {'suppliers':rows,'mapping_count':sum(len(x['material_mappings']) for x in rows),'provenance':{'dataset_id':prepared['dataset_id']}}
