"""Development-only, resumable PostgreSQL durable-runtime verification probe."""
import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from uuid_extensions import uuid7
from app.database import SessionLocal
from app.engine.runtime_store import RuntimeStore, RuntimeStoreError, RuntimeStoreConcurrencyError, RuntimeStoreLeaseError
from app.models.company import Company, User
from app.models.dataset import Dataset
from app.models.runtime import RuntimeCheckpoint, RuntimeExecution, RuntimeResultReference, RuntimeTask, RuntimeTaskAttempt

MODELS = (Company, User, Dataset, RuntimeExecution, RuntimeTask, RuntimeTaskAttempt, RuntimeCheckpoint, RuntimeResultReference)

def say(value): print(value, flush=True)
def counts(session): return {model.__tablename__: session.query(model).count() for model in MODELS}
def graph(session, probe):
    company = session.query(Company).filter_by(tax_id=probe + "_tax").one_or_none()
    if not company: raise ValueError("synthetic probe graph not found")
    execution = session.query(RuntimeExecution).filter_by(company_id=company.id, workflow_id=probe + "_workflow").one()
    return company, execution
def cleanup_graph(session, company, execution):
    for model in (RuntimeResultReference, RuntimeCheckpoint, RuntimeTaskAttempt, RuntimeTask, RuntimeExecution):
        session.query(model).filter_by(execution_id=execution.execution_id).delete(synchronize_session=False)
    dataset = session.query(Dataset).filter_by(company_id=company.id, source_type=company.tax_id[:-4]).one_or_none()
    if dataset: session.query(Dataset).filter_by(id=dataset.id).delete(synchronize_session=False)
    session.query(User).filter_by(company_id=company.id).delete(synchronize_session=False)
    session.query(Company).filter_by(id=company.id).delete(synchronize_session=False)
def stale(args):
    say("CLEANUP-STALE START"); session=SessionLocal()
    try:
        companies=session.query(Company).filter(Company.tax_id.like("phase2c_runtime_probe_%")).all()
        for company in companies:
            execution=session.query(RuntimeExecution).filter_by(company_id=company.id, workflow_id=company.tax_id[:-4] + "_workflow").one_or_none()
            if not execution: raise ValueError("unproven synthetic company graph")
            cleanup_graph(session, company, execution)
        session.commit(); say("CLEANUP-STALE PASS"); say("BASELINE=" + str(counts(session)))
    finally: session.close()
def setup(args):
    probe=args.probe_id or "phase2c_runtime_probe_" + str(uuid7()).replace("-", "")
    say("SETUP START"); session=SessionLocal()
    try:
        c=Company(id=uuid7(), name=probe+"_company", tax_id=probe+"_tax")
        u=User(id=uuid7(), company_id=c.id, email=probe+"@example.invalid", hashed_password="probe")
        d=Dataset(id=uuid7(), company_id=c.id, user_id=u.id, uploaded_by=u.id, dataset_hash=(str(uuid7())+str(uuid7())).replace("-", "")[:64], source_type=probe)
        session.add_all((c,u,d)); session.flush()
        e=RuntimeExecution(execution_id=uuid7(),company_id=c.id,user_id=u.id,dataset_id=d.id,workflow_id=probe+"_workflow",analysis_type="forecast",state="running")
        RuntimeStore(session).create_execution(e,[{"workflow_id":e.workflow_id,"task_id":"forecast","capability":"forecast","task_order":0,"required":True,"skippable":False,"max_attempts":3},{"workflow_id":e.workflow_id,"task_id":"simulation","capability":"simulation","task_order":1,"required":True,"skippable":False,"max_attempts":2}])
        session.commit(); say("PROBE_ID="+probe); say("SETUP PASS")
    finally: session.close()
def recovery(args):
    say("RECOVERY START"); session=SessionLocal()
    try:
        c,e=graph(session,args.probe_id); store=RuntimeStore(session); assert store.get_execution(e.execution_id,c.id); assert store.get_tasks(e.execution_id,c.id); assert store.get_execution_status(e.execution_id,c.id); say("RECOVERY PASS")
    finally: session.close()
