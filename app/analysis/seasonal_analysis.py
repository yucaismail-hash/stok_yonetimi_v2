import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any

def analyze_seasonal_pattern(weekly_data: List[float], group: str, pattern: str) -> Dict:
    """
    Haftalık verilerin mevsimsel analizini yap
    """
    n_weeks = len(weekly_data)
    if n_weeks < 12:
        return {'seasonal_factors': [], 'trend': 0, 'seasonality': False}
    
    # Aylık ortalamalar (4 hafta = 1 ay)
    month_avg = []
    for i in range(0, n_weeks, 4):
        month_data = weekly_data[i:i+4]
        if month_data:
            month_avg.append(np.mean(month_data))
    
    if len(month_avg) < 3:
        return {'seasonal_factors': [], 'trend': 0, 'seasonality': False}
    
    # Trend hesapla (doğrusal regresyon)
    x = np.arange(len(month_avg))
    y = np.array(month_avg)
    slope = np.polyfit(x, y, 1)[0]
    
    # Mevsimsellik kontrolü (CV > 0.3 ise mevsimsel)
    cv = np.std(month_avg) / (np.mean(month_avg) + 1e-10)
    
    # Mevsimsel faktörler (son 12 ay)
    seasonal_factors = []
    if cv > 0.3 and len(month_avg) >= 12:
        # Son 12 ayın ortalaması
        last_12 = month_avg[-12:]
        avg_12 = np.mean(last_12)
        for val in last_12:
            seasonal_factors.append(val / (avg_12 + 1e-10))
    
    return {
        'seasonal_factors': seasonal_factors,
        'trend': slope,
        'seasonality': cv > 0.3,
        'month_avg': month_avg,
        'cv': cv
    }