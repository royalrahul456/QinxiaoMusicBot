import logging
from enum import IntEnum
from typing import Optional
from pyrogram.enums import ChatMemberStatus
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.repositories.sudo_repo import SudoRepository

logger = logging.getLogger("QinxiaoMusic.Permissions")


class Role(IntEnum):
    USER = 1
    ADMIN = 2
    SUDO = 3
    OWNER = 4


async def get_user_role(client, chat_id: Optional[int], user_id: int, session: Optional[AsyncSession] = None) -> Role:
    """Determine the highest role of a user."""
    if user_id <= 0:
        return Role.USER

    # 1. Owner Check
    if settings.OWNER_ID > 0 and user_id == settings.OWNER_ID:
        return Role.OWNER

    # 2. Config/DB Sudo Check
    if user_id in settings.SUDO_USERS:
        return Role.SUDO

    if session:
        sudo_repo = SudoRepository(session)
        if await sudo_repo.is_sudo(user_id):
            return Role.SUDO

    # 3. Group Admin Check
    if chat_id and chat_id < 0 and client is not None:
        try:
            member = await client.get_chat_member(chat_id, user_id)
            if member and member.status in (
                ChatMemberStatus.OWNER,
                ChatMemberStatus.ADMINISTRATOR,
                "creator",
                "administrator",
                "owner",
            ):
                return Role.ADMIN
        except Exception as e:
            logger.debug(f"Failed to fetch chat member status for user {user_id} in {chat_id}: {e}")

    return Role.USER


async def is_owner(user_id: int) -> bool:
    return user_id > 0 and settings.OWNER_ID > 0 and user_id == settings.OWNER_ID


async def is_sudo(user_id: int, session: Optional[AsyncSession] = None) -> bool:
    if user_id <= 0:
        return False
    if (settings.OWNER_ID > 0 and user_id == settings.OWNER_ID) or user_id in settings.SUDO_USERS:
        return True
    if session:
        sudo_repo = SudoRepository(session)
        return await sudo_repo.is_sudo(user_id)
    return False


async def is_admin(client, chat_id: int, user_id: int, session: Optional[AsyncSession] = None) -> bool:
    role = await get_user_role(client, chat_id, user_id, session)
    return role >= Role.ADMIN


async def check_min_role(client, chat_id: Optional[int], user_id: int, min_role: Role, session: Optional[AsyncSession] = None) -> bool:
    user_role = await get_user_role(client, chat_id, user_id, session)
    return user_role >= min_role
