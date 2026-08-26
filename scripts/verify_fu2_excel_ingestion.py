"""Bounded PostgreSQL FU2 probe using the exact downloadable template shape."""
from pathlib import Path
import sys
from uuid import uuid4
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.canonical_excel_ingestion import CanonicalExcelIngestionService, template_bytes
from app.auth import RegisterRequest, register
from app.database import SessionLocal
from app.models import ActualWeeklyObservation, ActualWeeklyRevision, Company, Dataset, DatasetEvent, DatasetValidationResult, DatasetVersion, User
from app.models.security import CompanyEncryptionKey
from openpyxl import load_workbook
import io
from time import perf_counter
import os

PREFIX='FU2-'
def owner(tag):
 s=SessionLocal(); key=uuid4().hex
 try:
  data=register(RegisterRequest(email=f'{tag}-{key}@example.test',password='pilot-password-1',full_name='Pilot',company_name=f'{PREFIX}{tag}-{key}'),db=s); return data
 finally:s.close()
def cleanup():
 s=SessionLocal()
 try:
  ids=[x.id for x in s.query(Company).filter(Company.name.like(f'{PREFIX}%')).all()]
  if ids:
   ds=[x.id for x in s.query(Dataset).filter(Dataset.company_id.in_(ids)).all()]
   s.query(ActualWeeklyRevision).filter(ActualWeeklyRevision.company_id.in_(ids)).delete(synchronize_session=False);s.query(ActualWeeklyObservation).filter(ActualWeeklyObservation.company_id.in_(ids)).delete(synchronize_session=False)
   if ds:
    s.query(DatasetEvent).filter(DatasetEvent.dataset_id.in_(ds)).delete(synchronize_session=False);s.query(DatasetValidationResult).filter(DatasetValidationResult.dataset_id.in_(ds)).delete(synchronize_session=False);s.query(DatasetVersion).filter(DatasetVersion.dataset_id.in_(ds)).delete(synchronize_session=False);s.query(Dataset).filter(Dataset.id.in_(ds)).delete(synchronize_session=False)
   s.query(CompanyEncryptionKey).filter(CompanyEncryptionKey.company_id.in_(ids)).delete(synchronize_session=False);s.query(User).filter(User.company_id.in_(ids)).delete(synchronize_session=False);s.query(Company).filter(Company.id.in_(ids)).delete(synchronize_session=False)
  s.commit()
 finally:s.close()
def main():
 cleanup(); a=owner('a');b=owner('b')
 try:
  content=template_bytes(); wb=load_workbook(io.BytesIO(content)); ws=wb['Talep_Gecmisi']
  for week in range(3,13):ws.append(['SKU-FU2','sales','finished_good',f'2026-W{week:02d}',100+week,'G','C'])
  out=io.BytesIO();wb.save(out);content=out.getvalue(); service=CanonicalExcelIngestionService(); print('FU2-A template/parse ready',flush=True)
  started=perf_counter();s=SessionLocal(); d,retry=service.stage(s,a['company_id'],a['user_id'],'pilot.xlsx',content); did=d.id;assert not retry and d.state.value=='validated';print(f'FU2-B staged dataset_id={did} seconds={perf_counter()-started:.3f}',flush=True);s.close()
  s=SessionLocal(); assert s.query(ActualWeeklyObservation).filter_by(company_id=a['company_id']).count()==0; assert s.query(DatasetVersion).filter_by(dataset_id=did).count()==0; print('FU2-B no Actual/no version PASS',flush=True);s.close()
  started=perf_counter();s=SessionLocal(); accepted=service.accept(s,a['company_id'],a['user_id'],did);assert accepted['status']=='READY_FOR_WORKFLOW';print(f'FU2-C accepted version_id={accepted["version_id"]} seconds={perf_counter()-started:.3f}',flush=True);s.close()
  s=SessionLocal(); assert s.query(ActualWeeklyObservation).filter_by(company_id=a['company_id'],material_code='SKU-FU2',demand_type='sales').count()==10; assert s.query(ActualWeeklyObservation).filter_by(company_id=a['company_id']).count()==12; assert s.query(DatasetVersion).filter_by(dataset_id=did).count()==1;s.close()
  if os.getenv('FU2_CORE_ONLY') == '1':
   print('FU2-B/C PASS staged and accepted data reconstructed; cleanup follows', flush=True)
   return
  s=SessionLocal(); same,retry=service.stage(s,a['company_id'],a['user_id'],'pilot.xlsx',content);assert retry and same.id==did; assert service.accept(s,a['company_id'],a['user_id'],did)['idempotent'];s.close()
  s=SessionLocal(); other,_=service.stage(s,b['company_id'],b['user_id'],'pilot.xlsx',content);assert other.company_id!=a['company_id'];s.close()
  print('FU2 PASS template -> stage -> accept -> fresh ledger reconstruction; same-file idempotency and tenant isolation PASS')
 finally:cleanup()
if __name__=='__main__':main()
