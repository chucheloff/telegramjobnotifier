import logging
from typing import TypedDict

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

logger = logging.getLogger(__name__)


class ForwardResult(TypedDict):
    channel_id: int
    message_id: int | None
    ok: bool
    error: str | None


async def forward_to_channels(
    bot: Bot,
    channel_ids: tuple[int, ...] | list[int],
    from_chat_id: int,
    message_id: int,
    formatted_text: str | None = None,
) -> list[ForwardResult]:
    """Forward a message to one or more channels.

    If formatted_text is provided, sends a new message with that text
    instead of copying the original.

    Args:
        bot: The aiogram Bot instance.
        channel_ids: Target channel IDs.
        from_chat_id: Source chat/channel ID.
        message_id: Source message ID.
        formatted_text: Optional formatted text to send instead of copying.

    Returns:
        List of dicts with per-channel forwarding status.
    """
    results: list[ForwardResult] = []

    for target_id in channel_ids:
        try:
            if formatted_text:
                result = await bot.send_message(
                    chat_id=target_id,
                    text=formatted_text,
                )
            else:
                result = await bot.copy_message(
                    chat_id=target_id,
                    from_chat_id=from_chat_id,
                    message_id=message_id,
                )
            results.append(
                {
                    "channel_id": target_id,
                    "message_id": result.message_id,
                    "ok": True,
                    "error": None,
                }
            )
        except TelegramAPIError as exc:
            logger.warning("Failed to forward message to %s: %s", target_id, exc)
            results.append(
                {
                    "channel_id": target_id,
                    "message_id": None,
                    "ok": False,
                    "error": str(exc),
                }
            )

    return results
