"""Tests for bot handlers and middleware."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers import (
    forward_message_handler,
    help_handler,
    history_handler,
    start_handler,
    status_handler,
)
from bot.middleware import AdminAuthMiddleware


@pytest.fixture
def mock_message():
    msg = MagicMock()
    msg.text = "Hello world"
    msg.from_user.id = 123456
    msg.chat.id = 789012
    msg.message_id = 1
    msg.answer = AsyncMock()
    return msg


@pytest.fixture
def mock_admin_message():
    msg = MagicMock()
    msg.text = "Hello world"
    msg.from_user.id = 123456  # matches ADMIN_IDS in conftest
    msg.chat.id = 789012
    msg.message_id = 1
    msg.answer = AsyncMock()
    return msg


@pytest.fixture
def mock_non_admin_message():
    msg = MagicMock()
    msg.text = "Hello world"
    msg.from_user.id = 999999  # not in ADMIN_IDS
    msg.chat.id = 789012
    msg.message_id = 1
    msg.answer = AsyncMock()
    return msg


class TestAdminAuthMiddleware:
    @pytest.mark.asyncio
    async def test_admin_allowed(self, mock_admin_message):
        """Admin users should pass through to the handler."""
        middleware = AdminAuthMiddleware()
        mock_handler = AsyncMock(return_value=None)

        await middleware(mock_handler, mock_admin_message, {})

        # The handler should have been called
        mock_handler.assert_called_once_with(mock_admin_message, {})
        # Admin should NOT get denied message
        mock_admin_message.answer.assert_not_called()

    @pytest.mark.asyncio
    async def test_non_admin_denied(self, mock_non_admin_message):
        """Non-admin users should be denied access."""
        middleware = AdminAuthMiddleware()
        mock_handler = AsyncMock(return_value=None)

        await middleware(mock_handler, mock_non_admin_message, {})

        # The handler should NOT have been called
        mock_handler.assert_not_called()
        # Non-admin should get denied message
        mock_non_admin_message.answer.assert_called_once_with(
            "⛔ Access denied. You are not an authorized admin."
        )

    @pytest.mark.asyncio
    async def test_no_from_user(self):
        """Messages without from_user should be denied."""
        middleware = AdminAuthMiddleware()
        mock_handler = AsyncMock(return_value=None)
        msg = MagicMock()
        msg.from_user = None
        msg.answer = AsyncMock()

        await middleware(mock_handler, msg, {})

        mock_handler.assert_not_called()
        msg.answer.assert_called_once()


class TestStartHandler:
    @pytest.mark.asyncio
    async def test_start_handler(self, mock_admin_message):
        await start_handler(mock_admin_message)
        mock_admin_message.answer.assert_called_once()
        response = mock_admin_message.answer.call_args[0][0]
        assert "Welcome to Telegram Job Notifier" in response
        assert "/start" in response
        assert "/help" in response
        assert "/status" in response
        assert "/history" in response


class TestHelpHandler:
    @pytest.mark.asyncio
    async def test_help_handler_same_as_start(self, mock_admin_message):
        await help_handler(mock_admin_message)
        mock_admin_message.answer.assert_called_once()
        response = mock_admin_message.answer.call_args[0][0]
        assert "Welcome to Telegram Job Notifier" in response


class TestStatusHandler:
    @patch("bot.handlers.get_message_count")
    @pytest.mark.asyncio
    async def test_status_handler(self, mock_count, mock_admin_message):
        mock_count.return_value = 42
        await status_handler(mock_admin_message)
        mock_admin_message.answer.assert_called_once()
        response = mock_admin_message.answer.call_args[0][0]
        assert "📊 Status:" in response
        assert "Channels: 1 configured" in response
        assert "Total messages: 42" in response


class TestHistoryHandler:
    @patch("bot.handlers.get_message_count")
    @patch("bot.handlers.get_recent_users")
    @pytest.mark.asyncio
    async def test_history_handler_with_messages(
        self, mock_recent, mock_count, mock_admin_message
    ):
        mock_count.return_value = 5
        mock_recent.return_value = [{"user_id": 123456}]
        await history_handler(mock_admin_message)
        mock_admin_message.answer.assert_called_once()
        response = mock_admin_message.answer.call_args[0][0]
        assert "You have sent 5 message(s)" in response

    @patch("bot.handlers.get_message_count")
    @pytest.mark.asyncio
    async def test_history_handler_no_messages(self, mock_count, mock_admin_message):
        mock_count.return_value = 0
        await history_handler(mock_admin_message)
        mock_admin_message.answer.assert_called_once()
        response = mock_admin_message.answer.call_args[0][0]
        assert "No messages sent yet" in response


class TestForwardMessageHandler:
    @patch("bot.handlers.forward_to_channels")
    @patch("bot.handlers.save_message")
    @patch("bot.handlers.format_message")
    @patch("bot.handlers.bot")
    @pytest.mark.asyncio
    async def test_forward_with_text(
        self, mock_bot, mock_format, mock_save, mock_forward, mock_admin_message
    ):
        mock_format.return_value = "[NOTICE] Hello world"
        mock_result = MagicMock()
        mock_result.message_id = 42
        mock_forward.return_value = [{"channel_id": -1001, "message_id": 42}]

        await forward_message_handler(mock_admin_message)

        mock_format.assert_called_once_with(text="Hello world", prefix="", suffix="")
        mock_forward.assert_called_once()
        mock_save.assert_called_once()
        mock_admin_message.answer.assert_called_once()
        response = mock_admin_message.answer.call_args[0][0]
        assert "✅ Message forwarded to 1 channel(s)" in response

    @patch("bot.handlers.forward_to_channels")
    @patch("bot.handlers.save_message")
    @patch("bot.handlers.format_message")
    @patch("bot.handlers.bot")
    @pytest.mark.asyncio
    async def test_forward_no_text(
        self, mock_bot, mock_format, mock_save, mock_forward, mock_message
    ):
        """Messages without text should be ignored."""
        mock_message.text = None
        await forward_message_handler(mock_message)
        mock_forward.assert_not_called()
        mock_save.assert_not_called()
        mock_message.answer.assert_not_called()
