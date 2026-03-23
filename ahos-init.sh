#!/bin/bash

# ============================================================
# AHOS INIT — AI Handoff Operating System v2.0
# Solomon Christ Holdings Inc.
#
# Creates your full project folder so the AI skips setup
# and gets straight to building.
#
# Usage:
#   bash ahos-init.sh my-project-name
#
# Then paste CLAUDE.md / AGENTS.md / GEMINI.md into your AI.
# ============================================================

set -e

PROJECT="${1:-my-project}"
NOW=$(date -u +"%Y-%m-%d %H:%M UTC")
DATE=$(date -u +"%Y-%m-%d")

echo ""
echo "  AHOS v2.0 — AI Handoff Operating System"
echo "  Solomon Christ Holdings Inc."
echo "  ----------------------------------------"
echo "  Creating project: $PROJECT"
echo ""

mkdir -p "$PROJECT/docs"
cd "$PROJECT"
git init -q

# ── .gitignore ────────────────────────────────────────────
cat > .gitignore << 'EOF'
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
EOF

# ── docs/PROJECT_RULES.md ────────────────────────────────
cat > docs/PROJECT_RULES.md << EOF
# PROJECT RULES
# AHOS Version: 2.0 | Solomon Christ Holdings Inc.
# The rulebook. Every AI reads this first. Highest authority.

## What This Project Is
TODO — fill in after asking the owner

## What We Are Building With
TODO — ask the owner: language, framework, tools

## Rules Every AI Must Follow
- Save everything important to the files — not only in chat
- Update WHATS_HAPPENING_NOW.md before ending any session
- Update NEXT_STEPS.md when tasks are done or new ones come up
- Refresh QUICK_SUMMARY.md at the end of every session
- Follow WHAT_IS_ALLOWED.md before taking any big action
- Never save passwords or secret keys into project files

## File Organization
TODO — fill in as project develops

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
  5. WHAT_I_KNOW.md        — new stable information
  6. HOW_IT_WORKS.md       — design changed
  7. DECISIONS_WE_MADE.md  — important choice made
  8. ERRORS_WE_HIT.md      — something broke
  9. VERSION_HISTORY.md    — something finished
EOF

# ── docs/QUICK_SUMMARY.md ────────────────────────────────
cat > docs/QUICK_SUMMARY.md << EOF
# QUICK SUMMARY
# Read this first when catching up fast. Rewrite at end of every session.

## Last Updated
$NOW

## AI Tool Used Last
ahos-init.sh (setup script)

## This Project in One Sentence
TODO — ask the owner and fill this in

## Where We Are Right Now
Fresh setup — AHOS structure just created, no project content yet

## The Most Important Thing To Do Next
Ask the owner: what is this project, what are we building with, what's first?

## Anything Broken or Blocked
Nothing — brand new project

