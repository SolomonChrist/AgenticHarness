# AHOS — Your Universal AI Project System
## The Prompt That Makes Every AI Tool Work Together
### Version 2.0 | Solomon Christ Holdings Inc.

---

## HOW TO USE THIS

1. Create a new folder on your computer for your project (or open an existing project folder)
2. Open your AI tool — Claude Code, Gemini CLI, OpenCode, Antigravity, or any other
3. Copy everything below the dashed line and paste it into the AI
4. Answer a few questions when it asks — and start building

That's it. You're ready. The AI does the rest.

When your plan runs out or you want to switch tools: open the project folder in the new tool, paste this prompt again, and it picks up exactly where you left off.

---
---

# PASTE EVERYTHING BELOW THIS LINE INTO YOUR AI TOOL

---

You are a helpful AI assistant. Your first job is to set up and operate this project using the **AHOS system** — the AI Handoff Operating System. This system makes sure any AI tool can pick up this project and continue from exactly where the last one stopped. No wasted time. No lost work. No re-explaining.

## THE ONE RULE THAT MAKES THIS WORK

Everything important gets saved into files in this folder — not in chat, not in memory, in the files. That way, any AI — today, tomorrow, or next month — opens this folder and knows exactly what's going on.

Think of it like a detailed project notebook. The helper changes. The notebook stays.

---

## STEP 1 — IS THIS A NEW OR EXISTING PROJECT?

Look for a file called `docs/PROJECT_RULES.md` in this folder.

**If that file exists:** This is an existing project. Skip to the section at the bottom called "PICKING UP AN EXISTING PROJECT."

**If that file does NOT exist:** This is a new project. Follow every step below.

---

## STEP 2 — BUILD THE PROJECT FOLDER

Create these files and folders:

```
your-project/
├── CLAUDE.md
├── AGENTS.md
├── GEMINI.md
├── README.md
├── .gitignore
└── docs/
    ├── PROJECT_RULES.md
    ├── QUICK_SUMMARY.md
    ├── WHAT_I_KNOW.md
    ├── WHATS_HAPPENING_NOW.md
    ├── NEXT_STEPS.md
    ├── HOW_IT_WORKS.md
    ├── DECISIONS_WE_MADE.md
    ├── HOW_TO_TEST.md
    ├── TOOLS_AVAILABLE.md
    ├── WHAT_IS_ALLOWED.md
    ├── SESSION_HISTORY.md
    ├── ERRORS_WE_HIT.md
    ├── SETUP_GUIDE.md
    ├── VERSION_HISTORY.md
    └── PASSWORDS_NEEDED.md
```

---

## STEP 3 — FILL IN EVERY FILE

Create each file with exactly this content:

### `.gitignore`
```
.env
.env.*
!.env.example
secrets/
*.key
*.pem
node_modules/
vendor/
.venv/
__pycache__/
dist/
build/
.next/
.DS_Store
Thumbs.db
.vscode/
.idea/
```

---

### `docs/PROJECT_RULES.md`
```markdown
# PROJECT RULES
# AHOS Version: 2.0
# The rulebook. Every AI reads this first. Highest authority.

## What This Project Is
[Fill in after asking the user]

## What We're Building With
[Ask the user — language, tools, framework]

## Rules Every AI Must Follow
- Save everything important to the files — not only in chat
- Update WHATS_HAPPENING_NOW.md before ending any session
- Update NEXT_STEPS.md when tasks are done or new ones come up
- Refresh QUICK_SUMMARY.md at the end of every session
- Follow WHAT_IS_ALLOWED.md before taking any big action
- Never save passwords or secret keys into project files

## File Organization
[Fill in as project develops]

## Safety Rules
- Do not delete files without asking first
- Do not make major changes without checking WHAT_IS_ALLOWED.md
- Never share or log passwords or keys

## What Must Be Updated After Every Session
Every time — no exceptions:
  1. WHATS_HAPPENING_NOW.md
  2. NEXT_STEPS.md
  3. SESSION_HISTORY.md
  4. QUICK_SUMMARY.md

When something changed:
  5. WHAT_I_KNOW.md — new stable information learned
  6. HOW_IT_WORKS.md — design changed
  7. DECISIONS_WE_MADE.md — important choice was made
  8. ERRORS_WE_HIT.md — something broke
  9. VERSION_HISTORY.md — something was finished
```

---

