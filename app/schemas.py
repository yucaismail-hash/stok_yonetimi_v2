from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class TokenCostCreate(BaseModel):
    endpoint: str
    method: str = "POST"
    cost: int = 1
    is_active: bool = True

class TokenCostUpdate(BaseModel):
    cost: Optional[int] = None
    is_active: Optional[bool] = None

class TokenCostResponse(BaseModel):
    id: int
    endpoint: str
    method: str
    cost: int
    is_active: bool
    updated_at: datetime

class UserTokenUpdate(BaseModel):
    user_id: int
    token_balance: int

class SupplierCreate(BaseModel):
    code: str
    name: str
    factor: float = 1.0

class MaterialSupplierCreate(BaseModel):
    supplier_id: int
    share: float = 1.0
    is_primary: bool = False

class MaterialCreate(BaseModel):
    code: str
    name: str
    group: str
    lead_time_days: int
    unit_cost: float
    holding_rate: float
    shortage_cost: float
    initial_stock: float
    weekly_demand: List[float]
    eoq: float