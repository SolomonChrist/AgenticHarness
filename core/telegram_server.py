import os
import sys
import json
import asyncio
import datetime
import argparse
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from onboarding_manager import OnboardingManager

WORKSPACE_PATH = None
STATE_FILE = None

def get_state():
    if not STATE_FILE.exists():
        return {
            "authorized_chat_id": None,
            "last_team_comms_offset": 0,
            "ftue_active": False,
            "ftue_step": 1,
            "ftue_data": {}
        }
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except:
        return {
            "authorized_chat_id": None,
            "last_team_comms_offset": 0,
            "ftue_active": False,
            "ftue_step": 1,
            "ftue_data": {}
        }

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")

def is_authorized(chat_id, state):
    if state["authorized_chat_id"] is None:
        state["authorized_chat_id"] = chat_id
        save_state(state)
        return True
    return state["authorized_chat_id"] == chat_id

def read_file_safe(rel_path):
    p = WORKSPACE_PATH / rel_path
    if p.exists() and p.is_file():
        return p.read_text(encoding="utf-8")
    return "File not found."

# --- Commands ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    state = get_state()
    
    if not is_authorized(chat_id, state):
        return
        
    manager = OnboardingManager(WORKSPACE_PATH)
    if manager.is_onboarded():
        # Ensure our offset is caught up to avoid spamming the whole file on start
        comms_path = WORKSPACE_PATH / "MasterBot" / "workspace" / "TEAM_COMMUNICATION.md"
        if comms_path.exists():
            state["last_team_comms_offset"] = comms_path.stat().st_size
            save_state(state)
        await update.message.reply_text("Agentic Harness connected. MasterBot is active.")
        return
        
    # Start FTUE
    state["ftue_active"] = True
    state["ftue_step"] = 2
    state["ftue_data"] = {}
    save_state(state)
    await update.message.reply_text("Welcome to Agentic Harness.\nLet's configure your MasterBot.\n\nStep 2: What should we name your MasterBot? [Default: MasterBot]")

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = get_state()
    if not is_authorized(update.effective_chat.id, state): return
    content = read_file_safe("System/SYSTEM_STATUS.md")
    await update.message.reply_text(content[:4000])

async def board_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = get_state()
    if not is_authorized(update.effective_chat.id, state): return
    content = read_file_safe("MasterBot/workspace/MASTER_BOARD.md")
    await update.message.reply_text(content[:4000])

async def tasks_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = get_state()
    if not is_authorized(update.effective_chat.id, state): return
    content = read_file_safe("MasterBot/workspace/MASTER_TASKS.md")
    await update.message.reply_text(content[:4000])

# --- FTUE Handlers ---

async def handle_ftue(update: Update, state):
    text = update.message.text.strip()
    step = state["ftue_step"]
    data = state["ftue_data"]
    manager = OnboardingManager(WORKSPACE_PATH)
    
    if step == 2:
        # Step 2: Name
        data["name"] = text if text else "MasterBot"
        state["ftue_step"] = 2.1
        save_state(state)
        await update.message.reply_text("What is its Role Label? [Default: Chief of Staff]")
    
    elif step == 2.1:
        data["role"] = text if text else "Chief of Staff"
        state["ftue_step"] = 2.2
        save_state(state)
        await update.message.reply_text("What is its Movement Style? [Default: calm]")
        
    elif step == 2.2:
        data["style"] = text if text else "calm"
        state["ftue_step"] = 2.3
        save_state(state)
        await update.message.reply_text("Short Purpose? [Default: Coordinate work...]")
        
    elif step == 2.3:
        data["purpose"] = text if text else "Coordinate work and protect operator time."
        # Full step 2 complete, process
        manager.process_step(2, data)
        state["ftue_step"] = 3
        save_state(state)
        await update.message.reply_text("Step 3: Provider Setup.\nSend '1' for OpenAI, '2' for LM Studio, or '3' for Configure Later.")
        
    elif step == 3:
        choice = text if text in ["1", "2"] else "3"
        data["provider_choice"] = choice
        if choice == "2":
            state["ftue_step"] = 3.1
            save_state(state)
            await update.message.reply_text("Provide LM Studio Base URL [Default: http://localhost:1234/v1]")
        else:
            manager.process_step(3, data)
            state["ftue_step"] = 4
            save_state(state)
            await update.message.reply_text("Step 4: Create a first project? (yes/no)")
            
    elif step == 3.1: # LM Studio URL
        data["api_base"] = text if text else "http://localhost:1234/v1"
        manager.process_step(3, data)
        state["ftue_step"] = 4
        save_state(state)
        await update.message.reply_text("Step 4: Create a first project? (yes/no)")
        
    elif step == 4:
        if text.lower() in ['y', 'yes', 'true']:
            data["create_project"] = True
            state["ftue_step"] = 4.1
            save_state(state)
            await update.message.reply_text("Project Name? [Default: Research]")
        else:
            data["create_project"] = False
            manager.process_step(4, data)
            manager.process_step(5, data) # Finalize
            state["ftue_active"] = False
            save_state(state)
            await update.message.reply_text("Onboarding complete! MasterBot generated.")
            
    elif step == 4.1:
        data["project_name"] = text if text else "Research"
        state["ftue_step"] = 4.2
        save_state(state)
        await update.message.reply_text("Project Purpose?")
        
    elif step == 4.2:
        data["project_purpose"] = text if text else "Initial research and exploration."
        state["ftue_step"] = 4.3
        save_state(state)
        await update.message.reply_text("Real Absolute Workspace Path for pointer? (optional)")
        
    elif step == 4.3:
        data["project_path"] = text
        manager.process_step(4, data)
        manager.process_step(5, data) # Finalize
        state["ftue_active"] = False
        save_state(state)
        await update.message.reply_text("Onboarding complete! Your workspace is ready.\nUse /status or just send tasks here.")

