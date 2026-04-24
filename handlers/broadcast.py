from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from database.base import async_session
from filters import IsAdmin
from keyboards.reply import admin_menu_kb, broadcast_confirm_kb, cancel_kb
from services.broadcast import broadcast as do_broadcast, _send_to_user
from states import BroadcastStates

router = Router()
router.message.filter(IsAdmin())

CANCEL = "❌ Bekor qilish"
TEST = "🧪 Test"
SEND_ALL = "📢 Hammaga yuborish"

# sender_bot will be injected via middleware data (set in bot.py)


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
    # Store the whole message in FSM so we can use it later
    await state.update_data(saved_msg=message.model_dump())
    await state.set_state(BroadcastStates.confirm)
    await message.answer("Xabarni qayerga yuboramiz?", reply_markup=broadcast_confirm_kb())


@router.message(BroadcastStates.confirm, F.text == CANCEL)
async def cancel_confirm(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=admin_menu_kb())


@router.message(BroadcastStates.confirm, F.text == TEST)
async def send_test(message: Message, state: FSMContext, bot: Bot, sender_bot: Bot):
    data = await state.get_data()
    saved = Message.model_validate(data["saved_msg"])
    try:
        await _send_to_user(sender_bot, bot, message.from_user.id, saved)
        await message.answer(
            "✅ Test xabar yuborildi. Hammaga yuborasizmi?",
            reply_markup=broadcast_confirm_kb(),
        )
    except Exception as e:
        await message.answer(f"❌ Xato: {e}", reply_markup=broadcast_confirm_kb())


@router.message(BroadcastStates.confirm, F.text == SEND_ALL)
async def send_all(message: Message, state: FSMContext, bot: Bot, sender_bot: Bot):
    data = await state.get_data()
    saved = Message.model_validate(data["saved_msg"])
    await state.clear()

    progress_msg = await message.answer("⏳ Yuborilmoqda...", reply_markup=admin_menu_kb())

    async with async_session() as session:
        success, failed = await do_broadcast(
            sender_bot=sender_bot,
            receiver_bot=bot,
            session=session,
            msg=saved,
        )

    await progress_msg.edit_text(
        f"✅ Yuborish yakunlandi!\n"
        f"✔️ Muvaffaqiyatli: <b>{success}</b>\n"
        f"🚫 Bloklagan: <b>{failed}</b>",
        parse_mode="HTML",
    )
