# bot/main.py
import asyncio
import logging
import os
from logging.handlers import RotatingFileHandler
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web
from .config import TELEGRAM_BOT_TOKEN
from .handlers import router
from .baserow_client import BaserowClient
from .cache_manager import OrdersCache

logger = logging.getLogger(__name__)


def setup_logging():
    """Настраивает логирование в файл (с ротацией) и в консоль."""
    log_level = logging.INFO
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "bot.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=2,
        encoding="utf-8",
    )
    file_handler.setFormatter(log_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}" if WEBHOOK_HOST else None
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8080))


async def on_startup(bot: Bot):
    if WEBHOOK_URL:
        await bot.set_webhook(WEBHOOK_URL)
        logger.info(f"Webhook установлен на {WEBHOOK_URL}")


async def on_shutdown(bot: Bot):
    if WEBHOOK_URL:
        await bot.delete_webhook()
        logger.info("Webhook удалён")


async def main():
    setup_logging()
    logger.info("Запуск бота...")

    try:
        bot = Bot(
            token=TELEGRAM_BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        dp = Dispatcher(storage=MemoryStorage())

        baserow_client = BaserowClient()
        orders_cache = OrdersCache(baserow_client=baserow_client)

        dp.include_router(router)

        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)

        workflow_data = {
            "baserow_client": baserow_client,
            "orders_cache": orders_cache,
        }

        if WEBHOOK_URL:
            app = web.Application()
            SimpleRequestHandler(
                dispatcher=dp,
                bot=bot,
                **workflow_data,
            ).register(app, path=WEBHOOK_PATH)
            setup_application(app, dp, bot=bot, **workflow_data)
            logger.info(f"Запуск webhook-сервера на {WEBAPP_HOST}:{WEBAPP_PORT}")
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, WEBAPP_HOST, WEBAPP_PORT)
            await site.start()
            await asyncio.Event().wait()
        else:
            logger.info("Запуск polling...")
            await dp.start_polling(bot, **workflow_data)

    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен вручную")
    except Exception as e:
        logger.error(f"Необработанная ошибка на верхнем уровне: {e}", exc_info=True)