### `docs/QUICK_SUMMARY.md`
```markdown
# QUICK SUMMARY
# Read this first when catching up fast. Rewrite at end of every session.

## Last Updated
[Date and time — fill in each session]

## AI Tool Used Last
[e.g., Claude Code / Gemini CLI / OpenCode / Antigravity]

## This Project in One Sentence
[Fill in after asking the user]

## Where We Are Right Now
Just getting started — AHOS system just set up

## The Most Important Thing To Do Next
Ask the owner about this project and fill in the project details

## Anything Broken or Blocked Right Now
Nothing yet

## Quick Commands
```
Start: [fill in]
Test: [fill in]
Build: [fill in]
```

## Where Things Are
- Main files: [fill in]
- Settings: [fill in]
- Docs: /docs/
```

---

### `docs/WHAT_I_KNOW.md`
```markdown
# WHAT I KNOW
# Long-term stable facts. Nothing temporary. No session notes here.

## What We're Building With
[Fill in]

## Important Decisions (Short Version)
[One-liners — full detail in DECISIONS_WE_MADE.md]

## Things That Cannot Change
[Hard limits — technical or business requirements]

## How the Owner Likes Things Done
[Preferences for naming, style, formatting]

## Core Assumptions
[Things assumed that affect how everything is built]

## Notes for Any New AI Coming In
[Critical context that anyone starting fresh must know]
```

---

### `docs/WHATS_HAPPENING_NOW.md`
```markdown
# WHAT'S HAPPENING NOW
# The handoff file. Write this as if you're handing off to someone else forever.
# Update every single session — this is the most important file.

## Last Updated
[Date and time]

## AI Tool Used This Session
[Fill in]

## What We Got Done
- AHOS project system created

## Files We Changed
- All /docs/ files — created from scratch

## Commands We Ran
[Fill in]

## Tests We Ran
None yet

## Where Things Stand Right Now
Brand new setup. All files exist but need real project content.

## The Single Most Important Next Step
Ask the owner what this project is and fill in the project details.

## Problems or Blockers
None

## Notes for Whoever Works On This Next
Fresh project. Read PROJECT_RULES.md first, then fill in docs before coding.

## Areas That Are Fragile — Handle With Care
Nothing fragile yet — empty project
```

---

### `docs/NEXT_STEPS.md`
```markdown
# NEXT STEPS
# The to-do list. Keep this current.

## Must Do Now
- [ ] Fill in PROJECT_RULES.md with what this project is [Easy]
- [ ] Fill in WHAT_I_KNOW.md with the tech stack [Easy]
- [ ] Fill in HOW_IT_WORKS.md with the design [Medium]
- [ ] Fill in TOOLS_AVAILABLE.md with available tools [Easy]
- [ ] Get the dev environment running [Medium]

## Do Soon
- [ ] Set up testing [Medium]
- [ ] Set up deployment [Medium]

## Nice To Have
- [ ] Add more as project grows

## Done (keep for reference)
- [x] AHOS v2.0 initialized — [date]
```

---

### `docs/HOW_IT_WORKS.md`
```markdown
# HOW IT WORKS
# How this project is built. Any AI should understand the whole system in 2 minutes.

## The Big Picture
[Fill in after asking the user]

## The Pieces
| Piece | What It Does | Where It Lives |
|-------|-------------|----------------|
| [Name] | [Purpose] | [Path] |

## How Data Moves Through the System
[Fill in as project develops]

## External Services We Connect To
| Service | What It Does | How We Connect |
|---------|-------------|----------------|
| [Name] | [Purpose] | [Method] |

## Things We Know Need Improving Later
[Fill in as project develops]
```

---

### `docs/DECISIONS_WE_MADE.md`
```markdown
# DECISIONS WE MADE
# Every big choice. This stops us from doing the same thing twice or undoing good work.

## How To Write a Decision
### [Short title]
- **Date:** [When]
- **What we decided:** [The choice]
- **Why:** [The reason]
- **What else we considered:** [Other options]
- **What this affects:** [Impact]
- **How to undo it:** [If needed]

---

### Using AHOS as our project system
- **Date:** [Today]
- **What we decided:** Use AHOS v2.0 so any AI tool can work on this project
- **Why:** Makes switching between Claude, Gemini, OpenCode, Antigravity, etc. seamless
- **What else we considered:** No system — managing context manually
- **What this affects:** Every AI must follow the reading list and update the docs
- **How to undo it:** Remove the AHOS files and manage context manually
```

---

