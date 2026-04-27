from typing import Final

from dotenv import load_dotenv


def _get_required(key: str) -> str:
    from os import environ

    value = environ.get(key)
    if not value:
        raise ValueError(
            f"Missing required environment variable: {key}\n"
            f"Create a .env file with: {key}=your_value"
        )
    return value


def _get_env(key: str, default: str = "") -> str:
    from os import environ

    return environ.get(key, default)


def _parse_int_list(value: str) -> list[int]:
    if not value.strip():
        return []
    return [int(x.strip()) for x in value.split(",") if x.strip()]


load_dotenv()

BOT_TOKEN: Final[str] = _get_required("BOT_TOKEN")
CHANNEL_IDS: Final[list[int]] = _parse_int_list(_get_env("CHANNEL_IDS", ""))
ADMIN_IDS: Final[list[int]] = _parse_int_list(_get_env("ADMIN_IDS", ""))
WRAPPER_PREFIX: Final[str] = _get_env("WRAPPER_PREFIX", "")
WRAPPER_SUFFIX: Final[str] = _get_env("WRAPPER_SUFFIX", "")
