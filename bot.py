import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from config import TOKEN
from database import init_db, warn_scheduler
from handlers import register_handlers

# Инициализация
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# Регистрация хендлеров
register_handlers(dp)


async def main():
    await init_db()
    logging.info("База данных инициализирована.")

    # Запуск планировщика в фоне, передавая объект bot
    asyncio.create_task(warn_scheduler(bot))
    logging.info("Планировщик варнов запущен.")

    await dp.start_polling(bot)


if __name__ == "__main__":
    if sys.platform == 'win32':
        # Только для Windows, чтобы избежать ошибок с asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
