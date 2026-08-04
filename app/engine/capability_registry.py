# app/engine/capability_registry.py
"""
Capability Registry - DOCUMENT 04A
Maps business capabilities to execution engines.
"""

from typing import Dict, Any, Optional, Type
from enum import Enum
from dataclasses import dataclass  # ✅ EKLENDI
import logging


logger = logging.getLogger(__name__)


class Capability(str, Enum):
    """Business capabilities."""
    DEMAND_FORECAST = "demand_forecast"
    SAFETY_STOCK = "safety_stock"
    SIMULATION = "simulation"
    BACKTEST = "backtest"
    SUPPLIER_ANALYSIS = "supplier_analysis"
    PATTERN_ANALYSIS = "pattern_analysis"
    SEASONAL_ANALYSIS = "seasonal_analysis"


@dataclass
class CapabilityRegistration:
    """Capability registration record."""
    capability: Capability
    engine_name: str
    engine_class: Type
    engine_instance: Optional[Any] = None
    is_available: bool = True
    version: str = "1.0.0"


class CapabilityRegistry:
    """
    Capability Registry - DOCUMENT 04A
    
    Maps business capabilities to execution engines.
    Workflow Engine resolves capabilities through this registry.
    """
    
    def __init__(self):
        self._registrations: Dict[Capability, CapabilityRegistration] = {}
    
    def register(
        self,
        capability: Capability,
        engine_class: Type,
        engine_name: str,
        version: str = "1.0.0",
    ) -> bool:
        """Register a capability."""
        if capability in self._registrations:
            logger.warning(f"Capability already registered: {capability}")
            return False
        
        self._registrations[capability] = CapabilityRegistration(
            capability=capability,
            engine_name=engine_name,
            engine_class=engine_class,
            version=version,
        )
        
        logger.info(f"✅ Capability registered: {capability} -> {engine_name}")
        return True
    
    def resolve(self, capability: Capability) -> Optional[CapabilityRegistration]:
        """Resolve a capability to its engine."""
        return self._registrations.get(capability)
    
    def get_engine(self, capability: Capability) -> Optional[Any]:
        """Get engine instance for a capability."""
        registration = self.resolve(capability)
        if not registration:
            return None
        
        if registration.engine_instance is None:
            registration.engine_instance = registration.engine_class()
        
        return registration.engine_instance
    
    def is_available(self, capability: Capability) -> bool:
        """Check if a capability is available."""
        registration = self.resolve(capability)
        return registration is not None and registration.is_available
    
    def get_all_capabilities(self) -> list:
        """Get all registered capabilities."""
        return list(self._registrations.keys())
    
    def get_capability_info(self) -> Dict[str, Dict[str, Any]]:
        """Get capability information."""
        return {
            cap.value: {
                "engine_name": reg.engine_name,
                "version": reg.version,
                "is_available": reg.is_available,
            }
            for cap, reg in self._registrations.items()
        }
    
    def set_availability(self, capability: Capability, is_available: bool) -> bool:
        """Set capability availability."""
        registration = self.resolve(capability)
        if not registration:
            return False
        
        registration.is_available = is_available
        return True
    
    def register_default_capabilities(self):
        """Register default capabilities."""
        # Import engine classes
        try:
            from app.analysis.forecast import DemandForecaster
            from app.analysis.safety_stock import ComprehensiveSafetyStockOptimizer
            from app.simulation.monte_carlo import MonteCarloInventorySimulator
            from app.analysis.backtest import BacktestEngine
            from app.analysis.supplier import SupplierPerformanceAnalyzer
            from app.analysis.pattern import AdvancedDemandAnalyzer
        except ImportError as e:
            logger.warning(f"Could not import engine classes: {e}")
            return
        
        # Register capabilities
        self.register(
            capability=Capability.DEMAND_FORECAST,
            engine_class=DemandForecaster,
            engine_name="DemandForecaster",
            version="1.0.0",
        )
        
        self.register(
            capability=Capability.SAFETY_STOCK,
            engine_class=ComprehensiveSafetyStockOptimizer,
            engine_name="SafetyStockOptimizer",
            version="1.0.0",
        )
        
        self.register(
            capability=Capability.SIMULATION,
            engine_class=MonteCarloInventorySimulator,
            engine_name="MonteCarloSimulator",
            version="1.0.0",
        )
        
        self.register(
            capability=Capability.BACKTEST,
            engine_class=BacktestEngine,
            engine_name="BacktestEngine",
            version="1.0.0",
        )
        
        self.register(
            capability=Capability.SUPPLIER_ANALYSIS,
            engine_class=SupplierPerformanceAnalyzer,
            engine_name="SupplierAnalyzer",
            version="1.0.0",
        )
        
        self.register(
            capability=Capability.PATTERN_ANALYSIS,
            engine_class=AdvancedDemandAnalyzer,
            engine_name="PatternAnalyzer",
            version="1.0.0",
        )
        
        logger.info("✅ Default capabilities registered")


# Global capability registry instance
capability_registry = CapabilityRegistry()