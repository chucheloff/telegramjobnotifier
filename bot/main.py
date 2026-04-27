import asyncio
import logging

from bot.bot import bot, dp
from bot.handlers import register_handlers
from bot.http_server import app as http_app

logging.basicConfig(level=logging.INFO)


async def start_http_server() -> None:
    """Start the bot's HTTP server for receiving forward requests."""
    from uvicorn import Config, Server

    config = Config(http_app, host="0.0.0.0", port=8080, log_level="info")
    server = Server(config)
    await server.serve()


async def main() -> None:
    register_handlers(dp)
    # Run both Telegram polling and HTTP server concurrently
    await asyncio.gather(
        dp.start_polling(bot),
        start_http_server(),
    )


if __name__ == "__main__":
    asyncio.run(main())
