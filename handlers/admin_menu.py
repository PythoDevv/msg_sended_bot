from aiogram import Router, F
from aiogram.types import Message
from database.base import async_session
from database.crud import get_stats
from filters import IsAdmin
from keyboards.reply import admin_menu_kb

router = Router()
router.message.filter(IsAdmin())


@router.message(F.text == "📊 Statistika")
async def statistics(message: Message):
    async with async_session() as session:
        stats = await get_stats(session)

    await message.answer(
        f"📊 <b>Statistika</b>\n"
        f"━━━━━━━━━━━━\n"
        f"👥 Jami: <b>{stats['total']}</b>\n"
        f"✅ Aktiv: <b>{stats['active']}</b>\n"
        f"🚫 Blocklagan: <b>{stats['blocked']}</b>\n"
        f"👮 Adminlar: <b>{stats['admins']}</b>",
        parse_mode="HTML",
    )
