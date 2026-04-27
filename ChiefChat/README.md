# ChiefChat

ChiefChat is the fast operator chat service for `Chief_of_Staff`.

It is intentionally separate from Claude Code and Runner. Telegram, Visualizer,
console chat, and future transports write to `_messages/CHAT.md`; ChiefChat
reads that ledger, uses a cheap configurable model for normal replies, and
writes clean operator-facing responses back to the same ledger plus the legacy
human outbox.

Useful commands:

```powershell
py ChiefChat\setup_chief_chat.py
py service_manager.py start chief-chat
py service_manager.py status chief-chat
py ChiefChat\chief_chat_service.py --once
py ChiefChat\chief_chat_service.py --status
```

Supported chat providers:

- `openai-compatible` for LM Studio or any compatible local endpoint
- `ollama`
- `opencode`
- `fake` for local validation only

Claude Code and other heavy harnesses should still be used for bootstrap,
coding, research, and deep work. ChiefChat is the always-on conversation and
orchestration path.
