"""Tests for FastAPI server routes."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from server.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthCheck:
    def test_health_check(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestCreateMessage:
    @patch("server.routes.save_server_message")
    @patch("server.routes.get_message_by_id")
    def test_create_message_default_forward(
        self, mock_get, mock_save, client, mock_db_row
    ):
        mock_save.return_value = 1
        mock_get.return_value = mock_db_row

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
        data = resp.json()
        assert data["message_text"] == "Hello world"
        assert data["user_id"] == 123
        assert data["status"] == "pending"
        assert data["forward_immediately"] is True

    @patch("server.routes.save_server_message")
    @patch("server.routes.get_message_by_id")
    def test_create_message_no_forward(self, mock_get, mock_save, client, mock_db_row):
        mock_save.return_value = 1
        no_forward_row = dict(mock_db_row)
        no_forward_row["forward_immediately"] = 0
        mock_get.return_value = no_forward_row

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
        data = resp.json()
        assert data["forward_immediately"] is False
        assert data["status"] == "pending"

    @patch("server.routes.save_server_message")
    @patch("server.routes.get_message_by_id")
    def test_create_message_retrieve_failure(self, mock_get, mock_save, client):
        mock_save.return_value = 1
        mock_get.return_value = None

        resp = client.post(
            "/messages",
            json={"text": "Hello", "user_id": 123, "chat_id": 456},
        )
        assert resp.status_code == 500
        assert resp.json()["detail"] == "Failed to retrieve message"


class TestListMessages:
    @patch("server.routes.get_messages_with_filters")
    def test_list_messages_all(self, mock_filter, client, mock_db_row):
        mock_filter.return_value = [mock_db_row]

        resp = client.get("/messages")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["message_text"] == "Hello world"

    @patch("server.routes.get_messages_with_filters")
    def test_list_messages_with_filters(self, mock_filter, client, mock_db_row):
        mock_filter.return_value = [mock_db_row]

        resp = client.get(
            "/messages",
            params={
                "from_date": "2024-01-01",
                "to_date": "2024-12-31",
                "status": "pending",
                "limit": 10,
                "offset": 0,
            },
        )
        assert resp.status_code == 200
        mock_filter.assert_called_once()
        call_kwargs = mock_filter.call_args[1]
        assert call_kwargs["from_date"] == "2024-01-01"
        assert call_kwargs["status"] == "pending"
        assert call_kwargs["limit"] == 10

    @patch("server.routes.get_messages_with_filters")
    def test_list_messages_pagination(self, mock_filter, client, mock_db_row):
        mock_filter.return_value = [mock_db_row]

        resp = client.get("/messages", params={"limit": 5, "offset": 10})
        assert resp.status_code == 200
        call_kwargs = mock_filter.call_args[1]
        assert call_kwargs["limit"] == 5
        assert call_kwargs["offset"] == 10


class TestGetMessage:
    @patch("server.routes.get_message_by_id")
    def test_get_message_found(self, mock_get, client, mock_db_row):
        mock_get.return_value = mock_db_row

        resp = client.get("/messages/1")
        assert resp.status_code == 200
        assert resp.json()["message_text"] == "Hello world"

    @patch("server.routes.get_message_by_id")
    def test_get_message_not_found(self, mock_get, client):
        mock_get.return_value = None

        resp = client.get("/messages/999")
        assert resp.status_code == 404


class TestEditMessage:
    @patch("server.routes.edit_message")
    @patch("server.routes.get_message_by_id")
    def test_edit_message_success(self, mock_get, mock_edit, client, mock_db_row):
        mock_edit.return_value = True
        mock_get.return_value = mock_db_row

        resp = client.put("/messages/1", json={"text": "Updated text"})
        assert resp.status_code == 200
        mock_edit.assert_called_once_with(1, "Updated text")

    @patch("server.routes.edit_message")
    def test_edit_message_not_found(self, mock_edit, client):
        mock_edit.return_value = False

        resp = client.put("/messages/999", json={"text": "Updated"})
        assert resp.status_code == 404


class TestForwardMessage:
    @patch("server.routes.forward_message")
    @patch("server.routes.get_message_by_id")
    def test_forward_message_success(self, mock_get, mock_forward, client, mock_db_row):
        mock_get.return_value = mock_db_row
        mock_forward.return_value = {
            "message_id": 1,
            "status": "forwarded",
            "channel_ids": [-1001],
        }

        resp = client.post("/messages/1/forward", params={"channel_ids": [-1001]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "forwarded"
        assert data["message_id"] == 1

    @patch("server.routes.forward_message")
    @patch("server.routes.get_message_by_id")
    def test_forward_message_not_found(self, mock_get, mock_forward, client):
        mock_get.return_value = None

        resp = client.post("/messages/999/forward", params={"channel_ids": [-1001]})
        assert resp.status_code == 404

    @patch("server.routes.forward_message")
    @patch("server.routes.get_message_by_id")
    def test_forward_message_already_forwarded(
        self, mock_get, mock_forward, client, mock_db_row
    ):
        already_forwarded = dict(mock_db_row)
        already_forwarded["status"] = "forwarded"
        mock_get.return_value = already_forwarded

        resp = client.post("/messages/1/forward", params={"channel_ids": [-1001]})
        assert resp.status_code == 400

    @patch("server.routes.forward_message")
    @patch("server.routes.get_message_by_id")
    def test_forward_message_missing_channel_ids(
        self, mock_get, mock_forward, client, mock_db_row
    ):
        mock_get.return_value = mock_db_row

        resp = client.post("/messages/1/forward")
        assert resp.status_code == 400
