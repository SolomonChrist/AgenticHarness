@echo off
REM ============================================================
REM AHOS INIT — AI Handoff Operating System v2.0
REM Solomon Christ Holdings Inc.
REM
REM Creates your full project folder so the AI skips setup
REM and gets straight to building.
REM
REM Usage:
REM   ahos-init.bat my-project-name
REM
REM Then paste CLAUDE.md / AGENTS.md / GEMINI.md into your AI.
REM ============================================================

setlocal enabledelayedexpansion

if "%~1"=="" (
    set "PROJECT=my-project"
) else (
    set "PROJECT=%~1"
)

for /f "tokens=1-3 delims=/ " %%a in ("%date%") do (
    set "DATE=%%c-%%a-%%b"
)
set "NOW=%DATE% (local time)"

echo.
echo   AHOS v2.0 — AI Handoff Operating System
echo   Solomon Christ Holdings Inc.
echo   ----------------------------------------
echo   Creating project: %PROJECT%
echo.

mkdir "%PROJECT%\docs" 2>nul
cd "%PROJECT%"
git init -q 2>nul || echo   (Git not found — skipping git init)

REM ── .gitignore ──────────────────────────────────────────
(
echo .env
echo .env.*
echo !.env.example
echo secrets/
echo *.key
echo *.pem
echo node_modules/
echo vendor/
echo .venv/
echo __pycache__/
echo dist/
echo build/
echo .next/
echo .DS_Store
echo Thumbs.db
echo .vscode/
echo .idea/
) > .gitignore

REM ── docs/PROJECT_RULES.md ──────────────────────────────
(
echo # PROJECT RULES
echo # AHOS Version: 2.0 ^| Solomon Christ Holdings Inc.
echo # The rulebook. Every AI reads this first. Highest authority.
echo.
echo ## What This Project Is
echo TODO — fill in after asking the owner
echo.
echo ## What We Are Building With
echo TODO — ask the owner: language, framework, tools
echo.
echo ## Rules Every AI Must Follow
echo - Save everything important to the files — not only in chat
echo - Update WHATS_HAPPENING_NOW.md before ending any session
echo - Update NEXT_STEPS.md when tasks are done or new ones come up
echo - Refresh QUICK_SUMMARY.md at the end of every session
echo - Follow WHAT_IS_ALLOWED.md before taking any big action
echo - Never save passwords or secret keys into project files
echo.
echo ## Safety Rules
echo - Do not delete files without asking first
echo - Do not make major changes without checking WHAT_IS_ALLOWED.md
echo - Never share or log passwords or keys
echo.
echo ## What Must Be Updated After Every Session
echo Every time — no exceptions:
echo   1. WHATS_HAPPENING_NOW.md
echo   2. NEXT_STEPS.md
echo   3. SESSION_HISTORY.md
echo   4. QUICK_SUMMARY.md
echo.
echo When something changed:
echo   5. WHAT_I_KNOW.md        — new stable information
echo   6. HOW_IT_WORKS.md       — design changed
echo   7. DECISIONS_WE_MADE.md  — important choice made
echo   8. ERRORS_WE_HIT.md      — something broke
echo   9. VERSION_HISTORY.md    — something finished
) > docs\PROJECT_RULES.md

REM ── docs/QUICK_SUMMARY.md ──────────────────────────────
(
echo # QUICK SUMMARY
echo # Read this first when catching up fast. Rewrite at end of every session.
echo.
echo ## Last Updated
echo %NOW%
echo.
echo ## AI Tool Used Last
echo ahos-init.bat ^(setup script^)
echo.
echo ## This Project in One Sentence
echo TODO — ask the owner and fill this in
echo.
echo ## Where We Are Right Now
echo Fresh setup — AHOS structure just created, no project content yet
echo.
echo ## The Most Important Thing To Do Next
echo Ask the owner: what is this project, what are we building with, what is first?
echo.
echo ## Anything Broken or Blocked
echo Nothing — brand new project
echo.
echo ## Quick Commands
echo Start:  TODO
echo Test:   TODO
echo Build:  TODO
echo.
echo ## Where Things Are
echo - Docs: /docs/
echo - Main files: TODO
) > docs\QUICK_SUMMARY.md

