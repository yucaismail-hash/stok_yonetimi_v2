# app/services/dashboard_summary_builder.py
"""
Dashboard Summary Builder - Her modül için DashboardSummary oluşturur.
"""

from typing import List, Dict, Any
from datetime import datetime
import numpy as np


def build_forecast_dashboard_summary(
    results: List[Dict[str, Any]],
    analysis_id: int,
    dataset_id: int,
    horizon: int = 4
) -> Dict[str, Any]:
    """Forecast sonuçlarından DashboardSummary oluşturur."""
    total_items = len(results)
    
    # Trend analizi
    trend_up = sum(1 for r in results if r.get('trend_direction') == 'Artış')
    trend_down = sum(1 for r in results if r.get('trend_direction') == 'Azalış')
    
    # Outlier kontrolü
    outlier_count = sum(1 for r in results if r.get('outlier_info', {}).get('has_outliers', False))
    
    # Priority hesapla
    priority = 40  # Base
    
    # Trend etkisi
    if trend_up > trend_down * 1.5:
        priority += 20
    elif trend_down > trend_up * 1.5:
        priority += 15
    elif trend_up > trend_down:
        priority += 10
    
    # Outlier etkisi
    if outlier_count > total_items * 0.3:
        priority += 20
    elif outlier_count > total_items * 0.1:
        priority += 10
    
    # Ortalama RMSE
    rmse_values = [r.get('model_rmse', 0) for r in results if r.get('model_rmse')]
    if rmse_values:
        avg_rmse = sum(rmse_values) / len(rmse_values)
        if avg_rmse > 50:
            priority += 15
        elif avg_rmse > 30:
            priority += 5
    
    priority = min(100, max(0, priority))
    
    # Summary
    if trend_up > trend_down:
        summary = f"Talep {trend_up} üründe artış, {trend_down} üründe azalış gösteriyor."
    elif trend_down > trend_up:
        summary = f"Talep {trend_down} üründe azalış, {trend_up} üründe artış gösteriyor."
    else:
        summary = f"Talep trendi dengeli. {total_items} ürün analiz edildi."
    
    # Attention
    attention = []
    if outlier_count > 0:
        attention.append(f"{outlier_count} üründe aykırı değer tespit edildi.")
    if trend_up > total_items * 0.6:
        attention.append(f"Güçlü talep artışı: {trend_up} ürün.")
    if trend_down > total_items * 0.6:
        attention.append(f"Güçlü talep azalışı: {trend_down} ürün.")
    
    # Critical items
    critical_items = []
    for r in results[:5]:
        if r.get('outlier_info', {}).get('has_outliers', False):
            critical_items.append({
                'code': r.get('material_code', ''),
                'reason': 'Aykırı değer var',
                'trend': r.get('trend_direction', '')
            })
    
    return {
        'priority': priority,
        'summary': summary,
        'attention': attention,
        'business_value': 'Güncel talep tahmini ile stok planlaması optimize edilecek.',
        'analysis_id': analysis_id,
        'dataset_id': dataset_id,
        'target_page': '/forecast',
        'analysis_type': 'forecast',
        'last_run': datetime.utcnow().isoformat(),
        'status': 'success',
        'metrics': {
            'total_items': total_items,
            'trend_up': trend_up,
            'trend_down': trend_down,
            'outlier_count': outlier_count,
            'avg_rmse': sum(rmse_values) / len(rmse_values) if rmse_values else 0
        },
        'critical_items': critical_items,
        'trend_up': trend_up,
        'trend_down': trend_down
    }


