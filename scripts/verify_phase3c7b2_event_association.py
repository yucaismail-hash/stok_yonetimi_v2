"""Focused PostgreSQL proof for the read-only Event Association boundary."""
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
import json, sys, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from uuid_extensions import uuid7

from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.event_association import EventAssociationService
from app.application.event_observations import EventObservationService
from app.database import SessionLocal
from app.models.actuals import ActualWeeklyObservation, ActualWeeklyRevision
from app.models.company import Company, User, UserMaterial
from app.models.dataset import Dataset
from app.models.event_observation import EventObservation, EventRevision
from app.models.forecast_vintage import ForecastVintage, ForecastVintagePoint
from app.models.learning_evidence import LearningEvidence
from app.models.pattern_learning_memory import PatternLearningMemory
from app.models.runtime import RuntimeExecution, RuntimeResultReference
from app.models.security import CompanyEncryptionKey
from app.services.security import EncryptionService


def monday(week): return date.fromisocalendar(2026, week, 1)

def make_context():
    s=SessionLocal(); tag='event_association_'+str(uuid7())
    try:
        c=Company(id=uuid7(),name=tag,tax_id=tag);u=User(id=uuid7(),company_id=c.id,email=tag+'@x.invalid',hashed_password='x')
        s.add_all((c,u));s.flush()
        d=Dataset(id=uuid7(),company_id=c.id,user_id=u.id,uploaded_by=u.id,dataset_hash=sha256(tag.encode()).hexdigest(),source_type=tag,encrypted_data=EncryptionService(s).encrypt_dataset(u.id,{'items':[]}),is_active=True)
        s.add_all((d,UserMaterial(id=uuid7(),user_id=u.id,company_id=c.id,material_code='SKU',material_name='SKU',group='G',product_level='finished_good',product_class='C')));s.commit()
        return {'company_id':c.id,'user_id':u.id,'dataset_id':d.id}
    finally:s.close()

def ingest(root, demand, values, code='SKU'):
    rows=[{'material_code':code,'period':f'2026-W{w:02d}','quantity':v,'product_level':'finished_good','product_group':'G','product_class':'C'} for w,v in values.items()]
    return ActualWeeklyLedgerService().ingest_dataset_actuals(root['company_id'],root['user_id'],root['dataset_id'],rows,demand)

def event(root, identity, ref, week, *, demand='sales', scope='MATERIAL', value='SKU'):
    return EventObservationService().create(root['company_id'],event_identity=identity,event_type='campaign',source_occurrence_reference=ref,scope_type=scope,scope_value=None if scope=='COMPANY' else value,demand_type=demand,start_date=monday(week),end_date=monday(week)+timedelta(days=6),authority_type='COMPANY_EXPLICIT',source_system='company_event',provenance={'fixture':identity})

def vintage(root, *, available_at=datetime(2026,1,1,tzinfo=timezone.utc), target_weeks=(5,10,15,19,24)):
    s=SessionLocal()
    try:
        eid=uuid7();rid=uuid7(); s.add(RuntimeExecution(execution_id=eid,company_id=root['company_id'],user_id=root['user_id'],dataset_id=root['dataset_id'],workflow_id='event-association',analysis_type='forecast',state='completed'));s.flush()
        s.add(RuntimeResultReference(id=rid,company_id=root['company_id'],execution_id=eid,result_type='forecast',result_version='event_assoc',contract_version='1',storage_kind='inline_jsonb',inline_result={'fixture':True},validation_status='validated'));s.flush()
        v=ForecastVintage(id=uuid7(),company_id=root['company_id'],execution_id=eid,runtime_result_reference_id=rid,dataset_id=root['dataset_id'],forecast_available_at=available_at,forecast_origin_period='2026-W04',input_cutoff_period='2026-W04',demand_type='sales',result_version='event_assoc',contract_version='1');s.add(v);s.flush()
        for i,w in enumerate(target_weeks,1):s.add(ForecastVintagePoint(id=uuid7(),forecast_vintage_id=v.id,material_code='SKU',target_period=f'2026-W{w:02d}',forecast_value=100,product_level='finished_good',product_group='G',product_class='C',horizon_index=i))
        s.commit();return v.id
    finally:s.close()

def counts(cid):
    s=SessionLocal()
    try:return tuple(s.query(x).filter_by(company_id=cid).count() for x in (EventObservation,EventRevision,ActualWeeklyObservation,ActualWeeklyRevision,ForecastVintage,RuntimeExecution,LearningEvidence,PatternLearningMemory))
    finally:s.close()

