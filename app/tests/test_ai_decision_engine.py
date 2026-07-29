# tests/test_ai_decision_engine.py
# AI Decision Engine Testleri

import pytest
import json
from app.services.ai.ai_decision_engine import AIDecisionEngine


@pytest.fixture
def decision_engine():
    """AI Decision Engine instance'ı"""
    return AIDecisionEngine(language="English")


def test_extract_safety_stock_stats(decision_engine):
    """Safety Stock istatistik çıkarma testi"""
    results = [
        {
            'material_code': 'MAT001',
            'risk_score': 0.8,
            'cv': 0.9,
            'recommended_value': 150,
            'is_intermittent': True,
            'has_seasonality': False
        },
        {
            'material_code': 'MAT002',
            'risk_score': 0.6,
            'cv': 0.5,
            'recommended_value': 80,
            'is_intermittent': False,
            'has_seasonality': True
        },
        {
            'material_code': 'MAT003',
            'risk_score': 0.2,
            'cv': 0.2,
            'recommended_value': 30,
            'is_intermittent': False,
            'has_seasonality': False
        }
    ]
    
    stats = decision_engine._extract_safety_stock_stats(results)
    
    assert stats['critical_count'] == 2  # risk_score > 0.5
    assert stats['high_risk_count'] == 2
    assert stats['intermittent_count'] == 1
    assert stats['seasonal_count'] == 1
    assert stats['avg_cv'] == (0.9 + 0.5 + 0.2) / 3
    assert stats['top_risk_item']['material_code'] == 'MAT001'


def test_extract_forecast_stats(decision_engine):
    """Forecast istatistik çıkarma testi"""
    results = [
        {
            'material_code': 'MAT001',
            'selected_model': 'holt_winters',
            'trend_direction': 'Artış',
            'model_rmse': 15,
            'outlier_info': {'has_outliers': False}
        },
        {
            'material_code': 'MAT002',
            'selected_model': 'arima',
            'trend_direction': 'Azalış',
            'model_rmse': 25,
            'outlier_info': {'has_outliers': True}
        },
        {
            'material_code': 'MAT003',
            'selected_model': 'simple',
            'trend_direction': 'Artış',
            'model_rmse': 35,
            'outlier_info': {'has_outliers': False}
        }
    ]
    
    stats = decision_engine._extract_forecast_stats(results)
    
    assert stats['model_distribution']['holt_winters'] == 1
    assert stats['model_distribution']['arima'] == 1
    assert stats['model_distribution']['simple'] == 1
    assert stats['trend_up_count'] == 2
    assert stats['trend_down_count'] == 1
    assert stats['outlier_count'] == 1


def test_standardize_decision(decision_engine):
    """Karar standardizasyon testi"""
    raw_decision = {
        'decision': 'increase_safety_stock',
        'priority': 'high',
        'confidence': 0.93,
        'reasons': ['high_variability', 'intermittent_demand'],
        'explanation': 'Test açıklama'
    }
    
    standardized = decision_engine._standardize_decision(raw_decision, 'safety_stock')
    
    assert standardized['decision'] == 'increase_safety_stock'
    assert standardized['priority'] == 'high'
    assert standardized['confidence'] == 0.93
    assert standardized['analysis_type'] == 'safety_stock'
    assert 'generated_at' in standardized


def test_standardize_decision_with_missing_fields(decision_engine):
    """Eksik alanlı karar standardizasyon testi"""
    raw_decision = {
        'decision': 'invalid_decision',
        'priority': 'invalid_priority',
        'confidence': 1.5,
        'reasons': ['test']
        # explanation yok
    }
    
    standardized = decision_engine._standardize_decision(raw_decision, 'forecast')
    
    # Geçersiz değerler default'a çevrilmeli
    assert standardized['decision'] == 'maintain_current'
    assert standardized['priority'] == 'medium'
    assert standardized['confidence'] == 0.5
    assert 'explanation' in standardized
    assert standardized['analysis_type'] == 'forecast'


def test_get_fallback_decision(decision_engine):
    """Fallback karar testi"""
    fallback = decision_engine._get_fallback_decision('safety_stock', {})
    
    assert fallback['decision'] == 'maintain_current'
    assert fallback['priority'] == 'medium'
    assert fallback['confidence'] == 0.3
    assert fallback['is_fallback'] == True
    assert 'explanation' in fallback