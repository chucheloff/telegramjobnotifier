from aiogram import Bot

from config import CHANNEL_IDS


async def forward_to_channels(
    bot: Bot,
    from_chat_id: int,
    message_id: int,
    channel_ids: list[int] | None = None,
    formatted_text: str | None = None,
) -> list[dict]:
    """Forward a message to one or more channels.

    If formatted_text is provided, sends a new message with that text
    instead of copying the original.

    Args:
        bot: The aiogram Bot instance.
        from_chat_id: Source chat/channel ID.
        message_id: Source message ID.
        channel_ids: Target channel IDs. Defaults to CHANNEL_IDS from config.
        formatted_text: Optional formatted text to send instead of copying.

    Returns:
        List of dicts with 'channel_id' and 'message_id' of forwarded messages.
    """
    targets = channel_ids or CHANNEL_IDS
    results: list[dict] = []

    for target_id in targets:
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
            }
        )

    return results
