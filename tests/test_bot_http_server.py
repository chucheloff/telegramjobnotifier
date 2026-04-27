"""Tests for bot HTTP server."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from bot.http_server import app


@pytest.fixture
def client():
    return TestClient(app)


class TestBotHealthCheck:
    def test_health_check(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestForwardEndpoint:
    @patch("bot.http_server.bot")
    def test_forward_success(self, mock_bot, client):
        mock_result = MagicMock()
        mock_result.message_id = 42
        mock_bot.send_message.return_value = mock_result

        resp = client.post(
            "/forward",
            json={"message_id": 1, "text": "Hello world"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "forwarded"
        assert data["message_id"] == 1
        assert data["telegram_message_ids"] == [42]
        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args[1]
        assert call_kwargs["text"] == "Hello world"

    @patch("bot.http_server.bot")
    def test_forward_failure(self, mock_bot, client):
        mock_bot.send_message.side_effect = Exception("Telegram API error")

        resp = client.post(
            "/forward",
            json={"message_id": 1, "text": "Hello world"},
        )
        assert resp.status_code == 500
        mock_bot.send_message.assert_called_once()