### `docs/HOW_TO_TEST.md`
```markdown
# HOW TO TEST
# How to check everything is working.

## Run All Tests
```
[Fill in the test command]
```

## Types of Tests
- **Quick checks:** [What gets spot-checked]
- **Full tests:** [Integration tests]
- **End-to-end:** [Full run-through tests]

## What Passing Looks Like
[Fill in]

## Tests We're Skipping (and Why)
None yet

## Checklist Before Saving Work
- [ ] All tests pass
- [ ] No passwords in what we're saving
- [ ] WHATS_HAPPENING_NOW.md is updated
- [ ] Code follows the style guide in PROJECT_RULES.md
```

---

### `docs/TOOLS_AVAILABLE.md`
```markdown
# TOOLS AVAILABLE
# Every tool, app, connection, and service this project can use.

## Commands
| Command | What It Does |
|---------|-------------|
| [fill in] | [purpose] |

## Connected Services / MCPs
| Name | What It Does | How to Connect |
|------|-------------|----------------|
| [fill in] | [purpose] | [url or setup] |

## APIs
| API | Purpose | How We Log In |
|-----|---------|--------------|
| [fill in] | [purpose] | [method] |

## Notes for Each AI Tool
- **Claude Code:** [Any special settings]
- **Gemini CLI:** [Use @filename to reference docs, e.g. @docs/QUICK_SUMMARY.md]
- **OpenCode:** [Any special settings]
- **Antigravity:** [Any special settings]
- **Other tools:** [Any special settings]
```

---

### `docs/WHAT_IS_ALLOWED.md`
```markdown
# WHAT IS ALLOWED
# Rules for what the AI can and cannot do. These are rules, not suggestions.

## YES — Do These Freely
- Read any file in the project
- Write to any file in /docs/
- Run test commands
- Install development tools
- Create new files
- Commit and push to feature branches
- Run the formatter or linter

## ASK FIRST — Check Before Doing
- Delete any existing file
- Change the database structure
- Change environment variable names
- Install new packages the project depends on
- Push to the main branch
- Call external services in a way that changes data
- Rename or restructure folders
- Change how login or payments work

## NEVER — These Need Written Permission in This Chat
- Touch files with real passwords or keys
- Share, log, or send passwords or keys anywhere
- Deploy the project live to users
- Delete or wipe database tables
- Change billing or payment code
- Force overwrite work on any branch
- Turn off tests or safety checks permanently
- Run commands outside this project folder

## What To Do When You're Not Sure
  1. STOP
  2. Write the situation in WHATS_HAPPENING_NOW.md under "Problems or Blockers"
  3. Explain what you were trying to do and what permission you need
  4. Wait for instructions — do NOT guess and proceed
```

---

### `docs/SESSION_HISTORY.md`
```markdown
# SESSION HISTORY
# A log of every work session, in order.

## Template
### [Date and Time] — [AI Tool Used]
- **What we did:** [Summary]
- **What we learned:** [Anything important for the future]
- **Problems we hit:** [Issues and how they were resolved]
- **State when we stopped:** [Where things stood at the end]

---

### [Today's Date] — AHOS Setup
- **What we did:** Set up AHOS v2.0 project system
- **What we learned:** All files created, ready for real content
- **Problems we hit:** None
- **State when we stopped:** Clean initialization, all docs in template state
```

---

### `docs/ERRORS_WE_HIT.md`
```markdown
# ERRORS WE HIT
# Every significant problem. This stops us from hitting the same wall twice.

## Template
### [Short name] — [Date]
- **What the error was:** [The message or description]
- **What we were doing:** [Context]
- **Why it happened:** [Root cause]
- **How we fixed it:** [Solution]
- **How to avoid it in the future:** [Prevention]
- **Status:** FIXED / STILL OPEN / WORKAROUND

---

*No errors logged yet.*
```

---

### `docs/SETUP_GUIDE.md`
```markdown
# SETUP GUIDE
# How to get this project running on any computer from scratch.

## Step-by-Step Setup
```
[Fill in as project develops]
```

## What You Need Installed First
[List required software]

## Environment Variables Needed
[List the names — see PASSWORDS_NEEDED.md for the complete list]

## Test Environment
- Where: [URL or location]
- How to get access: [Instructions]
- How to deploy to it: [Command]

## Live Production Environment
- Where: [URL]
- Access: RESTRICTED — see WHAT_IS_ALLOWED.md
- How to deploy: RESTRICTED — needs explicit approval
```

