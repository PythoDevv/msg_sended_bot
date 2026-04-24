import asyncio
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession
from database.crud import get_all_active_user_ids, set_user_blocked


async def broadcast(
    bot: Bot,
    session: AsyncSession,
    from_chat_id: int,
    message_id: int,
) -> tuple[int, int]:
    user_ids = await get_all_active_user_ids(session)
    success = 0
    failed = 0

    for uid in user_ids:
        try:
            await bot.copy_message(
                chat_id=uid,
                from_chat_id=from_chat_id,
                message_id=message_id,
            )
            success += 1
        except TelegramForbiddenError:
            await set_user_blocked(session, uid, True)
            failed += 1
        except (TelegramBadRequest, Exception):
            failed += 1
        await asyncio.sleep(0.05)

    return success, failed
