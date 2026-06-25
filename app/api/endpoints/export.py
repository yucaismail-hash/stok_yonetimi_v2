from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any
from app.utils.excel_exporter import ExcelExporter
from app.auth import get_current_user
from app.models import User
import io
import pandas as pd
import numpy as np  # ✅ BUNU EKLE
from datetime import datetime

router = APIRouter()
exporter = ExcelExporter()


@router.post("/export/recommendations")
def export_recommendations(
    material_code: str,
    material_data: Dict[str, Any],
    simulation_result: Dict[str, Any],
    ai_analysis: Dict[str, Any],
    optimized_params: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Malzeme önerilerini Excel dosyası olarak dışa aktar
    """
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
    """
    Tüm malzemeler için toplu rapor oluştur
    """
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


# ✅ YENİ: Pattern sonuçlarını Excel'e aktar
@router.post("/export/pattern-results")
def export_pattern_results(
    data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Pattern analizi sonuçlarını Excel olarak dışa aktar
    """
    try:
        results = data.get('results', [])
        if not results:
            raise HTTPException(status_code=400, detail="Aktarılacak sonuç yok")
        
        # DataFrame oluştur
        df = pd.DataFrame(results)
        
        # Excel dosyası oluştur
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Ana veri sayfası
            df.to_excel(writer, sheet_name='Pattern Analizi', index=False)
            
            # Özet sayfası
            pattern_counts = df['pattern'].value_counts().to_dict()
            summary = {
                'Toplam Malzeme': len(results),
                'Analiz Tarihi': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'Pattern Dağılımı': str(pattern_counts)
            }
            summary_df = pd.DataFrame([summary])
            summary_df.to_excel(writer, sheet_name='Özet', index=False)
            
            # Pattern dağılımı detay
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


# ✅ YENİ: Safety Stock sonuçlarını Excel'e aktar
@router.post("/export/safety-stock-results")
def export_safety_stock_results(
    data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Safety Stock analizi sonuçlarını Excel olarak dışa aktar
    """
    try:
        results = data.get('results', [])
        if not results:
            raise HTTPException(status_code=400, detail="Aktarılacak sonuç yok")
        
        df = pd.DataFrame(results)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Safety Stock', index=False)
            
            # Özet
            summary = {
                'Toplam Malzeme': len(results),
                'Analiz Tarihi': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'Ortalama Hybrid SS': df['hybrid_ss'].mean() if 'hybrid_ss' in df.columns else 0
            }
            summary_df = pd.DataFrame([summary])
            summary_df.to_excel(writer, sheet_name='Özet', index=False)
        
        output.seek(0)
        
        filename = f"safety_stock_analiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ✅ YENİ: Forecast sonuçlarını Excel'e aktar
@router.post("/export/forecast-results")
def export_forecast_results(
    data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Forecast sonuçlarını zengin Excel olarak dışa aktar
    """
    try:
        results = data.get('results', [])
        if not results:
            raise HTTPException(status_code=400, detail="Aktarılacak sonuç yok")
        
        print(f"✅ {len(results)} forecast sonucu aktarılıyor...")
        
        model_labels = {
            'holt_winters': 'Holt-Winters (Mevsimsel)',
            'arima': 'ARIMA (Otoregresif)',
            'simple': 'Basit (MA+Trend)',
            'auto': 'Otomatik Seçim'
        }
        
        def get_mape_status(mape):
            if mape is None or mape >= 999: return "Hesaplanamadı"
            if mape < 20: return "Mükemmel"
            elif mape < 30: return "İyi"
            elif mape < 50: return "Orta"
            elif mape < 100: return "Zayıf"
            else: return "Çok Zayıf"

        def get_mape_advice(mape):
            if mape is None or mape >= 999: return "Veri yetersiz, daha fazla veri ekleyin."
            if mape < 20: return "Stok yönetimi için ideal, mevcut model başarılı."
            elif mape < 30: return "Kabul edilebilir, periyodik kontrol önerilir."
            elif mape < 50: return "Model iyileştirilebilir, daha fazla veri ekleyin."
            elif mape < 100: return "Tahmin modeli gözden geçirilmeli, alternatif modeller denenmeli."
            else: return "Veri kalitesi veya model seçimi hatalı. Uzman desteği alın."

        rows = []
        for r in results:
            forecast_vals = r.get('forecast', [])
            lower_80 = r.get('lower_80', [])
            upper_80 = r.get('upper_80', [])
            lower_95 = r.get('lower_95', [])
            upper_95 = r.get('upper_95', [])
            mape = r.get('model_rmse')
            selected_model = r.get('selected_model', 'unknown')
            
            row = {
                'Malzeme Kodu': r.get('material_code', ''),
                'Malzeme Grubu': r.get('group', ''),
                'Seçilen Model': model_labels.get(selected_model, selected_model),
                'Seçim Nedeni': r.get('selection_reason', ''),
                'Model Açıklaması': r.get('model_description', ''),
                'Trend Yönü': r.get('trend_direction', ''),
                'Trend Yüzdesi': f"{r.get('trend_percent', 0):.1f}%",
                'MAPE (%)': f"{mape:.1f}" if mape and mape < 999 else 'Hesaplanamadı',
                'MAPE Seviyesi': get_mape_status(mape),
                'Tavsiye': get_mape_advice(mape)
            }
            
            for i, val in enumerate(forecast_vals):
                row[f'{i+1}. Hafta Tahmin'] = round(val, 1) if val else None
                row[f'%80 Alt'] = round(lower_80[i], 1) if i < len(lower_80) else None
                row[f'%80 Üst'] = round(upper_80[i], 1) if i < len(upper_80) else None
                row[f'%95 Alt'] = round(lower_95[i], 1) if i < len(lower_95) else None
                row[f'%95 Üst'] = round(upper_95[i], 1) if i < len(upper_95) else None
            
            comparison = r.get('model_comparison', {})
            for model_name, model_data in comparison.items():
                model_label = {
                    'holt_winters': 'Holt-Winters RMSE',
                    'arima': 'ARIMA RMSE',
                    'simple': 'Basit MA RMSE',
                    'auto': 'Otomatik RMSE'
                }.get(model_name, f'{model_name} RMSE')
                row[model_label] = model_data.get('rmse', '-')
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Forecast Analizi', index=False)
            
            if results:
                model_counts = {}
                rmse_values = []
                for r in results:
                    model = r.get('selected_model', 'unknown')
                    model_label = model_labels.get(model, model)
                    model_counts[model_label] = model_counts.get(model_label, 0) + 1
                    rmse = r.get('model_rmse')
                    if rmse and rmse < 999:
                        rmse_values.append(rmse)
                
                summary = {
                    'Toplam Malzeme': len(results),
                    'En Çok Seçilen Model': results[0].get('best_model_label', '-') if results else '-',
                    'Ortalama MAPE': f"{sum(rmse_values) / len(rmse_values):.1f}%" if rmse_values else 'Hesaplanamadı',
                    'Artış Trendi Olan': len([r for r in results if r.get('trend_direction') == 'Artış']),
                    'Azalış Trendi Olan': len([r for r in results if r.get('trend_direction') == 'Azalış']),
                    'Analiz Tarihi': datetime.now().strftime('%Y-%m-%d %H:%M')
                }
                summary_df = pd.DataFrame([summary])
                summary_df.to_excel(writer, sheet_name='Özet', index=False)
                
                if model_counts:
                    model_df = pd.DataFrame([
                        {'Model': k, 'Malzeme Sayısı': v, 'Yüzde': f"{v/len(results)*100:.1f}%"} 
                        for k, v in model_counts.items()
                    ])
                    model_df.to_excel(writer, sheet_name='Model Dağılımı', index=False)
        
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

@router.get("/export/format-info")
def get_export_info():
    """Export format bilgilerini getir"""
    return {
        'sheets': [
            {'name': 'Özet', 'description': 'Genel özet bilgiler'},
            {'name': 'Detaylı Analiz', 'description': 'Detaylı istatistikler ve metod karşılaştırmaları'},
            {'name': 'Haftalık Talep', 'description': 'Tüm haftaların talep verileri'},
            {'name': 'Simülasyon Sonuçları', 'description': 'Simülasyon çıktıları'},
            {'name': 'Tedarikçi Bilgileri', 'description': 'Tedarikçi pay ve performans bilgileri'},
            {'name': 'Aksiyon Planı', 'description': 'Adım adım uygulama planı'}
        ],
        'filename_format': 'oneri_{material_code}_{YYYYMMDD_HHMMSS}.xlsx'
    }

@router.post("/export/forecast-results")
def export_forecast_results(
    data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Forecast sonuçlarını zengin Excel olarak dışa aktar
    """
    try:
        results = data.get('results', [])
        if not results:
            raise HTTPException(status_code=400, detail="Aktarılacak sonuç yok")
        
        print(f"✅ {len(results)} forecast sonucu aktarılıyor...")
        
        model_labels = {
            'holt_winters': 'Holt-Winters (Mevsimsel)',
            'arima': 'ARIMA (Otoregresif)',
            'simple': 'Basit (MA+Trend)',
            'auto': 'Otomatik Seçim'
        }
        
        def get_mape_status(mape):
            if mape is None or mape >= 999: return "Hesaplanamadı"
            if mape < 20: return "Mükemmel"
            elif mape < 30: return "İyi"
            elif mape < 50: return "Orta"
            elif mape < 100: return "Zayıf"
            else: return "Çok Zayıf"

        def get_mape_advice(mape):
            if mape is None or mape >= 999: return "Veri yetersiz, daha fazla veri ekleyin."
            if mape < 20: return "Stok yönetimi için ideal, mevcut model başarılı."
            elif mape < 30: return "Kabul edilebilir, periyodik kontrol önerilir."
            elif mape < 50: return "Model iyileştirilebilir, daha fazla veri ekleyin."
            elif mape < 100: return "Tahmin modeli gözden geçirilmeli, alternatif modeller denenmeli."
            else: return "Veri kalitesi veya model seçimi hatalı. Uzman desteği alın."

        rows = []
        for r in results:
            forecast_vals = r.get('forecast', [])
            lower_80 = r.get('lower_80', [])
            upper_80 = r.get('upper_80', [])
            lower_95 = r.get('lower_95', [])
            upper_95 = r.get('upper_95', [])
            mape = r.get('model_rmse')
            selected_model = r.get('selected_model', 'unknown')
            outlier_info = r.get('outlier_info', {})
            model_params = r.get('model_params', {})
            
            row = {
                'Malzeme Kodu': r.get('material_code', ''),
                'Malzeme Grubu': r.get('group', ''),
                'Seçilen Model': model_labels.get(selected_model, selected_model),
                'Seçim Nedeni': r.get('selection_reason', ''),
                'Model Açıklaması': r.get('model_description', ''),
                'Trend Yönü': r.get('trend_direction', ''),
                'Trend Yüzdesi': f"{r.get('trend_percent', 0):.1f}%",
                'MAPE (%)': f"{mape:.1f}" if mape and mape < 999 else 'Hesaplanamadı',
                'MAPE Seviyesi': get_mape_status(mape),
                'Tavsiye': get_mape_advice(mape),
                'Aykırı Değer Var mı?': 'Evet' if outlier_info.get('has_outliers') else 'Hayır',
                'Aykırı Değer Sayısı': outlier_info.get('outlier_count', 0),
                'Aykırı Değerler (Hafta:Değer)': ', '.join([f"{o.get('week', '?')}:{o.get('value', '?')}" for o in outlier_info.get('outliers', [])]) if outlier_info.get('outliers') else '-',
                'Model Parametreleri': str(model_params) if model_params else '-'
            }
            
            # Tahmin değerleri
            for i, val in enumerate(forecast_vals):
                row[f'{i+1}. Hafta Tahmin'] = round(val, 1) if val else None
                row[f'%80 Alt'] = round(lower_80[i], 1) if i < len(lower_80) else None
                row[f'%80 Üst'] = round(upper_80[i], 1) if i < len(upper_80) else None
                row[f'%95 Alt'] = round(lower_95[i], 1) if i < len(lower_95) else None
                row[f'%95 Üst'] = round(upper_95[i], 1) if i < len(upper_95) else None
            
            # Model Karşılaştırma
            comparison = r.get('model_comparison', {})
            for model_name, model_data in comparison.items():
                model_label = {
                    'holt_winters': 'Holt-Winters RMSE',
                    'arima': 'ARIMA RMSE',
                    'simple': 'Basit MA RMSE',
                    'auto': 'Otomatik RMSE'
                }.get(model_name, f'{model_name} RMSE')
                row[model_label] = model_data.get('rmse', '-')
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Forecast Analizi', index=False)
            
            if results:
                model_counts = {}
                rmse_values = []
                outlier_count = 0
                for r in results:
                    model = r.get('selected_model', 'unknown')
                    model_label = model_labels.get(model, model)
                    model_counts[model_label] = model_counts.get(model_label, 0) + 1
                    rmse = r.get('model_rmse')
                    if rmse and rmse < 999:
                        rmse_values.append(rmse)
                    if r.get('outlier_info', {}).get('has_outliers'):
                        outlier_count += 1
                
                summary = {
                    'Toplam Malzeme': len(results),
                    'En Çok Seçilen Model': results[0].get('best_model_label', '-') if results else '-',
                    'Ortalama MAPE': f"{sum(rmse_values) / len(rmse_values):.1f}%" if rmse_values else 'Hesaplanamadı',
                    'Artış Trendi Olan': len([r for r in results if r.get('trend_direction') == 'Artış']),
                    'Azalış Trendi Olan': len([r for r in results if r.get('trend_direction') == 'Azalış']),
                    'Aykırı Değer Olan Malzeme': outlier_count,
                    'Analiz Tarihi': datetime.now().strftime('%Y-%m-%d %H:%M')
                }
                summary_df = pd.DataFrame([summary])
                summary_df.to_excel(writer, sheet_name='Özet', index=False)
                
                if model_counts:
                    model_df = pd.DataFrame([
                        {'Model': k, 'Malzeme Sayısı': v, 'Yüzde': f"{v/len(results)*100:.1f}%"} 
                        for k, v in model_counts.items()
                    ])
                    model_df.to_excel(writer, sheet_name='Model Dağılımı', index=False)
        
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
    
# export.py - Tam export_simulation_results ve export_backtest_results

@router.post("/export/simulation-results")
def export_simulation_results(
    data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Simülasyon sonuçlarını zengin Excel olarak dışa aktar
    """
    try:
        results = data.get('results', [])
        config = data.get('config', {})
        raw_materials = data.get('raw_materials', [])
        
        if not results:
            raise HTTPException(status_code=400, detail="Aktarılacak sonuç yok")
        
        df_results = pd.DataFrame(results)
        
        # Tavsiye sütununu düzenle
        if 'recommendations' in df_results.columns:
            df_results['Tavsiyeler'] = df_results['recommendations'].apply(
                lambda x: '\n'.join(x) if isinstance(x, list) and x else x if isinstance(x, str) else '-'
            )
            df_results = df_results.drop(columns=['recommendations'])
        
        # ROP bilgileri
        if 'current_rop' in df_results.columns and 'recommended_rop' in df_results.columns:
            df_results['Mevcut ROP'] = df_results['current_rop']
            df_results['Önerilen ROP'] = df_results['recommended_rop']
            df_results['ROP Değişim'] = df_results['recommended_rop'] - df_results['current_rop']
            df_results = df_results.drop(columns=['current_rop', 'recommended_rop'])
        
        # Sütun adlarını Türkçe yap
        column_map = {
            'material_code': 'Malzeme Kodu',
            'group': 'Malzeme Grubu',
            'service_level': 'Servis Seviyesi (%)',
            'cvar_95': 'CVaR95 (En Kötü %5 Olasılıkla)',
            'tail_risk': 'Kuyruk Riski (Tail Risk)',
            'tail_risk_level': 'Kuyruk Risk Seviyesi',
            'cvar_risk': 'CVaR Risk Durumu',
            'service_gap': 'Servis Seviyesi Açığı (%)',
            'stockout_probability': 'Stok Tükenme Olasılığı (%)',
            'avg_stock': 'Ortalama Stok Seviyesi',
            'regime_used': 'Rejim Modeli Aktif',
            'copula_used': 'Copula Modeli Aktif',
            'adaptive_ss_used': 'Adaptif SS Aktif',
            'current_rop': 'Mevcut ROP',
            'recommended_rop': 'Önerilen ROP',
            'rop_change': 'ROP Değişimi',
            'recommendations': 'Tavsiye'
        }
        df_results = df_results.rename(columns=column_map)
        
        # Excel oluştur
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_results.to_excel(writer, sheet_name='Simülasyon Sonuçları', index=False)
            
            # Özet İstatistikler
            if 'Servis Seviyesi (%)' in df_results.columns:
                summary = {
                    'Toplam Malzeme': len(df_results),
                    'Ortalama Servis Seviyesi': f"{df_results['Servis Seviyesi (%)'].mean():.1f}%",
                    'Min Servis Seviyesi': f"{df_results['Servis Seviyesi (%)'].min():.1f}%",
                    'Max Servis Seviyesi': f"{df_results['Servis Seviyesi (%)'].max():.1f}%",
                    'Ortalama ROP Değişim': df_results['ROP Değişim'].mean() if 'ROP Değişim' in df_results.columns else 0,
                    'Analiz Tarihi': datetime.now().strftime('%Y-%m-%d %H:%M')
                }
                summary_df = pd.DataFrame([summary])
                summary_df.to_excel(writer, sheet_name='Özet', index=False)
            
            # Model Kullanım İstatistikleri
            if 'Rejim Aktif' in df_results.columns:
                model_stats = {
                    'Model': ['Rejim', 'Copula', 'Adaptif SS'],
                    'Aktif Malzeme': [
                        df_results[df_results['Rejim Aktif'] == True].shape[0],
                        df_results[df_results['Copula Aktif'] == True].shape[0],
                        df_results[df_results['Adaptif SS Aktif'] == True].shape[0]
                    ],
                    'Toplam Malzeme': [len(df_results)] * 3
                }
                model_df = pd.DataFrame(model_stats)
                model_df.to_excel(writer, sheet_name='Model Kullanımı', index=False)
        
        output.seek(0)
        filename = f"simulasyon_analiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return StreamingResponse(output, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={'Content-Disposition': f'attachment; filename={filename}'})
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/export/backtest-results")
def export_backtest_results(
    data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Backtest sonuçlarını zengin Excel olarak dışa aktar
    """
    try:
        results = data.get('results', [])
        if not results:
            raise HTTPException(status_code=400, detail="Aktarılacak sonuç yok")
        
        df = pd.DataFrame(results)
        
        # Servis seviyesini yüzdeye çevir
        if 'service_level' in df.columns:
            df['service_level'] = df['service_level'].apply(lambda x: round(x * 100, 1) if x else 0)
        
        # ROP bilgileri
        if 'current_rop' in df.columns and 'recommended_rop' in df.columns:
            df['Mevcut ROP'] = df['current_rop']
            df['Önerilen ROP'] = df['recommended_rop']
            df['ROP Değişim'] = df['recommended_rop'] - df['current_rop']
            df = df.drop(columns=['current_rop', 'recommended_rop'])
        
        # Tavsiyeyi düzenle
        if 'recommendation' in df.columns:
            df['Tavsiye'] = df['recommendation'].apply(
                lambda x: '\n'.join(x.split(' | ')) if isinstance(x, str) else '-'
            )
            df = df.drop(columns=['recommendation'])
        
        # Sütun adlarını Türkçe yap
        # export.py - export_backtest_results içinde

        column_map = {
            'material_code': 'Malzeme Kodu',
            'group': 'Malzeme Grubu',
            'best_strategy': 'En İyi Strateji',
            'service_level': 'Servis Seviyesi (%)',
            'total_cost': 'Toplam Maliyet (TL)',
            'holding_cost': 'Stok Tutma Maliyeti (TL)',
            'shortage_cost': 'Stok Tükenme Maliyeti (TL)',
            'stockout_probability': 'Stok Tükenme Olasılığı (%)',  # ✅ Anlamlı başlık
            'tail_risk': 'Kuyruk Riski (Tail Risk)',              # ✅ Anlamlı başlık
            'tail_risk_level': 'Kuyruk Risk Seviyesi',            # ✅ Anlamlı başlık
            'total_shortage': 'Toplam Stok Tükenme (Birim)',      # ✅ Anlamlı başlık
            'strategies_tested': 'Test Edilen Strateji Sayısı',
            'current_rop': 'Mevcut ROP',
            'recommended_rop': 'Önerilen ROP',
            'rop_change': 'ROP Değişimi',
            'recommendation': 'Tavsiye'
        }
        df = df.rename(columns=column_map)
        
        # Excel oluştur
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Backtest Sonuçları', index=False)
            
            # Özet
            if 'Servis Seviyesi (%)' in df.columns:
                summary = {
                    'Toplam Malzeme': len(df),
                    'Ortalama Servis Seviyesi': f"{df['Servis Seviyesi (%)'].mean():.1f}%",
                    'Min Servis Seviyesi': f"{df['Servis Seviyesi (%)'].min():.1f}%",
                    'Max Servis Seviyesi': f"{df['Servis Seviyesi (%)'].max():.1f}%",
                    'En Çok Kullanılan Strateji': df['En İyi Strateji'].mode()[0] if 'En İyi Strateji' in df.columns else '-',
                    'Ortalama ROP Değişim': df['ROP Değişim'].mean() if 'ROP Değişim' in df.columns else 0,
                    'Analiz Tarihi': datetime.now().strftime('%Y-%m-%d %H:%M')
                }
                summary_df = pd.DataFrame([summary])
                summary_df.to_excel(writer, sheet_name='Özet', index=False)
            
            # Strateji Dağılımı
            if 'En İyi Strateji' in df.columns:
                strategy_dist = df['En İyi Strateji'].value_counts().reset_index()
                strategy_dist.columns = ['Strateji', 'Malzeme Sayısı']
                strategy_dist.to_excel(writer, sheet_name='Strateji Dağılımı', index=False)
        
        output.seek(0)
        filename = f"backtest_analiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return StreamingResponse(output, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={'Content-Disposition': f'attachment; filename={filename}'})
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/export/supplier-results")
def export_supplier_results(
    data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Tedarikçi analizi sonuçlarını Excel olarak dışa aktar
    """
    try:
        suppliers = data.get('suppliers', [])
        recommendations = data.get('recommendations', [])
        
        if not suppliers:
            raise HTTPException(status_code=400, detail="Aktarılacak sonuç yok")
        
        print(f"✅ {len(suppliers)} tedarikçi, {len(recommendations)} tavsiye aktarılıyor...")
        
        # DataFrame
        df = pd.DataFrame(suppliers)
        
        # Sütun adlarını Türkçe yap
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
        
        # Risk skorunu yüzdeye çevir
        if 'Risk Skoru' in df.columns:
            df['Risk Skoru'] = df['Risk Skoru'].apply(lambda x: f"{x*100:.1f}%")
        if 'Performans Skoru' in df.columns:
            df['Performans Skoru'] = df['Performans Skoru'].apply(lambda x: f"{x*100:.1f}%")
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Tedarikçi Analizi', index=False)
            
            # Özet
            risk_high = len([s for s in suppliers if s.get('risk_score', 1) >= 0.4])
            risk_medium = len([s for s in suppliers if 0.2 <= s.get('risk_score', 0.5) < 0.4])
            risk_low = len([s for s in suppliers if s.get('risk_score', 0) < 0.2])
            
            # ✅ np.mean kullanımı düzeltildi
            avg_risk = np.mean([s.get('risk_score', 0) for s in suppliers]) if suppliers else 0
            avg_perf = np.mean([s.get('performance_score', 0) for s in suppliers]) if suppliers else 0
            
            summary = {
                'Toplam Tedarikçi': len(suppliers),
                'Düşük Risk Tedarikçi': risk_low,
                'Orta Risk Tedarikçi': risk_medium,
                'Yüksek Risk Tedarikçi': risk_high,
                'Ortalama Risk Skoru': f"{avg_risk*100:.1f}%",
                'Ortalama Performans': f"{avg_perf*100:.1f}%",
                'Analiz Tarihi': datetime.now().strftime('%Y-%m-%d %H:%M')
            }
            summary_df = pd.DataFrame([summary])
            summary_df.to_excel(writer, sheet_name='Özet', index=False)
            
            # Tavsiyeler
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
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
