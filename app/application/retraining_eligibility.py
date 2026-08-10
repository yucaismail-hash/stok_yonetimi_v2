"""Read-only, versioned retraining eligibility triage; never trains a model."""
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID
from app.models.forecast_evaluation import ForecastEvaluation, ForecastEvaluationPoint
from app.services.dataset.ingestion_policy import validate_demand_type
from app.services.dataset.weekly_normalization import parse_weekly_period

RETRAINING_ELIGIBILITY_CONTRACT_VERSION='1.0.0'

@dataclass(frozen=True)
class RetrainingEligibility:
    company_id: UUID; material_code: str; demand_type: str; product_level: str; product_group: str|None; product_class: str|None
    tier: str; reason_codes: tuple[str,...]; sample_count: int; evaluated_period_count: int
    current_wape: Decimal|None; baseline_wape: Decimal|None; mean_signed_error: Decimal|None
    performance_drift: bool; demand_drift: bool; recommended_action: str; contract_version: str=RETRAINING_ELIGIBILITY_CONTRACT_VERSION
    latest_evaluation_id: UUID|None=None; new_evidence_detected: bool=False

class RetrainingEligibilityService:
    """Evidence triage only: thresholds are explicit contract policy, not training triggers."""
    def __init__(self,session): self.session=session
    def evaluate(self,company_id,demand_type,start_period,end_period,last_seen_evaluation_id=None):
        demand_type=validate_demand_type(demand_type); start_period=parse_weekly_period(start_period).period; end_period=parse_weekly_period(end_period).period
        q=self.session.query(ForecastEvaluationPoint).join(ForecastEvaluation,ForecastEvaluationPoint.evaluation_id==ForecastEvaluation.id).filter(ForecastEvaluation.company_id==company_id,ForecastEvaluation.demand_type==demand_type,ForecastEvaluationPoint.target_period>=start_period,ForecastEvaluationPoint.target_period<=end_period)
        groups={}
        for p in q.all(): groups.setdefault(p.material_code,[]).append(p)
        return tuple(self._one(company_id,demand,rows,last_seen_evaluation_id) for _,rows in sorted(groups.items()))
    def _one(self,cid,demand,rows,last_seen):
        rows=sorted(rows,key=lambda p:p.target_period); n=len(rows); recent=rows[-3:]; prior=rows[:-3]
        def wape(points):
            den=sum((abs(Decimal(p.accepted_actual_quantity)) for p in points),Decimal(0)); return None if not den else sum((Decimal(p.absolute_error) for p in points),Decimal(0))/den
        current=wape(recent); baseline=wape(prior) if prior else None; mean_error=sum((Decimal(p.error) for p in rows),Decimal(0))/n
        deterioration=current is not None and baseline is not None and current-baseline>=Decimal('.15'); bias=abs(mean_error)>=max(Decimal('1'),sum((abs(Decimal(p.accepted_actual_quantity)) for p in rows),Decimal(0))/n*Decimal('.2'))
        demand_drift=len(recent)>=3 and prior and abs(sum((Decimal(p.accepted_actual_quantity) for p in recent),Decimal(0))/len(recent)-sum((Decimal(p.accepted_actual_quantity) for p in prior),Decimal(0))/len(prior))>=Decimal('0.3')*max(Decimal('1'),abs(sum((Decimal(p.accepted_actual_quantity) for p in prior),Decimal(0))/len(prior)))
        reasons=[]
        evaluations=self.session.query(ForecastEvaluation).filter(ForecastEvaluation.id.in_({p.evaluation_id for p in rows})).all(); latest=max(evaluations,key=lambda e:(e.recalculated_at,e.created_at,str(e.id))) if evaluations else None; is_new=latest is not None and str(latest.id)!=str(last_seen)
        if n<4: tier='TIER_1_EVALUATE'; reasons=['INSUFFICIENT_SAMPLE','NEW_EVALUATION']
        elif deterioration or bias or demand_drift:
            reasons += ['PERFORMANCE_DETERIORATION'] if deterioration else []; reasons += ['PERSISTENT_BIAS'] if bias else []; reasons += ['DEMAND_DRIFT'] if demand_drift else []
            tier='TIER_3_DEEP_LEARN_RETRAIN' if n>=8 and sum((deterioration,bias,demand_drift))>=2 else 'TIER_2_ANALYZE'
            if tier.startswith('TIER_3'): reasons.append('MULTI_SIGNAL_DRIFT')
        elif is_new: tier='TIER_1_EVALUATE'; reasons=['NEW_EVALUATION']
        else: tier='TIER_0_SKIP'; reasons=['STABLE_PERFORMANCE']
        p=rows[-1]; return RetrainingEligibility(cid,p.material_code,demand,p.product_level,p.product_group,p.product_class,tier,tuple(reasons),n,len({p.target_period for p in rows}),current,baseline,mean_error,deterioration or bias,demand_drift,{'TIER_0_SKIP':'SKIP','TIER_1_EVALUATE':'EVALUATE','TIER_2_ANALYZE':'ANALYZE','TIER_3_DEEP_LEARN_RETRAIN':'RETRAIN_ELIGIBLE'}[tier],latest.id if latest else None,is_new)
