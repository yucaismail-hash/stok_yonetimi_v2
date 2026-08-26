import io,json,sys
from pathlib import Path
from time import perf_counter
from uuid import UUID,uuid4
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));from openpyxl import load_workbook
from app.application.canonical_excel_ingestion import CanonicalExcelIngestionService,template_bytes
from app.auth import RegisterRequest,register
from app.database import SessionLocal
from app.models import ActualWeeklyObservation as A,ActualWeeklyRevision as R,Dataset,DatasetVersion as V,DatasetValidationResult as VR,DatasetEvent as DE,Company,User,RuntimeExecution,ForecastVintage,DecisionSnapshot
from app.models.security import CompanyEncryptionKey
M=Path(__file__).with_suffix('.json');CODE='SKU-FU2-R2D'
def wb(n):
 w=load_workbook(io.BytesIO(template_bytes()));s=w['Talep_Gecmisi'];s.delete_rows(2,s.max_row)
 for x in range(1,n+1):s.append([CODE,'sales','finished_good',f'2026-W{x:02d}',100+x,'G','C'])
 o=io.BytesIO();w.save(o);return o.getvalue()
def d():return json.loads(M.read_text())
def setup():
 k=uuid4().hex;s=SessionLocal();o=register(RegisterRequest(email=f'r2d-{k}@x.test',password='pilot-password-1',full_name='P',company_name=f'FU2-R2D-{k}'),db=s);s.close();x=CanonicalExcelIngestionService();s=SessionLocal();b,_=x.stage(s,o['company_id'],o['user_id'],'b.xlsx',wb(4));bid=str(b.id);s.close();s=SessionLocal();r=x.accept(s,o['company_id'],o['user_id'],bid);bvid=r['version_id'];s.close();s=SessionLocal();a,_=x.stage(s,o['company_id'],o['user_id'],'a.xlsx',wb(5));aid=str(a.id);assert s.query(V).filter_by(dataset_id=aid).count()==0 and s.query(A).filter_by(company_id=o['company_id'],material_code=CODE,period='2026-W05',demand_type='sales').count()==0;s.close();M.write_text(json.dumps({**o,'bid':bid,'bvid':bvid,'aid':aid}));print('FU2_R2D_SETUP_COMPLETE',flush=True)
def accept():
 m=d();s=SessionLocal();assert s.query(A).filter_by(company_id=m['company_id'],material_code=CODE,period='2026-W05',demand_type='sales').count()==0;t=perf_counter();r=CanonicalExcelIngestionService().accept(s,m['company_id'],m['user_id'],m['aid']);m['avid']=r['version_id'];M.write_text(json.dumps(m));s.close();print(f'FU2_R2D_ACCEPT_COMPLETE seconds={perf_counter()-t:.3f}',flush=True)
def audit():
 m=d();s=SessionLocal();rows=s.query(A).filter_by(company_id=m['company_id'],material_code=CODE,demand_type='sales').all();vals={x.period:float(x.quantity) for x in rows};assert vals=={f'2026-W{x:02d}':float(100+x) for x in range(1,6)} and len(rows)==5 and s.query(V).filter_by(id=m['bvid']).count()==1 and s.query(V).filter_by(id=m['avid']).count()==1 and s.query(R).filter_by(company_id=m['company_id'],material_code=CODE,period='2026-W05',approval_status='accepted').count()==1;assert s.query(RuntimeExecution).filter_by(company_id=m['company_id']).count()==0 and s.query(ForecastVintage).filter_by(company_id=m['company_id']).count()==0 and s.query(DecisionSnapshot).filter_by(company_id=m['company_id']).count()==0;s.close();print('FU2_R2D_AUDIT_COMPLETE',flush=True)
def cleanup():
 m=d();s=SessionLocal();c=UUID(m['company_id']);ds=[UUID(m['bid']),UUID(m['aid'])];s.query(R).filter_by(company_id=c).delete(synchronize_session=False);s.query(A).filter_by(company_id=c).delete(synchronize_session=False);s.query(DE).filter(DE.dataset_id.in_(ds)).delete(synchronize_session=False);s.query(VR).filter(VR.dataset_id.in_(ds)).delete(synchronize_session=False);s.query(V).filter(V.dataset_id.in_(ds)).delete(synchronize_session=False);s.query(Dataset).filter(Dataset.id.in_(ds)).delete(synchronize_session=False);s.query(CompanyEncryptionKey).filter_by(company_id=c).delete(synchronize_session=False);s.query(User).filter_by(company_id=c).delete(synchronize_session=False);s.query(Company).filter_by(id=c).delete(synchronize_session=False);s.commit();assert not s.query(Company).filter_by(id=c).count();s.close();M.unlink();print('FU2_R2D_CLEANUP_COMPLETE',flush=True)
if __name__=='__main__':{'setup':setup,'accept':accept,'audit':audit,'cleanup':cleanup}[sys.argv[1]]()
