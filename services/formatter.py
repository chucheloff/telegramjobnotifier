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
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    if prefix:
        parts.append(prefix.replace("{timestamp}", timestamp))

    parts.append(text)

    if suffix:
        parts.append(suffix.replace("{timestamp}", timestamp))

    wrapper_has_timestamp = "{timestamp}" in prefix or "{timestamp}" in suffix
    if include_timestamp and not wrapper_has_timestamp:
        parts.append(f"⏰ {timestamp}")

    return "\n".join(parts)
