from aiogram import Dispatcher
from aiogram.types import Message

from bot.bot import bot
from bot.middleware import AdminAuthMiddleware
from config import (
    CHANNEL_IDS,
    WRAPPER_PREFIX,
    WRAPPER_SUFFIX,
)
from services.formatter import format_message
from services.forwarder import forward_to_channels


def register_handlers(dp: Dispatcher) -> None:
    """Register all bot handlers and middleware."""
    dp.message.middleware(AdminAuthMiddleware())
    dp.message.register(forward_message_handler)
    dp.message.register(start_handler, command="start")
    dp.message.register(help_handler, command="help")
    dp.message.register(status_handler, command="status")


async def start_handler(message: Message) -> None:
    await message.answer(
        "👋 Welcome to Telegram Job Notifier!\n\n"
        "Send any text message to this bot and it will be forwarded "
        "to the configured channels.\n\n"
        "Available commands:\n"
        "/start — Show this message\n"
        "/help — Show available commands\n"
        "/status — Show current configuration"
    )


async def help_handler(message: Message) -> None:
    await start_handler(message)


async def status_handler(message: Message) -> None:
    await message.answer(
        f"📊 Status:\n"
        f"• Channels: {len(CHANNEL_IDS)} configured\n"
        f"• Wrappers: {'enabled' if WRAPPER_PREFIX or WRAPPER_SUFFIX else 'disabled'}\n"
        f"• Admin auth: {'enabled' if message.from_user else 'disabled'}"
    )


async def forward_message_handler(message: Message) -> None:
    """Handle incoming text messages and forward them to configured channels."""
    if not message.text:
        return

    formatted_text = format_message(
        text=message.text,
        prefix=WRAPPER_PREFIX,
        suffix=WRAPPER_SUFFIX,
    )

    results = await forward_to_channels(
        bot=bot,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
        formatted_text=formatted_text,
    )

    success_count = len(results)
    await message.answer(f"✅ Message forwarded to {success_count} channel(s).")