def claim(args):
    say("CLAIM START"); session=SessionLocal()
    try:
        c,e=graph(session,args.probe_id); store=RuntimeStore(session); task=store.get_tasks(e.execution_id,c.id)[0]; claimed,_=store.claim_task(e.execution_id,task.task_id,c.id,"worker_a",30,task.row_version)
        try: store.claim_task(e.execution_id,task.task_id,c.id,"worker_b",30,claimed.row_version); raise AssertionError("duplicate claim")
        except RuntimeStoreConcurrencyError: pass
        session.commit(); say("CLAIM PASS"); say("DUPLICATE CLAIM PASS")
    finally: session.close()
def reclaim(args):
    say("RECLAIM START"); session=SessionLocal()
    try:
        c,e=graph(session,args.probe_id); store=RuntimeStore(session); task=store.get_tasks(e.execution_id,c.id)[0]; old_token=task.lease_token; old_attempt=task.current_attempt; old_version=task.row_version; task_id=task.id; task.lease_expires_at=datetime.now(timezone.utc)-timedelta(seconds=1); session.commit(); session.refresh(task); claimed,_=store.claim_task(e.execution_id,task.task_id,c.id,"worker_b",30,task.row_version); session.flush(); session.expire_all(); persisted=session.query(RuntimeTask).filter_by(id=task_id, execution_id=e.execution_id, company_id=c.id).one(); attempts=session.query(RuntimeTaskAttempt).filter_by(runtime_task_id=task_id).order_by(RuntimeTaskAttempt.attempt_number).all(); active=[attempt for attempt in attempts if attempt.state=='running']; previous=[attempt for attempt in attempts if attempt.attempt_number < persisted.current_attempt]; assert persisted.task_id=='forecast' and persisted.state=='running' and persisted.assigned_worker_id=='worker_b' and persisted.lease_token != old_token and persisted.lease_expires_at>datetime.now(timezone.utc) and persisted.heartbeat_at and persisted.current_attempt==old_attempt+1 and persisted.row_version==old_version+1 and claimed.id==persisted.id and claimed.lease_token==persisted.lease_token and len(active)==1 and active[0].attempt_number==persisted.current_attempt and all(attempt.state=='failed' and attempt.retryable and attempt.error=={'code':'LEASE_EXPIRED'} for attempt in previous); session.commit(); say("RECLAIM PASS")
    finally: session.close()
def heartbeat(args):
    say("HEARTBEAT START"); session=SessionLocal()
    try:
        c,e=graph(session,args.probe_id); store=RuntimeStore(session); task=store.get_tasks(e.execution_id,c.id)[0]; token=task.lease_token; task_id=task.id; prior_heartbeat=task.heartbeat_at; prior_version=task.row_version; prior_attempt=task.current_attempt; prior_attempts=session.query(RuntimeTaskAttempt).filter_by(runtime_task_id=task_id).count(); prior_results=session.query(RuntimeResultReference).filter_by(runtime_task_id=task_id).count(); assert task.task_id=='forecast' and task.state=='running' and task.assigned_worker_id=='worker_b' and token and task.lease_expires_at>datetime.now(timezone.utc) and e.state not in ('completed','failed','cancelled'); store.heartbeat_task(e.execution_id,task.task_id,c.id,token,30); session.flush(); session.expire_all(); persisted=session.query(RuntimeTask).filter_by(id=task_id,execution_id=e.execution_id,company_id=c.id).one(); assert persisted.lease_token==token and persisted.state=='running' and persisted.assigned_worker_id=='worker_b' and persisted.current_attempt==prior_attempt and persisted.heartbeat_at>=prior_heartbeat and persisted.lease_expires_at>datetime.now(timezone.utc) and persisted.row_version==prior_version+1 and session.query(RuntimeTaskAttempt).filter_by(runtime_task_id=task_id).count()==prior_attempts and session.query(RuntimeResultReference).filter_by(runtime_task_id=task_id).count()==prior_results
        rejected_version=persisted.row_version; rejected_heartbeat=persisted.heartbeat_at
        try: store.heartbeat_task(e.execution_id,persisted.task_id,c.id,uuid7(),30); raise AssertionError("wrong token")
        except RuntimeStoreLeaseError: pass
        session.expire_all(); unchanged=session.query(RuntimeTask).filter_by(id=task_id).one(); assert unchanged.row_version==rejected_version and unchanged.heartbeat_at==rejected_heartbeat and unchanged.lease_token==token and unchanged.assigned_worker_id=='worker_b'
        unchanged.lease_expires_at=datetime.now(timezone.utc)-timedelta(seconds=1); session.commit()
        try: store.heartbeat_task(e.execution_id,unchanged.task_id,c.id,token,30); raise AssertionError("expired token")
        except RuntimeStoreLeaseError: pass
        session.expire_all(); expired=session.query(RuntimeTask).filter_by(id=task_id).one(); assert expired.state=='running' and expired.assigned_worker_id=='worker_b' and expired.lease_token==token and expired.current_attempt==prior_attempt and session.query(RuntimeTaskAttempt).filter_by(runtime_task_id=task_id).count()==prior_attempts and session.query(RuntimeResultReference).filter_by(runtime_task_id=task_id).count()==prior_results
        say("HEARTBEAT PASS"); say("WRONG TOKEN PASS"); say("EXPIRED LEASE PASS")
    finally: session.close()