REM ── docs/WHAT_I_KNOW.md ────────────────────────────────
(
echo # WHAT I KNOW
echo # Long-term stable facts only. No temporary notes.
echo.
echo ## What We Are Building With
echo TODO
echo.
echo ## Important Decisions ^(Short Version^)
echo None yet
echo.
echo ## Things That Cannot Change
echo TODO
echo.
echo ## How the Owner Likes Things Done
echo TODO
echo.
echo ## Notes for Any New AI Coming In
echo Fresh project. Read PROJECT_RULES.md, then ask the owner
echo what this project is before doing anything else.
) > docs\WHAT_I_KNOW.md

REM ── docs/WHATS_HAPPENING_NOW.md ────────────────────────
(
echo # WHAT'S HAPPENING NOW
echo # The handoff file. Update every single session.
echo.
echo ## Last Updated
echo %NOW%
echo.
echo ## AI Tool Used This Session
echo ahos-init.bat ^(setup script^)
echo.
echo ## What We Got Done
echo - AHOS v2.0 project structure created by init script
echo.
echo ## Where Things Stand Right Now
echo All AHOS files exist with template content.
echo Nothing project-specific has been filled in yet.
echo.
echo ## The Single Most Important Next Step
echo Ask the owner what this project is and fill in the project details.
echo.
echo ## Problems or Blockers
echo None
echo.
echo ## Notes for Whoever Works On This Next
echo Brand new project. Read PROJECT_RULES.md first.
echo Ask 3 questions before writing any code:
echo   1. What is this project?
echo   2. What are we building with?
echo   3. What is the first thing to build?
echo.
echo ## Areas That Are Fragile — Handle With Care
echo Nothing fragile yet — empty project
) > docs\WHATS_HAPPENING_NOW.md

REM ── docs/NEXT_STEPS.md ─────────────────────────────────
(
echo # NEXT STEPS
echo # The to-do list. Keep this current every session.
echo.
echo ## Must Do Now
echo - [ ] Ask the owner what this project is and fill in PROJECT_RULES.md [Easy]
echo - [ ] Fill in WHAT_I_KNOW.md with the tech stack [Easy]
echo - [ ] Fill in HOW_IT_WORKS.md with the system design [Medium]
echo - [ ] Fill in TOOLS_AVAILABLE.md with available tools [Easy]
echo - [ ] Get the development environment running [Medium]
echo.
echo ## Do Soon
echo - [ ] Set up testing [Medium]
echo - [ ] Set up deployment [Medium]
echo.
echo ## Nice To Have Later
echo - [ ] Add more tasks as project grows
echo.
echo ## Done
echo - [x] AHOS v2.0 initialized by script — %DATE%
) > docs\NEXT_STEPS.md

REM ── docs/HOW_IT_WORKS.md ───────────────────────────────
(
echo # HOW IT WORKS
echo # Full system design. Any AI should understand everything in 2 minutes.
echo.
echo ## The Big Picture
echo TODO — fill in after asking the owner
echo.
echo ## The Pieces
echo ^| Piece ^| What It Does ^| Where It Lives ^|
echo ^|-------^|-------------^|----------------^|
echo ^| TODO  ^| TODO        ^| TODO           ^|
echo.
echo ## How Data Moves Through the System
echo TODO
echo.
echo ## External Services We Connect To
echo ^| Service ^| What It Does ^| How We Connect ^|
echo ^|---------^|-------------^|----------------^|
echo ^| TODO    ^| TODO        ^| TODO           ^|
echo.
echo ## Things We Know Need Improving Later
echo None yet
) > docs\HOW_IT_WORKS.md