def cleanup(root):
    s=SessionLocal()
    try:
        ids=[x[0] for x in s.query(RuntimeExecution.execution_id).filter_by(company_id=root['company_id']).all()];vids=[x[0] for x in s.query(ForecastVintage.id).filter_by(company_id=root['company_id']).all()]
        s.query(ForecastVintagePoint).filter(ForecastVintagePoint.forecast_vintage_id.in_(vids)).delete(synchronize_session=False);s.query(ForecastVintage).filter_by(company_id=root['company_id']).delete(synchronize_session=False);s.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(ids)).delete(synchronize_session=False)
        s.query(EventRevision).filter_by(company_id=root['company_id']).delete(synchronize_session=False);s.query(EventObservation).filter_by(company_id=root['company_id']).delete(synchronize_session=False);s.query(ActualWeeklyRevision).filter_by(company_id=root['company_id']).delete(synchronize_session=False);s.query(ActualWeeklyObservation).filter_by(company_id=root['company_id']).delete(synchronize_session=False);s.query(UserMaterial).filter_by(company_id=root['company_id']).delete(synchronize_session=False);s.query(Dataset).filter_by(id=root['dataset_id']).delete(synchronize_session=False);s.query(CompanyEncryptionKey).filter_by(user_id=root['user_id']).delete(synchronize_session=False);s.query(User).filter_by(id=root['user_id']).delete(synchronize_session=False);s.query(Company).filter_by(id=root['company_id']).delete(synchronize_session=False);s.commit();assert s.query(Company).filter_by(id=root['company_id']).count()==0
    finally:s.close()

