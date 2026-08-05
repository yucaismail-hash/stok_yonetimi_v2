# app/integration/adapters/__init__.py
"""
Integration Adapters - DOCUMENT 07 APP-025 / REVISION 01

External systems SHALL communicate only with Integration Adapters.
"""

from app.integration.adapters.base_adapter import BaseAdapter
from app.integration.adapters.erp_adapter import ERPAdapter
from app.integration.adapters.ecommerce_adapter import ECommerceAdapter
from app.integration.adapters.custom_adapter import CustomAdapter

__all__ = [
    "BaseAdapter",
    "ERPAdapter",
    "ECommerceAdapter",
    "CustomAdapter",
]