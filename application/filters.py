from aiogram.filters import BaseFilter
from aiogram.types import Message

from application.database.requests import is_admin


class UnknownCommandFilter(BaseFilter):
    def __init__(self, commands: [str]) -> None:
        self.commands = commands

    async def __call__(self, message: Message) -> bool:
        return message.text not in self.commands


class AdminCommandFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return await is_admin(message.from_user.id)
