"""Focused PostgreSQL proof for explicit, atomic Champion rollback."""
import concurrent.futures, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from uuid_extensions import uuid7
from app.application.champion_registry import ChampionRegistryService
from app.application.champion_rollback import ChampionRollbackService
from app.database import SessionLocal
from app.models.champion_registry import ChampionRegistryCurrent, ChampionRegistryEntry, ChampionRegistryTransition
from app.models.company import Company

def _entry(s,cid,code='SKU',demand='sales'):
 e=ChampionRegistryEntry(company_id=cid,material_code=code,demand_type=demand,entry_type='classical_existing',classical_strategy='demand_forecaster_auto_v1',provenance={});s.add(e);s.flush();return e.id
def main():
 s=SessionLocal();cid=None
 try:
  tag='rollback_'+str(uuid7());c=Company(id=uuid7(),name=tag,tax_id=tag);s.add(c);s.commit();cid=c.id
  a=ChampionRegistryService().bootstrap(cid,'SKU','sales','finished_good');aid=a.active_entry_id;b=_entry(s,cid);c_id=_entry(s,cid);s.commit()
  # Synthetic, immutable-known history establishes A -> B -> C before governed rollback C -> B.
  cur=s.query(ChampionRegistryCurrent).filter_by(company_id=cid,material_code='SKU',demand_type='sales').one();cur.active_entry_id=b;cur.row_version=2;s.add(ChampionRegistryTransition(company_id=cid,material_code='SKU',demand_type='sales',transition_type='PROMOTION',source_entry_id=aid,destination_entry_id=b,source_decision_id=None,expected_current_entry_id=aid,reason='fixture A to B',idempotency_fingerprint='b'+str(cid).replace('-','')));s.commit();cur.active_entry_id=c_id;cur.row_version=3;s.add(ChampionRegistryTransition(company_id=cid,material_code='SKU',demand_type='sales',transition_type='PROMOTION',source_entry_id=b,destination_entry_id=c_id,source_decision_id=None,expected_current_entry_id=b,reason='fixture B to C',idempotency_fingerprint='c'+str(cid).replace('-','')));s.commit()
  svc=ChampionRollbackService();r=svc.rollback(cid,'SKU','sales',c_id,b,'known-good B');assert r.status=='ROLLED_BACK';repeat=svc.rollback(cid,'SKU','sales',c_id,b,'known-good B');assert repeat.status=='ALREADY_ROLLED_BACK'
  s.close();s=SessionLocal();cur=s.query(ChampionRegistryCurrent).filter_by(company_id=cid,material_code='SKU',demand_type='sales').one();assert cur.active_entry_id==b and cur.row_version==4 and s.query(ChampionRegistryTransition).filter_by(company_id=cid,transition_type='ROLLBACK').count()==1
  assert svc.rollback(cid,'SKU','sales',c_id,aid,'stale').status=='STALE_CURRENT_CHAMPION'
  assert svc.rollback(cid,'SKU','sales',b,uuid7(),'unknown').status=='INVALID_DESTINATION'
  # Genuine concurrent same rollback against fresh C state.
  cur.active_entry_id=c_id;cur.row_version=5;s.commit()
  import threading
  barrier=threading.Barrier(2)
  def call(): barrier.wait();return ChampionRollbackService().rollback(cid,'SKU','sales',c_id,b,'concurrent C to B').status
  with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool: outcomes=list(pool.map(lambda _:call(),range(2)))
  s.close();s=SessionLocal();cur=s.query(ChampionRegistryCurrent).filter_by(company_id=cid,material_code='SKU',demand_type='sales').one();assert set(outcomes)=={'ROLLED_BACK','ALREADY_ROLLED_BACK'} and cur.active_entry_id==b and cur.row_version==6
  # Competing destinations race under the same PostgreSQL current-pointer lock.
  cur.active_entry_id=c_id;cur.row_version=7;s.commit();barrier=threading.Barrier(2)
  def competing(destination,reason):barrier.wait();return ChampionRollbackService().rollback(cid,'SKU','sales',c_id,destination,reason).status
  with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool: race=list(pool.map(lambda value:competing(*value),[(b,'race C to B'),(aid,'race C to A')]))
  s.close();s=SessionLocal();cur=s.query(ChampionRegistryCurrent).filter_by(company_id=cid,material_code='SKU',demand_type='sales').one();assert sorted(race)==['ROLLED_BACK','STALE_CURRENT_CHAMPION'] and cur.row_version==8 and cur.active_entry_id in (aid,b)
  history=s.query(ChampionRegistryTransition).filter_by(company_id=cid).all();assert {x.id for x in history} and {aid,b,c_id}.issubset({x.id for x in s.query(ChampionRegistryEntry).filter_by(company_id=cid).all()})
  print('PHASE3C3B3B2 ROLLBACK CORE PASS',{'idempotent':repeat.status,'same':sorted(outcomes),'competing':sorted(race),'row_version':cur.row_version,'history':len(history)})
 finally:
  if s:
   s.rollback()
   if cid:
    s.query(ChampionRegistryCurrent).filter_by(company_id=cid).delete(synchronize_session=False);s.query(ChampionRegistryTransition).filter_by(company_id=cid).delete(synchronize_session=False);s.query(ChampionRegistryEntry).filter_by(company_id=cid).delete(synchronize_session=False);s.query(Company).filter_by(id=cid).delete(synchronize_session=False);s.commit()
   s.close()
if __name__=='__main__':main()
