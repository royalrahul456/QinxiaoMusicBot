from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatModel


class ChatRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, chat_id: int, title: Optional[str] = None) -> ChatModel:
        stmt = select(ChatModel).where(ChatModel.chat_id == chat_id)
        res = await self.session.execute(stmt)
        chat = res.scalar_one_or_none()

        if not chat:
            chat = ChatModel(chat_id=chat_id, title=title)
            self.session.add(chat)
            await self.session.flush()
        elif title and chat.title != title:
            chat.title = title
            await self.session.flush()

        return chat

    async def update_settings(self, chat_id: int, **kwargs) -> Optional[ChatModel]:
        stmt = select(ChatModel).where(ChatModel.chat_id == chat_id)
        res = await self.session.execute(stmt)
        chat = res.scalar_one_or_none()
        if chat:
            for key, val in kwargs.items():
                if hasattr(chat, key) and val is not None:
                    setattr(chat, key, val)
            await self.session.flush()
        return chat

    async def get_247_chats(self) -> List[ChatModel]:
        stmt = select(ChatModel).where(ChatModel.is_247 == True)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
