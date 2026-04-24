import io
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, BufferedInputFile
from database.base import async_session
from database.crud import get_all_users, upsert_users_bulk
from filters import IsAdmin
from keyboards.reply import admin_menu_kb
from services.excel import users_to_excel, excel_to_users

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(IsAdmin())


@router.message(F.text == "📥 Excel yuklab olish")
async def download_excel(message: Message, bot: Bot):
    async with async_session() as session:
        users = await get_all_users(session)

    if not users:
        await message.answer("Bazada foydalanuvchilar yo'q.")
        return

    data = users_to_excel(users)
    file = BufferedInputFile(data, filename="users.xlsx")
    await message.answer_document(file, caption=f"👥 Jami: {len(users)} ta foydalanuvchi")


@router.message(F.text == "📂 Excel yuklash")
async def ask_excel_upload(message: Message):
    await message.answer("Excel faylini yuboring (.xlsx formatda)\nUstunlar: A=tg_id | B=full_name")


@router.message(F.document)
async def handle_excel_upload(message: Message, bot: Bot):
    doc = message.document
    if not (doc.file_name or "").lower().endswith(".xlsx"):
        await message.answer("Faqat .xlsx fayl qabul qilinadi.")
        return

    try:
        buf = await bot.download(doc.file_id)
        users = excel_to_users(buf.read())
    except Exception as e:
        logger.exception("Excel o'qishda xato")
        await message.answer(f"❌ Faylni o'qishda xato:\n<code>{e}</code>", parse_mode="HTML")
        return

    if not users:
        await message.answer("Faylda yaroqli foydalanuvchilar topilmadi.\nA ustunda tg_id, B ustunda ism bo'lishi kerak.")
        return

    try:
        async with async_session() as session:
            await upsert_users_bulk(session, users)
    except Exception as e:
        logger.exception("DB ga yozishda xato")
        await message.answer(f"❌ Bazaga yozishda xato:\n<code>{e}</code>", parse_mode="HTML")
        return

    await message.answer(
        f"✅ <b>{len(users)}</b> ta foydalanuvchi bazaga qo'shildi/yangilandi.",
        parse_mode="HTML",
        reply_markup=admin_menu_kb(),
    )
