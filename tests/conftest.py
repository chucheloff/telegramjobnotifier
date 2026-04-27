"""Test configuration and fixtures."""

import os

import pytest

# Set dummy env vars before any imports
os.environ["BOT_TOKEN"] = "123456:ABCdefGHIjklMNOpqrsTUVwxyz"
os.environ["ADMIN_IDS"] = "123456"
os.environ["CHANNEL_IDS"] = "-1001234567890"
os.environ["WRAPPER_PREFIX"] = ""
os.environ["WRAPPER_SUFFIX"] = ""


@pytest.fixture
def mock_db_row():
    return {
        "id": 1,
        "user_id": 123,
        "chat_id": 456,
        "message_text": "Hello world",
        "edited_text": None,
        "message_type": "text",
        "forward_immediately": 1,
        "status": "pending",
        "sent_at": "2024-01-01T00:00:00+00:00",
        "forwarded_to_channels": None,
        "created_at": "2024-01-01T00:00:00+00:00",
    }