---

### `docs/VERSION_HISTORY.md`
```markdown
# VERSION HISTORY
# Important milestones. What changed and when.

## Coming Up
### Added
- AHOS system initialized

## Version 0.0.1 — [Today's Date]
### Added
- Project created with AHOS v2.0
```

---

### `docs/PASSWORDS_NEEDED.md`
```markdown
# PASSWORDS AND KEYS NEEDED
# Lists WHAT we need — never the actual values.
# Real passwords go in a .env file on your computer. Never in this project.

## What This Project Needs
| Key Name | What It's For | Where To Get It |
|----------|--------------|-----------------|
| [KEY_NAME] | [purpose] | [how to get it] |

## Format for Your Local .env File
```
[KEY_NAME]=
```

## Rotation Schedule
| Key | Last Changed | Change Every |
|-----|-------------|--------------|
| [KEY_NAME] | [date] | [how often] |
```

---

### `CLAUDE.md`
```markdown
# FOR CLAUDE — Claude Code and Claude.ai
# AHOS v2.0 | Solomon Christ Holdings Inc.

## READ THESE IN ORDER — Do Not Skip
1. docs/PROJECT_RULES.md        ← The rulebook — read this first always
2. docs/QUICK_SUMMARY.md        ← Fast catch-up
3. docs/WHAT_I_KNOW.md          ← Stable project knowledge
4. docs/WHATS_HAPPENING_NOW.md  ← Where we left off
5. docs/NEXT_STEPS.md           ← What to do
6. docs/WHAT_IS_ALLOWED.md      ← What you can do without asking
7. docs/TOOLS_AVAILABLE.md      ← What you have to work with
8. docs/HOW_IT_WORKS.md         ← How the project is designed
9. docs/DECISIONS_WE_MADE.md    ← Why things are the way they are
10. docs/ERRORS_WE_HIT.md       ← Problems to know about and avoid

## Operating Rules
- The files are your only source of truth. Never rely on chat history.
- Do not assume anything not written in the files.
- Do not end a session without completing the checklist below.
- WHAT_IS_ALLOWED.md is law. No exceptions.

## Notes for Claude
- Use extended thinking for big design decisions
- Memory between sessions is NOT reliable — the docs are your memory
- When you open a project, confirm: "I've read the project files. Current state: [X]. Next action: [Y]."

## End-of-Session Checklist — Do Every Single One
- [ ] WHATS_HAPPENING_NOW.md updated with full session summary
- [ ] NEXT_STEPS.md updated — done items checked, new items added
- [ ] SESSION_HISTORY.md new entry added
- [ ] QUICK_SUMMARY.md rewritten with current state
- [ ] WHAT_I_KNOW.md updated if we learned something permanent
- [ ] HOW_IT_WORKS.md updated if the design changed
- [ ] DECISIONS_WE_MADE.md updated if a big choice was made
- [ ] ERRORS_WE_HIT.md updated if something broke
- [ ] VERSION_HISTORY.md updated if something significant was finished
- [ ] git add . && git commit -m "[claude] what was done"
- [ ] git push
```

---

### `AGENTS.md`
```markdown
# FOR AGENTS — OpenAI Tools, Codex, AutoGen, and Others
# AHOS v2.0 | Solomon Christ Holdings Inc.

## READ THESE IN ORDER — Do Not Skip
1. docs/PROJECT_RULES.md
2. docs/QUICK_SUMMARY.md
3. docs/WHAT_I_KNOW.md
4. docs/WHATS_HAPPENING_NOW.md
5. docs/NEXT_STEPS.md
6. docs/WHAT_IS_ALLOWED.md
7. docs/TOOLS_AVAILABLE.md
8. docs/HOW_IT_WORKS.md
9. docs/DECISIONS_WE_MADE.md
10. docs/ERRORS_WE_HIT.md

## Operating Rules
- The files are your only source of truth. Never rely on agent memory.
- Do not skip the reading list even if it seems redundant.
- WHAT_IS_ALLOWED.md is law. No exceptions.

## If Multiple AIs Are Working At the Same Time
- Use WHATS_HAPPENING_NOW.md as a signal — if another AI is active, wait
- Do not edit files another AI is currently editing
- Add your AI name to session log entries

## End-of-Session Checklist
- [ ] WHATS_HAPPENING_NOW.md updated
- [ ] NEXT_STEPS.md updated
- [ ] SESSION_HISTORY.md new entry added
- [ ] QUICK_SUMMARY.md rewritten
- [ ] git add . && git commit -m "[agent-name] what was done"
- [ ] git push
```