# --- Message Handler ---

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    state = get_state()
    
    if not is_authorized(chat_id, state): return
    
    if state.get("ftue_active"):
        await handle_ftue(update, state)
        return
        
    # Operator Note Logic
    msg = update.message.text.strip()
    if not msg: return
    
    notes_path = WORKSPACE_PATH / "MasterBot" / "workspace" / "OPERATOR_NOTES.md"
    current = ""
    if notes_path.exists():
        current = notes_path.read_text(encoding="utf-8")
        
    ts = datetime.datetime.now().astimezone().isoformat(timespec='seconds')
    entry = f"\n## Entry\nTimestamp: {ts}\nOperator: Operator\nStatus: new\n\n{msg}\n"
    
    if current and not current.endswith("\n"): current += "\n"
    
    # Write and confirm
    notes_path.parent.mkdir(parents=True, exist_ok=True)
    notes_path.write_text(current + entry, encoding="utf-8", newline="\n")
    # Small confirmation receipt so user knows it was logged
    await update.message.reply_text("✔️ Appended to OPERATOR_NOTES.md")

# --- Background Watcher ---

async def watch_communications(app: Application):
    comms_path = WORKSPACE_PATH / "MasterBot" / "workspace" / "TEAM_COMMUNICATION.md"
    
    while True:
        await asyncio.sleep(2)
        state = get_state()
        chat_id = state.get("authorized_chat_id")
        
        if not chat_id or state.get("ftue_active") or not comms_path.exists():
            continue
            
        offset = state.get("last_team_comms_offset", 0)
        current_size = comms_path.stat().st_size
        
        if current_size < offset:
            # File was truncated/cleared
            offset = 0
            
        if current_size > offset:
            # Read only the new bytes
            with open(comms_path, "rb") as f:
                f.seek(offset)
                new_bytes = f.read(current_size - offset)
                
            new_text = new_bytes.decode("utf-8", errors="replace").strip()
            
            # Update offset before sending to avoid double-sends on error
            state["last_team_comms_offset"] = current_size
            save_state(state)
            
            if new_text:
                # Send the new chunk. Telegram has a 4096 char limit per message.
                for i in range(0, len(new_text), 4000):
                    chunk = new_text[i:i+4000]
                    try:
                        await app.bot.send_message(chat_id=chat_id, text=chunk)
                    except Exception as e:
                        print(f"Telegram send error: {e}")

# --- Main ---

def main():
    global WORKSPACE_PATH, STATE_FILE
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True, help="Path to workspace")
    parser.add_argument("--token", help="Telegram Bot Token. Alternately set TELEGRAM_BOT_TOKEN env var.")
    args = parser.parse_args()
    
    WORKSPACE_PATH = Path(args.workspace).resolve()
    STATE_FILE = WORKSPACE_PATH / "System" / "TELEGRAM_STATE.json"
    
    token = args.token or os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("ERROR: Must provide --token or export TELEGRAM_BOT_TOKEN.")
        sys.exit(1)
        
    print(f"Connecting Agentic Harness to Telegram for workspace: {WORKSPACE_PATH}")
    app = Application.builder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("board", board_cmd))
    app.add_handler(CommandHandler("tasks", tasks_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Schedule background watcher
    loop = asyncio.get_event_loop()
    loop.create_task(watch_communications(app))
    
    # Run long-polling
    app.run_polling()

if __name__ == "__main__":
    main()
