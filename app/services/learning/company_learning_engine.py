# app/services/learning/company_learning_engine.py
"""
Company Learning Engine
DOCUMENT 01 - Company Learning

Learns company-specific operational behaviour.
Stores learned parameters, NOT raw business datasets.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import hashlib
import json
import logging
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.learning import CompanyLearningMemory
from app.models.company import User, UserMaterial

logger = logging.getLogger(__name__)


class CompanyLearningEngine:
    """
    Company Learning Motoru.
    
    Şirkete özel operasyonel davranışları öğrenir.
    - Talep desenleri
    - Mevsimsellik faktörleri
    - Tedarikçi performansı
    - Stok davranışları
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def learn_from_execution(
        self,
        user_id: int,
        execution_result: Dict[str, Any],
        dataset_id: int,
    ) -> List[CompanyLearningMemory]:
        """
        Bir çalıştırma sonucundan öğren.
        """
        learned_rules = []
        
        # 1. Talep deseni öğren
        forecast_result = execution_result.get("forecast", {})
        if forecast_result:
            pattern_rules = self._learn_demand_patterns(user_id, forecast_result)
            learned_rules.extend(pattern_rules)
        
        # 2. Mevsimsellik öğren
        seasonal_rules = self._learn_seasonality(user_id, forecast_result)
        learned_rules.extend(seasonal_rules)
        
        # 3. Tedarikçi performansı öğren
        supplier_result = execution_result.get("supplier", {})
        if supplier_result:
            supplier_rules = self._learn_supplier_performance(user_id, supplier_result)
            learned_rules.extend(supplier_rules)
        
        # 4. Stok davranışı öğren
        safety_stock_result = execution_result.get("safety_stock", {})
        if safety_stock_result:
            stock_rules = self._learn_stock_behavior(user_id, safety_stock_result)
            learned_rules.extend(stock_rules)
        
        # Kaydet
        for rule in learned_rules:
            self.db.add(rule)
        
        self.db.commit()
        
        logger.info(f"✅ Company learning completed for user {user_id}: {len(learned_rules)} rules")
        
        return learned_rules
    
    def _learn_demand_patterns(self, user_id: int, forecast_result: Dict) -> List[CompanyLearningMemory]:
        """Talep desenlerini öğren."""
        rules = []
        
        patterns = forecast_result.get("patterns", {})
        
        for sku, pattern_data in patterns.items():
            pattern_type = pattern_data.get("type", "stable")
            confidence = pattern_data.get("confidence", 0.5)
            
            if confidence < 0.6:
                continue
            
            rule = CompanyLearningMemory(
                user_id=user_id,
                rule_id=f"demand_pattern_{sku}_{int(datetime.now().timestamp())}",
                rule_name=f"Demand Pattern - {sku}",
                rule_type="demand_pattern",
                pattern_data={
                    "sku": sku,
                    "pattern_type": pattern_type,
                    "params": pattern_data.get("params", {}),
                    "confidence": confidence,
                },
                confidence_score=confidence,
                first_seen_at=datetime.now(),
                last_seen_at=datetime.now(),
                is_active=True,
                is_verified=confidence > 0.8,
            )
            rules.append(rule)
        
        return rules
    
    def _learn_seasonality(self, user_id: int, forecast_result: Dict) -> List[CompanyLearningMemory]:
        """Mevsimsellik faktörlerini öğren."""
        rules = []
        
        seasonality = forecast_result.get("seasonality", {})
        
        for sku, seasonal_data in seasonality.items():
            seasonal_factors = seasonal_data.get("factors", {})
            confidence = seasonal_data.get("confidence", 0.5)
            
            if confidence < 0.6 or not seasonal_factors:
                continue
            
            rule = CompanyLearningMemory(
                user_id=user_id,
                rule_id=f"seasonality_{sku}_{int(datetime.now().timestamp())}",
                rule_name=f"Seasonality - {sku}",
                rule_type="seasonality",
                pattern_data={
                    "sku": sku,
                    "factors": seasonal_factors,
                    "period": seasonal_data.get("period", 52),
                    "confidence": confidence,
                },
                confidence_score=confidence,
                first_seen_at=datetime.now(),
                last_seen_at=datetime.now(),
                is_active=True,
                is_verified=confidence > 0.8,
            )
            rules.append(rule)
        
        return rules
    
    def _learn_supplier_performance(self, user_id: int, supplier_result: Dict) -> List[CompanyLearningMemory]:
        """Tedarikçi performansını öğren."""
        rules = []
        
        suppliers = supplier_result.get("suppliers", {})
        
        for supplier_id, supplier_data in suppliers.items():
            risk_score = supplier_data.get("risk_score", 0)
            performance_score = supplier_data.get("performance_score", 0)
            
            if risk_score == 0 and performance_score == 0:
                continue
            
            rule = CompanyLearningMemory(
                user_id=user_id,
                rule_id=f"supplier_{supplier_id}_{int(datetime.now().timestamp())}",
                rule_name=f"Supplier Performance - {supplier_id}",
                rule_type="supplier_performance",
                pattern_data={
                    "supplier_id": supplier_id,
                    "risk_score": risk_score,
                    "performance_score": performance_score,
                    "lt_mean": supplier_data.get("lt_mean"),
                    "lt_std": supplier_data.get("lt_std"),
                },
                confidence_score=0.8,
                first_seen_at=datetime.now(),
                last_seen_at=datetime.now(),
                is_active=True,
                is_verified=True,
            )
            rules.append(rule)
        
        return rules
    
    def _learn_stock_behavior(self, user_id: int, safety_stock_result: Dict) -> List[CompanyLearningMemory]:
        """Stok davranışını öğren."""
        rules = []
        
        stocks = safety_stock_result.get("stocks", {})
        
        for sku, stock_data in stocks.items():
            stock_status = stock_data.get("status", "unknown")
            safety_stock = stock_data.get("safety_stock", 0)
            reorder_point = stock_data.get("reorder_point", 0)
            
            if safety_stock == 0 and reorder_point == 0:
                continue
            
            rule = CompanyLearningMemory(
                user_id=user_id,
                rule_id=f"stock_behavior_{sku}_{int(datetime.now().timestamp())}",
                rule_name=f"Stock Behavior - {sku}",
                rule_type="stock_behavior",
                pattern_data={
                    "sku": sku,
                    "status": stock_status,
                    "safety_stock": safety_stock,
                    "reorder_point": reorder_point,
                    "current_stock": stock_data.get("current_stock"),
                    "service_level": stock_data.get("service_level"),
                },
                confidence_score=0.7,
                first_seen_at=datetime.now(),
                last_seen_at=datetime.now(),
                is_active=True,
                is_verified=False,
            )
            rules.append(rule)
        
        return rules
    
    def get_learning_memory(self, user_id: int, rule_type: Optional[str] = None) -> List[CompanyLearningMemory]:
        """Öğrenilen bilgileri getir."""
        query = self.db.query(CompanyLearningMemory).filter(
            CompanyLearningMemory.user_id == user_id,
            CompanyLearningMemory.is_active == True
        )
        
        if rule_type:
            query = query.filter(CompanyLearningMemory.rule_type == rule_type)
        
        return query.order_by(CompanyLearningMemory.confidence_score.desc()).all()
    
    def update_confidence(
        self,
        user_id: int,
        rule_id: str,
        success: bool,
    ) -> Optional[CompanyLearningMemory]:
        """
        Öğrenilen kuralın güven skorunu güncelle.
        """
        rule = self.db.query(CompanyLearningMemory).filter(
            CompanyLearningMemory.user_id == user_id,
            CompanyLearningMemory.rule_id == rule_id,
            CompanyLearningMemory.is_active == True
        ).first()
        
        if not rule:
            return None
        
        # Güven skorunu güncelle
        if success:
            rule.confidence_score = min(1.0, rule.confidence_score + 0.05)
            rule.success_count += 1
        else:
            rule.confidence_score = max(0.0, rule.confidence_score - 0.05)
        
        rule.usage_count += 1
        rule.last_used_at = datetime.now()
        
        # 10 kullanımdan sonra verify
        if rule.usage_count >= 10 and rule.confidence_score > 0.8:
            rule.is_verified = True
        
        self.db.commit()
        
        logger.info(f"✅ Confidence updated for rule {rule_id}: {rule.confidence_score}")
        
        return rule