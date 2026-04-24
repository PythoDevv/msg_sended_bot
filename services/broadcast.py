import asyncio
import io
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.types import Message, BufferedInputFile
from sqlalchemy.ext.asyncio import AsyncSession
from database.crud import get_all_active_user_ids, set_user_blocked


async def _send_to_user(sender_bot: Bot, receiver_bot: Bot, user_id: int, msg: Message):
    """Send a message to user using sender_bot, downloading files via receiver_bot if needed."""

    kwargs = {}
    if msg.caption:
        kwargs["caption"] = msg.caption
        kwargs["caption_entities"] = msg.caption_entities or []

    if msg.text:
        await sender_bot.send_message(
            chat_id=user_id,
            text=msg.text,
            entities=msg.entities or [],
        )

    elif msg.photo:
        file_bytes = await _download(receiver_bot, msg.photo[-1].file_id)
        await sender_bot.send_photo(
            chat_id=user_id,
            photo=BufferedInputFile(file_bytes, "photo.jpg"),
            **kwargs,
        )

    elif msg.video:
        file_bytes = await _download(receiver_bot, msg.video.file_id)
        await sender_bot.send_video(
            chat_id=user_id,
            video=BufferedInputFile(file_bytes, msg.video.file_name or "video.mp4"),
            **kwargs,
        )

    elif msg.animation:
        file_bytes = await _download(receiver_bot, msg.animation.file_id)
        await sender_bot.send_animation(
            chat_id=user_id,
            animation=BufferedInputFile(file_bytes, msg.animation.file_name or "anim.gif"),
            **kwargs,
        )

    elif msg.document:
        file_bytes = await _download(receiver_bot, msg.document.file_id)
        await sender_bot.send_document(
            chat_id=user_id,
            document=BufferedInputFile(file_bytes, msg.document.file_name or "file"),
            **kwargs,
        )

    elif msg.voice:
        file_bytes = await _download(receiver_bot, msg.voice.file_id)
        await sender_bot.send_voice(
            chat_id=user_id,
            voice=BufferedInputFile(file_bytes, "voice.ogg"),
            **kwargs,
        )

    elif msg.video_note:
        file_bytes = await _download(receiver_bot, msg.video_note.file_id)
        await sender_bot.send_video_note(
            chat_id=user_id,
            video_note=BufferedInputFile(file_bytes, "vnote.mp4"),
        )

    elif msg.audio:
        file_bytes = await _download(receiver_bot, msg.audio.file_id)
        await sender_bot.send_audio(
            chat_id=user_id,
            audio=BufferedInputFile(file_bytes, msg.audio.file_name or "audio.mp3"),
            **kwargs,
        )

    elif msg.sticker:
        # Sticker file_id works across bots for sending
        await sender_bot.send_sticker(chat_id=user_id, sticker=msg.sticker.file_id)


async def _download(bot: Bot, file_id: str) -> bytes:
    file = await bot.get_file(file_id)
    buf = io.BytesIO()
    await bot.download_file(file.file_path, buf)
    return buf.getvalue()


async def broadcast(
    sender_bot: Bot,
    receiver_bot: Bot,
    session: AsyncSession,
    msg: Message,
) -> tuple[int, int]:
    user_ids = await get_all_active_user_ids(session)
    success = 0
    failed = 0

    for uid in user_ids:
        try:
            await _send_to_user(sender_bot, receiver_bot, uid, msg)
            success += 1
        except TelegramForbiddenError:
            await set_user_blocked(session, uid, True)
            failed += 1
        except (TelegramBadRequest, Exception):
            failed += 1
        await asyncio.sleep(0.04)

    return success, failed
