🚀 AHOS: The Agentic Harness Operating System
"One Prompt to Rule Them All. Build Anything, Anywhere, with Any AI." 


🧠 The Problem
You’re crushing a project with Claude Code and suddenly... BOOM. You hit your daily message limit. 🛑

You want to switch to Gemini CLI or OpenCode to keep the momentum going, but the new AI has no idea what you were doing. You spend an hour re-explaining the project, or worse, the AI makes a mistake because it lacks context.

✨ The Solution (AHOS)
AHOS turns your GitHub repo into the Brain. The AI is just the Muscle.

By keeping all "memory," "rules," and "todo lists" inside specific files in your repo, you can swap AIs like changing a battery. The new AI reads the repo, sees exactly where the last one left off, and gets straight back to work.

🛠️ How it Works (The "Brain-Swap" Workflow)
Code snippet
graph TD
    A[📂 Your Project Repo] --> B{🧠 AHOS "Brain"}
    B --> C[📄 PROJECT_RULES.md]
    B --> D[📄 __MEMORY__.md]
    B --> E[📄 TODO.md]
    
    subgraph "The Muscle (Hot-Swappable)"
    F[🤖 Claude Code] -.->|Reads/Writes| B
    G[♊ Gemini CLI] -.->|Reads/Writes| B
    H[🔓 OpenCode/Local] -.->|Reads/Writes| B
    end

    F -- "Limit Reached" --> G
    G -- "Swap Anytime" --> H
    H -- "Back to" --> F
🚀 Get Started in 60 Seconds
Create a new folder and run git init (keep it private if you prefer!).

Open your AI Harness (Claude Code, Gemini CLI, OpenClaw, etc.).

Copy & Paste the Genesis Prompt below.

Watch the magic happen. The AI will build its own documentation and start the project.

📦 The AHOS Folder Structure
Once initialized, your project will look like this:

📂 /docs: The persistent memory center.

📜 PROJECT_RULES.md: The Constitution. Tells the AI exactly how to code and behave.

💾 __MEMORY__.md: Long-term "facts" about the project.

📋 TODO.md: The master checklist.

🔄 LAST_WORK_ITEMS.md: The "Save Game" file for the next AI.

🛡️ __PERMISSIONS__.md: What the AI can and can't do without asking.

🏁 __CLAUDE.md / __GEMINI.md / __AGENTS.md: Entry points that tell each specific AI how to "boot up" the project brain.

⚡ The Genesis Prompt
Paste this into your AI to initialize the system immediately:

Markdown
# AHOS INITIALIZATION PROTOCOL v2.0
You are now the Lead Architect and Agentic Engineer. Your mission is to build a "Portable Repo Intelligence" that works across ANY AI system (Claude, Gemini, OpenCode, OpenClaw, etc.).

### STEP 1: SCAFFOLDING
Create the following structure immediately:
- /docs/PROJECT_RULES.md (The Project Constitution)
- /docs/__MEMORY__.md (Long-term project knowledge/facts)
- /docs/__TOOLS__.md (Registry of CLI/MCP tools available)
- /docs/__PERMISSIONS__.md (Safety guardrails: Pre-approved vs. Ask-first)
- /docs/LAST_WORK_ITEMS.md (The "Save Game" checkpoint for handoffs)
- /docs/TODO.md (The execution queue)
- /docs/ARCHITECTURE.md (High-level system design)
- /docs/DECISIONS.md (Log of why we made certain choices)
- /docs/TESTING.md (How to verify work is correct)
- /docs/SESSION_LOG.md (Chronological audit trail)
- __CLAUDE.md__, __GEMINI.md__, __AGENTS.md__ (Harness-specific entry points)

### STEP 2: THE "RELIANCE" RULE
- Never store critical information ONLY in your chat history.
- If it isn't in the `/docs` or a Git commit, it doesn't exist.
- You MUST update `LAST_WORK_ITEMS.md` and `TODO.md` before ending any session.

### STEP 3: EXECUTION
- If this is a new project: Initialize the files and ask "What are we building today?"
- If this is an existing project: Read all files in `/docs` and say "I am fully synchronized. Ready to continue from [Last Task]."

BEGIN AHOS INITIALIZATION NOW.
💡 ELI5: Why does this work?
Imagine you are building a Lego castle, but you have to switch builders every hour.

Without AHOS, the new builder has to guess where the towers go. With AHOS, the first builder leaves a detailed instruction book, a map of the floor, and a note saying, "I just finished the north gate; you need to start on the dragon next."

The project never stops, and it never gets confused.

🤝 Community & Support
AHOS is designed for the Agentic Age. If you find a way to make the "Brain" smarter, fork this repo and share it!

Built for builders. Powered by whatever AI you have on hand. 🛠️
