# AHOS — AI Handoff Operating System
## Any AI. Any Project. Any Time. Zero Lost Work.
### Version 2.0 | Solomon Christ Holdings Inc.

---

## What Is This?

AHOS is a simple system that lets you work on any project using any AI tool — and switch between tools anytime without losing a single thing.

**The problem it solves:** Every AI tool has a memory that disappears when the session ends. When you switch tools or come back after a break, you have to re-explain everything from scratch. That's a huge waste of time.

**The solution:** AHOS saves all of your project's knowledge into files in your project folder — not in the AI. When you open a new AI tool or start a new session, the AI reads those files and picks up exactly where you left off.

---

## The Simple Version

Imagine you're writing a book and you have a notebook full of your plot, characters, and next chapters. If your writer gets sick, you hire a new one — they read the notebook and keep writing from the exact right place. The notebook is what matters, not the writer.

AHOS is that notebook. Your AI tools are the writers.

---

## How It Works — In 3 Steps

**Step 1:** You have a project folder. Inside it is a `docs/` folder with files that describe everything about your project.

**Step 2:** Any AI tool you use — Claude Code, Gemini CLI, OpenCode, Antigravity, or anything else — reads those files first. It instantly knows what the project is, where you left off, and what to do next.

**Step 3:** When the AI finishes working, it updates those files before it stops. The next AI (or the same one, next time) reads the updates and continues seamlessly.

---

## Who This Is For

**Anyone.** You don't need to know how to code. You don't need any technical background. If you can copy, paste, and answer a few questions, you can use AHOS.

This is for people who:
- Use AI tools to build projects and want to switch between them freely
- Come back to projects after days or weeks and don't want to re-explain everything
- Are working on multiple projects at the same time (Project A today, Project C tomorrow)
- Run out of credits on one AI tool and need to keep going with a different one

---

## Supported AI Tools

AHOS works with any AI tool that can read and write files. This includes:

| Tool | How to Use It |
|------|-------------|
| Claude Code | Use `CLAUDE.md` — read it into your session |
| Gemini CLI | Use `GEMINI.md` — use `@filename` syntax |
| OpenCode | Use `AGENTS.md` |
| Antigravity | Use `AGENTS.md` |
| Any future tool | Use `AGENTS.md` — works with anything |

---

## Getting Started — 3 Ways

### Option 1: Just Paste the Prompt (Easiest)
1. Create a new folder for your project
2. Open any AI tool
3. Copy `AHOS_PROMPT.md` and paste the whole thing into the AI
4. Answer 3 questions when it asks
5. You're building

### Option 2: Run the Setup Script
If you're comfortable with a terminal:
```bash
bash ahos-init.sh my-project-name
```
The script creates everything in under 30 seconds.

### Option 3: Use as a GitHub Template
Fork this repo and use it as a template. Every new project starts ready to go.

---

## Switching Between AI Tools

This is the whole point. Here's exactly what you do:

1. Make sure the current AI finished its session (all files updated, work saved)
2. Open your project folder in the new AI tool
3. Paste `CLAUDE.md`, `AGENTS.md`, or `GEMINI.md` into it (whichever matches your new tool)
4. The AI reads the files and says where things are
5. Keep building

No explanation needed. No starting over. Zero wasted time.

---

## Working on Multiple Projects

You can have as many AHOS projects as you want. Each has its own folder with its own `docs/` folder.

When you want to work on Project A: open that folder, paste the prompt or the adapter file, go.

When you feel like switching to Project F: close that session, open Project F's folder, paste the prompt, go.

Each project remembers exactly where it left off — indefinitely.

---

## What's In Your Project Folder

Every AHOS project has this structure. Here's what each piece does, in plain language:

### The 3 Adapter Files (at the root)
These tell each AI tool how to get started. One for Claude, one for Gemini, one for everyone else.

| File | For |
|------|-----|
| `CLAUDE.md` | Claude Code and Claude.ai |
| `GEMINI.md` | Gemini CLI and Google AI tools |
| `AGENTS.md` | OpenCode, Antigravity, and everything else |

### The docs/ Folder — The Project Brain

