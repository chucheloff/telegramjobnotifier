import asyncio
import logging

from bot import bot, dp
from bot.handlers import register_handlers

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    register_handlers(dp)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
