from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from app.analysis.pattern import AdvancedDemandAnalyzer

router = APIRouter()
analyzer = AdvancedDemandAnalyzer()

class PatternRequest(BaseModel):
    weekly_data: List[float]

@router.post("/pattern")
def analyze_pattern(request: PatternRequest):
    try:
        pattern, stats = analyzer.analyze_demand_pattern(request.weekly_data)
        return {
            "pattern": pattern,
            "cv": stats['cv'],
            "zero_ratio": stats['zero_ratio'],
            "trend": stats['trend'],
            "mean": stats['mean'],
            "std": stats['std'],
            "median": stats['median']
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    