REM ── docs/DECISIONS_WE_MADE.md ──────────────────────────
(
echo # DECISIONS WE MADE
echo # Every big choice logged here.
echo.
echo ## Template
echo ### [Short title]
echo - **Date:** [When]
echo - **What we decided:** [The choice]
echo - **Why:** [The reason]
echo - **What else we considered:** [Other options]
echo - **How to undo it:** [If needed]
echo.
echo ---
echo.
echo ### Using AHOS as our project system
echo - **Date:** %DATE%
echo - **What we decided:** Use AHOS v2.0 so any AI tool can work on this project
echo - **Why:** Makes switching between Claude, Gemini, OpenCode, Antigravity seamless
echo - **What else we considered:** No system — managing context manually
echo - **How to undo it:** Remove the AHOS files and manage context manually
) > docs\DECISIONS_WE_MADE.md

REM ── docs/HOW_TO_TEST.md ────────────────────────────────
(
echo # HOW TO TEST
echo.
echo ## Run All Tests
echo TODO — fill in test command
echo.
echo ## Checklist Before Saving Work
echo - [ ] All tests pass
echo - [ ] No passwords in files being saved
echo - [ ] WHATS_HAPPENING_NOW.md is updated
) > docs\HOW_TO_TEST.md

REM ── docs/TOOLS_AVAILABLE.md ────────────────────────────
(
echo # TOOLS AVAILABLE
echo.
echo ## Commands
echo ^| Command ^| What It Does ^|
echo ^|---------^|-------------^|
echo ^| TODO    ^| TODO        ^|
echo.
echo ## Connected Services / MCPs
echo ^| Name ^| What It Does ^| How to Connect ^|
echo ^|------^|-------------^|----------------^|
echo ^| TODO ^| TODO        ^| TODO           ^|
echo.
echo ## Notes for Each AI Tool
echo - **Claude Code:** Works out of the box
echo - **Gemini CLI:** Use @filename, e.g. @docs/QUICK_SUMMARY.md
echo - **OpenCode:** No special settings needed
echo - **Antigravity:** No special settings needed
) > docs\TOOLS_AVAILABLE.md

REM ── docs/WHAT_IS_ALLOWED.md ────────────────────────────
(
echo # WHAT IS ALLOWED
echo # Rules for what the AI can and cannot do. Rules, not suggestions.
echo.
echo ## YES — Do These Freely
echo - Read any file in the project
echo - Write to any file in /docs/
echo - Run test commands
echo - Install development tools
echo - Create new files
echo - Commit and push to feature branches
echo.
echo ## ASK FIRST — Check Before Doing
echo - Delete any existing file
echo - Change the database structure
echo - Install new packages the project depends on
echo - Push to the main branch
echo - Rename or restructure folders
echo.
echo ## NEVER — These Need Written Permission
echo - Touch files with real passwords or keys
echo - Deploy the project live to users
echo - Delete or wipe database tables
echo - Change billing or payment code
echo - Turn off tests or safety checks permanently
echo.
echo ## What To Do When Not Sure
echo   1. STOP
echo   2. Write it in WHATS_HAPPENING_NOW.md under Problems
echo   3. Say what you need permission for
echo   4. Wait for instructions
) > docs\WHAT_IS_ALLOWED.md

REM ── docs/SESSION_HISTORY.md ────────────────────────────
(
echo # SESSION HISTORY
echo.
echo ## Template
echo ### [Date] — [AI Tool]
echo - **What we did:** [Summary]
echo - **Problems we hit:** [Issues]
echo - **State when we stopped:** [Where things stood]
echo.
echo ---
echo.
echo ### %NOW% — ahos-init.bat ^(setup script^)
echo - **What we did:** Created full AHOS v2.0 project structure
echo - **Problems we hit:** None
echo - **State when we stopped:** Clean init, all docs in template state
) > docs\SESSION_HISTORY.md

