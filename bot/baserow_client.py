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
        }

    @retry(
        reraise=True,
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
    )
    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        headers = dict(self.headers)
        if "json" in kwargs:
            headers["Content-Type"] = "application/json"

        # Первое место
        async with httpx.AsyncClient(timeout=30.0, verify=False, follow_redirects=True) as client:
            response = await client.request(method, url, headers=headers, **kwargs)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error(f"Baserow API Error: {e.response.text}")
                raise
            return response

    async def create_record(self, fields: Dict[str, Any]) -> Dict:
        url = f"{self.base_url}/api/database/rows/table/{BASEROW_TABLE_ID}/?user_field_names=true"
        response = await self._request("POST", url, json=fields)
        return response.json()

    async def get_order_names(self) -> List[str]:
        if not BASEROW_ORDERS_TABLE_ID:
            raise ValueError("BASEROW_ORDERS_TABLE_ID не настроен")
        url = f"{self.base_url}/api/database/rows/table/{BASEROW_ORDERS_TABLE_ID}/"
        names =[]
        page = 1  # Начинаем сами считать страницы
        
        async with httpx.AsyncClient(timeout=20.0, verify=False, follow_redirects=True) as client:
            while True:
                # Передаем номер страницы явно
                params = {"user_field_names": "true", "fields": "Name,Статус", "page": page}
                response = await client.get(url, headers=self.headers, params=params)
                
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as e:
                    logger.error(f"Baserow API Error (get_orders): {e.response.text}")
                    raise
                
                data = response.json()
                for record in data.get("results",[]):
                    name = record.get("Name")
                    status = record.get("Статус")
                    if isinstance(status, dict):
                        status = status.get("value", "")
                    if isinstance(status, str) and status.strip() in EXCLUDED_STATUSES:
                        continue
                    if name and isinstance(name, str):
                        names.append(name.strip())
                
                # Если ссылки на следующую страницу нет - прерываем цикл
                if not data.get("next"):
                    break
                
                # Увеличиваем номер страницы для следующего запроса
                page += 1
                
        return names

    async def upload_file_from_url(self, file_url: str) -> Dict:
        # Третье место
        async with httpx.AsyncClient(timeout=30.0, verify=False, follow_redirects=True) as client:
            file_response = await client.get(file_url)
            file_response.raise_for_status()
            file_content = file_response.content

        filename = file_url.split("/")[-1]
        if not filename or "?" in filename:
            filename = "attachment.file"

        url = f"{self.base_url}/api/user-files/upload-file/"
        files = {"file": (filename, file_content)}
        
        response = await self._request("POST", url, files=files)
        return response.json()
