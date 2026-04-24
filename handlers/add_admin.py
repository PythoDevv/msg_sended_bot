from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from database.base import async_session
from database.crud import add_admin, is_admin
from filters import IsAdmin
from keyboards.reply import admin_menu_kb, cancel_kb
from states import AddAdminStates

router = Router()
router.message.filter(IsAdmin())


@router.message(F.text == "➕ Admin qo'shish")
async def ask_admin_id(message: Message, state: FSMContext):
    await state.set_state(AddAdminStates.waiting_for_tg_id)
    await message.answer(
        "Yangi adminning Telegram ID sini yuboring:",
        reply_markup=cancel_kb(),
    )


@router.message(AddAdminStates.waiting_for_tg_id, F.text == "❌ Bekor qilish")
async def cancel_add_admin(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=admin_menu_kb())


@router.message(AddAdminStates.waiting_for_tg_id)
async def save_new_admin(message: Message, state: FSMContext):
    if not message.text or not message.text.strip().lstrip("-").isdigit():
        await message.answer("Iltimos, faqat raqam kiriting (Telegram ID):")
        return

    new_admin_id = int(message.text.strip())

    async with async_session() as session:
        already = await is_admin(session, new_admin_id)
        if already:
            await message.answer("Bu foydalanuvchi allaqachon admin.", reply_markup=admin_menu_kb())
            await state.clear()
            return
        await add_admin(session, tg_id=new_admin_id, added_by=message.from_user.id)

    await state.clear()
    await message.answer(
        f"✅ <b>{new_admin_id}</b> admin qilib qo'shildi.",
        parse_mode="HTML",
        reply_markup=admin_menu_kb(),
    )
