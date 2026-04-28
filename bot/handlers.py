from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

from bot.middleware import AdminAuthMiddleware
from config import Settings
from services.database import (
    get_message_count,
    get_messages,
    save_message,
)
from services.formatter import format_message
from services.forwarder import forward_to_channels


def register_handlers(dp: Dispatcher, bot: Bot, settings: Settings) -> None:
    """Register all bot handlers and middleware."""
    dp.message.middleware(AdminAuthMiddleware(settings.admin_ids))

    async def _status_handler(message: Message) -> None:
        await status_handler(message, settings)

    async def _forward_message_handler(message: Message) -> None:
        await forward_message_handler(message, bot, settings)

    dp.message.register(start_handler, Command("start"))
    dp.message.register(help_handler, Command("help"))
    dp.message.register(_status_handler, Command("status"))
    dp.message.register(history_handler, Command("history"))
    dp.message.register(_forward_message_handler, F.text, ~F.text.startswith("/"))


async def start_handler(message: Message) -> None:
    await message.answer(
        "👋 Welcome to Telegram Job Notifier!\n\n"
        "Send any text message to this bot and it will be forwarded "
        "to the configured channels.\n\n"
        "Available commands:\n"
        "/start — Show this message\n"
        "/help — Show available commands\n"
        "/status — Show current configuration\n"
        "/history — Show your recent messages"
    )


async def help_handler(message: Message) -> None:
    await start_handler(message)


async def status_handler(message: Message, settings: Settings) -> None:
    total = get_message_count()
    wrappers_enabled = bool(settings.wrapper_prefix or settings.wrapper_suffix)
    await message.answer(
        f"📊 Status:\n"
        f"• Channels: {len(settings.channel_ids)} configured\n"
        f"• Wrappers: {'enabled' if wrappers_enabled else 'disabled'}\n"
        f"• Total messages: {total}"
    )


async def history_handler(message: Message) -> None:
    """Show the user's recent forwarded messages."""
    user_id = message.from_user.id
    messages = get_messages(user_id=user_id, limit=5)
    total = get_message_count(user_id)

    if total == 0:
        await message.answer("📭 No messages sent yet.")
        return

    recent = "\n".join(
        f"• {item['sent_at']}: {(item['message_text'] or '')[:80]}" for item in messages
    )
    await message.answer(
        f"📬 You have sent {total} message(s).\n\nRecent messages:\n{recent}"
    )


async def forward_message_handler(
    message: Message,
    bot: Bot,
    settings: Settings,
) -> None:
    """Handle incoming text messages and forward them to configured channels."""
    if not message.text:
        return

    user_id = message.from_user.id
    chat_id = message.chat.id

    formatted_text = format_message(
        text=message.text,
        prefix=settings.wrapper_prefix,
        suffix=settings.wrapper_suffix,
        include_timestamp=settings.include_timestamp,
    )

    results = await forward_to_channels(
        bot=bot,
        channel_ids=settings.channel_ids,
        from_chat_id=chat_id,
        message_id=message.message_id,
        formatted_text=formatted_text,
    )

    successful_channels = [r["channel_id"] for r in results if r["ok"]]
    save_message(
        user_id=user_id,
        chat_id=chat_id,
        message_text=message.text,
        forwarded_channels=successful_channels,
    )

    success_count = len(successful_channels)
    failed_count = len(results) - success_count
    if failed_count:
        await message.answer(
            f"⚠️ Message forwarded to {success_count} channel(s); {failed_count} failed."
        )
    else:
        await message.answer(f"✅ Message forwarded to {success_count} channel(s).")
