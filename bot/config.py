from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

AUTHORIZED_USERS = set(
    int(uid.strip())
    for uid in os.getenv("AUTHORIZED_USERS", "").split(",")
    if uid.strip()
)

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не указан в .env")

BASEROW_URL = os.getenv("BASEROW_URL", "http://localhost")
BASEROW_TOKEN = os.getenv("BASEROW_TOKEN")
BASEROW_TABLE_ID = os.getenv("BASEROW_TABLE_ID")
BASEROW_ORDERS_TABLE_ID = os.getenv("BASEROW_ORDERS_TABLE_ID")

if not all([BASEROW_TOKEN, BASEROW_TABLE_ID, BASEROW_ORDERS_TABLE_ID]):
    raise ValueError("Один или несколько Baserow параметров не указаны в .env")

EXCLUDED_STATUSES = set(
    os.getenv("EXCLUDED_STATUSES", "Расчет,Отменен,Отложен").split(",")
)
