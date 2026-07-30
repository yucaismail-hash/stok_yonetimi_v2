# app/api/endpoints/export.py - GÜNCELLENMİŞ
# 7 Sayfalık Excel Raporu - Safety Stock

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
from app.utils.excel_exporter import ExcelExporter
from app.auth import get_current_user
from app.models import User
from app.database import get_db
from sqlalchemy.orm import Session
import io
import pandas as pd
import numpy as np
from datetime import datetime

router = APIRouter()
exporter = ExcelExporter()


# ============================================================
# 📌 MEVCUT ENDPOINT'LER (KORUNUYOR)
# ============================================================

@router.post("/export/recommendations")
def export_recommendations(
    material_code: str,
    material_data: Dict[str, Any],
    simulation_result: Dict[str, Any],
    ai_analysis: Dict[str, Any],
    optimized_params: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Malzeme önerilerini Excel dosyası olarak dışa aktar"""
    try:
        excel_file = exporter.export_recommendations(
            material_code=material_code,
            material_data=material_data,
            simulation_result=simulation_result,
            ai_analysis=ai_analysis,
            optimized_params=optimized_params
        )
        
        filename = f"oneri_{material_code}_{exporter.timestamp}.xlsx"
        
        return StreamingResponse(
            excel_file,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/export/bulk-report")
def export_bulk_report(
    materials_data: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user)
):
    """Tüm malzemeler için toplu rapor oluştur"""
    try:
        excel_file = exporter.export_bulk_report(materials_data)
        filename = f"toplu_rapor_{exporter.timestamp}.xlsx"
        
        return StreamingResponse(
            excel_file,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/export/pattern-results")
def export_pattern_results(
    data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Pattern analizi sonuçlarını Excel olarak dışa aktar"""
    try:
        results = data.get('results', [])
        if not results:
            raise HTTPException(status_code=400, detail="Aktarılacak sonuç yok")
        
        df = pd.DataFrame(results)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Pattern Analizi', index=False)
            
            pattern_counts = df['pattern'].value_counts().to_dict() if 'pattern' in df.columns else {}
            summary = {
                'Toplam Malzeme': len(results),
                'Analiz Tarihi': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'Pattern Dağılımı': str(pattern_counts)
            }
            summary_df = pd.DataFrame([summary])
            summary_df.to_excel(writer, sheet_name='Özet', index=False)
            
            if pattern_counts:
                pattern_df = pd.DataFrame([
                    {'Pattern': k, 'Adet': v} for k, v in pattern_counts.items()
                ])
                pattern_df.to_excel(writer, sheet_name='Pattern Dağılımı', index=False)
        
        output.seek(0)
        filename = f"pattern_analiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# 📌 YENİ: 7 SAYFALIK SAFETY STOCK RAPORU
# ============================================================

@router.post("/export/safety-stock-results")
def export_safety_stock_results(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    7 Sayfalık Safety Stock Raporu
    """
    try:
        results = request.get('results', [])
        if not results:
            raise HTTPException(status_code=400, detail="Aktarılacak sonuç yok!")
        
        print(f"📊 Excel export başladı: {len(results)} sonuç")
        print(f"📊 Kullanıcı: {current_user.email}")
        
        learning_rules = request.get('learning_rules', [])
        ai_decision = request.get('ai_decision', {})
        executive_summary = request.get('executive_summary', {})
        
        # ✅ ExcelExporter'ı doğru çağır
        excel_file = exporter.export_bulk_report(
            materials_data=results,
            learning_rules=learning_rules,
            ai_decision=ai_decision,
            executive_summary=executive_summary
        )
        
        filename = f"safety_stock_rapor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        print(f"✅ Excel export tamamlandı: {filename}")
        
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        print(f"❌ Safety Stock export hatası: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================
# 📌 YENİ: FORECAST EXPORT (7 SAYFA)
# ============================================================

@router.post("/export/forecast-results")
def export_forecast_results(
    data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Forecast sonuçlarını zengin Excel olarak dışa aktar"""
    try:
        results = data.get('results', [])
        if not results:
            raise HTTPException(status_code=400, detail="Aktarılacak sonuç yok")
        
        model_labels = {
            'holt_winters': 'Holt-Winters',
            'arima': 'ARIMA',
            'simple': 'Basit MA',
            'auto': 'Otomatik'
        }
        
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # Ana veri
            rows = []
            for r in results:
                forecast_vals = r.get('forecast', [])
                mape = r.get('model_rmse')
                selected_model = r.get('selected_model', 'unknown')
                
                row = {
                    'Malzeme Kodu': r.get('material_code', ''),
                    'Grup': r.get('group', ''),
                    'Seçilen Model': model_labels.get(selected_model, selected_model),
                    'Seçim Nedeni': r.get('selection_reason', ''),
                    'Trend Yönü': r.get('trend_direction', ''),
                    'Trend %': f"{r.get('trend_percent', 0):.1f}%",
                    'RMSE': f"{mape:.2f}" if mape and mape < 999 else '-'
                }
                
                # Tahmin değerleri
                for i, val in enumerate(forecast_vals[:13]):  # ilk 13 hafta
                    row[f'{i+1}. Hafta'] = round(val, 1) if val else '-'
                
                rows.append(row)
            
            df = pd.DataFrame(rows)
            df.to_excel(writer, sheet_name='Forecast Analizi', index=False)
            
            # Özet
            if results:
                rmse_values = [r.get('model_rmse') for r in results if r.get('model_rmse') and r.get('model_rmse') < 999]
                summary = {
                    'Toplam Malzeme': len(results),
                    'Ortalama RMSE': f"{sum(rmse_values) / len(rmse_values):.2f}" if rmse_values else '-',
                    'Artış Trendi Olan': len([r for r in results if r.get('trend_direction') == 'Artış']),
                    'Azalış Trendi Olan': len([r for r in results if r.get('trend_direction') == 'Azalış']),
                    'Analiz Tarihi': datetime.now().strftime('%Y-%m-%d %H:%M')
                }
                summary_df = pd.DataFrame([summary])
                summary_df.to_excel(writer, sheet_name='Özet', index=False)
        
        output.seek(0)
        filename = f"forecast_analiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
        
    except Exception as e:
        print(f"❌ Forecast export hatası: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# 📌 YENİ: SUPPLIER EXPORT
# ============================================================

@router.post("/export/supplier-results")
def export_supplier_results(
    data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Tedarikçi analizi sonuçlarını Excel olarak dışa aktar"""
    try:
        suppliers = data.get('suppliers', [])
        recommendations = data.get('recommendations', [])
        
        if not suppliers:
            raise HTTPException(status_code=400, detail="Aktarılacak sonuç yok")
        
        df = pd.DataFrame(suppliers)
        
        column_map = {
            'supplier_id': 'Tedarikçi Kodu',
            'name': 'Tedarikçi Adı',
            'risk_score': 'Risk Skoru',
            'performance_score': 'Performans Skoru',
            'ontime_rate': 'Zamanında Teslim (%)',
            'lt_mean': 'Lead Time (Gün)',
            'lt_std': 'Lead Time Std',
            'factor': 'Tedarikçi Faktörü',
            'material_count': 'Malzeme Sayısı',
            'total_share': 'Toplam Pay',
            'risk_level': 'Risk Seviyesi',
            'performance_level': 'Performans Seviyesi',
            'recommendation': 'Tavsiye'
        }
        df = df.rename(columns=column_map)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Tedarikçi Analizi', index=False)
            
            # Özet
            risk_high = len([s for s in suppliers if s.get('risk_score', 1) >= 0.4])
            risk_medium = len([s for s in suppliers if 0.2 <= s.get('risk_score', 0.5) < 0.4])
            risk_low = len([s for s in suppliers if s.get('risk_score', 0) < 0.2])
            
            avg_risk = np.mean([s.get('risk_score', 0) for s in suppliers]) if suppliers else 0
            avg_perf = np.mean([s.get('performance_score', 0) for s in suppliers]) if suppliers else 0
            
            summary = {
                'Toplam Tedarikçi': len(suppliers),
                'Düşük Risk': risk_low,
                'Orta Risk': risk_medium,
                'Yüksek Risk': risk_high,
                'Ortalama Risk': f"{avg_risk*100:.1f}%",
                'Ortalama Performans': f"{avg_perf*100:.1f}%",
                'Analiz Tarihi': datetime.now().strftime('%Y-%m-%d %H:%M')
            }
            summary_df = pd.DataFrame([summary])
            summary_df.to_excel(writer, sheet_name='Özet', index=False)
            
            if recommendations:
                rec_df = pd.DataFrame({'Öneriler': recommendations})
                rec_df.to_excel(writer, sheet_name='Tavsiyeler', index=False)
        
        output.seek(0)
        filename = f"tedarikci_analiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
        
    except Exception as e:
        print(f"❌ Tedarikçi export hatası: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# 📌 YENİ: SIMULATION EXPORT
# ============================================================

@router.post("/export/simulation-results")
def export_simulation_results(
    data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Simülasyon sonuçlarını Excel olarak dışa aktar"""
    try:
        results = data.get('results', [])
        if not results:
            raise HTTPException(status_code=400, detail="Aktarılacak sonuç yok")
        
        df = pd.DataFrame(results)
        
        column_map = {
            'material_code': 'Malzeme Kodu',
            'group': 'Grup',
            'service_level': 'Servis Seviyesi (%)',
            'cvar_95': 'CVaR95',
            'tail_risk': 'Kuyruk Riski',
            'tail_risk_level': 'Risk Seviyesi',
            'service_gap': 'Servis Açığı',
            'stockout_probability': 'Stok Tükenme Olasılığı',
            'avg_stock': 'Ortalama Stok',
            'regime_used': 'Rejim Aktif',
            'copula_used': 'Copula Aktif',
            'adaptive_ss_used': 'Adaptif SS Aktif'
        }
        df = df.rename(columns=column_map)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Simülasyon Sonuçları', index=False)
            
            summary = {
                'Toplam Malzeme': len(results),
                'Ortalama Servis Seviyesi': f"{np.mean([r.get('service_level', 0) for r in results]):.1f}%",
                'Ortalama Kuyruk Riski': f"{np.mean([r.get('tail_risk', 0) for r in results]):.3f}",
                'Analiz Tarihi': datetime.now().strftime('%Y-%m-%d %H:%M')
            }
            summary_df = pd.DataFrame([summary])
            summary_df.to_excel(writer, sheet_name='Özet', index=False)
        
        output.seek(0)
        filename = f"simulasyon_analiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
        
    except Exception as e:
        print(f"❌ Simülasyon export hatası: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# 📌 YENİ: BACKTEST EXPORT
# ============================================================

@router.post("/export/backtest-results")
def export_backtest_results(
    data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Backtest sonuçlarını Excel olarak dışa aktar"""
    try:
        results = data.get('results', [])
        if not results:
            raise HTTPException(status_code=400, detail="Aktarılacak sonuç yok")
        
        df = pd.DataFrame(results)
        
        column_map = {
            'material_code': 'Malzeme Kodu',
            'group': 'Grup',
            'best_strategy': 'En İyi Strateji',
            'service_level': 'Servis Seviyesi (%)',
            'total_cost': 'Toplam Maliyet',
            'holding_cost': 'Stok Tutma Maliyeti',
            'shortage_cost': 'Stok Tükenme Maliyeti',
            'stockout_probability': 'Stok Tükenme Olasılığı (%)',
            'tail_risk': 'Kuyruk Riski',
            'tail_risk_level': 'Risk Seviyesi',
            'total_shortage': 'Toplam Stok Tükenme'
        }
        df = df.rename(columns=column_map)
        
        # Servis seviyesini yüzdeye çevir
        if 'Servis Seviyesi (%)' in df.columns:
            df['Servis Seviyesi (%)'] = df['Servis Seviyesi (%)'].apply(lambda x: round(x * 100, 1) if x else 0)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Backtest Sonuçları', index=False)
            
            # Strateji dağılımı
            if 'En İyi Strateji' in df.columns:
                strategy_dist = df['En İyi Strateji'].value_counts().reset_index()
                strategy_dist.columns = ['Strateji', 'Malzeme Sayısı']
                strategy_dist.to_excel(writer, sheet_name='Strateji Dağılımı', index=False)
            
            summary = {
                'Toplam Malzeme': len(results),
                'En Çok Kullanılan Strateji': df['En İyi Strateji'].mode()[0] if 'En İyi Strateji' in df.columns else '-',
                'Analiz Tarihi': datetime.now().strftime('%Y-%m-%d %H:%M')
            }
            summary_df = pd.DataFrame([summary])
            summary_df.to_excel(writer, sheet_name='Özet', index=False)
        
        output.seek(0)
        filename = f"backtest_analiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
        
    except Exception as e:
        print(f"❌ Backtest export hatası: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# 📌 FORMAT BİLGİSİ
# ============================================================

@router.get("/export/format-info")
def get_export_info():
    """Export format bilgilerini getir"""
    return {
        'sheets': [
            {'name': 'Yönetici Özeti', 'description': 'KPI ve AI yorumları'},
            {'name': 'Kritik Ürünler', 'description': 'Yüksek riskli ürünler'},
            {'name': 'Tüm Sonuçlar', 'description': 'Detaylı sonuç tablosu'},
            {'name': 'AI Kararları', 'description': 'Ürün bazında AI kararları'},
            {'name': 'İşletme Hafızası', 'description': 'Learning Engine kuralları'},
            {'name': 'Teknik Analiz', 'description': 'CV, Pattern, ABC, XYZ, vb.'},
            {'name': 'AI Açıklamaları', 'description': 'Detaylı AI değerlendirmeleri'}
        ],
        'filename_format': 'safety_stock_rapor_{YYYYMMDD_HHMMSS}.xlsx'
    }