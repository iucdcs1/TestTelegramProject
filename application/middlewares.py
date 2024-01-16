from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message


class CounterMiddleware(BaseMiddleware):
    def __init__(self, unrestricted_users):
        self.unrestricted_users = unrestricted_users

    async def __call__(self,
                       handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
                       event: Message,
                       data: Dict[str, Any]) -> Any:
        if str(event.from_user.id) in self.unrestricted_users:
            return await handler(event, data)
        else:
            await event.answer("К сожалению, Вас нет в whitelist`е бота.\n"
                               "Если у Вас должен быть доступ - пожалуйста, напишите @NPggL",
                               show_alert=True
                               )
            return
