from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CurrentPilotDatasetResponse(BaseModel):
    dataset_id: str
    status: str
    accepted: bool
    accepted_at: datetime
    created_at: datetime
    source_name: Optional[str] = None
    record_count: int
    material_count: int
