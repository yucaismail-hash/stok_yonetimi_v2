"""Post-completion, deterministic Business Workflow Decision-plan projection."""
from dataclasses import dataclass
from app.application.decision_evidence_resolver import DecisionEvidenceResolver
from app.application.decision_policy import DecisionPolicy
from app.application.decision_snapshot import DecisionSnapshotService
from app.database import SessionLocal
from app.models.runtime import RuntimeExecution, RuntimeResultReference

@dataclass(frozen=True)
class DynamicOperationalPlan:
 execution_id: object; company_id: object; decision_cutoff_period: str; demand_type: str; decision_context: str
 materials_total: int; items: tuple; limitations: tuple

class BusinessDecisionPlanService:
 """Derives a compact plan after analytics complete; it never executes an action."""
 def __init__(self,session_factory=SessionLocal): self._sf=session_factory
 def materialize(self,company_id,execution_id):
  s=self._sf()
  try:
   e=s.query(RuntimeExecution).filter_by(execution_id=execution_id,company_id=company_id,analysis_type='business_workflow',state='completed').one_or_none()
   if not e: raise ValueError('completed Business Workflow is unavailable')
   metadata=e.metadata_ or {}; req=metadata.get('request_metadata') or {}; params=req.get('params') or req
   cutoff=params.get('analysis_cutoff_period') or params.get('forecast_cutoff_period') or (params.get('forecast_vintage') or {}).get('input_cutoff_period')
   demand=params.get('demand_type') or (params.get('forecast_vintage') or {}).get('demand_type')
   if not cutoff or not demand: raise ValueError('Business Workflow lacks authoritative Decision scope')
   forecast=s.query(RuntimeResultReference).filter_by(execution_id=execution_id,company_id=company_id,result_type='forecast',validation_status='validated').first()
   materials=tuple(sorted({item.get('material_code') for item in (forecast.inline_result or {}).get('items',[]) if isinstance(item,dict) and item.get('material_code')})) if forecast else ()
  finally:s.close()
  resolver=DecisionEvidenceResolver(); policy=DecisionPolicy(); snapshots=DecisionSnapshotService();items=[];limits=[]
  for material in materials:
   try: envelope=resolver.resolve(company_id,material,demand,cutoff,'REPLENISHMENT')
   except Exception as exc:
    limits.append({'material_code':material,'code':'DECISION_LIMITED','failure_stage':'resolver','error_class':type(exc).__name__,'detail':str(exc)});continue
   try: result=policy.evaluate(envelope)
   except Exception as exc:
    limits.append({'material_code':material,'code':'DECISION_LIMITED','failure_stage':'policy','error_class':type(exc).__name__,'detail':str(exc)});continue
   try: saved=snapshots.materialize(envelope,result)
   except Exception as exc:
    limits.append({'material_code':material,'code':'DECISION_LIMITED','failure_stage':'snapshot','error_class':type(exc).__name__,'detail':str(exc)});continue
   top=result.candidates[0] if result.candidates else None;items.append({'material_code':material,'decision_snapshot_id':str(saved.snapshot_id),'top_candidate':top.candidate_type if top else None,'candidate_count':len(result.candidates),'agreement_status':result.agreement_status,'confidence':result.confidence,'reason_codes':top.reason_codes if top else (), 'status':result.status})
  return DynamicOperationalPlan(execution_id,company_id,cutoff,demand,'REPLENISHMENT',len(materials),tuple(items),tuple(limits))
