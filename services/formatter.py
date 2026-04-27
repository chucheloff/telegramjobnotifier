from datetime import datetime, timezone


def format_message(
    text: str,
    prefix: str = "",
    suffix: str = "",
    include_timestamp: bool = True,
) -> str:
    """Format a message with optional prefix, suffix, and timestamp.

    Args:
        text: The original message text.
        prefix: Text to prepend before the message.
        suffix: Text to append after the message.
        include_timestamp: Whether to add a timestamp.

    Returns:
        The formatted message string.
    """
    parts: list[str] = []

    if prefix:
        parts.append(prefix)

    parts.append(text)

    if suffix:
        parts.append(suffix)

    if include_timestamp:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        parts.append(f"⏰ {timestamp}")

    return "\n".join(parts)
