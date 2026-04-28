import asyncio
import logging

from bot import create_bot, create_dispatcher
from bot.handlers import register_handlers
from config import get_settings
from services.database import configure_database

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    settings = get_settings()
    configure_database(settings.db_path)
    bot = create_bot(settings)
    dp = create_dispatcher()
    register_handlers(dp, bot, settings)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
