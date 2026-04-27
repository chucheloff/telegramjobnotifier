import os
import tempfile

import pytest

import services.database as db


@pytest.fixture(autouse=True)
def _temp_db():
    """Use a temporary database for each test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db.DB_PATH = f.name
    yield
    os.unlink(f.name)


class TestSaveMessage:
    def test_save_text_message(self):
        msg_id = db.save_message(
            user_id=123,
            chat_id=456,
            message_text="Hello world",
            message_type="text",
            forwarded_channels=[-1001, -1002],
        )
        assert msg_id == 1

    def test_save_message_without_channels(self):
        msg_id = db.save_message(
            user_id=789,
            chat_id=101,
            message_text="Test",
        )
        assert msg_id == 1

    def test_save_multiple_messages(self):
        db.save_message(111, 222, "msg1")
        db.save_message(111, 222, "msg2")
        db.save_message(333, 444, "msg3")
        assert db.get_message_count() == 3


class TestGetMessageCount:
    def test_count_all(self):
        db.save_message(1, 2, "a")
        db.save_message(3, 4, "b")
        assert db.get_message_count() == 2

    def test_count_by_user(self):
        db.save_message(100, 200, "msg1")
        db.save_message(100, 200, "msg2")
        db.save_message(300, 400, "msg3")
        assert db.get_message_count(user_id=100) == 2
        assert db.get_message_count(user_id=300) == 1
        assert db.get_message_count(user_id=999) == 0


class TestGetMessages:
    def test_get_all(self):
        db.save_message(1, 2, "msg1")
        db.save_message(3, 4, "msg2")
        messages = db.get_messages(limit=10)
        assert len(messages) == 2

    def test_get_by_user(self):
        db.save_message(100, 200, "from user 100")
        db.save_message(200, 300, "from user 200")
        messages = db.get_messages(user_id=100, limit=10)
        assert len(messages) == 1
        assert messages[0]["message_text"] == "from user 100"

    def test_get_with_pagination(self):
        for i in range(5):
            db.save_message(1, 2, f"msg{i}")
        page1 = db.get_messages(limit=2, offset=0)
        page2 = db.get_messages(limit=2, offset=2)
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0]["message_text"] == "msg4"  # newest first
        assert page2[0]["message_text"] == "msg2"

    def test_message_fields(self):
        db.save_message(42, 99, "hello", forwarded_channels=[-100])
        messages = db.get_messages()
        msg = messages[0]
        assert msg["user_id"] == 42
        assert msg["chat_id"] == 99
        assert msg["message_text"] == "hello"
        assert msg["message_type"] == "text"
        assert msg["forwarded_to_channels"] == "-100"
        assert msg["sent_at"] is not None
        assert msg["created_at"] is not None


class TestGetRecentUsers:
    def test_get_recent_users(self):
        db.save_message(100, 200, "msg1")
        db.save_message(200, 300, "msg2")
        db.save_message(100, 200, "msg3")
        users = db.get_recent_users(limit=10)
        assert len(users) == 2
        assert users[0]["user_id"] == 100
        assert users[0]["message_count"] == 2
        assert users[1]["user_id"] == 200
        assert users[1]["message_count"] == 1

    def test_empty_users(self):
        users = db.get_recent_users()
        assert len(users) == 0


class TestSaveServerMessage:
    def test_save_server_message(self):
        msg_id = db.save_server_message(
            text="API message",
            user_id=555,
            chat_id=666,
            forward_immediately=True,
        )
        assert msg_id == 1
        msg = db.get_message_by_id(msg_id)
        assert msg["message_text"] == "API message"
        assert msg["status"] == "pending"
        assert msg["forward_immediately"] == 1

    def test_save_server_message_not_immediate(self):
        msg_id = db.save_server_message(
            text="Queue this",
            user_id=555,
            chat_id=666,
            forward_immediately=False,
        )
        msg = db.get_message_by_id(msg_id)
        assert msg["forward_immediately"] == 0


class TestGetMessagesWithFilters:
    def test_filter_by_status(self):
        db.save_server_message("pending1", 1, 2, forward_immediately=True)
        db.save_server_message("pending2", 3, 4, forward_immediately=True)
        db.forward_message(1, [-1001])

        pending = db.get_messages_with_filters(status="pending")
        forwarded = db.get_messages_with_filters(status="forwarded")

        assert len(pending) == 1
        assert len(forwarded) == 1
        assert forwarded[0]["message_text"] == "pending1"

    def test_filter_by_date_range(self):
        db.save_server_message("old", 1, 2)
        db.save_server_message("new", 3, 4)

        all_msgs = db.get_messages_with_filters()
        assert len(all_msgs) == 2

    def test_filter_combined(self):
        db.save_server_message("msg1", 1, 2)
        db.save_server_message("msg2", 3, 4)

        result = db.get_messages_with_filters(status="pending", limit=1)
        assert len(result) == 1


class TestGetMessageById:
    def test_get_existing(self):
        msg_id = db.save_message(10, 20, "exists")
        msg = db.get_message_by_id(msg_id)
        assert msg is not None
        assert msg["message_text"] == "exists"
        assert msg["user_id"] == 10

    def test_get_nonexistent(self):
        msg = db.get_message_by_id(99999)
        assert msg is None


class TestEditMessage:
    def test_edit_existing(self):
        msg_id = db.save_message(1, 2, "original")
        result = db.edit_message(msg_id, "edited text")
        assert result is True
        msg = db.get_message_by_id(msg_id)
        assert msg["edited_text"] == "edited text"
        assert msg["status"] == "pending"

    def test_edit_nonexistent(self):
        result = db.edit_message(99999, "nope")
        assert result is False


class TestForwardMessage:
    def test_forward_message(self):
        msg_id = db.save_server_message("to forward", 1, 2)
        result = db.forward_message(msg_id, [-1001, -1002])
        assert result["status"] == "forwarded"
        assert result["message_id"] == msg_id
        assert result["channel_ids"] == [-1001, -1002]

        msg = db.get_message_by_id(msg_id)
        assert msg["status"] == "forwarded"
        assert msg["forwarded_to_channels"] == "-1001,-1002"


class TestUpdateMessageStatus:
    def test_update_status(self):
        msg_id = db.save_server_message("test", 1, 2)
        result = db.update_message_status(msg_id, "failed")
        assert result is True
        msg = db.get_message_by_id(msg_id)
        assert msg["status"] == "failed"

    def test_update_nonexistent(self):
        result = db.update_message_status(99999, "failed")
        assert result is False
