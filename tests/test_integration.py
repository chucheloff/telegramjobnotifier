"""Integration tests for server -> bot -> Telegram flow."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from server.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestServerToBotIntegration:
    """Test the full flow: server receives message, calls bot to forward."""

    @patch("server.routes.save_server_message")
    @patch("server.routes.get_message_by_id")
    def test_create_message_triggers_bot_forward(
        self, mock_get, mock_save, client, mock_db_row
    ):
        """When forward_immediately=True, server calls bot's /forward endpoint."""
        mock_save.return_value = 1
        mock_get.return_value = mock_db_row

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "forwarded",
            "message_id": 1,
            "telegram_message_ids": [42],
        }

        with patch("server.routes.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            resp = client.post(
                "/messages",
                json={
                    "text": "Hello world",
                    "user_id": 123,
                    "chat_id": 456,
                    "forward_immediately": True,
                },
            )
            assert resp.status_code == 201
            assert resp.json()["status"] == "pending"
            mock_client.post.assert_called_once()

    @patch("server.routes.save_server_message")
    @patch("server.routes.get_message_by_id")
    def test_create_message_no_forward_skips_bot(
        self, mock_get, mock_save, client, mock_db_row
    ):
        """When forward_immediately=False, server does NOT call bot."""
        mock_save.return_value = 1
        no_forward_row = dict(mock_db_row)
        no_forward_row["forward_immediately"] = 0
        mock_get.return_value = no_forward_row

        with patch("server.routes.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            resp = client.post(
                "/messages",
                json={
                    "text": "Save for later",
                    "user_id": 123,
                    "chat_id": 456,
                    "forward_immediately": False,
                },
            )
            assert resp.status_code == 201
            assert resp.json()["forward_immediately"] is False
            mock_client_cls.assert_not_called()

    @patch("server.routes.save_server_message")
    @patch("server.routes.get_message_by_id")
    def test_bot_failure_sets_status_failed(
        self, mock_get, mock_save, client, mock_db_row
    ):
        """When bot call fails, message status is set to 'failed'."""
        mock_save.return_value = 1
        mock_get.return_value = mock_db_row

        mock_response = AsyncMock()
        mock_response.status_code = 500

        with patch("server.routes.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            resp = client.post(
                "/messages",
                json={
                    "text": "Hello",
                    "user_id": 123,
                    "chat_id": 456,
                    "forward_immediately": True,
                },
            )
            assert resp.status_code == 201
