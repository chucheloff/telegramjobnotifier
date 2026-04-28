from types import SimpleNamespace

import pytest
from aiogram.exceptions import TelegramAPIError
from aiogram.methods import SendMessage

from services.forwarder import forward_to_channels


class FakeBot:
    def __init__(self, failing_channel: int | None = None) -> None:
        self.failing_channel = failing_channel

    async def send_message(self, chat_id: int, text: str):
        if chat_id == self.failing_channel:
            method = SendMessage(chat_id=chat_id, text=text)
            raise TelegramAPIError(method=method, message="channel unavailable")
        return SimpleNamespace(message_id=chat_id * -1)

    async def copy_message(self, chat_id: int, from_chat_id: int, message_id: int):
        return SimpleNamespace(message_id=message_id)


@pytest.mark.asyncio
async def test_forward_to_channels_records_successes():
    results = await forward_to_channels(
        bot=FakeBot(),
        channel_ids=(-1001, -1002),
        from_chat_id=1,
        message_id=10,
        formatted_text="hello",
    )

    assert [result["ok"] for result in results] == [True, True]
    assert [result["channel_id"] for result in results] == [-1001, -1002]


@pytest.mark.asyncio
async def test_forward_to_channels_continues_after_telegram_error():
    results = await forward_to_channels(
        bot=FakeBot(failing_channel=-1001),
        channel_ids=(-1001, -1002),
        from_chat_id=1,
        message_id=10,
        formatted_text="hello",
    )

    assert results[0]["ok"] is False
    assert results[0]["message_id"] is None
    assert "channel unavailable" in results[0]["error"]
    assert results[1]["ok"] is True
