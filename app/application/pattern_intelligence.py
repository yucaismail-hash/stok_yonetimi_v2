"""Read-only deterministic Pattern Intelligence over canonical accepted Actuals."""
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json, math

from app.models.actuals import ActualWeeklyObservation, ActualWeeklyRevision
from app.services.dataset.ingestion_policy import validate_demand_type
from app.services.dataset.weekly_normalization import parse_weekly_period

FEATURE_VERSION = "pattern_features_v1"
POLICY_VERSION = "pattern_policy_v1"
CONFIDENCE_POLICY_VERSION = "pattern_confidence_v1"
MIN_HISTORY = 8

@dataclass(frozen=True)
class PatternIntelligenceResult:
    company_id: object; material_code: str; demand_type: str; cutoff_period: str
    feature_version: str; policy_version: str; confidence_policy_version: str; source_fingerprint: str
    status: str; sample_count: int; first_period: str|None; last_period: str|None; coverage_ratio: float; missing_periods: tuple[str,...]
    mean_demand: float|None; std_demand: float|None; coefficient_of_variation: float|None; squared_coefficient_of_variation: float|None
    zero_demand_count: int; zero_demand_ratio: float; nonzero_demand_count: int; adi: float|None
    trend_slope: float|None; trend_strength: float|None; recent_change_ratio: float|None
    seasonality_status: str; classification: str; confidence: float
    product_level: str|None; product_group: str|None; product_class: str|None; source_actual_observation_ids: tuple[str,...]

def _canonical(value):
    if isinstance(value, Decimal): return format(value, 'f')
    return str(value) if value is not None and not isinstance(value,(str,int,float,bool,list,dict,tuple)) else value

class PatternIntelligenceService:
    """Calculation-only boundary; no memory, Learning Evidence, or runtime mutation."""
    def __init__(self, session): self.session=session
    def calculate(self, company_id, material_code, demand_type, cutoff_period):
        demand=validate_demand_type(demand_type); cutoff=parse_weekly_period(cutoff_period).period
        rows=[r for r in self.session.query(ActualWeeklyObservation).filter_by(company_id=company_id,material_code=material_code,demand_type=demand).all() if parse_weekly_period(r.period).period<=cutoff]
        rows=sorted(rows,key=lambda r:(parse_weekly_period(r.period).year,parse_weekly_period(r.period).week))
        values=[float(r.quantity) for r in rows]; periods=[r.period for r in rows]
        missing=self._missing(periods); coverage=len(rows)/(len(rows)+len(missing)) if rows else 0.0
        revisions=self.session.query(ActualWeeklyRevision).filter(ActualWeeklyRevision.observation_id.in_([r.id for r in rows]),ActualWeeklyRevision.approval_status=='accepted').all() if rows else []
        payload={'company_id':str(company_id),'material_code':material_code,'demand_type':demand,'cutoff':cutoff,'feature_version':FEATURE_VERSION,'policy_version':POLICY_VERSION,'actuals':[(str(r.id),str(r.quantity),r.period) for r in rows],'accepted_revisions':sorted((str(r.id) for r in revisions))}
        fp=sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),default=_canonical).encode()).hexdigest()
        meta=rows[-1] if rows else None
        common=dict(company_id=company_id,material_code=material_code,demand_type=demand,cutoff_period=cutoff,feature_version=FEATURE_VERSION,policy_version=POLICY_VERSION,confidence_policy_version=CONFIDENCE_POLICY_VERSION,source_fingerprint=fp,sample_count=len(rows),first_period=periods[0] if periods else None,last_period=periods[-1] if periods else None,coverage_ratio=coverage,missing_periods=tuple(missing),product_level=meta.product_level if meta else None,product_group=meta.product_group if meta else None,product_class=meta.product_class if meta else None,source_actual_observation_ids=tuple(str(r.id) for r in rows))
        if len(rows)<MIN_HISTORY: return PatternIntelligenceResult(**common,status='INSUFFICIENT_HISTORY',mean_demand=None,std_demand=None,coefficient_of_variation=None,squared_coefficient_of_variation=None,zero_demand_count=sum(x==0 for x in values),zero_demand_ratio=(sum(x==0 for x in values)/len(rows) if rows else 0),nonzero_demand_count=sum(x!=0 for x in values),adi=None,trend_slope=None,trend_strength=None,recent_change_ratio=None,seasonality_status='SEASONALITY_NOT_ESTABLISHED',classification='INSUFFICIENT_HISTORY',confidence=0.0)
        mean=sum(values)/len(values); std=math.sqrt(sum((x-mean)**2 for x in values)/len(values)); cv=(std/mean if mean else None); cv2=(cv*cv if cv is not None else None); zeros=sum(x==0 for x in values); nonzero=len(values)-zeros; adi=(len(values)/nonzero if nonzero else None)
        xmean=(len(values)-1)/2; denom=sum((i-xmean)**2 for i in range(len(values))); slope=sum((i-xmean)*(v-mean) for i,v in enumerate(values))/denom if denom else 0; strength=abs(slope)/(std or 1)
        window=min(4,len(values)//2); base=sum(values[:-window])/len(values[:-window]); recent=sum(values[-window:])/window; change=(recent-base)/max(abs(base),1.0)
        # B2A deliberately requires two annual cycles before seasonal classification.
        seasonal='SEASONALITY_NOT_ESTABLISHED'
        # Zeros establish intermittency; lumpy additionally requires variable
        # nonzero arrival sizes. Total-series CV² would make regular sparse
        # demand lumpy merely because it contains zeros.
        nonzero_values=[x for x in values if x!=0]
        nonzero_mean=sum(nonzero_values)/len(nonzero_values) if nonzero_values else 0
        nonzero_std=math.sqrt(sum((x-nonzero_mean)**2 for x in nonzero_values)/len(nonzero_values)) if nonzero_values else 0
        nonzero_cv2=(nonzero_std/nonzero_mean)**2 if nonzero_mean else None
        if adi and adi>1.32 and nonzero_cv2 is not None and nonzero_cv2>0.49: classification='LUMPY'
        elif adi and adi>1.32: classification='INTERMITTENT'
        elif abs(change)>=.30 and strength>=.20: classification='STRUCTURAL_CHANGE'
        elif strength>=.20: classification='TRENDING'
        elif cv is not None and cv>=.50: classification='VOLATILE'
        else: classification='STABLE'
        confidence=round(min(.95,(len(rows)/24)*.5 + coverage*.3 + (nonzero/len(rows))*.2),3)
        return PatternIntelligenceResult(**common,status='OK',mean_demand=mean,std_demand=std,coefficient_of_variation=cv,squared_coefficient_of_variation=cv2,zero_demand_count=zeros,zero_demand_ratio=zeros/len(rows),nonzero_demand_count=nonzero,adi=adi,trend_slope=slope,trend_strength=strength,recent_change_ratio=change,seasonality_status=seasonal,classification=classification,confidence=confidence)
    @staticmethod
    def _missing(periods):
        if len(periods)<2:return []
        keys=[parse_weekly_period(p) for p in periods]; found=set(periods); missing=[]; y,w=keys[0].year,keys[0].week
        while f'{y:04d}-W{w:02d}' != periods[-1]:
            import datetime
            nxt=(datetime.date.fromisocalendar(y,w,1)+datetime.timedelta(days=7)).isocalendar(); y,w=nxt.year,nxt.week
            p=f'{y:04d}-W{w:02d}'
            if p not in found:missing.append(p)
        return missing
