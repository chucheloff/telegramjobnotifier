from typing import Any, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message

from config import ADMIN_IDS


class AdminAuthMiddleware(BaseMiddleware):
    """Only allow admin users to interact with the bot."""

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Any],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        if not event.from_user or event.from_user.id not in ADMIN_IDS:
            await event.answer("⛔ Access denied. You are not an authorized admin.")
            return

        return await handler(event, data)