def setup_batch2(args):
    say("SETUP-BATCH2 START"); setup(args); say("SETUP-BATCH2 PASS")
def setup_batch3(args):
    args.probe_id=args.probe_id or "phase2c_runtime_probe_" + str(uuid7()).replace('-', ''); say('SETUP-BATCH3 START'); setup(args); session=SessionLocal()
    try:
        c,e=graph(session,args.probe_id); session.add_all((RuntimeTask(execution_id=e.execution_id,company_id=c.id,workflow_id=e.workflow_id,task_id='backtest',capability='backtest',task_order=2,required=False,skippable=True,max_attempts=2),RuntimeTask(execution_id=e.execution_id,company_id=c.id,workflow_id=e.workflow_id,task_id='cancel_task',capability='forecast',task_order=3,required=False,skippable=True,max_attempts=2))); session.commit(); say('SETUP-BATCH3 PASS')
    finally: session.close()
def batch3(args):
    say('BATCH3 START'); a=SessionLocal(); c,e=graph(a,args.probe_id); stale=e.row_version; b=SessionLocal()
    try:
        cb,eb=graph(b,args.probe_id); RuntimeStore(b).transition_execution(eb.execution_id,cb.id,'running','waiting',eb.row_version); b.commit()
    finally: b.close()
    try: RuntimeStore(a).transition_execution(e.execution_id,c.id,'running','waiting',stale); raise AssertionError('stale execution')
    except RuntimeStoreConcurrencyError: a.rollback()
    finally: a.close()
    s=SessionLocal()
    try:
        c,e=graph(s,args.probe_id); store=RuntimeStore(s); store.transition_execution(e.execution_id,c.id,'waiting','running',e.row_version); s.commit()
    finally: s.close()
    a=SessionLocal(); b=SessionLocal()
    try:
        ca,ea=graph(a,args.probe_id); ta=a.query(RuntimeTask).filter_by(execution_id=ea.execution_id,task_id='forecast').one(); tb=b.query(RuntimeTask).filter_by(execution_id=ea.execution_id,task_id='forecast').one(); claimed,attempt=RuntimeStore(a).claim_task(ea.execution_id,'forecast',ca.id,'worker_a',120,ta.row_version); a.commit()
        try: RuntimeStore(b).claim_task(ea.execution_id,'forecast',ca.id,'worker_b',120,tb.row_version); raise AssertionError('stale task')
        except RuntimeStoreConcurrencyError: b.rollback()
    finally: a.close(); b.close()
    s=SessionLocal()
    try:
        c,e=graph(s,args.probe_id); store=RuntimeStore(s); sim=s.query(RuntimeTask).filter_by(execution_id=e.execution_id,task_id='simulation').one(); won,_=store.claim_task(e.execution_id,'simulation',c.id,'worker_a',120,sim.row_version); s.commit()
    finally: s.close()
    b=SessionLocal()
    try:
        c,e=graph(b,args.probe_id); sim=b.query(RuntimeTask).filter_by(execution_id=e.execution_id,task_id='simulation').one()
        try: RuntimeStore(b).claim_task(e.execution_id,'simulation',c.id,'worker_b',120,sim.row_version); raise AssertionError('competing claim')
        except RuntimeStoreConcurrencyError: b.rollback()
    finally: b.close()
    s=SessionLocal()
    try:
        c,e=graph(s,args.probe_id); store=RuntimeStore(s); tasks={t.task_id:t for t in store.get_tasks(e.execution_id,c.id)}
        for name in ('forecast','simulation','backtest'): store.register_result_reference(c.id,e.execution_id,'analysis',{'task':name},runtime_task_id=tasks[name].id)
        store.register_result_reference(c.id,e.execution_id,'bundle',{'ok':True}); s.commit()
    finally: s.close()
    dup=SessionLocal()
    try:
        c,e=graph(dup,args.probe_id); t=dup.query(RuntimeTask).filter_by(execution_id=e.execution_id,task_id='forecast').one()
        try: RuntimeStore(dup).register_result_reference(c.id,e.execution_id,'analysis',{'duplicate':True},runtime_task_id=t.id); dup.commit(); raise AssertionError('duplicate result')
        except Exception: dup.rollback()
    finally: dup.close()
    s=SessionLocal()
    try:
        c,e=graph(s,args.probe_id); store=RuntimeStore(s)
        try: store.register_result_reference(c.id,e.execution_id,'invalid',{'bad':datetime.now(timezone.utc)}); raise AssertionError('invalid result')
        except RuntimeStoreError: pass
        other=Company(id=uuid7(),name=args.probe_id+'_other',tax_id=args.probe_id+'_other_tax'); s.add(other); s.flush(); assert store.get_execution(e.execution_id,other.id) is None and store.get_execution_status(e.execution_id,other.id) is None
        try: store.claim_task(e.execution_id,'backtest',other.id,'other',120,1); raise AssertionError('tenant claim')
        except RuntimeStoreConcurrencyError: pass
        s.query(Company).filter_by(id=other.id).delete(synchronize_session=False); e=store.get_execution(e.execution_id,c.id); cancelled=store.request_cancellation(e.execution_id,c.id,e.row_version); s.flush(); assert cancelled.state=='cancelled' and cancelled.cancellation_requested
        tasks={t.task_id:t for t in store.get_tasks(e.execution_id,c.id)}
        for name in ('backtest','forecast'):
            try: store.claim_task(e.execution_id,name,c.id,'blocked',120,tasks[name].row_version); raise AssertionError('cancelled claim')
            except RuntimeStoreConcurrencyError: pass
        try: store.heartbeat_task(e.execution_id,'forecast',c.id,tasks['forecast'].lease_token,120); raise AssertionError('terminal heartbeat')
        except RuntimeStoreLeaseError: pass
        try: store.complete_task_attempt(e.execution_id,'forecast',c.id,tasks['forecast'].lease_token,'late',{'ok':True}); raise AssertionError('terminal complete')
        except RuntimeStoreLeaseError: pass
        try: store.fail_task_attempt(e.execution_id,'forecast',c.id,tasks['forecast'].lease_token,{'code':'X'},False); raise AssertionError('terminal fail')
        except RuntimeStoreLeaseError: pass
        s.commit(); say('BATCH3 PASS')
    finally: s.close()
