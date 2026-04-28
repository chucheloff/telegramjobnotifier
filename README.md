# Telegram Job Notifier

A Telegram bot that forwards text messages from approved admins to one or more Telegram channels, with optional message wrappers and timestamps.

## Features

- **Admin Authentication** — only whitelisted users can send messages to channels
- **Custom Wrappers** — prepend/append text and add timestamps to forwarded messages
- **Message History** — store forwarded text messages in SQLite for lightweight auditing
- **Multi-Channel Support** — forward to multiple channels from a single bot
- **Partial Failure Reporting** — continue forwarding if one channel fails

## Project Structure

```
telegramjobnotifier/
├── main.py                  # Bot entry point
├── config.py                # Configuration: bot token, channel IDs, admin IDs
├── .env                     # Secrets (not tracked in git)
├── bot/
│   ├── __init__.py
│   ├── bot.py               # Bot setup and dispatcher
│   ├── handlers.py          # Message forwarding and admin commands
│   └── middleware.py        # Admin authentication middleware
├── services/
│   ├── __init__.py
│   ├── forwarder.py         # Core forwarding logic
│   ├── database.py          # SQLite message history
│   └── formatter.py         # Custom wrappers and timestamp formatting
├── tests/
│   ├── __init__.py
│   ├── test_database.py
│   └── test_formatter.py
└── .gitignore
```

## Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) — fast Python package manager
- A Telegram Bot Token ([get one from @BotFather](https://t.me/BotFather))

### Installation

```bash
# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your bot token, channel IDs, and admin IDs
```

### Running

```bash
uv run main.py
```

## Configuration

Create a `.env` file in the project root:

```env
BOT_TOKEN=your_telegram_bot_token
CHANNEL_IDS=-1001234567890,-1000987654321
ADMIN_IDS=123456789
WRAPPER_PREFIX=[Posted via Telegram Job Notifier]
WRAPPER_SUFFIX=Posted at {timestamp}
INCLUDE_TIMESTAMP=true
DB_PATH=data/messages.db
```

| Variable | Description |
|---|---|
| `BOT_TOKEN` | Your Telegram bot token from @BotFather |
| `CHANNEL_IDS` | Comma-separated list of target channel IDs (use negative IDs) |
| `ADMIN_IDS` | Comma-separated list of your Telegram user IDs |
| `WRAPPER_PREFIX` | Text prepended to every forwarded message |
| `WRAPPER_SUFFIX` | Text appended to every forwarded message |
| `INCLUDE_TIMESTAMP` | Add a timestamp when prefix/suffix do not include `{timestamp}` |
| `DB_PATH` | SQLite database path for message history |

### Getting Your Telegram IDs

- **Bot Token**: Send `/newbot` to [@BotFather](https://t.me/BotFather)
- **User ID**: Send a message to [@userinfobot](https://t.me/userinfobot)
- **Channel ID**: Add the bot to the channel, then send a message and check the bot's update via [@getidsbot](https://t.me/getidsbot) (channel IDs are negative)

## Usage

### Sending a Message

Simply send any text message to the bot in a private chat. The bot will:

1. Verify you're an authorized admin
2. Apply the configured wrapper (prefix + suffix)
3. Forward the message to all configured channels

### Admin Commands

| Command | Description |
|---|---|
| `/start` | Start the bot and show help |
| `/help` | Show available commands and usage |
| `/status` | Show current configuration and channel status |
| `/history` | Show your recent forwarded messages |

## How It Works

```
You (Admin) ──→ Telegram Bot ──→ [Auth Check] ──→ [Format Message] ──→ Channels
```

1. **Receive** — Bot receives your message in a private chat
2. **Authenticate** — Middleware verifies your user ID is in the admin list
3. **Format** — Formatter applies wrappers and timestamp rules
4. **Forward** — Core forwarder sends the message to all configured channels
5. **Record** — Successful forwarding targets are saved to SQLite

## Data Storage

The bot stores admin user IDs, chat IDs, message text, timestamps, and successful target channel IDs in SQLite. Set `DB_PATH` to control the database location. Do not use this history database for sensitive content unless that retention behavior is acceptable for your deployment.

## Development

```bash
# Run tests
uv run pytest

# Run linter
uv run ruff check .

# Format code
uv run ruff format .
```

## Tech Stack

- **[aiogram 3.x](https://docs.aiogram.dev/)** — Async Telegram Bot API framework
- **[uv](https://github.com/astral-sh/uv)** — Fast Python package manager
- **[python-dotenv](https://github.com/theskumar/python-dotenv)** — Environment variable management

## License

MIT
