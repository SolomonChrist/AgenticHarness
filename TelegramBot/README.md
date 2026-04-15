# TELEGRAM BOT

Optional Telegram bridge for the active `Chief_of_Staff` / MasterBot.

This server does not manage the swarm directly.

Its only job is to let you chat with the active MasterBot when the chosen harness does not natively support Telegram or remote messaging.

## Model

- Telegram bot receives your message
- it writes that message into `_messages/Chief_of_Staff.md`
- the active MasterBot reads that file and responds by writing to `_messages/human_<HumanID>.md`
- the Telegram bot forwards those replies back to your phone

The Telegram layer is a transport bridge only.

The MasterBot remains the one that communicates with the system.

## Required Files In The Harness Root

- `AGENTIC_HARNESS.md`
- `HUMANS.md`
- `_messages/Chief_of_Staff.md`
- `_messages/human_<HumanID>.md`

## Setup

1. Copy the template:

```powershell
copy .env.telegram.template .env.telegram
```

2. Fill in:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ALLOWED_USER_IDS`
- `HARNESS_ROOT`
- `HUMAN_ID`

3. Install dependencies:

```powershell
pip install requests python-dotenv
```

4. Start:

```powershell
python telegram_bot.py
```

## Commands

- `/start`
- `/help`
- `/wake`

Everything else is treated as a direct message to the MasterBot.
