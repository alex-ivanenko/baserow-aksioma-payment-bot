import httpx
import logging
from typing import Dict, Any, List
from tenacity import retry, wait_exponential, stop_after_attempt
from .config import (
    BASEROW_URL,
    BASEROW_TOKEN,
    BASEROW_TABLE_ID,
    BASEROW_ORDERS_TABLE_ID,
    EXCLUDED_STATUSES,
)

logger = logging.getLogger(__name__)


class BaserowClient:
    def __init__(self):
        self.base_url = BASEROW_URL.rstrip("/")
        self.headers = {
            "Authorization": f"Token {BASEROW_TOKEN}",
            "Content-Type": "application/json",
        }

    @retry(
        reraise=True,
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
    )
    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response

    async def create_record(self, fields: Dict[str, Any]) -> Dict:
        url = f"{self.base_url}/api/database/rows/table/{BASEROW_TABLE_ID}/?user_field_names=true"
        response = await self._request("POST", url, json=fields)
        return response.json()

    async def get_order_names(self) -> List[str]:
        if not BASEROW_ORDERS_TABLE_ID:
            raise ValueError("BASEROW_ORDERS_TABLE_ID не настроен")

        url = f"{self.base_url}/api/database/rows/table/{BASEROW_ORDERS_TABLE_ID}/"
        names = []
        params = {"user_field_names": "true", "fields": "Name,Статус"}

        async with httpx.AsyncClient(timeout=20.0) as client:
            while True:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()

                for record in data.get("results", []):
                    name = record.get("Name")
                    status = record.get("Статус")

                    if isinstance(status, dict):
                        status = status.get("value", "")
                    if isinstance(status, str) and status.strip() in EXCLUDED_STATUSES:
                        continue
                    if name and isinstance(name, str):
                        names.append(name.strip())

                next_url = data.get("next")
                if not next_url:
                    break
                url = next_url
                params = {}

        return names

    async def upload_file_from_url(self, file_url: str) -> Dict:
        url = f"{self.base_url}/api/user-files/upload-via-url/"
        payload = {"url": file_url}
        response = await self._request("POST", url, json=payload)
        return response.json()
