"""Tests for services/forwarder.py."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.forwarder import forward_to_channels


@pytest.fixture
def mock_bot():
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    bot.copy_message = AsyncMock()
    return bot


@pytest.fixture
def mock_send_result():
    result = MagicMock()
    result.message_id = 42
    return result


class TestForwardToChannels:
    @pytest.mark.asyncio
    async def test_forward_with_formatted_text(self, mock_bot, mock_send_result):
        """When formatted_text is provided, send_message is used."""
        mock_bot.send_message.return_value = mock_send_result

        result = await forward_to_channels(
            bot=mock_bot,
            from_chat_id=100,
            message_id=1,
            channel_ids=[-1001, -1002],
            formatted_text="Custom formatted text",
        )

        assert len(result) == 2
        assert result[0]["channel_id"] == -1001
        assert result[0]["message_id"] == 42
        assert result[1]["channel_id"] == -1002
        assert result[1]["message_id"] == 42
        assert mock_bot.send_message.call_count == 2
        mock_bot.copy_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_forward_without_formatted_text(self, mock_bot, mock_send_result):
        """When no formatted_text, copy_message is used."""
        mock_bot.copy_message.return_value = mock_send_result

        result = await forward_to_channels(
            bot=mock_bot,
            from_chat_id=100,
            message_id=1,
            channel_ids=[-1001],
        )

        assert len(result) == 1
        assert result[0]["channel_id"] == -1001
        assert result[0]["message_id"] == 42
        mock_bot.copy_message.assert_called_once_with(
            chat_id=-1001, from_chat_id=100, message_id=1
        )
        mock_bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_forward_uses_default_channels(self, mock_bot, mock_send_result):
        """When channel_ids is None, uses CHANNEL_IDS from config."""
        mock_bot.send_message.return_value = mock_send_result

        with patch("services.forwarder.CHANNEL_IDS", [-1003, -1004, -1005]):
            result = await forward_to_channels(
                bot=mock_bot,
                from_chat_id=100,
                message_id=1,
                channel_ids=None,
                formatted_text="test",
            )

        assert len(result) == 3
        assert mock_bot.send_message.call_count == 3

    @pytest.mark.asyncio
    async def test_forward_empty_channels(self, mock_bot):
        """When no channels configured, returns empty list."""
        result = await forward_to_channels(
            bot=mock_bot,
            from_chat_id=100,
            message_id=1,
            channel_ids=[],
            formatted_text="test",
        )

        assert result == []
        mock_bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_forward_single_channel(self, mock_bot, mock_send_result):
        """Single channel forwarding works correctly."""
        mock_bot.send_message.return_value = mock_send_result

        result = await forward_to_channels(
            bot=mock_bot,
            from_chat_id=100,
            message_id=1,
            channel_ids=[-1001],
            formatted_text="single",
        )

        assert len(result) == 1
        assert result[0]["channel_id"] == -1001