REM ── docs/ERRORS_WE_HIT.md ─────────────────────────────
(
echo # ERRORS WE HIT
echo # Every significant problem. Stops us hitting the same wall twice.
echo.
echo ## Template
echo ### [Short name] — [Date]
echo - **What the error was:** [Description]
echo - **How we fixed it:** [Solution]
echo - **Status:** FIXED / OPEN / WORKAROUND
echo.
echo ---
echo.
echo *No errors logged yet.*
) > docs\ERRORS_WE_HIT.md

REM ── docs/SETUP_GUIDE.md ────────────────────────────────
(
echo # SETUP GUIDE
echo.
echo ## Step-by-Step Setup
echo TODO — fill in as project develops
echo.
echo ## What You Need Installed
echo TODO
echo.
echo ## Environment Variables Needed
echo See PASSWORDS_NEEDED.md for the full list.
) > docs\SETUP_GUIDE.md

REM ── docs/VERSION_HISTORY.md ────────────────────────────
(
echo # VERSION HISTORY
echo.
echo ## Coming Up
echo ### Added
echo - AHOS v2.0 system initialized
echo.
echo ## Version 0.0.1 — %DATE%
echo ### Added
echo - Project created with AHOS v2.0
) > docs\VERSION_HISTORY.md

REM ── docs/PASSWORDS_NEEDED.md ───────────────────────────
(
echo # PASSWORDS AND KEYS NEEDED
echo # Lists WHAT we need — never actual values.
echo # Real passwords go in .env on your computer. Never commit .env.
echo.
echo ## What This Project Needs
echo ^| Key Name ^| What It's For ^| Where To Get It ^|
echo ^|----------^|--------------^|-----------------^|
echo ^| TODO     ^| TODO         ^| TODO            ^|
echo.
echo ## .env Format
echo TODO_KEY=
) > docs\PASSWORDS_NEEDED.md

REM ── CLAUDE.md ──────────────────────────────────────────
(
echo # FOR CLAUDE — Claude Code and Claude.ai
echo # AHOS v2.0 ^| Solomon Christ Holdings Inc.
echo.
echo ## READ THESE IN ORDER — Do Not Skip Any
echo 1.  docs/PROJECT_RULES.md        ^<- The rulebook — read this first
echo 2.  docs/QUICK_SUMMARY.md        ^<- Fast catch-up
echo 3.  docs/WHAT_I_KNOW.md          ^<- Stable project facts
echo 4.  docs/WHATS_HAPPENING_NOW.md  ^<- Where we left off
echo 5.  docs/NEXT_STEPS.md           ^<- What to do
echo 6.  docs/WHAT_IS_ALLOWED.md      ^<- What you can do without asking
echo 7.  docs/TOOLS_AVAILABLE.md      ^<- What tools you have
echo 8.  docs/HOW_IT_WORKS.md         ^<- How the project is designed
echo 9.  docs/DECISIONS_WE_MADE.md    ^<- Why things are the way they are
echo 10. docs/ERRORS_WE_HIT.md        ^<- Problems to avoid
echo.
echo ## Operating Rules
echo - The files are your only source of truth — never rely on chat history
echo - Do not assume anything not in the files
echo - Do not end any session without completing the checklist
echo - WHAT_IS_ALLOWED.md is law — no exceptions
echo.
echo ## End-of-Session Checklist — Complete Every One
echo - [ ] WHATS_HAPPENING_NOW.md updated
echo - [ ] NEXT_STEPS.md updated
echo - [ ] SESSION_HISTORY.md new entry added
echo - [ ] QUICK_SUMMARY.md rewritten
echo - [ ] Other docs updated as needed
echo - [ ] git add . ^&^& git commit -m "[claude] what was done"
echo - [ ] git push
) > CLAUDE.md

