# app/services/execution/internal_api.py
"""
Internal API Client
Internal analiz endpoint'lerini çağırır.
"""

import httpx
import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class InternalAPIClient:
    """
    Internal API istemcisi.
    /api/v2/internal/forecast, /api/v2/internal/safety-stock vb. çağırır.
    """
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or "http://localhost:8000"
        self.timeout = 300  # 5 dakika
    
    async def call(
        self,
        endpoint: str,
        method: str = "POST",
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Internal API'yi çağır.
        """
        # Internal endpoint'e çevir
        if not endpoint.startswith("/api/v2/internal/"):
            endpoint = f"/api/v2/internal/{endpoint.lstrip('/')}"
        
        url = f"{self.base_url}{endpoint}"
        
        logger.info(f"📡 Calling internal API: {method} {url}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method.upper() == "POST":
                    response = await client.post(url, json=data)
                elif method.upper() == "GET":
                    response = await client.get(url, params=data)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException:
            logger.error(f"⏰ Internal API timeout: {url}")
            raise HTTPException(504, f"Internal API timeout: {endpoint}")
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Internal API error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(e.response.status_code, f"Internal API error: {e.response.text}")
        except Exception as e:
            logger.error(f"❌ Internal API call failed: {str(e)}")
            raise HTTPException(500, f"Internal API call failed: {str(e)}")