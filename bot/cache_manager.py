import json
import time
from pathlib import Path
from typing import List
from .baserow_client import BaserowClient

CACHE_DIR = Path(__file__).parent.parent / "cache"
CACHE_FILE = CACHE_DIR / "orders_cache.json"
CACHE_MAX_AGE = 24 * 3600


class OrdersCache:
    def __init__(self, baserow_client: BaserowClient):
        self.client = baserow_client

    def _is_cache_fresh(self) -> bool:
        if not CACHE_FILE.exists():
            return False
        file_age = time.time() - CACHE_FILE.stat().st_mtime
        return file_age < CACHE_MAX_AGE

    def _load_from_cache(self) -> List[str]:
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("orders", [])
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return []

    async def _fetch_and_cache(self) -> List[str]:
        try:
            orders = await self.client.get_order_names()
            CACHE_DIR.mkdir(exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(
                    {"updated_at": time.time(), "orders": orders},
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
            return orders
        except Exception as e:
            if CACHE_FILE.exists():
                return self._load_from_cache()
            return []

    async def get_orders(self) -> List[str]:
        if self._is_cache_fresh():
            return self._load_from_cache()
        else:
            return await self._fetch_and_cache()
