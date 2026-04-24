from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from database.base import async_session
from filters import IsAdmin
from keyboards.reply import admin_menu_kb, broadcast_confirm_kb, cancel_kb
from services.broadcast import broadcast as do_broadcast
from states import BroadcastStates

router = Router()
router.message.filter(IsAdmin())

CANCEL = "❌ Bekor qilish"
TEST = "🧪 Test"
SEND_ALL = "📢 Hammaga yuborish"


@router.message(F.text == "📤 Xabar yuborish")
async def ask_message(message: Message, state: FSMContext):
    await state.set_state(BroadcastStates.waiting_for_message)
    await message.answer(
        "Yubormoqchi bo'lgan xabaringizni yuboring:\n"
        "(matn, rasm, video, GIF — qanday kelsa shunday uzatiladi)",
        reply_markup=cancel_kb(),
    )


@router.message(BroadcastStates.waiting_for_message, F.text == CANCEL)
async def cancel_waiting(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=admin_menu_kb())


@router.message(BroadcastStates.waiting_for_message)
async def got_message(message: Message, state: FSMContext):
    await state.update_data(msg_id=message.message_id, from_chat=message.chat.id)
    await state.set_state(BroadcastStates.confirm)
    await message.answer(
        "Xabarni qayerga yuboramiz?",
        reply_markup=broadcast_confirm_kb(),
    )


@router.message(BroadcastStates.confirm, F.text == CANCEL)
async def cancel_confirm(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=admin_menu_kb())


@router.message(BroadcastStates.confirm, F.text == TEST)
async def send_test(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await bot.copy_message(
        chat_id=message.from_user.id,
        from_chat_id=data["from_chat"],
        message_id=data["msg_id"],
    )
    await message.answer("✅ Test xabar yuborildi. Hammaga yuborasizmi?", reply_markup=broadcast_confirm_kb())


@router.message(BroadcastStates.confirm, F.text == SEND_ALL)
async def send_all(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()

    progress_msg = await message.answer("⏳ Yuborilmoqda...", reply_markup=admin_menu_kb())

    async with async_session() as session:
        success, failed = await do_broadcast(
            bot=bot,
            session=session,
            from_chat_id=data["from_chat"],
            message_id=data["msg_id"],
        )

    await progress_msg.edit_text(
        f"✅ Yuborish yakunlandi!\n"
        f"✔️ Muvaffaqiyatli: <b>{success}</b>\n"
        f"🚫 Bloklagan: <b>{failed}</b>",
        parse_mode="HTML",
    )