def main():
    root=make_context()
    try:
        values={w:100 for w in range(1,31)}
        values.update({5:130,10:130,6:70,11:70,7:101,12:99,8:130,13:70,18:130,23:130,19:130,24:130,20:130})
        ingest(root,'sales',values); ingest(root,'consumption',{w:40 for w in range(1,31)})
        ids={}
        for ident,weeks in {'POS':(5,10),'NEG':(6,11),'CLEAR':(7,12),'MIX':(8,13),'FALLBACK':(18,23),'ONE':(20,),'FORECAST':(19,24)}.items():
            ids[ident]=[event(root,ident,f'{ident}-{w}',w).event_id for w in weeks]
        # All explicit scope types resolve only through canonical material metadata.
        ids['GROUP']=[event(root,'GROUP','GROUP-15',15,scope='PRODUCT_GROUP',value='G').event_id]
        ids['CLASS']=[event(root,'CLASS','CLASS-16',16,scope='PRODUCT_CLASS',value='C').event_id]
        ids['COMPANY']=[event(root,'COMPANY','COMPANY-17',17,scope='COMPANY',value=None).event_id]
        ids['CONSUMPTION']=[event(root,'POS','CONSUMPTION-5',5,demand='consumption').event_id]
        vid=vintage(root); as_of=datetime.now(timezone.utc); svc=EventAssociationService()
        positive=svc.calculate(root['company_id'],'SKU','sales','POS','2026-W25',as_of=as_of);negative=svc.calculate(root['company_id'],'SKU','sales','NEG','2026-W25',as_of=as_of);clear=svc.calculate(root['company_id'],'SKU','sales','CLEAR','2026-W25',as_of=as_of);mixed=svc.calculate(root['company_id'],'SKU','sales','MIX','2026-W25',as_of=as_of);one=svc.calculate(root['company_id'],'SKU','sales','ONE','2026-W25',as_of=as_of);forecast=svc.calculate(root['company_id'],'SKU','sales','FORECAST','2026-W25',as_of=as_of)
        assert positive.classification=='POSITIVE_ASSOCIATION' and negative.classification=='NEGATIVE_ASSOCIATION' and clear.classification=='NO_CLEAR_EFFECT' and mixed.classification=='INCONSISTENT_EFFECT' and one.classification=='INSUFFICIENT_EVIDENCE'
        fallback=svc.calculate(root['company_id'],'SKU','sales','FALLBACK','2026-W25',as_of=as_of)
        assert forecast.baseline_method=='forecast_vintage' and str(vid) in forecast.baseline_source_vintage_ids and fallback.baseline_method=='historical_pre_event' and len(fallback.baseline_source_periods)>=3 and positive.pre_event_mean is not None and positive.post_event_mean is not None and positive.strongest_lag_weeks in {1,2}
        assert all(svc.calculate(root['company_id'],'SKU','sales',x,'2026-W25',as_of=as_of).occurrence_count==1 for x in ('GROUP','CLASS','COMPANY'))
        group_before=svc.calculate(root['company_id'],'SKU','sales','GROUP','2026-W25',as_of=as_of);scope_change=EventObservationService().propose_correction(root['company_id'],ids['GROUP'][0],root['user_id'],scope_value='OTHER');EventObservationService().accept_correction(root['company_id'],scope_change.revision_id,root['user_id']);assert EventAssociationService().calculate(root['company_id'],'SKU','sales','GROUP','2026-W25',as_of=datetime.now(timezone.utc)).occurrence_count==0 and group_before.occurrence_count==1
        consumption=svc.calculate(root['company_id'],'SKU','consumption','POS','2026-W25',as_of=as_of);assert consumption.demand_type=='consumption' and consumption.event_actual_mean==40.0
        # Same-cutoff leakage: later actual/event/vintage state cannot affect earlier as-of output.
        before=positive; time.sleep(.02); ingest(root,'sales',{26:999});event(root,'POS','POS-FUTURE',26);vintage(root,available_at=datetime(2026,7,1,tzinfo=timezone.utc));assert svc.calculate(root['company_id'],'SKU','sales','POS','2026-W25',as_of=as_of)==before
        # Accepted vs rejected actual corrections are visible only after acceptance/as-of.
        time.sleep(.02); change=ingest(root,'sales',{5:150});ActualWeeklyLedgerService().approve_revision(root['company_id'],change['revision_ids'][0],root['user_id']);after_actual=svc.calculate(root['company_id'],'SKU','sales','POS','2026-W25',as_of=datetime.now(timezone.utc));assert after_actual.source_fingerprint!=before.source_fingerprint and after_actual.event_actual_mean>before.event_actual_mean
        reject=ingest(root,'sales',{10:999});ActualWeeklyLedgerService().reject_revision(root['company_id'],reject['revision_ids'][0],root['user_id']);after_reject=svc.calculate(root['company_id'],'SKU','sales','POS','2026-W25',as_of=datetime.now(timezone.utc));assert (after_reject.source_fingerprint,after_reject.event_actual_mean,after_reject.baseline_mean,after_reject.classification)==(after_actual.source_fingerprint,after_actual.event_actual_mean,after_actual.baseline_mean,after_actual.classification)
        # Event correction is temporal; rejected proposal is a no-op; cancellation preserves old as-of truth.
        ev=EventObservationService();time.sleep(.02);p=ev.propose_correction(root['company_id'],ids['NEG'][0],root['user_id'],event_type='campaign_v2');ev.accept_correction(root['company_id'],p.revision_id,root['user_id']);corrected=svc.calculate(root['company_id'],'SKU','sales','NEG','2026-W25',as_of=datetime.now(timezone.utc));assert corrected.source_fingerprint!=negative.source_fingerprint
        r=ev.propose_correction(root['company_id'],ids['NEG'][1],root['user_id'],event_type='other');ev.reject_correction(root['company_id'],r.revision_id,root['user_id']);after_event_reject=svc.calculate(root['company_id'],'SKU','sales','NEG','2026-W25',as_of=datetime.now(timezone.utc));assert (after_event_reject.source_fingerprint,after_event_reject.classification,after_event_reject.event_actual_mean)==(corrected.source_fingerprint,corrected.classification,corrected.event_actual_mean)
        prior=svc.calculate(root['company_id'],'SKU','sales','ONE','2026-W25',as_of=datetime.now(timezone.utc));prior_asof=prior.as_of;time.sleep(.02);ev.cancel(root['company_id'],ids['ONE'][0],root['user_id']);assert svc.calculate(root['company_id'],'SKU','sales','ONE','2026-W25',as_of=prior_asof)==prior and svc.calculate(root['company_id'],'SKU','sales','ONE','2026-W25',as_of=datetime.now(timezone.utc)).occurrence_count==0
        # Explicit overlap means no ungrounded attribution.
        event(root,'OVERLAP','OVERLAP-5',5);overlap=svc.calculate(root['company_id'],'SKU','sales','POS','2026-W25',as_of=datetime.now(timezone.utc));assert overlap.overlap_confounded and overlap.classification=='INSUFFICIENT_EVIDENCE'
        read_before=counts(root['company_id']);fresh=EventAssociationService().calculate(root['company_id'],'SKU','sales','MIX','2026-W25',as_of=datetime.now(timezone.utc));again=EventAssociationService().calculate(root['company_id'],'SKU','sales','MIX','2026-W25',as_of=fresh.as_of);assert fresh==again and counts(root['company_id'])==read_before
        print('PHASE 3C7B2 PROBE PASS',json.dumps({'positive':positive.classification,'negative':negative.classification,'clear':clear.classification,'mixed':mixed.classification,'forecast_baseline':forecast.baseline_method,'read_only':True}),flush=True)
    finally: cleanup(root)

if __name__=='__main__': main()
