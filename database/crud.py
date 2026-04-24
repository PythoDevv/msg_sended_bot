from sqlalchemy import select, func, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Admin
from config import OWNER_ID


async def upsert_user(session: AsyncSession, tg_id: int, full_name: str, username: str | None):
    stmt = insert(User).values(tg_id=tg_id, full_name=full_name, username=username)
    stmt = stmt.on_conflict_do_update(
        index_elements=["tg_id"],
        set_={"full_name": full_name, "username": username},
    )
    await session.execute(stmt)
    await session.commit()


async def set_user_blocked(session: AsyncSession, tg_id: int, blocked: bool):
    await session.execute(update(User).where(User.tg_id == tg_id).values(is_blocked=blocked))
    await session.commit()


async def get_all_active_user_ids(session: AsyncSession) -> list[int]:
    result = await session.execute(select(User.tg_id).where(User.is_blocked == False))
    return [row[0] for row in result.fetchall()]


async def get_all_users(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User))
    return result.scalars().all()


async def get_stats(session: AsyncSession) -> dict:
    total = await session.scalar(select(func.count()).select_from(User))
    blocked = await session.scalar(select(func.count()).select_from(User).where(User.is_blocked == True))
    admins = await session.scalar(select(func.count()).select_from(Admin))
    return {
        "total": total,
        "active": total - blocked,
        "blocked": blocked,
        "admins": admins,
    }


async def is_admin(session: AsyncSession, tg_id: int) -> bool:
    if tg_id == OWNER_ID:
        return True
    result = await session.scalar(select(Admin.tg_id).where(Admin.tg_id == tg_id))
    return result is not None


async def add_admin(session: AsyncSession, tg_id: int, added_by: int):
    stmt = insert(Admin).values(tg_id=tg_id, added_by=added_by)
    stmt = stmt.on_conflict_do_nothing()
    await session.execute(stmt)
    await session.commit()


async def remove_admin(session: AsyncSession, tg_id: int):
    from sqlalchemy import delete
    await session.execute(delete(Admin).where(Admin.tg_id == tg_id))
    await session.commit()


async def upsert_users_bulk(session: AsyncSession, users: list[dict]):
    for u in users:
        stmt = insert(User).values(
            tg_id=u["tg_id"],
            full_name=u["full_name"],
            username=u.get("username"),
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["tg_id"],
            set_={"full_name": u["full_name"], "username": u.get("username")},
        )
        await session.execute(stmt)
    await session.commit()
