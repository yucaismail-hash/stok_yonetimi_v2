"""PostgreSQL proof that Supplier RuntimeResultReferences enrich downstream evidence."""
import asyncio,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.verify_phase3b1_supplier_business_branch import make,clean,run_all
from app.database import SessionLocal
from app.engine.runtime_store import RuntimeStore

H=[3,5,2,6,4,7,3,8,4,9,5,10,6,11,7,12,8,13]
def item(code='MAT',level='finished_good'): return {'sku_code':code,'product_level':level,'demand_history':H,'lead_time_days':14,'initial_stock':80,'eoq':25}
async def completed(name,payload):
 f=make(name,payload);p=await run_all(f[3],f[1]);s=SessionLocal();refs={r.result_type:r for r in RuntimeStore(s).get_execution_result_references(f[3],f[1])};s.close();return f,p,refs
async def main():
 fixtures=[]
 try:
  absent,p,refs=await completed('b2_absent',{'items':[item()]});fixtures.append(absent);ss=refs['safety_stock'].inline_result['items'][0];sim=refs['simulation'].inline_result['items'][0];assert p==[25,50,75,100] and ss['lead_time_source']=='dataset_manual' and ss['supplier_enrichment']['status']=='unavailable' and sim['supplier_enrichment']['status']=='unavailable'
  single,p,refs=await completed('b2_single',{'items':[item()], 'suppliers':{'S':{'delivery_records':[{'planned_days_ago':12,'actual_days_ago':9,'planned_qty':10,'actual_qty':10}]}},'supplier_mapping':{'MAT':{'supplier_id':'S','share':1}}});fixtures.append(single);ss=refs['safety_stock'].inline_result['items'][0];sim=refs['simulation'].inline_result['items'][0];assert p==[20,40,60,80,100] and ss['supplier_enrichment']['status']=='used' and ss['lead_time_source']=='supplier_single' and refs['supplier'].id and sim['supplier_enrichment']['lead_time_source']=='supplier_single'
  multi,p,refs=await completed('b2_multi',{'items':[item()], 'suppliers':{'A':{'delivery_records':[{'planned_days_ago':20,'actual_days_ago':18,'planned_qty':10,'actual_qty':10}]},'B':{'delivery_records':[{'planned_days_ago':20,'actual_days_ago':5,'planned_qty':10,'actual_qty':8}]}},'supplier_mapping':{'MAT':[{'supplier_id':'A','share':.75},{'supplier_id':'B','share':.25}]}});fixtures.append(multi);assert refs['safety_stock'].inline_result['items'][0]['supplier_enrichment']['lead_time_source']=='supplier_weighted'
  insufficient,p,refs=await completed('b2_insufficient',{'items':[item()], 'suppliers':{'A':{'delivery_records':[{'planned_days_ago':10,'actual_days_ago':8,'planned_qty':10,'actual_qty':10}]},'B':{'delivery_records':[{'planned_days_ago':12,'actual_days_ago':7,'planned_qty':10,'actual_qty':10}]}},'supplier_mapping':{'MAT':[{'supplier_id':'A'},{'supplier_id':'B'}]}});fixtures.append(insufficient);assert refs['safety_stock'].inline_result['items'][0]['supplier_enrichment']['status']=='insufficient'
  print('PHASE3B2 PASS',{'fallback':True,'single':'supplier_single','insufficient':True},flush=True)
 finally:
  for f in fixtures:clean(f)
if __name__=='__main__':asyncio.run(main())