def build_safety_stock_dashboard_summary(
    results: List[Dict[str, Any]],
    analysis_id: int,
    dataset_id: int,
    service_level: float = 0.95
) -> Dict[str, Any]:
    """Safety Stock sonuçlarından DashboardSummary oluşturur."""
    total_items = len(results)
    
    # Kritik ürünler
    critical_items = [r for r in results if r.get('risk_level') == 'Yüksek']
    high_risk_items = [r for r in results if r.get('risk_score', 0) > 0.5]
    
    critical_count = len(critical_items)
    high_risk_count = len(high_risk_items)
    
    ai_comment = ""
    if critical_count > 0:
        top_critical = critical_items[0]
        ai_comment = f"{critical_count} kritik ürün tespit edildi. En riskli: {top_critical.get('material_code', 'Bilinmiyor')}. Stok seviyeleri hızlıca gözden geçirilmeli."
    elif high_risk_count > 0:
        ai_comment = f"{high_risk_count} ürün yüksek risk taşıyor. Detaylı analiz önerilir."
    else:
        ai_comment = "Tüm ürünler güvende. Mevcut stok politikası başarılı."

    # Priority hesapla
    priority = 40  # Base
    
    if critical_count > 20:
        priority += 50
    elif critical_count > 10:
        priority += 35
    elif critical_count > 5:
        priority += 20
    elif critical_count > 0:
        priority += 10
    
    # Aralıklı talep
    intermittent_count = sum(1 for r in results if r.get('is_intermittent', False))
    if intermittent_count > total_items * 0.3:
        priority += 15
    
    priority = min(100, max(0, priority))
    
    # Summary
    if critical_count > 0:
        top_critical = critical_items[0]
        summary = f"{critical_count} kritik ürün. En riskli: {top_critical.get('material_code', 'Bilinmiyor')}"
    else:
        summary = f"Tüm ürünler güvende. {total_items} ürün analiz edildi."
    
    # Attention
    attention = []
    for item in critical_items[:3]:
        attention.append(f"{item.get('material_code', '')} - Risk: {item.get('risk_score', 0):.2f}")
    
    if intermittent_count > total_items * 0.3:
        attention.append(f"{intermittent_count} ürün aralıklı talep gösteriyor.")
    
    # Critical items
    critical_list = []
    for item in critical_items[:5]:
        critical_list.append({
            'code': item.get('material_code', ''),
            'risk_score': item.get('risk_score', 0),
            'ss': item.get('hybrid_ss', 0),
            'risk_level': item.get('risk_level', '')
        })
    
    return {
        'priority': priority,
        'summary': summary,
        'attention': attention,
        'business_value': 'Kritik ürünlerin stok seviyeleri hızlıca gözden geçirilecek.',
        'analysis_id': analysis_id,
        'dataset_id': dataset_id,
        'target_page': '/safety-stock',
        'analysis_type': 'safety_stock',
        'last_run': datetime.utcnow().isoformat(),
        'status': 'success',
        'metrics': {
            'total_items': total_items,
            'critical_count': critical_count,
            'high_risk_count': high_risk_count,
            'intermittent_count': intermittent_count,
            'service_level': service_level
        },
        'critical_items': critical_items[:10],  # ✅ Max 10 kritik ürün
        'critical_count': critical_count,
        'high_risk_count': high_risk_count,
        'ai_comment': ai_comment,  # ✅ AI comment eklendi
    }


def build_supplier_dashboard_summary(
    suppliers: List[Dict[str, Any]],
    analysis_id: int,
    dataset_id: int
) -> Dict[str, Any]:
    """Supplier sonuçlarından DashboardSummary oluşturur."""
    total_items = len(suppliers)
    
    # Yüksek riskli tedarikçiler
    high_risk = [s for s in suppliers if s.get('risk_level') == 'YÜKSEK']
    low_perf = [s for s in suppliers if s.get('performance_level') == 'KÖTÜ']
    
    high_risk_count = len(high_risk)
    low_perf_count = len(low_perf)
    
    # Priority hesapla
    priority = 40  # Base
    
    if high_risk_count > 5:
        priority += 45
    elif high_risk_count > 3:
        priority += 30
    elif high_risk_count > 0:
        priority += 15
    
    if low_perf_count > 3:
        priority += 15
    elif low_perf_count > 0:
        priority += 5
    
    priority = min(100, max(0, priority))
    
    # Summary
    if high_risk_count > 0:
        top_risk = high_risk[0]
        summary = f"{high_risk_count} tedarikçi yüksek riskli. En riskli: {top_risk.get('name', 'Bilinmiyor')}"
    else:
        summary = f"Tüm tedarikçiler güvende. {total_items} tedarikçi analiz edildi."
    
    # Attention
    attention = []
    for s in high_risk[:3]:
        attention.append(f"{s.get('name', '')} - Risk: {s.get('risk_score', 0):.2f}")
    for s in low_perf[:3]:
        attention.append(f"{s.get('name', '')} - Düşük performans")
    
    # Critical items
    critical_list = []
    for s in high_risk[:5]:
        critical_list.append({
            'name': s.get('name', ''),
            'risk_score': s.get('risk_score', 0),
            'ontime_rate': s.get('ontime_rate', 0)
        })
    
    return {
        'priority': priority,
        'summary': summary,
        'attention': attention,
        'business_value': 'Tedarik zinciri riskleri değerlendirilip aksiyon alınacak.',
        'analysis_id': analysis_id,
        'dataset_id': dataset_id,
        'target_page': '/supplier',
        'analysis_type': 'supplier',
        'last_run': datetime.utcnow().isoformat(),
        'status': 'success',
        'metrics': {
            'total_items': total_items,
            'high_risk_count': high_risk_count,
            'low_perf_count': low_perf_count
        },
        'critical_items': critical_list,
        'high_risk_count': high_risk_count
    }


