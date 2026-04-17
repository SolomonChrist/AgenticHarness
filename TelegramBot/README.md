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

## Chief_of_Staff Contract

The active `Chief_of_Staff` / MasterBot should follow this simple rule:

- read `_messages/Chief_of_Staff.md`
- reply to the operator by writing to `_messages/human_<HumanID>.md`

The Telegram bridge does not orchestrate the swarm.

It only transports messages between you and the active MasterBot.

## First Telegram Test

1. Start your core Agentic Harness system first.
2. Make sure `Chief_of_Staff` is already active.
3. Copy `.env.telegram.template` to `.env.telegram`.
4. Fill in:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_ALLOWED_USER_IDS`
   - `HARNESS_ROOT`
   - `HUMAN_ID`
5. Start the bridge:

```powershell
python telegram_bot.py
```

6. In Telegram, send:
   - `/start`
   - a normal message such as `What is the current status?`
   - `/wake`

Expected behavior:

- your message is appended to `_messages/Chief_of_Staff.md`
- the active `Chief_of_Staff` reads that file
- the active `Chief_of_Staff` writes the reply to `_messages/human_<HumanID>.md`
- the Telegram bridge forwards that reply back to your phone

## Troubleshooting

- If `/start` works but normal replies do not come back, the bridge is running but `Chief_of_Staff` is not writing to `_messages/human_<HumanID>.md`.
- If the bridge says the harness root is missing, check `HARNESS_ROOT` in `.env.telegram`.
- If Telegram messages do not arrive, verify `TELEGRAM_ALLOWED_USER_IDS` and the bot token.

## Commands

- `/start`
- `/help`
- `/wake`

Everything else is treated as a direct message to the MasterBot.
