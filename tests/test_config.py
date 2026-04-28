from pathlib import Path

import pytest

from config import Settings


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "123456:ABCDEF")
    monkeypatch.setenv("CHANNEL_IDS", "-1001,-1002")
    monkeypatch.setenv("ADMIN_IDS", "42,99")
    monkeypatch.setenv("WRAPPER_PREFIX", "[prefix]")
    monkeypatch.setenv("INCLUDE_TIMESTAMP", "false")
    monkeypatch.setenv("DB_PATH", "/tmp/messages-test.db")

    settings = Settings.from_env()

    assert settings.bot_token == "123456:ABCDEF"
    assert settings.channel_ids == (-1001, -1002)
    assert settings.admin_ids == frozenset({42, 99})
    assert settings.wrapper_prefix == "[prefix]"
    assert settings.include_timestamp is False
    assert settings.db_path == Path("/tmp/messages-test.db")


def test_settings_requires_channels(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "123456:ABCDEF")
    monkeypatch.delenv("CHANNEL_IDS", raising=False)
    monkeypatch.setenv("ADMIN_IDS", "42")

    with pytest.raises(ValueError, match="CHANNEL_IDS"):
        Settings.from_env()


def test_settings_rejects_invalid_integer_lists(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "123456:ABCDEF")
    monkeypatch.setenv("CHANNEL_IDS", "-1001")
    monkeypatch.setenv("ADMIN_IDS", "not-an-id")

    with pytest.raises(ValueError, match="comma-separated integers"):
        Settings.from_env()