def build_simulation_dashboard_summary(
    results: List[Dict[str, Any]],
    analysis_id: int,
    dataset_id: int,
    config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Simulation sonuçlarından DashboardSummary oluşturur."""
    total_items = len(results)
    
    # Ortalama servis seviyesi
    service_levels = [r.get('service_level', 0) for r in results if r.get('service_level')]
    avg_service = sum(service_levels) / len(service_levels) if service_levels else 0
    
    # Yüksek tail risk
    high_risk = [r for r in results if r.get('tail_risk', 0) > 0.5]
    high_risk_count = len(high_risk)
    
    # Priority hesapla
    priority = 30  # Base
    
    if high_risk_count > total_items * 0.3:
        priority += 40
    elif high_risk_count > total_items * 0.1:
        priority += 20
    elif high_risk_count > 0:
        priority += 10
    
    if avg_service < 85:
        priority += 20
    elif avg_service < 90:
        priority += 10
    
    priority = min(100, max(0, priority))
    
    # Summary
    summary = f"Ortalama servis: %{avg_service:.1f}. {total_items} ürün simüle edildi."
    
    # Attention
    attention = []
    if high_risk_count > 0:
        attention.append(f"{high_risk_count} ürün yüksek tail risk taşıyor.")
    if avg_service < 85:
        attention.append(f"Servis seviyesi düşük (%{avg_service:.1f}).")
    
    return {
        'priority': priority,
        'summary': summary,
        'attention': attention,
        'business_value': 'Farklı senaryolar ile stok performansı test edilecek.',
        'analysis_id': analysis_id,
        'dataset_id': dataset_id,
        'target_page': '/simulation',
        'analysis_type': 'simulation',
        'last_run': datetime.utcnow().isoformat(),
        'status': 'success',
        'metrics': {
            'total_items': total_items,
            'avg_service_level': avg_service,
            'high_risk_count': high_risk_count
        },
        'avg_service_level': avg_service
    }


def build_backtest_dashboard_summary(
    results: List[Dict[str, Any]],
    analysis_id: int,
    dataset_id: int,
    test_window: int = 8
) -> Dict[str, Any]:
    """Backtest sonuçlarından DashboardSummary oluşturur."""
    total_items = len(results)
    
    # Ortalama servis seviyesi
    service_levels = [r.get('service_level', 0) for r in results if r.get('service_level')]
    avg_service = sum(service_levels) / len(service_levels) if service_levels else 0
    
    # Yüksek tail risk
    high_risk = [r for r in results if r.get('tail_risk', 0) > 0.5]
    high_risk_count = len(high_risk)
    
    # Priority hesapla
    priority = 20  # Base
    
    if avg_service < 85:
        priority += 30
    elif avg_service < 90:
        priority += 15
    
    if high_risk_count > total_items * 0.3:
        priority += 20
    elif high_risk_count > total_items * 0.1:
        priority += 10
    
    priority = min(100, max(0, priority))
    
    # Summary
    summary = f"Ortalama servis: %{avg_service:.1f}. {total_items} ürün test edildi."
    
    # Attention
    attention = []
    if avg_service < 85:
        attention.append(f"Servis seviyesi düşük (%{avg_service:.1f}).")
    if high_risk_count > 0:
        attention.append(f"{high_risk_count} ürün yüksek tail risk taşıyor.")
    
    return {
        'priority': priority,
        'summary': summary,
        'attention': attention,
        'business_value': 'Geçmiş veriler ile strateji performansı doğrulanacak.',
        'analysis_id': analysis_id,
        'dataset_id': dataset_id,
        'target_page': '/backtest',
        'analysis_type': 'backtest',
        'last_run': datetime.utcnow().isoformat(),
        'status': 'success',
        'metrics': {
            'total_items': total_items,
            'avg_service_level': avg_service,
            'high_risk_count': high_risk_count
        },
        'avg_service_level': avg_service
    }