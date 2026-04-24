from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from database.base import async_session
from database.crud import upsert_user, is_admin
from keyboards.reply import admin_menu_kb

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    async with async_session() as session:
        await upsert_user(
            session,
            tg_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username,
        )
        admin = await is_admin(session, message.from_user.id)

    if admin:
        await message.answer("Admin paneliga xush kelibsiz!", reply_markup=admin_menu_kb())
    else:
        await message.answer("Salom! Botga xush kelibsiz.")
