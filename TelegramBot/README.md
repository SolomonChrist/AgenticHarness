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

The user should only need to do two manual things:

1. Create the Telegram bot and get the bot token.
2. Get their Telegram user ID.

After that, the active `Chief_of_Staff` should be able to fill `TelegramBot/.env.telegram` for them when the operator explicitly asks to enable the Telegram add-on and provides:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ALLOWED_USER_IDS`

and the local harness root is already known.

Once Telegram is configured, `Chief_of_Staff` should try to start the Telegram bridge for the operator if the local harness can safely execute the command. If it cannot, it should immediately provide the exact command to run next.

Recommended instruction to give `Chief_of_Staff`:

```text
Configure the Telegram bridge for this install.
Use the Telegram bot token and Telegram user ID I provide.
Write the correct values into TelegramBot/.env.telegram.
Use the current harness root for HARNESS_ROOT.
Use the operator Human ID from HUMANS.md for HUMAN_ID.
After writing the file, continue using Telegram as transport only by reading _messages/Chief_of_Staff.md and replying through _messages/human_<HumanID>.md.
```

Manual fallback:

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
py -m pip install requests python-dotenv
python -m pip install requests python-dotenv
```

4. Start:

```powershell
py telegram_bot.py
python telegram_bot.py
```

## Chief_of_Staff Contract

The active `Chief_of_Staff` / MasterBot should follow this simple rule:

- read `_messages/Chief_of_Staff.md`
- reply to the operator by writing to `_messages/human_<HumanID>.md`

The Telegram bridge does not orchestrate the swarm.

It only transports messages between you and the active MasterBot.

If Telegram is the operator's active remote channel, the MasterBot should also mirror operator-facing questions, approvals needed, and status updates into `_messages/human_<HumanID>.md` rather than keeping them only in the local harness session.

## First Telegram Test

1. Start your core Agentic Harness system first.
2. Make sure `Chief_of_Staff` is already active.
3. Get your bot token from `@BotFather`.
4. Get your Telegram user ID from `@userinfobot`.
5. Give those values to `Chief_of_Staff` and ask it to configure `TelegramBot/.env.telegram`.
6. Confirm that `.env.telegram` now contains:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_ALLOWED_USER_IDS`
   - `HARNESS_ROOT`
   - `HUMAN_ID`
7. Start the bridge:

```powershell
py telegram_bot.py
python telegram_bot.py
```

8. In Telegram, send:
   - `/start`
   - a normal message such as `What is the current status?`
   - `/wake`

Expected behavior:

- your message is appended to `_messages/Chief_of_Staff.md`
- the active `Chief_of_Staff` reads that file
- the active `Chief_of_Staff` writes the reply to `_messages/human_<HumanID>.md`
- the Telegram bridge forwards that reply back to your phone

## Troubleshooting

- If `pip install` fails on Windows, use `py -m pip install requests python-dotenv`.
- If `py` is not available, use `python -m pip install requests python-dotenv`.
- If `/start` works but normal replies do not come back, the bridge is running but `Chief_of_Staff` is not writing to `_messages/human_<HumanID>.md`.
- If the bridge says the harness root is missing, check `HARNESS_ROOT` in `.env.telegram`.
- If Telegram messages do not arrive, verify `TELEGRAM_ALLOWED_USER_IDS` and the bot token.

## Commands

- `/start`
- `/help`
- `/wake`

Everything else is treated as a direct message to the MasterBot.
