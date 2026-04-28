from dataclasses import dataclass
from os import environ
from pathlib import Path

from dotenv import load_dotenv


def _get_required(key: str) -> str:
    value = environ.get(key)
    if not value:
        raise ValueError(
            f"Missing required environment variable: {key}\n"
            f"Create a .env file with: {key}=your_value"
        )
    return value


def _get_env(key: str, default: str = "") -> str:
    return environ.get(key, default)


def _parse_int_list(value: str) -> list[int]:
    if not value.strip():
        return []
    try:
        return [int(x.strip()) for x in value.split(",") if x.strip()]
    except ValueError as exc:
        raise ValueError(f"Expected comma-separated integers, got: {value!r}") from exc


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    bot_token: str
    channel_ids: tuple[int, ...]
    admin_ids: frozenset[int]
    wrapper_prefix: str = ""
    wrapper_suffix: str = ""
    include_timestamp: bool = True
    db_path: Path = Path("data/messages.db")

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        channel_ids = tuple(_parse_int_list(_get_env("CHANNEL_IDS", "")))
        admin_ids = frozenset(_parse_int_list(_get_env("ADMIN_IDS", "")))

        if not channel_ids:
            raise ValueError("CHANNEL_IDS must contain at least one channel ID")
        if not admin_ids:
            raise ValueError("ADMIN_IDS must contain at least one admin user ID")

        return cls(
            bot_token=_get_required("BOT_TOKEN"),
            channel_ids=channel_ids,
            admin_ids=admin_ids,
            wrapper_prefix=_get_env("WRAPPER_PREFIX", ""),
            wrapper_suffix=_get_env("WRAPPER_SUFFIX", ""),
            include_timestamp=_parse_bool(_get_env("INCLUDE_TIMESTAMP", "true")),
            db_path=Path(_get_env("DB_PATH", "data/messages.db")),
        )


def get_settings() -> Settings:
    return Settings.from_env()
