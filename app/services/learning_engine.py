# app/services/learning_engine.py
# Learning Engine - Şirket davranış kalıplarını öğrenen servis

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.models import CompanyLearningMemory, AnalysisResult, UserLearningData
from app.database import SessionLocal

logger = logging.getLogger(__name__)


class LearningEngine:
    """
    Learning Engine - Şirketin geçmiş analizlerini inceleyerek
    davranış kalıplarını tespit eder ve güven skorlarını hesaplar.
    
    Bu servis tamamen Stokonomi'ye aittir, LLM değildir.
    Gemini'nin arkasında çalışır.
    """
    
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        
        # Kural tipleri
        self.RULE_TYPES = {
            'seasonal': 'Mevsimsel Davranış',
            'intermittent': 'Aralıklı Talep',
            'lead_time': 'Lead Time Davranışı',
            'trend': 'Trend Davranışı',
            'supplier': 'Tedarikçi Davranışı',
            'successful_method': 'Başarılı Yöntem'
        }
    
    def analyze_and_learn(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Yeni bir analiz sonucunu işleyerek öğrenme yapar.
        
        Args:
            analysis_result: Yeni analiz sonucu (JSON)
            
        Returns:
            {
                'new_rules': [...],
                'updated_rules': [...],
                'confidence_scores': {...}
            }
        """
        try:
            result_type = analysis_result.get('result_type', '')
            results_data = analysis_result.get('data', {})
            results_list = results_data.get('results', [])
            
            if not results_list:
                return {'new_rules': [], 'updated_rules': [], 'confidence_scores': {}}
            
            # 1. Mevcut kuralları al
            existing_rules = self._get_existing_rules()
            
            # 2. Yeni davranışları tespit et
            detected_patterns = self._detect_patterns(results_list, result_type)
            
            # 3. Mevcut kuralları güncelle veya yeni kural oluştur
            updated_rules = []
            new_rules = []
            
            for pattern in detected_patterns:
                rule_id = pattern.get('rule_id')
                existing = existing_rules.get(rule_id)
                
                if existing:
                    # Mevcut kuralı güncelle
                    updated = self._update_rule(existing, pattern)
                    updated_rules.append(updated)
                else:
                    # Yeni kural oluştur
                    new_rule = self._create_rule(pattern)
                    new_rules.append(new_rule)
            
            # 4. Güven skorlarını güncelle
            confidence_scores = self._update_confidence_scores(new_rules + updated_rules)
            
            # 5. Değişiklikleri kaydet
            self.db.commit()
            
            return {
                'new_rules': new_rules,
                'updated_rules': updated_rules,
                'confidence_scores': confidence_scores
            }
            
        except Exception as e:
            logger.error(f"❌ Learning Engine hatası: {e}")
            self.db.rollback()
            return {'error': str(e)}
    
    def _get_existing_rules(self) -> Dict[str, CompanyLearningMemory]:
        """Mevcut kuralları getirir"""
        rules = self.db.query(CompanyLearningMemory).filter(
            CompanyLearningMemory.user_id == self.user_id,
            CompanyLearningMemory.is_active == True
        ).all()
        
        return {rule.rule_id: rule for rule in rules}
    
    def _detect_patterns(self, results: List[Dict], result_type: str) -> List[Dict]:
        """
        Analiz sonuçlarından davranış kalıplarını tespit eder.
        """
        patterns = []
        
        # 1. Mevsimsel Kalıplar
        seasonal_patterns = self._detect_seasonal_patterns(results)
        patterns.extend(seasonal_patterns)
        
        # 2. Aralıklı Talep Kalıpları
        intermittent_patterns = self._detect_intermittent_patterns(results)
        patterns.extend(intermittent_patterns)
        
        # 3. Trend Kalıpları
        trend_patterns = self._detect_trend_patterns(results)
        patterns.extend(trend_patterns)
        
        # 4. Başarılı Yöntem Kalıpları
        method_patterns = self._detect_method_patterns(results, result_type)
        patterns.extend(method_patterns)
        
        # 5. Lead Time Kalıpları
        lead_time_patterns = self._detect_lead_time_patterns(results)
        patterns.extend(lead_time_patterns)
        
        return patterns
    
    def _detect_seasonal_patterns(self, results: List[Dict]) -> List[Dict]:
        """
        Mevsimsel davranış kalıplarını tespit eder.
        """
        patterns = []
        
        # Gruplara göre mevsimsel analiz
        group_seasonal = {}
        
        for result in results:
            group = result.get('group', 'GENEL')
            has_seasonality = result.get('has_seasonality', False)
            seasonality_strength = result.get('seasonality_strength', 0)
            
            if has_seasonality and seasonality_strength > 0.3:
                if group not in group_seasonal:
                    group_seasonal[group] = {
                        'count': 0,
                        'total_strength': 0,
                        'materials': []
                    }
                group_seasonal[group]['count'] += 1
                group_seasonal[group]['total_strength'] += seasonality_strength
                group_seasonal[group]['materials'].append(result.get('material_code', ''))
        
        # Her grup için kural oluştur
        for group, data in group_seasonal.items():
            if data['count'] >= 3:  # En az 3 ürün
                avg_strength = data['total_strength'] / data['count']
                rule_id = f"seasonal_{group.lower()}"
                
                patterns.append({
                    'rule_id': rule_id,
                    'rule_name': f"{group} Grubu Mevsimsel Talep",
                    'rule_type': 'seasonal',
                    'description': f"{group} grubunda mevsimsel talep artışı tespit edildi. {data['count']} üründe ortalama {avg_strength:.2f} güç.",
                    'pattern_data': {
                        'group': group,
                        'material_count': data['count'],
                        'avg_strength': avg_strength,
                        'materials': data['materials']
                    },
                    'confidence': min(0.9, 0.3 + (data['count'] / 10) * 0.3 + (avg_strength / 2) * 0.3)
                })
        
        return patterns
    
    def _detect_intermittent_patterns(self, results: List[Dict]) -> List[Dict]:
        """
        Aralıklı talep kalıplarını tespit eder.
        """
        patterns = []
        
        # Gruplara göre aralıklı talep analizi
        group_intermittent = {}
        
        for result in results:
            group = result.get('group', 'GENEL')
            is_intermittent = result.get('is_intermittent', False)
            intermittent_level = result.get('intermittent_level', '')
            zero_ratio = result.get('zero_ratio', 0)
            
            if is_intermittent and zero_ratio > 0.3:
                if group not in group_intermittent:
                    group_intermittent[group] = {
                        'count': 0,
                        'total_zero_ratio': 0,
                        'levels': {},
                        'materials': []
                    }
                group_intermittent[group]['count'] += 1
                group_intermittent[group]['total_zero_ratio'] += zero_ratio
                group_intermittent[group]['levels'][intermittent_level] = \
                    group_intermittent[group]['levels'].get(intermittent_level, 0) + 1
                group_intermittent[group]['materials'].append(result.get('material_code', ''))
        
        # Her grup için kural oluştur
        for group, data in group_intermittent.items():
            if data['count'] >= 2:  # En az 2 ürün
                avg_zero_ratio = data['total_zero_ratio'] / data['count']
                dominant_level = max(data['levels'].items(), key=lambda x: x[1])[0] if data['levels'] else 'Orta'
                
                rule_id = f"intermittent_{group.lower()}"
                
                patterns.append({
                    'rule_id': rule_id,
                    'rule_name': f"{group} Grubu Aralıklı Talep",
                    'rule_type': 'intermittent',
                    'description': f"{group} grubunda aralıklı talep sürekli tekrar ediyor. {data['count']} üründe ortalama sıfır oranı: {avg_zero_ratio:.2f}",
                    'pattern_data': {
                        'group': group,
                        'material_count': data['count'],
                        'avg_zero_ratio': avg_zero_ratio,
                        'dominant_level': dominant_level,
                        'materials': data['materials']
                    },
                    'confidence': min(0.85, 0.2 + (data['count'] / 5) * 0.4 + (avg_zero_ratio / 2) * 0.25)
                })
        
        return patterns
    
    def _detect_trend_patterns(self, results: List[Dict]) -> List[Dict]:
        """
        Trend kalıplarını tespit eder.
        """
        patterns = []
        
        # Gruplara göre trend analizi
        group_trend = {}
        
        for result in results:
            group = result.get('group', 'GENEL')
            trend_direction = result.get('trend_direction', '')
            trend_percent = abs(result.get('trend_percent', 0))
            
            if trend_direction and trend_percent > 5:  # %5'ten büyük trend
                if group not in group_trend:
                    group_trend[group] = {
                        'up': 0,
                        'down': 0,
                        'total_percent': 0,
                        'count': 0,
                        'materials': []
                    }
                group_trend[group]['count'] += 1
                group_trend[group]['total_percent'] += trend_percent
                group_trend[group]['materials'].append(result.get('material_code', ''))
                
                if trend_direction == 'Artış':
                    group_trend[group]['up'] += 1
                else:
                    group_trend[group]['down'] += 1
        
        # Her grup için kural oluştur
        for group, data in group_trend.items():
            if data['count'] >= 3:  # En az 3 ürün
                avg_percent = data['total_percent'] / data['count']
                direction = 'Artış' if data['up'] > data['down'] else 'Azalış'
                ratio = data['up'] / data['count'] if data['up'] > 0 else 0
                
                rule_id = f"trend_{group.lower()}_{direction.lower()}"
                
                patterns.append({
                    'rule_id': rule_id,
                    'rule_name': f"{group} Grubu {direction} Trendi",
                    'rule_type': 'trend',
                    'description': f"{group} grubunda {direction} trendi tespit edildi. {data['count']} üründe ortalama {avg_percent:.1f}% değişim.",
                    'pattern_data': {
                        'group': group,
                        'direction': direction,
                        'material_count': data['count'],
                        'avg_percent': avg_percent,
                        'up_ratio': ratio,
                        'materials': data['materials']
                    },
                    'confidence': min(0.8, 0.2 + (data['count'] / 10) * 0.4 + (ratio) * 0.2)
                })
        
        return patterns
    
    def _detect_method_patterns(self, results: List[Dict], result_type: str) -> List[Dict]:
        """
        Başarılı yöntem kalıplarını tespit eder.
        """
        patterns = []
        
        # Metot dağılımı
        method_counts = {}
        method_success = {}
        
        for result in results:
            if result_type == 'forecast':
                method = result.get('selected_model', 'auto')
                rmse = result.get('model_rmse', None)
                if rmse and rmse < 100:
                    if method not in method_success:
                        method_success[method] = {'total': 0, 'success': 0}
                    method_success[method]['total'] += 1
                    if rmse < 30:  # Başarılı
                        method_success[method]['success'] += 1
            else:
                method = result.get('recommended_method', 'hybrid_ss')
                method_counts[method] = method_counts.get(method, 0) + 1
        
        # En çok kullanılan yöntem
        if method_counts:
            most_common = max(method_counts.items(), key=lambda x: x[1])
            if most_common[1] >= 3:  # En az 3 ürün
                rule_id = f"method_{most_common[0]}"
                patterns.append({
                    'rule_id': rule_id,
                    'rule_name': f"{most_common[0]} Yöntemi Başarılı",
                    'rule_type': 'successful_method',
                    'description': f"{most_common[0]} yöntemi {most_common[1]} üründe başarılı şekilde kullanıldı.",
                    'pattern_data': {
                        'method': most_common[0],
                        'usage_count': most_common[1],
                        'result_type': result_type
                    },
                    'confidence': min(0.85, 0.3 + (most_common[1] / 20) * 0.55)
                })
        
        return patterns
    
    def _detect_lead_time_patterns(self, results: List[Dict]) -> List[Dict]:
        """
        Lead Time kalıplarını tespit eder.
        """
        patterns = []
        
        # Tedarikçi bazlı Lead Time analizi
        if 'supplier' in str(results).lower():
            # Tedarikçi verilerinden LT analizi
            for result in results:
                lt_mean = result.get('lt_mean', 0)
                lt_std = result.get('lt_std', 0)
                supplier_name = result.get('name', '')
                
                if lt_mean > 20 and lt_std > 5:
                    rule_id = f"lead_time_{supplier_name.lower().replace(' ', '_')}"
                    patterns.append({
                        'rule_id': rule_id,
                        'rule_name': f"{supplier_name} Lead Time Artışı",
                        'rule_type': 'lead_time',
                        'description': f"{supplier_name} tedarikçisinde Lead Time yükseliyor. Ortalama: {lt_mean}gün, Std: {lt_std}gün.",
                        'pattern_data': {
                            'supplier': supplier_name,
                            'lt_mean': lt_mean,
                            'lt_std': lt_std
                        },
                        'confidence': min(0.7, 0.3 + (lt_mean / 50) * 0.4)
                    })
        
        return patterns
    
    def _create_rule(self, pattern: Dict) -> Dict:
        """Yeni kural oluşturur"""
        now = datetime.utcnow()
        
        rule = CompanyLearningMemory(
            user_id=self.user_id,
            rule_id=pattern['rule_id'],
            rule_name=pattern['rule_name'],
            rule_type=pattern['rule_type'],
            description=pattern.get('description', ''),
            pattern_data=pattern.get('pattern_data', {}),
            confidence_score=pattern.get('confidence', 0.5),
            usage_count=0,
            success_count=0,
            first_seen_at=now,
            last_seen_at=now,
            is_active=True,
            is_verified=False
        )
        
        self.db.add(rule)
        self.db.flush()
        
        return {
            'id': rule.id,
            'rule_id': rule.rule_id,
            'rule_name': rule.rule_name,
            'confidence': rule.confidence_score,
            'is_new': True
        }
    
    def _update_rule(self, existing: CompanyLearningMemory, pattern: Dict) -> Dict:
        """Mevcut kuralı günceller"""
        # Güven skorunu güncelle
        new_confidence = pattern.get('confidence', 0.5)
        old_confidence = existing.confidence_score
        
        # Ağırlıklı ortalama
        if existing.usage_count > 0:
            weight = 0.7  # Eski verinin ağırlığı
            updated_confidence = (old_confidence * weight) + (new_confidence * (1 - weight))
        else:
            updated_confidence = new_confidence
        
        # Kullanım sayısını artır
        existing.usage_count += 1
        existing.confidence_score = updated_confidence
        existing.last_seen_at = datetime.utcnow()
        
        # Eğer güven 0.7'den yüksekse doğrula
        if updated_confidence > 0.7:
            existing.is_verified = True
        
        self.db.flush()
        
        return {
            'id': existing.id,
            'rule_id': existing.rule_id,
            'rule_name': existing.rule_name,
            'confidence': existing.confidence_score,
            'usage_count': existing.usage_count,
            'is_verified': existing.is_verified,
            'is_updated': True
        }
    
    def _update_confidence_scores(self, rules: List[Dict]) -> Dict[str, float]:
        """Tüm kuralların güven skorlarını günceller"""
        scores = {}
        
        for rule_info in rules:
            rule_id = rule_info.get('rule_id')
            if rule_id:
                rule = self.db.query(CompanyLearningMemory).filter(
                    CompanyLearningMemory.rule_id == rule_id,
                    CompanyLearningMemory.user_id == self.user_id
                ).first()
                
                if rule:
                    # Zaman faktörü: Eski kuralların güveni zamanla azalır
                    days_since_last = (datetime.utcnow() - rule.last_seen_at).days
                    if days_since_last > 30:
                        decay = 0.95 ** (days_since_last / 30)  # Ayda %5 azalma
                        rule.confidence_score *= decay
                        rule.confidence_score = max(0.3, rule.confidence_score)
                    
                    scores[rule_id] = rule.confidence_score
        
        return scores
    
    def get_company_memory(self, limit: int = 50) -> List[Dict]:
        """
        Şirket hafızasındaki tüm kuralları getirir.
        """
        rules = self.db.query(CompanyLearningMemory).filter(
            CompanyLearningMemory.user_id == self.user_id,
            CompanyLearningMemory.is_active == True
        ).order_by(
            desc(CompanyLearningMemory.confidence_score),
            desc(CompanyLearningMemory.last_seen_at)
        ).limit(limit).all()
        
        return [
            {
                'id': rule.id,
                'rule_id': rule.rule_id,
                'rule_name': rule.rule_name,
                'rule_type': rule.rule_type,
                'description': rule.description,
                'pattern_data': rule.pattern_data,
                'confidence_score': rule.confidence_score,
                'usage_count': rule.usage_count,
                'is_verified': rule.is_verified,
                'first_seen_at': rule.first_seen_at.isoformat() if rule.first_seen_at else None,
                'last_seen_at': rule.last_seen_at.isoformat() if rule.last_seen_at else None
            }
            for rule in rules
        ]
    
    def get_verified_rules(self) -> List[Dict]:
        """
        Sadece doğrulanmış kuralları getirir.
        """
        rules = self.db.query(CompanyLearningMemory).filter(
            CompanyLearningMemory.user_id == self.user_id,
            CompanyLearningMemory.is_active == True,
            CompanyLearningMemory.is_verified == True
        ).order_by(
            desc(CompanyLearningMemory.confidence_score)
        ).all()
        
        return [
            {
                'id': rule.id,
                'rule_id': rule.rule_id,
                'rule_name': rule.rule_name,
                'rule_type': rule.rule_type,
                'description': rule.description,
                'confidence_score': rule.confidence_score,
                'usage_count': rule.usage_count,
                'pattern_data': rule.pattern_data
            }
            for rule in rules
        ]