---

### `GEMINI.md`
```markdown
# FOR GEMINI — Gemini CLI and Google AI Tools
# AHOS v2.0 | Solomon Christ Holdings Inc.

## READ THESE IN ORDER — Do Not Skip
1. docs/PROJECT_RULES.md
2. docs/QUICK_SUMMARY.md
3. docs/WHAT_I_KNOW.md
4. docs/WHATS_HAPPENING_NOW.md
5. docs/NEXT_STEPS.md
6. docs/WHAT_IS_ALLOWED.md
7. docs/TOOLS_AVAILABLE.md
8. docs/HOW_IT_WORKS.md
9. docs/DECISIONS_WE_MADE.md
10. docs/ERRORS_WE_HIT.md

## Operating Rules
- The files are your only source of truth. Never rely on chat history.
- Do not skip the reading list.
- WHAT_IS_ALLOWED.md is law. No exceptions.

## Notes for Gemini
- Use @filename syntax to reference docs: @docs/QUICK_SUMMARY.md
- If context window is limited, start with QUICK_SUMMARY.md
- Check suggestions against PROJECT_RULES.md before applying

## End-of-Session Checklist
- [ ] WHATS_HAPPENING_NOW.md updated
- [ ] NEXT_STEPS.md updated
- [ ] SESSION_HISTORY.md new entry added
- [ ] QUICK_SUMMARY.md rewritten
- [ ] git add . && git commit -m "[gemini] what was done"
- [ ] git push
```

---

### `README.md`
```markdown
# [Project Name]

[Fill in: what this project is and what it does]

## Getting Started
[Fill in setup instructions as the project develops]

## For AI Tools
Read `CLAUDE.md`, `AGENTS.md`, or `GEMINI.md` depending on your tool.
Every AI must follow the reading list before starting work.

## Key Files
| File | Purpose |
|------|---------|
| docs/PROJECT_RULES.md | The rulebook — read first |
| docs/QUICK_SUMMARY.md | Quick catch-up — current state |
| docs/NEXT_STEPS.md | The to-do list |
| docs/WHATS_HAPPENING_NOW.md | Where we left off |

---
Powered by AHOS v2.0 — Any AI, Any Project, Any Time.
Solomon Christ Holdings Inc.
```

---

## STEP 4 — MAKE THE FIRST SAVE

After creating all files, run:
```
git add .
git commit -m "Project started with AHOS v2.0"
```

To save it to a private GitHub repo:
```
gh repo create your-project-name --private --source=. --remote=origin --push
```

---

## STEP 5 — TELL ME ABOUT THE PROJECT

Now I need to know three things so we can fill in the real details:

1. **What is this project?** What are you building and what should it do when it's done?
2. **What are we building it with?** (website, mobile app, automation script, AI tool — whatever it is)
3. **What's the first thing you want to get working?**

Once you answer, I'll fill in all the files with real information and we'll start building right away.

---
---

# PICKING UP AN EXISTING PROJECT

If AHOS is already set up in this folder:

1. Read `docs/QUICK_SUMMARY.md` — fastest way to catch up
2. Then read in order:
   - `docs/PROJECT_RULES.md`
   - `docs/WHATS_HAPPENING_NOW.md`
   - `docs/NEXT_STEPS.md`
   - `docs/WHAT_IS_ALLOWED.md`
   - Others as needed
3. Confirm out loud: *"I've read the project files. We're at [current state]. The next thing to do is [next task]."*
4. Start working from `docs/NEXT_STEPS.md`

---

## THE END-OF-SESSION RULE — NON-NEGOTIABLE

At the end of every session — no matter how small or short:

1. Update `docs/WHATS_HAPPENING_NOW.md` — full summary of what happened
2. Update `docs/NEXT_STEPS.md` — check off done, add new
3. Add entry to `docs/SESSION_HISTORY.md`
4. Rewrite `docs/QUICK_SUMMARY.md` with current state
5. Save: `git add . && git commit -m "[ai-tool-name] what was done"`
6. Push: `git push`

This is what makes it possible to switch between Claude Code, Gemini CLI, OpenCode, Antigravity, or any future tool — with zero lost work, every single time.

---

*AHOS v2.0 — Any AI, Any Project, Any Time.*
*Solomon Christ Holdings Inc.*
