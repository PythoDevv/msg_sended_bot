from aiogram.filters import BaseFilter
from aiogram.types import Message
from database.base import async_session
from database.crud import is_admin as _is_admin


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        async with async_session() as session:
            return await _is_admin(session, message.from_user.id)
