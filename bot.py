import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from flask import Flask
import threading

# Импорты из наших файлов
from config import TOKEN
from database import init_db, warn_scheduler
from handlers import register_handlers

# Создаем Flask app для веб-сервера
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Telegram Bot is running on Render!"

@app.route('/health')
def health():
    return "✅ OK"

@app.route('/ping')
def ping():
    return "pong"

def run_flask_app():
    """Запуск Flask сервера в отдельном потоке"""
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

# Инициализация бота
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# Регистрация хендлеров
register_handlers(dp)

async def main():
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.daemon = True
    flask_thread.start()
    logging.info("🌐 Flask server started on port " + os.environ.get('PORT', '10000'))

    # Инициализируем базу данных
    await init_db()
    logging.info("✅ База данных инициализирована.")

    # Запуск планировщика в фоне
    asyncio.create_task(warn_scheduler(bot))
    logging.info("✅ Планировщик варнов запущен.")

    # Запускаем бота
    logging.info("🚀 Telegram Bot запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
