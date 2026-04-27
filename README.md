# Telegram Job Notifier

A Telegram bot that forwards messages from you (admin) to one or more Telegram channels — with custom message wrappers and restructuring.

## Features

- **Admin Authentication** — only whitelisted users can send messages to channels
- **Custom Wrappers** — prepend/append text, add timestamps, and channel attribution to every forwarded message
- **Message Restructuring** — edit message content (text formatting, content modifications) before forwarding
- **Multi-Channel Support** — forward to multiple channels from a single bot

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
│   └── formatter.py         # Custom wrappers and message restructuring
├── tests/
│   ├── __init__.py
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
WRAPPER_SUFFIX=⏰ {timestamp}
```

| Variable | Description |
|---|---|
| `BOT_TOKEN` | Your Telegram bot token from @BotFather |
| `CHANNEL_IDS` | Comma-separated list of target channel IDs (use negative IDs) |
| `ADMIN_IDS` | Comma-separated list of your Telegram user IDs |
| `WRAPPER_PREFIX` | Text prepended to every forwarded message |
| `WRAPPER_SUFFIX` | Text appended to every forwarded message |

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
| `/add_channel <id>` | Add a new target channel |
| `/remove_channel <id>` | Remove a target channel |

## How It Works

```
You (Admin) ──→ Telegram Bot ──→ [Auth Check] ──→ [Format Message] ──→ Channels
```

1. **Receive** — Bot receives your message in a private chat
2. **Authenticate** — Middleware verifies your user ID is in the admin list
3. **Format** — Formatter applies wrappers and restructuring rules
4. **Forward** — Core forwarder sends the message to all configured channels

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
