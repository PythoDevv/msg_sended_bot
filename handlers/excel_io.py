import io
from aiogram import Router, F, Bot
from aiogram.types import Message, BufferedInputFile
from database.base import async_session
from database.crud import get_all_users, upsert_users_bulk
from filters import IsAdmin
from keyboards.reply import admin_menu_kb
from services.excel import users_to_excel, excel_to_users

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
    await message.answer(
        "Excel faylini yuboring (.xlsx formatda)\n"
        "Ustunlar: tg_id | full_name | username",
    )


@router.message(F.document)
async def handle_excel_upload(message: Message):
    doc = message.document
    if not doc.file_name.endswith(".xlsx"):
        await message.answer("Faqat .xlsx fayl qabul qilinadi.")
        return

    bot: Bot = message.bot
    file = await bot.get_file(doc.file_id)
    buf = io.BytesIO()
    await bot.download_file(file.file_path, buf)
    buf.seek(0)

    try:
        users = excel_to_users(buf.read())
    except Exception as e:
        await message.answer(f"Faylni o'qishda xato: {e}")
        return

    if not users:
        await message.answer("Faylda foydalanuvchilar topilmadi.")
        return

    async with async_session() as session:
        await upsert_users_bulk(session, users)

    await message.answer(
        f"✅ {len(users)} ta foydalanuvchi bazaga qo'shildi/yangilandi.",
        reply_markup=admin_menu_kb(),
    )