def complete(args):
    say("COMPLETE START"); session=SessionLocal()
    try:
        c,e=graph(session,args.probe_id); store=RuntimeStore(session); task=session.query(RuntimeTask).filter_by(execution_id=e.execution_id,company_id=c.id,task_id='forecast').one(); claimed,attempt=store.claim_task(e.execution_id,'forecast',c.id,'batch2_forecast',120,task.row_version); ref=store.complete_task_attempt(e.execution_id,'forecast',c.id,claimed.lease_token,'forecast_result',{'status':'ok','value':1}); session.flush(); session.expire_all(); task=session.query(RuntimeTask).filter_by(id=claimed.id).one(); done=session.query(RuntimeTaskAttempt).filter_by(id=attempt.id).one(); persisted=session.query(RuntimeResultReference).filter_by(id=ref.id).one(); assert task.state=='completed' and task.lease_token is None and done.state=='completed' and persisted.validation_status=='validated' and persisted.storage_kind=='inline_jsonb' and float(e.progress)==50.0
        snapshot=(task.state,task.row_version,session.query(RuntimeResultReference).count())
        for token in (claimed.lease_token,uuid7()):
            try: store.complete_task_attempt(e.execution_id,'forecast',c.id,token,'forecast_result',{'status':'ok','value':1}); raise AssertionError('duplicate completion')
            except RuntimeStoreLeaseError: pass
        session.expire_all(); unchanged=session.query(RuntimeTask).filter_by(id=task.id).one(); assert (unchanged.state,unchanged.row_version,session.query(RuntimeResultReference).count())==snapshot; session.commit(); say('COMPLETE PASS')
    finally: session.close()