## Quick Commands
\`\`\`
Start:  TODO
Test:   TODO
Build:  TODO
\`\`\`

## Where Things Are
- Docs:       /docs/
- Main files: TODO
- Config:     TODO
EOF

# ── docs/WHAT_I_KNOW.md ──────────────────────────────────
cat > docs/WHAT_I_KNOW.md << EOF
# WHAT I KNOW
# Long-term stable facts only. No temporary notes. No session info here.

## What We Are Building With
TODO

## Important Decisions (Short Version)
None yet — see DECISIONS_WE_MADE.md for full entries

## Things That Cannot Change
TODO

## How the Owner Likes Things Done
TODO

## Core Assumptions
TODO

## Notes for Any New AI Coming In
This project was just created. Read PROJECT_RULES.md, then ask the owner
what this project is before doing anything else.
EOF

# ── docs/WHATS_HAPPENING_NOW.md ──────────────────────────
cat > docs/WHATS_HAPPENING_NOW.md << EOF
# WHAT'S HAPPENING NOW
# The handoff file. Update every single session.
# Write it like you're handing off to someone else forever.

## Last Updated
$NOW

## AI Tool Used This Session
ahos-init.sh (setup script — not an AI session)

## What We Got Done
- AHOS v2.0 project structure created by init script

## Files Changed
- All /docs/ files created from template
- CLAUDE.md, AGENTS.md, GEMINI.md created
- README.md and .gitignore created

## Commands Run
\`\`\`
bash ahos-init.sh $PROJECT
\`\`\`

## Tests Run
None — project just created

## Where Things Stand Right Now
All AHOS files exist with template content.
Nothing project-specific has been filled in yet.

## The Single Most Important Next Step
Ask the owner what this project is and fill in the project details.

## Problems or Blockers
None

## Notes for Whoever Works On This Next
Brand new project. Read PROJECT_RULES.md first.
Ask 3 questions before writing any code:
  1. What is this project?
  2. What are we building with?
  3. What is the first thing to build?

## Areas That Are Fragile — Handle With Care
Nothing fragile yet — empty project
EOF

# ── docs/NEXT_STEPS.md ───────────────────────────────────
cat > docs/NEXT_STEPS.md << EOF
# NEXT STEPS
# The to-do list. Keep this current every session.

## Must Do Now
- [ ] Ask the owner what this project is and fill in PROJECT_RULES.md [Easy]
- [ ] Fill in WHAT_I_KNOW.md with the tech stack [Easy]
- [ ] Fill in HOW_IT_WORKS.md with the system design [Medium]
- [ ] Fill in TOOLS_AVAILABLE.md with available tools and MCPs [Easy]
- [ ] Get the development environment running [Medium]

## Do Soon
- [ ] Set up testing [Medium]
- [ ] Set up deployment [Medium]

## Nice To Have Later
- [ ] Add more tasks as project grows

## Done
- [x] AHOS v2.0 initialized by script — $DATE
EOF

# ── docs/HOW_IT_WORKS.md ─────────────────────────────────
cat > docs/HOW_IT_WORKS.md << EOF
# HOW IT WORKS
# Full system design. Any AI should understand everything in 2 minutes.

## The Big Picture
TODO — fill in after asking the owner

## The Pieces
| Piece | What It Does | Where It Lives |
|-------|-------------|----------------|
| TODO  | TODO        | TODO           |

## How Data Moves Through the System
TODO

## External Services We Connect To
| Service | What It Does | How We Connect |
|---------|-------------|----------------|
| TODO    | TODO        | TODO           |

## Things We Know Need Improving Later
None yet
EOF

# ── docs/DECISIONS_WE_MADE.md ────────────────────────────
cat > docs/DECISIONS_WE_MADE.md << EOF
# DECISIONS WE MADE
# Every big choice. Stops us doing the same thing twice or undoing good work.

## Template
### [Short title]
- **Date:** [When]
- **What we decided:** [The choice]
- **Why:** [The reason]
- **What else we considered:** [Other options]
- **What this affects:** [Impact]
- **How to undo it:** [If needed]

---

### Using AHOS as our project system
- **Date:** $DATE
- **What we decided:** Use AHOS v2.0 so any AI tool can work on this project
- **Why:** Makes switching between Claude, Gemini, OpenCode, Antigravity etc. seamless — zero lost work
- **What else we considered:** No system — managing context manually
- **What this affects:** Every AI must read the docs and update them after every session
- **How to undo it:** Remove the AHOS files and manage context manually
EOF

# ── docs/HOW_TO_TEST.md ──────────────────────────────────
cat > docs/HOW_TO_TEST.md << EOF
# HOW TO TEST
# How to check everything is working.

## Run All Tests
\`\`\`
TODO — fill in test command
\`\`\`

## Types of Tests
- **Quick checks:** TODO
- **Full tests:** TODO
- **End-to-end:** TODO

## What Passing Looks Like
TODO

## Tests We Are Skipping (and Why)
None yet

## Checklist Before Saving Work
- [ ] All tests pass
- [ ] No passwords in files being saved
- [ ] WHATS_HAPPENING_NOW.md is updated
- [ ] Code follows the style in PROJECT_RULES.md
EOF

# ── docs/TOOLS_AVAILABLE.md ──────────────────────────────
cat > docs/TOOLS_AVAILABLE.md << EOF
# TOOLS AVAILABLE
# Every tool, app, connection, and service this project can use.

## Commands
| Command | What It Does |
|---------|-------------|
| TODO    | TODO        |

## Connected Services / MCPs
| Name | What It Does | How to Connect |
|------|-------------|----------------|
| TODO | TODO        | TODO           |

## APIs
| API  | Purpose | How We Log In |
|------|---------|--------------|
| TODO | TODO    | TODO         |

## Notes for Each AI Tool
- **Claude Code:** No special settings needed — works out of the box
- **Gemini CLI:** Use @filename to reference docs, e.g. @docs/QUICK_SUMMARY.md
- **OpenCode:** No special settings needed
- **Antigravity:** No special settings needed
- **Other tools:** Works with any AI that can read and write files
EOF

# ── docs/WHAT_IS_ALLOWED.md ──────────────────────────────
cat > docs/WHAT_IS_ALLOWED.md << EOF
# WHAT IS ALLOWED
# Rules for what the AI can and cannot do. Rules, not suggestions.

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

## What To Do When Not Sure
  1. STOP
  2. Write the situation in WHATS_HAPPENING_NOW.md under "Problems or Blockers"
  3. Explain what you were trying to do and what permission you need
  4. Wait for instructions — do NOT guess and proceed
EOF

# ── docs/SESSION_HISTORY.md ──────────────────────────────
cat > docs/SESSION_HISTORY.md << EOF
# SESSION HISTORY
# A log of every work session across all AI tools, in order.

## Template
### [Date and Time] — [AI Tool Used]
- **What we did:** [Summary]
- **What we learned:** [Anything important for the future]
- **Problems we hit:** [Issues and how they were resolved]
- **State when we stopped:** [Where things stood at the end]

---

### $NOW — ahos-init.sh (setup script)
- **What we did:** Created full AHOS v2.0 project structure
- **What we learned:** All files created with template content, ready for real project info
- **Problems we hit:** None
- **State when we stopped:** Clean init — all docs in template state, no project content yet
EOF

# ── docs/ERRORS_WE_HIT.md ───────────────────────────────
cat > docs/ERRORS_WE_HIT.md << EOF
# ERRORS WE HIT
# Every significant problem. Stops us hitting the same wall twice.

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
EOF

# ── docs/SETUP_GUIDE.md ──────────────────────────────────
cat > docs/SETUP_GUIDE.md << EOF
# SETUP GUIDE
# How to get this project running on any computer from scratch.

## Step-by-Step Setup
\`\`\`
TODO — fill in as project develops
\`\`\`

## What You Need Installed First
TODO

## Environment Variables Needed
See PASSWORDS_NEEDED.md for the full list of key names.

## Test Environment
- Where: TODO
- How to get access: TODO
- How to deploy: TODO

## Live Production Environment
- Where: TODO
- Access: RESTRICTED — see WHAT_IS_ALLOWED.md
- How to deploy: RESTRICTED — needs explicit written approval
EOF

# ── docs/VERSION_HISTORY.md ──────────────────────────────
cat > docs/VERSION_HISTORY.md << EOF
# VERSION HISTORY
# Important milestones. What changed and when.

## Coming Up
### Added
- AHOS v2.0 system initialized

## Version 0.0.1 — $DATE
### Added
- Project created with AHOS v2.0
EOF

# ── docs/PASSWORDS_NEEDED.md ─────────────────────────────
cat > docs/PASSWORDS_NEEDED.md << EOF
# PASSWORDS AND KEYS NEEDED
# Lists WHAT we need — never the actual values.
# Real passwords go in a .env file on your computer. Never commit .env.

## What This Project Needs
| Key Name  | What It's For | Where To Get It |
|-----------|--------------|-----------------|
| TODO      | TODO         | TODO            |

## Format for Your Local .env File
\`\`\`
TODO_KEY=
\`\`\`

## Rotation Schedule
| Key      | Last Changed | Change Every |
|----------|-------------|--------------|
| TODO_KEY | $DATE       | TODO         |
EOF

# ── CLAUDE.md ────────────────────────────────────────────
cat > CLAUDE.md << EOF
# FOR CLAUDE — Claude Code and Claude.ai
# AHOS v2.0 | Solomon Christ Holdings Inc.

## READ THESE IN ORDER — Do Not Skip Any
1. docs/PROJECT_RULES.md        ← The rulebook — read this first, always
2. docs/QUICK_SUMMARY.md        ← Fast catch-up on current state
3. docs/WHAT_I_KNOW.md          ← Stable facts about this project
4. docs/WHATS_HAPPENING_NOW.md  ← Where we left off
5. docs/NEXT_STEPS.md           ← What to do next
6. docs/WHAT_IS_ALLOWED.md      ← What you can do without asking
7. docs/TOOLS_AVAILABLE.md      ← What tools you have access to
8. docs/HOW_IT_WORKS.md         ← How the project is designed
9. docs/DECISIONS_WE_MADE.md    ← Why things are the way they are
10. docs/ERRORS_WE_HIT.md       ← Problems to know about and avoid

## Operating Rules
- The files are your only source of truth — never rely on chat history
- Do not assume anything not written in the files
- Do not end any session without completing the checklist below
- WHAT_IS_ALLOWED.md is law — no exceptions

## Notes for Claude
- Use extended thinking for big architectural decisions
- Memory between sessions is not reliable — the docs are your memory
- When you open a project say: "I have read the project files.
  Current state: [X]. Next action: [Y]."

## End-of-Session Checklist — Complete Every Single One
- [ ] WHATS_HAPPENING_NOW.md updated with full session summary
- [ ] NEXT_STEPS.md updated — done tasks checked off, new ones added
- [ ] SESSION_HISTORY.md new entry added
- [ ] QUICK_SUMMARY.md rewritten with current state
- [ ] WHAT_I_KNOW.md updated if something permanent was learned
- [ ] HOW_IT_WORKS.md updated if the design changed
- [ ] DECISIONS_WE_MADE.md updated if a big choice was made
- [ ] ERRORS_WE_HIT.md updated if something broke
- [ ] VERSION_HISTORY.md updated if something significant was finished
- [ ] git add . && git commit -m "[claude] what was done"
- [ ] git push
EOF

# ── AGENTS.md ────────────────────────────────────────────
cat > AGENTS.md << EOF
# FOR AGENTS — OpenCode, Antigravity, Codex, and Any Other AI Tool
# AHOS v2.0 | Solomon Christ Holdings Inc.

## READ THESE IN ORDER — Do Not Skip Any
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
- The files are your only source of truth — never rely on agent memory
- Do not skip the reading list even if it seems redundant
- WHAT_IS_ALLOWED.md is law — no exceptions

## If Multiple AIs Are Working At the Same Time
- Use WHATS_HAPPENING_NOW.md as a signal — if another AI is active, wait
- Do not edit files another AI is currently editing
- Add your AI name to session log entries

## End-of-Session Checklist — Complete Every Single One
- [ ] WHATS_HAPPENING_NOW.md updated
- [ ] NEXT_STEPS.md updated
- [ ] SESSION_HISTORY.md new entry added
- [ ] QUICK_SUMMARY.md rewritten
- [ ] git add . && git commit -m "[your-ai-name] what was done"
- [ ] git push
EOF

# ── GEMINI.md ────────────────────────────────────────────
cat > GEMINI.md << EOF
# FOR GEMINI — Gemini CLI and Google AI Tools
# AHOS v2.0 | Solomon Christ Holdings Inc.

## READ THESE IN ORDER — Do Not Skip Any
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
- The files are your only source of truth — never rely on chat history
- Do not skip the reading list
- WHAT_IS_ALLOWED.md is law — no exceptions

## Notes for Gemini
- Use @filename syntax to reference docs: @docs/QUICK_SUMMARY.md
- If context window is limited, read QUICK_SUMMARY.md first
- Check all suggestions against PROJECT_RULES.md before applying

## End-of-Session Checklist — Complete Every Single One
- [ ] WHATS_HAPPENING_NOW.md updated
- [ ] NEXT_STEPS.md updated
- [ ] SESSION_HISTORY.md new entry added
- [ ] QUICK_SUMMARY.md rewritten
- [ ] git add . && git commit -m "[gemini] what was done"
- [ ] git push
EOF

# ── README.md ────────────────────────────────────────────
cat > README.md << EOF
# $PROJECT

TODO — describe what this project is and what it does

## Getting Started
\`\`\`
TODO — fill in setup steps as the project develops
\`\`\`

## For AI Tools
Read \`CLAUDE.md\`, \`AGENTS.md\`, or \`GEMINI.md\` depending on your tool.
All AI tools must follow the reading list in those files before starting work.

## Key Files
| File | Purpose |
|------|---------|
| docs/PROJECT_RULES.md | The rulebook — read first |
| docs/QUICK_SUMMARY.md | Quick catch-up — current state |
| docs/NEXT_STEPS.md | The to-do list |
| docs/WHATS_HAPPENING_NOW.md | Where we left off |
| docs/HOW_IT_WORKS.md | How it's all built |

---
Powered by AHOS v2.0 — Any AI, Any Project, Any Time.
Solomon Christ Holdings Inc.
EOF

# ── Initial commit ────────────────────────────────────────
git add .
git -c user.email="ahos@init" -c user.name="AHOS Init" commit -q -m "[ahos] init: project created with AHOS v2.0" 2>/dev/null || true

echo "  Done. Project ready in: ./$PROJECT"
echo ""
echo "  Next steps:"
echo "  1. cd $PROJECT"
echo "  2. Create a private GitHub repo (optional but recommended):"
echo "     gh repo create $PROJECT --private --source=. --remote=origin --push"
echo ""
echo "  3. Open your AI tool and paste ONE of these files:"
echo "     CLAUDE.md   — for Claude Code or Claude.ai"
echo "     GEMINI.md   — for Gemini CLI"
echo "     AGENTS.md   — for OpenCode, Antigravity, or anything else"
echo ""
echo "  The AI will read the project files and ask what you want to build."
echo "  No setup needed — it goes straight to work."
echo ""
