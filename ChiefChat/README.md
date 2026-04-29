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

Web/current-info requests use a source-first path. ChiefChat creates a durable
`TASK-WEB-*` task, gathers clean web evidence with Playwright, then asks the
cheap model to answer only from that evidence. Weather requests use a direct
Open-Meteo lookup so a message like `check the weather in Toronto` returns the
actual current conditions instead of a "checking now" placeholder. If the cheap
model fails or only sends a progress update, ChiefChat replies with the extracted
source evidence and leaves the task open for deeper follow-up.

Task intake is protected from the web path. If the operator says things like
`add these tasks`, `put this in the task list`, `figure out which team members
we need`, or `delegate these items`, ChiefChat writes `TASK-INTAKE-*` items to
`LAYER_TASK_LIST.md`, creates wake requests for the recommended owner roles, and
only then confirms the routing. Lists that contain words like "research",
"Google Drive", or "AI news" are still treated as backlog/delegation requests
when the operator asked for task capture.

ChiefChat runs an intent gate before using the cheap chat model or browser
path. The current high-level intents are presence, model identity, task intake,
role routing, weather, web/current-info, and normal chat. This matters because
human conversation like "today was a lot, help me think" should stay a normal
Chief conversation, while "what events are happening in Toronto tonight?" should
use the web evidence path.

Location incident requests, such as "I am at Bloor and Bathurst and there is a
huge lineup, what is going on?", should trigger situational investigation mode:
normalize speech-to-text location errors, fan out across events, venue schedules,
news, Reddit/Twitter-like public traces, and nearby likely venues, then answer
with a sourced best guess and confidence instead of saying it cannot see the
street.

ChiefChat should be truthful about its own runtime. When asked what model it is
using, it reports the live ChiefChat provider/model first and distinguishes that
from deeper Runner role models such as Claude Code. It also asks a quick
clarifying question for ambiguous places instead of guessing, and it only says a
task was routed after writing the task and wake-request files.

Claude Code and other heavy harnesses should still be used for bootstrap,
coding, research, and deep work. ChiefChat is the always-on conversation and
orchestration path.
