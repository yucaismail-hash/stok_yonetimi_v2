from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any  # YENİ - eklendi
from app.utils.excel_exporter import ExcelExporter
from app.auth import get_current_user
from app.models import User
import io

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