# app/api/v2/internal/__init__.py
"""
Internal API V2
Only called by Workflow Engine.
NOT exposed to external users.
"""

from fastapi import APIRouter

from app.api.v2.internal import forecast, safety_stock, simulation, backtest, supplier

router = APIRouter(prefix="/internal")

router.include_router(forecast.router, prefix="/forecast", tags=["Internal"])
router.include_router(safety_stock.router, prefix="/safety-stock", tags=["Internal"])
router.include_router(simulation.router, prefix="/simulation", tags=["Internal"])
router.include_router(backtest.router, prefix="/backtest", tags=["Internal"])
router.include_router(supplier.router, prefix="/supplier", tags=["Internal"])