REM ── AGENTS.md ──────────────────────────────────────────
(
echo # FOR AGENTS — OpenCode, Antigravity, Codex, and Any Other AI
echo # AHOS v2.0 ^| Solomon Christ Holdings Inc.
echo.
echo ## READ THESE IN ORDER — Do Not Skip Any
echo 1.  docs/PROJECT_RULES.md
echo 2.  docs/QUICK_SUMMARY.md
echo 3.  docs/WHAT_I_KNOW.md
echo 4.  docs/WHATS_HAPPENING_NOW.md
echo 5.  docs/NEXT_STEPS.md
echo 6.  docs/WHAT_IS_ALLOWED.md
echo 7.  docs/TOOLS_AVAILABLE.md
echo 8.  docs/HOW_IT_WORKS.md
echo 9.  docs/DECISIONS_WE_MADE.md
echo 10. docs/ERRORS_WE_HIT.md
echo.
echo ## Operating Rules
echo - The files are your only source of truth
echo - Do not skip the reading list
echo - WHAT_IS_ALLOWED.md is law
echo.
echo ## End-of-Session Checklist
echo - [ ] WHATS_HAPPENING_NOW.md updated
echo - [ ] NEXT_STEPS.md updated
echo - [ ] SESSION_HISTORY.md new entry added
echo - [ ] QUICK_SUMMARY.md rewritten
echo - [ ] git add . ^&^& git commit -m "[your-ai-name] what was done"
echo - [ ] git push
) > AGENTS.md

REM ── GEMINI.md ──────────────────────────────────────────
(
echo # FOR GEMINI — Gemini CLI and Google AI Tools
echo # AHOS v2.0 ^| Solomon Christ Holdings Inc.
echo.
echo ## READ THESE IN ORDER — Do Not Skip Any
echo 1.  docs/PROJECT_RULES.md
echo 2.  docs/QUICK_SUMMARY.md
echo 3.  docs/WHAT_I_KNOW.md
echo 4.  docs/WHATS_HAPPENING_NOW.md
echo 5.  docs/NEXT_STEPS.md
echo 6.  docs/WHAT_IS_ALLOWED.md
echo 7.  docs/TOOLS_AVAILABLE.md
echo 8.  docs/HOW_IT_WORKS.md
echo 9.  docs/DECISIONS_WE_MADE.md
echo 10. docs/ERRORS_WE_HIT.md
echo.
echo ## Operating Rules
echo - The files are your only source of truth
echo - Do not skip the reading list
echo - WHAT_IS_ALLOWED.md is law
echo.
echo ## Gemini Notes
echo - Use @filename syntax: @docs/QUICK_SUMMARY.md
echo - If context is limited, read QUICK_SUMMARY.md first
echo.
echo ## End-of-Session Checklist
echo - [ ] WHATS_HAPPENING_NOW.md updated
echo - [ ] NEXT_STEPS.md updated
echo - [ ] SESSION_HISTORY.md new entry added
echo - [ ] QUICK_SUMMARY.md rewritten
echo - [ ] git add . ^&^& git commit -m "[gemini] what was done"
echo - [ ] git push
) > GEMINI.md

REM ── README.md ──────────────────────────────────────────
(
echo # %PROJECT%
echo.
echo TODO — describe what this project is
echo.
echo ## For AI Tools
echo Read CLAUDE.md, AGENTS.md, or GEMINI.md depending on your tool.
echo.
echo ---
echo Powered by AHOS v2.0 — Any AI, Any Project, Any Time.
echo Solomon Christ Holdings Inc.
) > README.md

REM ── Git commit ─────────────────────────────────────────
git add . -q 2>nul
git commit -q -m "[ahos] init: project created with AHOS v2.0" 2>nul

echo   Done. Project ready in: .\%PROJECT%
echo.
echo   Next steps:
echo   1. cd %PROJECT%
echo   2. Open your AI tool and paste ONE of these files:
echo      CLAUDE.md   — for Claude Code or Claude.ai
echo      GEMINI.md   — for Gemini CLI
echo      AGENTS.md   — for OpenCode, Antigravity, or anything else
echo.
echo   The AI reads the project files and asks what you want to build.
echo   No setup needed — straight to work.
echo.

endlocal
