import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from database.base import create_tables
from handlers import start, admin_menu, add_admin, broadcast, excel_io

logging.basicConfig(level=logging.INFO)


async def main():
    await create_tables()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(admin_menu.router)
    dp.include_router(add_admin.router)
    dp.include_router(broadcast.router)
    dp.include_router(excel_io.router)

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
