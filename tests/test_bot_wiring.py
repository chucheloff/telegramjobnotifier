from bot import create_dispatcher
from bot.handlers import register_handlers
from config import Settings


def test_register_handlers_uses_aiogram3_filters():
    settings = Settings(
        bot_token="123456:ABCDEF",
        channel_ids=(-1001,),
        admin_ids=frozenset({42}),
    )
    dp = create_dispatcher()

    register_handlers(dp, bot=object(), settings=settings)

    assert len(dp.message.handlers) == 5
