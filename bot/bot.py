from aiogram import Bot, Dispatcher

from config import Settings


def create_bot(settings: Settings) -> Bot:
    return Bot(token=settings.bot_token)


def create_dispatcher() -> Dispatcher:
    return Dispatcher()
