"""Focused PostgreSQL verification for the read-only Decision Evidence Resolver."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.application.decision_evidence_resolver import DecisionEvidenceResolver
from app.application.event_intelligence_materialization import EventIntelligenceMaterializationService
from app.database import SessionLocal
from app.models.event_intelligence_memory import EventIntelligenceMemory
from app.models.forecast_vintage import ForecastVintage
from app.models.runtime import RuntimeExecution,RuntimeResultReference
from scripts.verify_phase3c7b3_event_intelligence_memory import fixture,clean as clean_base
from scripts.verify_phase3c7b2_event_association import make_context
def counts(cid):
 s=SessionLocal()
 try:return (s.query(EventIntelligenceMemory).filter_by(company_id=cid).count(),s.query(ForecastVintage).filter_by(company_id=cid).count(),s.query(RuntimeExecution).filter_by(company_id=cid).count(),s.query(RuntimeResultReference).filter_by(company_id=cid).count())
 finally:s.close()
def main():
 roots=[]
 try:
  root=make_context();roots.append(root);other=make_context();roots.append(other);fixture(root);fixture(other);cid=root['company_id'];cutoff='2026-W25';m=EventIntelligenceMaterializationService()
  for identity in ('POS','NEG','CLEAR','MIX'):assert m.materialize(cid,'SKU','sales',identity,cutoff).status in {'CREATED','UNCHANGED'}
  before=counts(cid);r=DecisionEvidenceResolver();a=r.resolve(cid,'SKU','sales',cutoff,'FORECAST_REVIEW');b=DecisionEvidenceResolver().resolve(cid,'SKU','sales',cutoff,'FORECAST_REVIEW')
  assert a.status=='READY' and a==b and len(dict(a.optional)['event']['entries'])==4
  assert r.resolve(cid,'SKU','sales','2026-W03','FORECAST_REVIEW').status=='INSUFFICIENT_REQUIRED_EVIDENCE'
  assert r.resolve(cid,'SKU','consumption',cutoff,'FORECAST_REVIEW').status=='INSUFFICIENT_REQUIRED_EVIDENCE'
  tenant=r.resolve(other['company_id'],'SKU','sales',cutoff,'FORECAST_REVIEW');assert tenant.status=='READY' and tenant.company_id==other['company_id'] and tenant.fingerprint!=a.fingerprint
  assert r.resolve(cid,'MISSING','sales',cutoff,'FORECAST_REVIEW').status=='INSUFFICIENT_REQUIRED_EVIDENCE'
  assert counts(cid)==before
  print('PHASE 3D2 PROBE PASS',{'fingerprint':a.fingerprint,'event_entries':len(dict(a.optional)['event']['entries']),'read_only':True},flush=True)
 finally:
  for root in reversed(roots):clean_base(root)
if __name__=='__main__':main()