| File | What It Does | Updated |
|------|-------------|---------|
| `PROJECT_RULES.md` | The rulebook — all AIs read this first | When rules change |
| `QUICK_SUMMARY.md` | Fast catch-up — what's happening right now | Every session |
| `WHAT_I_KNOW.md` | Stable facts about this project | When facts change |
| `WHATS_HAPPENING_NOW.md` | The handoff — where we left off | Every session |
| `NEXT_STEPS.md` | The to-do list | Every session |
| `HOW_IT_WORKS.md` | How the project is designed | When design changes |
| `DECISIONS_WE_MADE.md` | Why we chose to do things this way | When decisions are made |
| `HOW_TO_TEST.md` | How to check everything works | When tests change |
| `TOOLS_AVAILABLE.md` | What tools, apps, and APIs the AI can use | When tools change |
| `WHAT_IS_ALLOWED.md` | What the AI can do without asking | When rules change |
| `SESSION_HISTORY.md` | A log of every work session | Every session |
| `ERRORS_WE_HIT.md` | Problems we hit and how we fixed them | When errors happen |
| `SETUP_GUIDE.md` | How to set the project up from scratch | When setup changes |
| `VERSION_HISTORY.md` | What changed and when — milestone log | When milestones hit |
| `PASSWORDS_NEEDED.md` | What keys/passwords are needed (never values) | When secrets change |

---

## The End-of-Session Rule

This is what makes the whole system work. Every time an AI finishes a session — whether it's 5 minutes or 5 hours — it must do these 6 things before stopping:

1. Update `WHATS_HAPPENING_NOW.md` with a full summary
2. Update `NEXT_STEPS.md` — check off done, add new tasks
3. Add a new entry to `SESSION_HISTORY.md`
4. Rewrite `QUICK_SUMMARY.md` with the current state
5. Save: `git add . && git commit -m "[tool-name] what was done"`
6. Push: `git push`

That's the seal. If these 6 things happened, the next AI — on any platform, any time — can pick this up in under 60 seconds.

---

## What AI Tools Can and Can't Do

Every AHOS project has a `WHAT_IS_ALLOWED.md` file that defines clear rules:

**Green light — do freely:**
Read files, write to the docs folder, run tests, install dev tools, create new files, commit to branches

**Yellow light — ask first:**
Delete files, change the database, push to the main branch, install new packages, rename folders

**Red light — never without written permission:**
Touch passwords/keys, deploy to production, delete database tables, change payment code, force-push

If an AI isn't sure which category something falls into, it stops, documents the situation in `WHATS_HAPPENING_NOW.md`, and waits for instruction.

---

## The Git Commit Format

Every time an AI saves work, it uses this format so you can see exactly who did what:

```
[claude] added user login page
[gemini] fixed the broken API connection
[opencode] updated architecture docs
[antigravity] completed checkout flow
```

---

## Common Questions

**Do I need to know how to code?**
No. The prompt handles all the setup. You just answer questions about your project.

**What if I don't use GitHub?**
The git parts are optional but recommended. The core AHOS system works with just the files — git is just how you back up and track changes.

**Can I have different rules for different projects?**
Yes. Each project has its own `docs/` folder with its own rules. Project A can have completely different settings from Project B.

**What if an AI doesn't follow the rules?**
Paste the adapter file again and tell it to read `docs/PROJECT_RULES.md` first. The files always have the correct state.

**Can multiple people use this?**
Yes. Each person's AI reads the same files. As long as everyone follows the end-of-session rule, the project stays in sync.

**What if I forget to tell the AI to save at the end?**
Just do it at the start of the next session — ask the AI to update `WHATS_HAPPENING_NOW.md` with what it remembers from last time before moving on.

---

## Version History

**v2.0** — Current
- Renamed all files to plain English (no jargon)
- Added `QUICK_SUMMARY.md` for fast catch-up in any tool
- Added `ERRORS_WE_HIT.md` to prevent repeating mistakes
- Added `SETUP_GUIDE.md` and `VERSION_HISTORY.md`
- Added `PASSWORDS_NEEDED.md` to safely track required credentials
- Simplified all language to work for non-technical users
- Added support notes for Antigravity and OpenCode

**v1.0** — Original
- Core 10-file structure
- Three adapter files
- Session lifecycle protocol

---

## Repository Structure

```
ahos/
├── README.md                ← You are here
├── AHOS_PROMPT.md           ← The single paste prompt — start here
├── ahos-init.sh             ← One-command setup script
├── AHOS_Complete_Guide.pdf  ← Full documentation (PDF)
└── AHOS_Report.md           ← Full documentation (Markdown)
```

---

## License

Open source. Use it, fork it, share it, build on it.

---

*AHOS v2.0 — Any AI, Any Project, Any Time.*
*Solomon Christ Holdings Inc.*
