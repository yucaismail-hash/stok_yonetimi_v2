import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
from app.analysis.pattern import AdvancedDemandAnalyzer
from app.analysis.safety_stock import ComprehensiveSafetyStockOptimizer
from app.analysis.learning import LearningSystem

class ExcelProcessor:
    """Excel işleme ve öğrenme sınıfı"""
    
    def __init__(self):
        self.pattern_analyzer = AdvancedDemandAnalyzer()
        self.ss_optimizer = ComprehensiveSafetyStockOptimizer()
        self.learning_system = LearningSystem()
    
    def process_excel(self, file_path: str, user_id: int) -> Dict[str, Any]:
        """
        Excel dosyasını işle, öğren ve sonuçları döndür
        """
        # 1. Excel'i oku
        sheets = pd.read_excel(file_path, sheet_name=None, header=0)
        df_main = sheets.get('Temel_Veriler')
        if df_main is None:
            return {'success': False, 'error': "'Temel_Veriler' sheet'i bulunamadı"}
        
        # 2. W sütunlarını bul
        week_cols = self._find_week_columns(df_main.columns)
        if len(week_cols) < 12:
            return {'success': False, 'error': f'Yetersiz hafta: {len(week_cols)}'}
        
        # 3. Her malzeme için işlem yap
        results = []
        learning_data = []
        
        for idx, row in df_main.iterrows():
            material_code = str(row.get('Malzeme_Kodu', '')).strip()
            if not material_code:
                continue
            
            # Haftalık verileri al
            weekly_data = []
            for col in week_cols:
                val = row.get(col)
                try:
                    weekly_data.append(float(val) if pd.notna(val) else 0)
                except:
                    weekly_data.append(0)
            
            group = str(row.get('Mal_Grubu', 'GENEL'))
            lead_time = int(row.get('Termin_Suresi', 14) or 14)
            
            # Pattern analizi
            pattern, pattern_stats = self.pattern_analyzer.analyze_demand_pattern(weekly_data)
            
            # Safety Stock hesapla (6 metod)
            ss_results = self.ss_optimizer.calculate_all_methods(weekly_data, lead_time, 0.95)
            
            # Öğrenme verisi oluştur
            learning_key = f"{user_id}_{group}_{pattern}"
            
            # Sonuçları topla
            result_item = {
                'material_code': material_code,
                'group': group,
                'pattern': pattern,
                'pattern_stats': pattern_stats,
                'safety_stock': ss_results,
                'weekly_data': weekly_data[:8],  # Sadece ilk 8 haftayı sakla
                'lead_time_days': lead_time
            }
            results.append(result_item)
            
            # Öğrenme verisi
            learning_data.append({
                'key': learning_key,
                'group': group,
                'pattern': pattern,
                'multiplier': ss_results.get('hybrid_ss', 1.0) / (weekly_data[0] + 1) if weekly_data else 1.0
            })
        
        # 4. Öğrenme verilerini kaydet
        self._save_learning_data(user_id, learning_data)
        
        # 5. Sonuçları kullanıcıya özel kaydet (15 gün)
        self._save_analysis_results(user_id, results)
        
        return {
            'success': True,
            'total_materials': len(results),
            'results': results,
            'learning_updated': len(learning_data)
        }
    
    def _find_week_columns(self, columns) -> List[str]:
        """W sütunlarını bul"""
        week_cols = []
        for col in columns:
            col_str = str(col).strip().upper()
            if col_str.startswith('W') and len(col_str) > 1:
                if col_str[1:].isdigit():
                    week_cols.append(col)
        week_cols.sort(key=lambda x: int(str(x).upper()[1:]))
        return week_cols
    
    def _save_learning_data(self, user_id: int, learning_data: List[Dict]):
        """Öğrenme verilerini kaydet"""
        from app.database import SessionLocal
        from app.models import UserLearningData
        
        db = SessionLocal()
        try:
            for data in learning_data:
                existing = db.query(UserLearningData).filter(
                    UserLearningData.user_id == user_id,
                    UserLearningData.learning_key == data['key']
                ).first()
                
                if existing:
                    # Güncelle
                    existing.pattern_multiplier = (existing.pattern_multiplier * existing.sample_count + data['multiplier']) / (existing.sample_count + 1)
                    existing.sample_count += 1
                    existing.confidence = min(1.0, existing.sample_count / 50)
                else:
                    # Yeni kayıt
                    new_learning = UserLearningData(
                        user_id=user_id,
                        learning_key=data['key'],
                        pattern_multiplier=data['multiplier'],
                        seasonal_multiplier=1.0,
                        confidence=0.02,
                        sample_count=1
                    )
                    db.add(new_learning)
            db.commit()
        finally:
            db.close()
    
    def _save_analysis_results(self, user_id: int, results: List[Dict]):
        """Analiz sonuçlarını kaydet (15 gün)"""
        from app.database import SessionLocal
        from app.models import UserAnalysisResult
        import json
        
        db = SessionLocal()
        try:
            expires_at = datetime.utcnow() + timedelta(days=15)
            
            for result in results:
                # Önce eski kayıtları temizle (aynı malzeme için)
                db.query(UserAnalysisResult).filter(
                    UserAnalysisResult.user_id == user_id,
                    UserAnalysisResult.material_code == result['material_code']
                ).delete()
                
                new_result = UserAnalysisResult(
                    user_id=user_id,
                    result_type='excel_analysis',
                    material_code=result['material_code'],
                    material_group=result['group'],
                    result_data=result,
                    params={'lead_time_days': result['lead_time_days']},
                    expires_at=expires_at
                )
                db.add(new_result)
            db.commit()
        finally:
            db.close()
    
    def get_user_results(self, user_id: int, material_code: str = None) -> List[Dict]:
        """Kullanıcının kayıtlı sonuçlarını getir"""
        from app.database import SessionLocal
        from app.models import UserAnalysisResult
        
        db = SessionLocal()
        try:
            query = db.query(UserAnalysisResult).filter(
                UserAnalysisResult.user_id == user_id,
                UserAnalysisResult.expires_at > datetime.utcnow()
            )
            if material_code:
                query = query.filter(UserAnalysisResult.material_code == material_code)
            
            results = query.order_by(UserAnalysisResult.created_at.desc()).all()
            return [{'id': r.id, 'material_code': r.material_code, 'data': r.result_data, 'created_at': r.created_at} for r in results]
        finally:
            db.close()