def failure(args):
    say('FAILURE START'); session=SessionLocal()
    try:
        c,e=graph(session,args.probe_id); store=RuntimeStore(session); task=session.query(RuntimeTask).filter_by(execution_id=e.execution_id,company_id=c.id,task_id='simulation').one(); claimed,attempt=store.claim_task(e.execution_id,'simulation',c.id,'batch2_simulation',120,task.row_version); error={'code':'CAPABILITY_EXECUTION_FAILED','message':'synthetic controlled failure','category':'operational','retryable':True,'occurred_at':datetime.now(timezone.utc).isoformat(),'details':{'probe':True}}; failed=store.fail_task_attempt(e.execution_id,'simulation',c.id,claimed.lease_token,error,True); session.flush(); assert failed.state=='pending' and failed.lease_token is None and float(e.progress)==50.0; failed_attempt=session.query(RuntimeTaskAttempt).filter_by(id=attempt.id).one(); assert failed_attempt.state=='failed' and failed_attempt.retryable and failed_attempt.error==error and session.query(RuntimeResultReference).filter_by(runtime_task_id=failed.id).count()==0; before=failed.current_attempt; retried,_=store.claim_task(e.execution_id,'simulation',c.id,'batch2_retry',120,failed.row_version); assert retried.current_attempt==before+1; session.commit(); say('FAILURE PASS'); say('RETRY BOUNDARY PASS')
    finally: session.close()
def checkpoint(args):
    say('CHECKPOINT START'); session=SessionLocal()
    try:
        c,e=graph(session,args.probe_id); store=RuntimeStore(session); forecast=session.query(RuntimeTask).filter_by(execution_id=e.execution_id,task_id='forecast').one(); simulation=session.query(RuntimeTask).filter_by(execution_id=e.execution_id,task_id='simulation').one(); refs=store.get_execution_result_references(e.execution_id,c.id); first=RuntimeCheckpoint(company_id=c.id,execution_id=e.execution_id,runtime_task_id=forecast.id,checkpoint_version=1,state='running',stage='forecast_completed',completed_task_ids=['forecast'],retry_counters={'simulation':0},result_references={'forecast':str(refs[0].id)},recovery_metadata={'probe':True}); second=RuntimeCheckpoint(company_id=c.id,execution_id=e.execution_id,runtime_task_id=simulation.id,checkpoint_version=2,state='running',stage='simulation_retry',completed_task_ids=['forecast'],retry_counters={'simulation':1},result_references={'forecast':str(refs[0].id)},recovery_metadata={'probe':True}); store.create_checkpoint(first); store.create_checkpoint(second); session.flush(); latest=store.get_latest_checkpoint(e.execution_id,c.id); assert latest.id==second.id and first.completed_task_ids==['forecast'] and latest.checkpoint_version==2 and latest.company_id==c.id; session.commit(); say('CHECKPOINT PASS')
    finally: session.close()
def progress(args):
    say('PROGRESS START'); session=SessionLocal()
    try:
        c,e=graph(session,args.probe_id); tasks=RuntimeStore(session).get_tasks(e.execution_id,c.id); required=[task for task in tasks if task.required]; forecast=[task for task in tasks if task.task_id=='forecast'][0]; simulation=[task for task in tasks if task.task_id=='simulation'][0]; assert len(required)==2 and forecast.state=='completed' and float(e.progress)==50.0 and simulation.state=='running'; say('PROGRESS PASS')
    finally: session.close()
def cleanup(args):
    say("CLEANUP START"); session=SessionLocal()
    try:
        c,e=graph(session,args.probe_id); cleanup_graph(session,c,e); session.commit(); assert not session.query(Company).filter_by(tax_id=args.probe_id+"_tax").count(); say("CLEANUP PASS")
    finally: session.close()
def main():
    parser=argparse.ArgumentParser(); sub=parser.add_subparsers(dest="command",required=True)
    for name,fn in {"cleanup-stale":stale,"setup":setup,"setup-batch2":setup_batch2,"setup-batch3":setup_batch3,"batch3":batch3,"recovery":recovery,"claim":claim,"reclaim":reclaim,"heartbeat":heartbeat,"complete":complete,"failure":failure,"checkpoint":checkpoint,"progress":progress,"cleanup":cleanup}.items():
        p=sub.add_parser(name); p.add_argument("--probe-id"); p.set_defaults(fn=fn)
    args=parser.parse_args(); args.fn(args)
if __name__=="__main__": main()
