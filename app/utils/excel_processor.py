import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from app.analysis.pattern import AdvancedDemandAnalyzer
from app.analysis.safety_stock import ComprehensiveSafetyStockOptimizer
from app.analysis.forecast import DemandForecaster
from app.simulation.monte_carlo import MonteCarloInventorySimulator
from app.analysis.learning import LearningSystem
from app.analysis.historical_learning import HistoricalLearningSystem
from app.analysis.supplier import SupplierPerformanceAnalyzer, SupplierShareOptimizer
from app.utils.excel_reader import ExcelReader

class ExcelProcessor:
    """
    Excel işleme ve tam entegre analiz motoru
    Çalışma Prensibi v1'e tam uyumlu - Mevcut kodlarla entegre
    """
    
    def __init__(self):
        self.pattern_analyzer = AdvancedDemandAnalyzer(days_per_week=6)
        self.ss_optimizer = ComprehensiveSafetyStockOptimizer(days_per_week=6)
        self.forecast_model = DemandForecaster(seasonal_periods=52)
        self.simulator = MonteCarloInventorySimulator(n_simulations=500)
        self.learning_system = LearningSystem()
        self.historical_learning = HistoricalLearningSystem()
        self.supplier_analyzer = SupplierPerformanceAnalyzer()
        self.supplier_optimizer = SupplierShareOptimizer(self.supplier_analyzer)
        self.reader = ExcelReader()
    
    def process_excel(self, file_path: str, user_id: int, 
                      mode: str = 'detailed') -> Dict[str, Any]:
        """
        Excel dosyasını işle, öğren ve sonuçları döndür
        
        Args:
            file_path: Excel dosya yolu
            user_id: Kullanıcı ID
            mode: 'quick' veya 'detailed'
        
        Returns:
            {
                'success': bool,
                'total_materials': int,
                'results': List[Dict],
                'learning_updated': int,
                'errors': List[str],
                'warnings': List[str]
            }
        """
        # 1. Excel'i oku ve doğrula
        read_result = self.reader.read_file(file_path)
        if not read_result['success']:
            return {
                'success': False,
                'error': read_result['errors'][0] if read_result['errors'] else 'Bilinmeyen hata',
                'warnings': read_result.get('warnings', [])
            }
        
        materials = read_result['data']['materials']
        supplier_mapping = read_result['data'].get('supplier_mapping', {})
        suppliers = read_result['data'].get('suppliers', {})
        week_cols = read_result['data']['week_columns']
        
        # 2. Tedarikçi verilerini yükle
        for supplier_id, supplier_data in suppliers.items():
            # SupplierPerformanceAnalyzer'a tedarikçi verilerini ekle
            if supplier_id not in self.supplier_analyzer.supplier_data:
                self.supplier_analyzer.supplier_data[supplier_id] = {
                    'delivery_history': [],
                    'quality_history': [],
                    'lead_time_history': [],
                    'risk_score': 1.0 - supplier_data.get('ontime_rate', 0.8),
                    'performance_score': supplier_data.get('ontime_rate', 0.8),
                    'supplier_factor': supplier_data.get('factor', 1.0)
                }
        
        # 3. Her malzeme için analiz yap
        results = []
        learning_data = []
        errors = []
        warnings = read_result['warnings'].copy()
        
        for material in materials:
            try:
                demand = material['historical_demand']
                lead_time = material['lead_time_days']
                group = material['group']
                material_code = material['code']
                
                # 3.1. Talep Paterni Analizi (pattern.py)
                pattern, pattern_stats = self.pattern_analyzer.analyze_demand_pattern(demand)
                
                # 3.2. 6 SS Metodu hesapla (safety_stock.py)
                ss_results = self.ss_optimizer.calculate_all_methods(
                    demand, lead_time, service_level=0.95
                )
                
                # 3.3. Tahmin (forecast.py)
                try:
                    forecast_result = self.forecast_model.forecast(
                        historical_data=demand,
                        horizon=4,
                        model_type="auto"
                    )
                except Exception as e:
                    forecast_result = {
                        'mean': [np.mean(demand[-4:]) if len(demand) >= 4 else np.mean(demand)] * 4,
                        'lower_80': [],
                        'upper_80': [],
                        'lower_95': [],
                        'upper_95': []
                    }
                    warnings.append(f"Forecast hatası ({material_code}): {str(e)}")
                
                # 3.4. Monte Carlo Simülasyonu (monte_carlo.py)
                n_sim = 100 if mode == 'quick' else 500
                sim_weeks = 13 if mode == 'quick' else 26
                
                # ROP hesapla
                avg_demand = np.mean(demand[-12:]) if len(demand) >= 12 else np.mean(demand)
                lead_time_demand = avg_demand * (lead_time / 7)
                hybrid_ss = ss_results.get('hybrid_ss', ss_results.get('classic_ss', 0))
                rop = lead_time_demand + hybrid_ss
                
                # Tedarikçi bilgilerini hazırla
                material_suppliers = supplier_mapping.get(material_code, [])
                supplier_list = []
                for ms in material_suppliers:
                    supp = suppliers.get(ms['supplier_id'])
                    if supp:
                        supplier_list.append({
                            'supplier_id': ms['supplier_id'],
                            'share': ms['share'],
                            'factor': supp.get('factor', 1.0),
                            'ontime_rate': supp.get('ontime_rate', 0.8),
                            'lt_mean': supp.get('lt_mean', lead_time),
                            'lt_std': supp.get('lt_std', lead_time * 0.2)
                        })
                
                # Simülasyonu çalıştır
                try:
                    sim_result = self.simulator.simulate(
                        initial_stock=material['initial_stock'],
                        lead_time_mean=lead_time,
                        lead_time_std=max(1, lead_time * 0.2),
                        demand_mean=avg_demand,
                        demand_std=np.std(demand[-12:]) if len(demand) >= 12 else np.std(demand),
                        eoq=material['eoq'],
                        rop=rop,
                        weeks=sim_weeks,
                        lead_time_dist='lognormal',
                        use_regime=mode == 'detailed' and len(demand) >= 24,
                        historical_demand=demand if len(demand) >= 24 else None,
                        use_copula=mode == 'detailed',
                        correlation=0.7,
                        use_adaptive_ss=mode == 'detailed',
                        target_service=0.95,
                        review_period=4,
                        inc_rate=0.08,
                        dec_rate=0.03
                    )
                except Exception as e:
                    sim_result = {
                        'service_level': 0,
                        'stockout_probability': [0.1] * sim_weeks,
                        'avg_stock': [material['initial_stock']] * sim_weeks,
                        'cvar_95': 0,
                        'regime_used': False,
                        'copula_used': False,
                        'adaptive_ss_used': False
                    }
                    warnings.append(f"Simülasyon hatası ({material_code}): {str(e)}")
                
                # 3.5. Optimizasyon parametreleri
                optimized_params = self._optimize_parameters(
                    material, pattern_stats, ss_results, sim_result
                )
                
                # 3.6. Tarihsel Öğrenme (historical_learning.py)
                try:
                    learning_result = self.historical_learning.learn_from_material(
                        material_code=material_code,
                        group=group,
                        weekly_data=demand,
                        lead_time_days=lead_time,
                        service_level=0.95
                    )
                    if learning_result.get('success', False):
                        learning_data.append({
                            'key': f"{user_id}_{group}_{pattern}",
                            'group': group,
                            'pattern': pattern,
                            'multiplier': optimized_params.get('pattern_multiplier', 1.0),
                            'ss_value': optimized_params.get('safety_stock', 0),
                            'service_level': sim_result.get('service_level', 0)
                        })
                except Exception as e:
                    warnings.append(f"Öğrenme hatası ({material_code}): {str(e)}")
                
                # 3.7. Tedarikçi optimizasyonu (supplier.py)
                supplier_optimization = None
                if supplier_list and len(supplier_list) > 1:
                    try:
                        current_shares = {s['supplier_id']: s['share'] for s in supplier_list}
                        candidates = self.supplier_optimizer.generate_candidates(
                            suppliers=supplier_list,
                            current_share_map=current_shares,
                            delta_min=0.02,
                            delta_max=0.15,
                            delta_step=0.01
                        )
                        supplier_optimization = {
                            'current_shares': current_shares,
                            'num_candidates': len(candidates),
                            'weighted_factor': self.supplier_optimizer.calculate_weighted_supplier_factor(supplier_list),
                            'weighted_risk': self.supplier_optimizer.calculate_weighted_risk_score(supplier_list)
                        }
                    except Exception as e:
                        warnings.append(f"Tedarikçi optimizasyon hatası ({material_code}): {str(e)}")
                
                # 3.8. Sonuçları topla
                result_item = {
                    'material_code': material_code,
                    'material': material,
                    'group': group,
                    'pattern': pattern,
                    'pattern_stats': pattern_stats,
                    'safety_stock_methods': ss_results,
                    'forecast': forecast_result,
                    'simulation': sim_result,
                    'optimized_params': optimized_params,
                    'supplier_optimization': supplier_optimization,
                    'lead_time_days': lead_time,
                    'week_data': demand[:52]
                }
                results.append(result_item)
                
            except Exception as e:
                errors.append(f"Malzeme {material.get('code', 'Bilinmeyen')}: {str(e)}")
                continue
        
        # 4. Öğrenme verilerini kaydet
        if learning_data:
            self._save_learning_data(user_id, learning_data)
        
        # 5. Analiz sonuçlarını kaydet (15 gün)
        self._save_analysis_results(user_id, results)
        
        return {
            'success': True,
            'total_materials': len(results),
            'results': results,
            'learning_updated': len(learning_data),
            'errors': errors,
            'warnings': warnings,
            'mode': mode
        }
    
    def _optimize_parameters(self, material: Dict, pattern_stats: Dict,
                            ss_results: Dict, sim_result: Dict) -> Dict:
        """Optimizasyon parametrelerini hesapla"""
        # Hybrid SS'yi ana SS olarak kullan
        safety_stock = ss_results.get('hybrid_ss', ss_results.get('classic_ss', 0))
        
        # Lead time demand
        avg_demand = np.mean(material['historical_demand']) if material['historical_demand'] else 0
        lead_time_demand = avg_demand * (material['lead_time_days'] / 7)
        
        # ROP
        rop = lead_time_demand + safety_stock
        
        # EOQ optimizasyonu
        current_eoq = material['eoq']
        optimal_eoq = current_eoq
        if material['unit_cost'] > 0 and material['holding_rate'] > 0:
            annual_demand = avg_demand * 52
            order_cost = 50
            holding_cost = material['unit_cost'] * material['holding_rate']
            if holding_cost > 0:
                optimal_eoq = int(np.sqrt((2 * annual_demand * order_cost) / holding_cost))
                optimal_eoq = max(10, min(optimal_eoq, 10000))
        
        # Risk seviyesi
        stockout_prob = np.mean(sim_result.get('stockout_probability', [0]))
        if stockout_prob < 0.02:
            risk_level = 'DÜŞÜK'
        elif stockout_prob < 0.07:
            risk_level = 'ORTA'
        else:
            risk_level = 'YÜKSEK'
        
        # Pattern multiplier
        cv = pattern_stats.get('cv', 0)
        if cv > 0.7:
            pattern_multiplier = 1.3
        elif cv > 0.4:
            pattern_multiplier = 1.15
        else:
            pattern_multiplier = 1.0
        
        return {
            'safety_stock': round(safety_stock, 2),
            'optimal_rop': round(rop, 2),
            'lead_time_demand': round(lead_time_demand, 2),
            'optimal_eoq': optimal_eoq,
            'recommended_initial_stock': max(material['initial_stock'], rop + 10),
            'risk_level': risk_level,
            'pattern_multiplier': pattern_multiplier,
            'service_level_achieved': sim_result.get('service_level', 0)
        }
    
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
                    total_samples = existing.sample_count + 1
                    existing.pattern_multiplier = (
                        (existing.pattern_multiplier * existing.sample_count + data['multiplier']) / total_samples
                    )
                    existing.sample_count = total_samples
                    existing.confidence = min(1.0, total_samples / 50)
                else:
                    new_learning = UserLearningData(
                        user_id=user_id,
                        learning_key=data['key'],
                        pattern_multiplier=data['multiplier'],
                        seasonal_multiplier=1.0,
                        confidence=0.02,
                        sample_count=1,
                        pattern=data['pattern']
                    )
                    db.add(new_learning)
            db.commit()
        finally:
            db.close()
    
    def _save_analysis_results(self, user_id: int, results: List[Dict]):
        """Analiz sonuçlarını kaydet (15 gün)"""
        from app.database import SessionLocal
        from app.models import UserAnalysisResult
        
        db = SessionLocal()
        try:
            expires_at = datetime.utcnow() + timedelta(days=15)
            
            for result in results:
                # Eski kayıtları temizle
                db.query(UserAnalysisResult).filter(
                    UserAnalysisResult.user_id == user_id,
                    UserAnalysisResult.material_code == result['material_code']
                ).delete()
                
                summary_data = {
                    'pattern': result['pattern'],
                    'pattern_stats': result['pattern_stats'],
                    'safety_stock': result['optimized_params']['safety_stock'],
                    'optimal_eoq': result['optimized_params']['optimal_eoq'],
                    'optimal_rop': result['optimized_params']['optimal_rop'],
                    'risk_level': result['optimized_params']['risk_level'],
                    'service_level': result['simulation'].get('service_level', 0),
                    'ss_methods': result['safety_stock_methods'],
                    'forecast': result['forecast'],
                    'supplier_optimization': result.get('supplier_optimization')
                }
                
                new_result = UserAnalysisResult(
                    user_id=user_id,
                    result_type='excel_analysis_v2',
                    material_code=result['material_code'],
                    material_group=result['group'],
                    result_data=summary_data,
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
            return [
                {
                    'id': r.id,
                    'material_code': r.material_code,
                    'data': r.result_data,
                    'created_at': r.created_at
                }
                for r in results
            ]
        finally:
            db.close()


# ============================================
# ✅ process_excel FONKSİYONU (upload.py için)
# ============================================

def process_excel(file_content: bytes) -> Dict[str, Any]:
    """
    Excel dosyasını işle ve malzeme verilerini döndür (Basit versiyon)
    
    Args:
        file_content: Excel dosyasının bytes içeriği
    
    Returns:
        {
            'materials': List[Dict],
            'supplier_mapping': Dict,
            'suppliers': Dict,
            'week_columns': List[str]
        }
    """
    import tempfile
    import os
    
    reader = ExcelReader()
    
    # Bytes'i geçici dosyaya yaz
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        tmp.write(file_content)
        temp_path = tmp.name
    
    try:
        # Excel'i oku
        read_result = reader.read_file(temp_path)
        
        if not read_result['success']:
            raise ValueError(read_result.get('errors', ['Dosya okunamadı'])[0])
        
        data = read_result['data']
        
        return {
            'materials': data.get('materials', []),
            'supplier_mapping': data.get('supplier_mapping', {}),
            'suppliers': data.get('suppliers', {}),
            'week_columns': data.get('week_columns', [])
        }
    finally:
        # Geçici dosyayı temizle
        if os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass


def process_excel_detailed(file_path: str, user_id: int, mode: str = 'detailed') -> Dict[str, Any]:
    """
    Excel dosyasını detaylı işle (ExcelProcessor sınıfını kullanarak)
    
    Args:
        file_path: Excel dosya yolu
        user_id: Kullanıcı ID
        mode: 'quick' veya 'detailed'
    
    Returns:
        Dict: İşlem sonuçları
    """
    processor = ExcelProcessor()
    return processor.process_excel(file_path, user_id, mode)