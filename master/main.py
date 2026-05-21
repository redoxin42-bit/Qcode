# Путь: master/main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import TOKEN
from master.handlers import router
from database.db import init_db

logging.basicConfig(level=logging.INFO)

async def main():
    # Инициализируем базу данных
    await init_db()
    
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    print("🚀 Мастер-Бот Qcode успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
