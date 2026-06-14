import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import models
from bot import ai_helpers

logger = logging.getLogger(__name__)

# In-memory throttle for Vibe Check interventions (group_id -> last_timestamp)
vibe_check_throttle = {}

def check_and_announce_unblocked_tasks(task_id: int, bot, group_id: int):
    """Checks if any tasks are blocked by the given task, and pings the group if they are now unblocked."""
    import sqlite3
    conn = models.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE blocked_by = ?", (task_id,))
    blocked_tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    import asyncio
    for bt in blocked_tasks:
        bt_assignee_str = ""
        if bt["assigned_to"]:
            bt_user = models.get_task(bt["id"])
            if bt_user:
                name = bt_user["assignee_username"] or bt_user["assignee_first_name"]
                bt_assignee_str = f" assigned to @{name}" if bt_user["assignee_username"] else f" assigned to {name}"
        
        unblock_msg = (
            f"🔓 *Task Unblocked!* \n"
            f"Blocker Task {task_id} completed. Task {bt['id']}: *\"{bt['description']}\"*{bt_assignee_str} is now unblocked and ready for work!"
        )
        try:
            asyncio.create_task(bot.send_message(
                chat_id=group_id,
                text=unblock_msg,
                parse_mode="Markdown"
            ))
        except Exception as e:
            print(f"Failed to send unblock message: {e}")

def get_username_or_name(user):
    """Returns username if present (prefixed with @), otherwise first_name."""
    if user.username:
        return f"@{user.username}"
    return user.first_name

def register_group_and_member(update: Update):
    """Ensures group, user, and membership are registered in SQLite on any interaction."""
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return
    models.save_user(user.id, user.username, user.first_name, user.last_name)
    if chat.type in ["group", "supergroup"]:
        models.save_group(chat.id, chat.title)
        models.add_group_member(chat.id, user.id)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    register_group_and_member(update)
    user = update.effective_user
    chat = update.effective_chat
    
    welcome_text = (
        "🔄 **Gradeline AI (SyncUp)**\n"
        "*The Accountability Bot for Student Group Projects*\n\n"
        "I am here to eliminate slacking, resolve teammate friction, automatically parse rubrics, "
        "and track contribution shares with an interactive web dashboard!\n\n"
        "💡 **What I Do & How I Help:**\n"
        "1. 📚 **AI Rubric Parser:** Automatically extracts deliverables and due dates from assignments.\n"
        "2. 🤝 **Fair Workload Balancing:** Claim tasks, release them with SOS when overwhelmed.\n"
        "3. 🤫 **Anonymous Nudges:** Gently remind a slacking teammate without social awkwardness.\n"
        "4. 📝 **AI Standup Summary:** Summarizes group chat discussions and decisions automatically.\n"
        "5. 🏆 **Reliability Leaderboard:** Encourages participation with XP points and tracks contribution shares.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💬 **NATURAL LANGUAGE COMMANDS (No slashes needed!)**\n"
        "Just talk to me in plain English! I will analyze your words and take action:\n"
        "• *\"show tasks\"* or *\"what are the tasks\"* — List group deliverables\n"
        "• *\"I claim task 3\"* or *\"I will do task 3\"* — Assign task to yourself\n"
        "• *\"done with task 2\"* or *\"task 2 is complete\"* — Complete task & get XP\n"
        "• *\"I need backup on task 2\"* or *\"sos task 2\"* — Release task back to pool\n"
        "• *\"brief us\"* or *\"standup summary\"* — Get AI standup chat summary\n"
        "• *\"show leaderboard\"* or *\"stats\"* — Check group XP scores\n"
        "• *\"project receipt\"* or *\"grade receipt\"* — Get contribution markdown proof\n\n"
        "🤫 **ANONYMOUS REMINDERS:**\n"
        "• *\"nudge task 3\"* or *\"nudge teammate on task 3\"*\n"
        "👉 _Note: To nudge anonymously, you MUST send this text to me in our private DM chat so your team doesn't see!_\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🛠️ **SLASH COMMANDS (Quick Shortcuts):**\n"
        "• `/start` or `/help` — Display this onboarding guide\n"
        "• `/analyze [rubric_text]` — Paste or reply to rubric to parse tasks\n"
        "• `/tasks` — Show task list with interactive buttons\n"
        "• `/claim [task_id]` — Claim a task (e.g. `/claim 2`)\n"
        "• `/complete [task_id]` — Mark task as done (e.g. `/complete 2`)\n"
        "• `/sos [task_id]` — Release task back to pool (e.g. `/sos 2`)\n"
        "• `/nudge [task_id]` — Send anonymous check-in (DM only)\n"
        "• `/standup` — Request AI standup log summary\n"
        "• `/stats` — View team leaderboard\n"
        "• `/receipt` — Get contribution receipt markdown\n\n"
        "🌐 **Web Dashboard URL:** http://localhost:8000"
    )
    
    if chat.type in ["group", "supergroup"]:
        await update.message.reply_text(welcome_text, parse_mode="Markdown")
    else:
        # Direct Message Welcome
        dm_header = (
            f"👋 Hi {user.first_name}! Thanks for opening me.\n\n"
            "⚠️ **IMPORTANT:** To use me fully, please add me to your project group chat!\n"
            "Once added, I will automatically start tracking your messages and rubrics.\n\n"
        )
        await update.message.reply_text(dm_header + welcome_text, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /help command."""
    await start_command(update, context)

async def auto_register_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Middleware running on every group text message to log history, check vibes, and parse NLP intents."""
    if not update.message or not update.message.text:
        return
        
    chat = update.effective_chat
    user = update.effective_user
    text = update.message.text
    
    # Skip processing if message is a standard slash command
    if text.startswith("/"):
        return
        
    # Auto-register group, user and membership
    register_group_and_member(update)
    
    # Log message for /standup summary
    models.log_message(chat.id, user.id, user.username or user.first_name, text)
    
    # Passive Sentiment Vibe Check
    if chat.type in ["group", "supergroup"]:
        if ai_helpers.check_text_for_toxic_vibe(text):
            now = datetime.now().timestamp()
            last_intervention = vibe_check_throttle.get(chat.id, 0)
            
            # Throttle intervention to once every 10 minutes per group to avoid spam
            if now - last_intervention > 600:
                # Double check with lightweight LLM
                recent_messages = models.get_recent_messages(chat.id, limit=10)
                if ai_helpers.evaluate_vibe_severity_ai(recent_messages):
                    vibe_check_throttle[chat.id] = now
                    intervention_text = (
                        "🤖 *Vibe Check:* Hey team, things seem a bit stressful! "
                        "Remember you can say *'show tasks'* to re-align workload, "
                        "or *'I need backup on task 2'* to share deliverables easily. Let's sync up! 🤝"
                    )
                    await update.message.reply_text(intervention_text, parse_mode="Markdown")

    # NLP Intent Parser Router
    bot_username = context.bot.username
    is_private = chat.type == "private"
    is_mentioned = bot_username and f"@{bot_username}" in text
    
    action_keywords = ["task", "tasks", "claim", "done", "complete", "completed", "nudge", "stats", "leaderboard", "sos", "backup", "receipt", "standup", "deliverables"]
    has_keywords = any(kw in text.lower() for kw in action_keywords)
    
    if is_private or is_mentioned or has_keywords:
        # Call Gemini parser to extract intent
        nlp_res = ai_helpers.parse_natural_language_intent(text)
        intent = nlp_res.get("intent", "none")
        task_id = nlp_res.get("task_id")
        
        if intent == "none":
            return
            
        logger.info(f"NLP parsed action - Text: '{text}' | Intent: {intent} | Task ID: {task_id}")
        
        if intent == "show_tasks":
            await tasks_command(update, context)
            
        elif intent == "claim_task":
            if task_id:
                task = models.get_task(task_id)
                if not task or (chat.type in ["group", "supergroup"] and task["group_id"] != chat.id):
                    await update.message.reply_text("❌ Task not found.")
                    return
                if models.is_task_blocked(task_id):
                    blocker_desc = task.get("blocker_description", f"Task {task['blocked_by']}")
                    await update.message.reply_text(f"⚠️ *Task Blocked!* You cannot claim Task {task_id} because it is blocked by Task {task['blocked_by']} (*\"{blocker_desc}\"*), which is not completed yet.", parse_mode="Markdown")
                    return
                success = models.claim_task(task_id, user.id)
                if success:
                    name = get_username_or_name(user)
                    await update.message.reply_text(f"🤝 Task {task_id} ('{task['description']}') has been claimed by *{name}*!", parse_mode="Markdown")
                else:
                    await update.message.reply_text(f"❌ Task {task_id} is already claimed or completed.")
            else:
                await update.message.reply_text("❓ I heard you want to claim a task, but I couldn't capture the task ID. Please specify, e.g. 'I will claim task 3'.")
                
        elif intent == "complete_task":
            if task_id:
                task = models.get_task(task_id)
                if not task or (chat.type in ["group", "supergroup"] and task["group_id"] != chat.id):
                    await update.message.reply_text("❌ Task not found.")
                    return
                if not task["assigned_to"]:
                    await update.message.reply_text("❌ Cannot complete an unassigned task.")
                    return
                if models.is_task_blocked(task_id):
                    blocker_desc = task.get("blocker_description", f"Task {task['blocked_by']}")
                    await update.message.reply_text(f"⚠️ *Task Blocked!* You cannot complete Task {task_id} because it is blocked by Task {task['blocked_by']} (*\"{blocker_desc}\"*), which is not completed yet.", parse_mode="Markdown")
                    return
                success = models.complete_task(task_id)
                if success:
                    assignee_name = task["assignee_username"] or task["assignee_first_name"]
                    assignee = f"@{assignee_name}" if task["assignee_username"] else assignee_name
                    await update.message.reply_text(
                        f"✅ Task {task_id} ('{task['description']}') has been completed! *{assignee}* receives +10 Reliability Points! 🏆",
                        parse_mode="Markdown"
                    )
                    check_and_announce_unblocked_tasks(task_id, context.bot, chat.id)
                else:
                    await update.message.reply_text(f"❌ Task {task_id} could not be marked as complete.")
            else:
                await update.message.reply_text("❓ I heard you want to complete a task, but I couldn't capture the task ID. Please specify, e.g. 'Task 2 is complete'.")
                
        elif intent == "sos_task":
            if task_id:
                task = models.get_task(task_id)
                if not task or (chat.type in ["group", "supergroup"] and task["group_id"] != chat.id):
                    await update.message.reply_text("❌ Task not found.")
                    return
                if task["assigned_to"] != user.id:
                    await update.message.reply_text("❌ You can only request SOS backup for tasks currently assigned to you!")
                    return
                success = models.release_task(task_id)
                if success:
                    username = get_username_or_name(user)
                    sos_message = (
                        f"🚨 *Workload Backup Requested!* \n"
                        f"{username} is overwhelmed and requested help on *Task {task_id}*:\n"
                        f"_\"{task['description']}\"_ \n\n"
                        f"The task is now unassigned and back in the pool. Who can take over or split this load? "
                        f"Type 'I claim task {task_id}' to help out! 🤝"
                    )
                    await update.message.reply_text(sos_message, parse_mode="Markdown")
            else:
                await update.message.reply_text("❓ I heard you need help on a task, but I couldn't capture the task ID. Please specify, e.g. 'I need backup on task 3'.")
                
        elif intent == "nudge_task":
            if task_id:
                if chat.type in ["group", "supergroup"]:
                    await update.message.reply_text(
                        "🤫 *Private Nudges preserve anonymity!* Please send this nudge message in a private chat "
                        f"to me (@{context.bot.username}) so your teammates don't see who requested the reminder."
                    )
                    return
                # In DM
                task = models.get_task(task_id)
                if not task:
                    await update.message.reply_text("❌ Task not found.")
                    return
                if task["status"] != "claimed" or not task["assigned_to"]:
                    await update.message.reply_text("❌ You can only nudge tasks claimed by a teammate.")
                    return
                if task["assigned_to"] == user.id:
                    await update.message.reply_text("❌ You cannot nudge yourself!")
                    return
                members = models.get_group_members(task["group_id"])
                if not any(m["id"] == user.id for m in members):
                    await update.message.reply_text("❌ You do not belong to the group chat that owns this task.")
                    return
                models.record_nudge(task["group_id"], task_id, user.id, task["assigned_to"])
                assignee_name = task["assignee_username"] or task["assignee_first_name"]
                assignee = f"@{assignee_name}" if task["assignee_username"] else assignee_name
                nudge_alert = (
                    f"🔔 *Friendly Check-in!* \n"
                    f"Hey {assignee}, a teammate asked me to gently check in on *Task {task_id}*:\n"
                    f"_\"{task['description']}\"_ \n\n"
                    f"Let the team know in the chat if you need help or need workload rebalancing! 🤝"
                )
                await context.bot.send_message(chat_id=task["group_id"], text=nudge_alert, parse_mode="Markdown")
                await update.message.reply_text(f"✅ *Nudge sent anonymously!* I have posted a polite reminder in the group.")
            else:
                await update.message.reply_text("❓ I heard you want to nudge someone, but I couldn't capture the task ID. Please specify, e.g. 'Nudge task 2'.")
                
        elif intent == "show_stats":
            await stats_command(update, context)
            
        elif intent == "show_standup":
            await standup_command(update, context)
            
        elif intent == "show_receipt":
            await receipt_command(update, context)

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /analyze command to parse assignment rubrics."""
    register_group_and_member(update)
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("❌ Rubrics must be analyzed within a group chat project context.")
        return
        
    # Get rubric text from argument or replied message
    rubric_text = ""
    if context.args:
        rubric_text = " ".join(context.args)
    elif update.message.reply_to_message and update.message.reply_to_message.text:
        rubric_text = update.message.reply_to_message.text
        
    if not rubric_text:
        await update.message.reply_text(
            "❌ Please paste the rubric text after `/analyze` or reply to a text message containing the rubric.\n\n"
            "Example: `/analyze Assignment 1: Design a SQLite database for a bot. Due Friday.`"
        )
        return
        
    status_msg = await update.message.reply_text("🤖 *Analyzing assignment rubric with Gemini AI... Please wait.*", parse_mode="Markdown")
    
    # Call Gemini LLM parser
    parsed_tasks = ai_helpers.analyze_rubric(rubric_text)
    
    if not parsed_tasks:
        await status_msg.edit_text("❌ Failed to parse any deliverables from the rubric text. Please check content.")
        return
        
    # Create tasks in DB
    response_lines = ["📋 *AI Parsed Deliverables Added:*"]
    for task in parsed_tasks:
        desc = task.get("description", "").strip()
        due = task.get("due_date", "").strip()
        if desc:
            due_str = f" (Due: {due})" if due else ""
            task_id = models.create_task(chat.id, desc, due)
            response_lines.append(f"{task_id}. **{desc}**{due_str} — `/claim {task_id}`")
            
    response_lines.append("\n👉 Use `/claim [task_id]` or click on `/tasks` to claim a deliverable!")
    
    await status_msg.delete()
    await update.message.reply_text("\n".join(response_lines), parse_mode="Markdown")

async def tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /tasks command to view active deliverables."""
    register_group_and_member(update)
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("❌ Please use `/tasks` in your group chat to see group deliverables.")
        return
        
    tasks = models.get_tasks_for_group(chat.id)
    if not tasks:
        await update.message.reply_text("📋 No deliverables registered yet! Paste a rubric with `/analyze [text]` to get started.")
        return
        
    text_lines = ["📋 *Project Deliverables:*"]
    for task in tasks:
        status_emoji = "🟢" if task["status"] == "open" else ("🟡" if task["status"] == "claimed" else "✅")
        due_str = f" (Due: {task['due_date']})" if task["due_date"] else ""
        
        assignee = "Unassigned"
        if task["status"] != "open":
            assignee_name = task["assignee_username"] or task["assignee_first_name"]
            assignee = f"@{assignee_name}" if task["assignee_username"] else assignee_name
            
        status_txt = "Open" if task["status"] == "open" else ("Claimed" if task["status"] == "claimed" else "Done")
        
        text_lines.append(
            f"**{status_emoji} Task {task['id']}:** {task['description']}{due_str}\n"
            f"   └ Status: `{status_txt}` | Assignee: *{assignee}*"
        )
        
    # Add keyboard shortcut action buttons for quick claim/complete/nudge
    keyboard = []
    open_tasks = [t for t in tasks if t["status"] == "open"][:3]
    claimed_tasks = [t for t in tasks if t["status"] == "claimed"][:3]
    
    for t in open_tasks:
        keyboard.append([InlineKeyboardButton(f"Claim Task {t['id']}", callback_data=f"claim_{t['id']}")])
    for t in claimed_tasks:
        keyboard.append([
            InlineKeyboardButton(f"Complete Task {t['id']}", callback_data=f"complete_{t['id']}"),
            InlineKeyboardButton(f"Nudge Task {t['id']}", callback_data=f"nudge_{t['id']}")
        ])
        
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    await update.message.reply_text("\n\n".join(text_lines), reply_markup=reply_markup, parse_mode="Markdown")

async def inline_keyboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles callback clicks from inline keyboards."""
    query = update.callback_query
    user = update.effective_user
    data = query.data
    
    await query.answer()
    
    action, task_id_str = data.split("_", 1)
    task_id = int(task_id_str)
    task = models.get_task(task_id)
    
    if not task:
        await query.edit_message_reply_markup(reply_markup=None)
        return
        
    if action == "claim":
        if models.is_task_blocked(task_id):
            blocker_desc = task.get("blocker_description", f"Task {task['blocked_by']}")
            await context.bot.send_message(
                chat_id=task["group_id"],
                text=f"⚠️ *Task Blocked!* You cannot claim Task {task_id} because it is blocked by Task {task['blocked_by']} (*\"{blocker_desc}\"*), which is not completed yet.",
                parse_mode="Markdown"
            )
            return
        success = models.claim_task(task_id, user.id)
        if success:
            models.save_user(user.id, user.username, user.first_name, user.last_name)
            models.add_group_member(task["group_id"], user.id)
            name = get_username_or_name(user)
            await context.bot.send_message(
                chat_id=task["group_id"],
                text=f"🤝 Task {task_id} ('{task['description']}') has been claimed by *{name}*!",
                parse_mode="Markdown"
            )
        else:
            await context.bot.send_message(
                chat_id=task["group_id"],
                text=f"❌ Task {task_id} is already claimed or completed."
            )
            
    elif action == "complete":
        if not task["assigned_to"]:
            await context.bot.send_message(chat_id=task["group_id"], text="❌ Cannot complete an unassigned task.")
            return
        if models.is_task_blocked(task_id):
            blocker_desc = task.get("blocker_description", f"Task {task['blocked_by']}")
            await context.bot.send_message(
                chat_id=task["group_id"],
                text=f"⚠️ *Task Blocked!* You cannot complete Task {task_id} because it is blocked by Task {task['blocked_by']} (*\"{blocker_desc}\"*), which is not completed yet.",
                parse_mode="Markdown"
            )
            return
        success = models.complete_task(task_id)
        if success:
            assignee_name = task["assignee_username"] or task["assignee_first_name"]
            assignee = f"@{assignee_name}" if task["assignee_username"] else assignee_name
            await context.bot.send_message(
                chat_id=task["group_id"],
                text=f"✅ Task {task_id} ('{task['description']}') has been completed! *{assignee}* receives +10 Reliability Points! 🏆",
                parse_mode="Markdown"
            )
            check_and_announce_unblocked_tasks(task_id, context.bot, task["group_id"])
        else:
            await context.bot.send_message(
                chat_id=task["group_id"],
                text=f"❌ Task {task_id} could not be marked as complete."
            )
            
    elif action == "nudge":
        nudge_instructions = (
            f"🤫 *Anonymous Nudge:* To nudge teammate on Task {task_id} without them knowing it was you, "
            f"please open a private chat with me (@{context.bot.username}) and type:\n\n"
            f"`/nudge {task_id}`"
        )
        await context.bot.send_message(
            chat_id=task["group_id"],
            text=nudge_instructions,
            parse_mode="Markdown"
        )

async def claim_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /claim [task_id] command."""
    register_group_and_member(update)
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("❌ Please claim tasks inside the group chat.")
        return
        
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("❌ Usage: `/claim [task_id]` (e.g. `/claim 3`)", parse_mode="Markdown")
        return
        
    task_id = int(context.args[0])
    task = models.get_task(task_id)
    
    if not task or task["group_id"] != chat.id:
        await update.message.reply_text("❌ Task not found in this group.")
        return
        
    if models.is_task_blocked(task_id):
        blocker_desc = task.get("blocker_description", f"Task {task['blocked_by']}")
        await update.message.reply_text(f"⚠️ *Task Blocked!* You cannot claim Task {task_id} because it is blocked by Task {task['blocked_by']} (*\"{blocker_desc}\"*), which is not completed yet.", parse_mode="Markdown")
        return
        
    success = models.claim_task(task_id, user.id)
    if success:
        models.save_user(user.id, user.username, user.first_name, user.last_name)
        models.add_group_member(chat.id, user.id)
        name = get_username_or_name(user)
        await update.message.reply_text(f"🤝 Task {task_id} ('{task['description']}') claimed by *{name}*!", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Task is already claimed or completed.")

async def complete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /complete [task_id] command."""
    register_group_and_member(update)
    chat = update.effective_chat
    
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("❌ Please complete tasks inside the group chat.")
        return
        
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("❌ Usage: `/complete [task_id]` (e.g. `/complete 3`)", parse_mode="Markdown")
        return
        
    task_id = int(context.args[0])
    task = models.get_task(task_id)
    
    if not task or task["group_id"] != chat.id:
        await update.message.reply_text("❌ Task not found in this group.")
        return
        
    if models.is_task_blocked(task_id):
        blocker_desc = task.get("blocker_description", f"Task {task['blocked_by']}")
        await update.message.reply_text(f"⚠️ *Task Blocked!* You cannot complete Task {task_id} because it is blocked by Task {task['blocked_by']} (*\"{blocker_desc}\"*), which is not completed yet.", parse_mode="Markdown")
        return
        
    success = models.complete_task(task_id)
    if success:
        assignee_name = task["assignee_username"] or task["assignee_first_name"]
        assignee = f"@{assignee_name}" if task["assignee_username"] else assignee_name
        await update.message.reply_text(
            f"✅ Task {task_id} ('{task['description']}') marked as done! *{assignee}* gets +10 Reliability Points! 🏆",
            parse_mode="Markdown"
        )
        check_and_announce_unblocked_tasks(task_id, context.bot, chat.id)
    else:
        await update.message.reply_text("❌ Task is already completed or has no assignee to credit.")

async def nudge_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the anonymous /nudge [task_id] command (should be run in DM)."""
    register_group_and_member(update)
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type in ["group", "supergroup"]:
        await update.message.reply_text(
            "🤫 *Private Nudges preserve anonymity!* Please send this `/nudge` command in a private message "
            f"to me (@{context.bot.username}) so your teammates don't see who requested the reminder.",
            parse_mode="Markdown"
        )
        try:
            await update.message.delete()
        except Exception:
            pass
        return
        
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("❌ Usage in DM: `/nudge [task_id]` (e.g. `/nudge 2`)", parse_mode="Markdown")
        return
        
    task_id = int(context.args[0])
    task = models.get_task(task_id)
    
    if not task:
        await update.message.reply_text("❌ Task not found.")
        return
        
    if task["status"] != "claimed" or not task["assigned_to"]:
        await update.message.reply_text("❌ You can only nudge tasks that are currently claimed by a teammate.")
        return
        
    if task["assigned_to"] == user.id:
        await update.message.reply_text("❌ You cannot nudge yourself!")
        return
        
    members = models.get_group_members(task["group_id"])
    if not any(m["id"] == user.id for m in members):
        await update.message.reply_text("❌ You do not belong to the group chat that owns this task.")
        return
        
    models.record_nudge(task["group_id"], task_id, user.id, task["assigned_to"])
    
    assignee_name = task["assignee_username"] or task["assignee_first_name"]
    assignee = f"@{assignee_name}" if task["assignee_username"] else assignee_name
    nudge_alert = (
        f"🔔 *Friendly Check-in!* \n"
        f"Hey {assignee}, a teammate asked me to gently check in on *Task {task_id}*:\n"
        f"_\"{task['description']}\"_ \n\n"
        f"Let the team know in the chat if you need help, are blocked, or need workload rebalancing! 🤝"
    )
    
    try:
        await context.bot.send_message(chat_id=task["group_id"], text=nudge_alert, parse_mode="Markdown")
        await update.message.reply_text(f"✅ *Nudge sent anonymously!* I have posted a polite reminder in the group.")
    except Exception as e:
        logger.error(f"Failed to send nudge: {e}")
        await update.message.reply_text("❌ Failed to broadcast nudge in group chat.")

async def sos_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /sos [task_id] workload balancer command."""
    register_group_and_member(update)
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("❌ Please request backup inside the group chat.")
        return
        
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("❌ Usage: `/sos [task_id]` (e.g. `/sos 4`)", parse_mode="Markdown")
        return
        
    task_id = int(context.args[0])
    task = models.get_task(task_id)
    
    if not task or task["group_id"] != chat.id:
        await update.message.reply_text("❌ Task not found in this group.")
        return
        
    if task["assigned_to"] != user.id:
        await update.message.reply_text("❌ You can only request SOS backup for tasks currently assigned to you!")
        return
        
    success = models.release_task(task_id)
    if success:
        username = get_username_or_name(user)
        sos_message = (
            f"🚨 *Workload Backup Requested!* \n"
            f"{username} is overwhelmed and requested help on *Task {task_id}*:\n"
            f"_\"{task['description']}\"_ \n\n"
            f"The task is now unassigned and back in the pool. Who can take over or split this load? "
            f"Use `/claim {task_id}` to help a teammate out! 🤝"
        )
        await update.message.reply_text(sos_message, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Could not process SOS request.")

async def standup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /standup command to generate AI summaries."""
    register_group_and_member(update)
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("❌ Standup summaries must be requested within a group chat.")
        return
        
    status_msg = await update.message.reply_text("🤖 *Reading recent logs and compiling AI standup summary...*", parse_mode="Markdown")
    messages = models.get_recent_messages(chat.id, limit=60)
    if not messages:
        await status_msg.edit_text("📋 No recent chat messages found. Chat with your team first!")
        return
        
    summary = ai_helpers.generate_standup(messages)
    header = f"📝 *SyncUp AI Standup Summary ({chat.title}):*\n\n"
    footer = "\n\n_Summarized using Gemini AI. Use /tasks to update task status._"
    
    await status_msg.delete()
    await update.message.reply_text(f"{header}{summary}{footer}", parse_mode="Markdown")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /stats contribution leaderboard."""
    register_group_and_member(update)
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("❌ View project contribution stats inside the group chat.")
        return
        
    stats = models.get_group_stats(chat.id)
    leaderboard = stats["leaderboard"]
    
    if not leaderboard:
        await update.message.reply_text("🏆 No team stats logged yet. Claim and complete tasks to gain reliability points!")
        return
        
    response_lines = ["🏆 *SyncUp Team Reliability Leaderboard:*", ""]
    medals = ["🥇", "🥈", "🥉"]
    
    for idx, user in enumerate(leaderboard):
        medal = medals[idx] if idx < len(medals) else "👤"
        username_str = f" (@{user['username']})" if user["username"] else ""
        response_lines.append(
            f"{medal} *{user['first_name']}*{username_str} \n"
            f"   └ Points: `{user['reliability_points']} XP` | Completed: `{user['completed_tasks']} tasks`"
        )
        
    await update.message.reply_text("\n".join(response_lines), parse_mode="Markdown")

async def receipt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /receipt command exporting contribution summary."""
    register_group_and_member(update)
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("❌ Project receipts can only be generated in group chats.")
        return
        
    tasks = models.get_tasks_for_group(chat.id)
    stats = models.get_group_stats(chat.id)
    leaderboard = stats["leaderboard"]
    
    if not tasks:
        await update.message.reply_text("❌ No tasks registered yet. Analyze a rubric or add tasks to build a receipt.")
        return
        
    completed_tasks = [t for t in tasks if t["status"] == "completed"]
    total_completed = len(completed_tasks)
    total_tasks = len(tasks)
    
    receipt_date = datetime.now().strftime("%B %d, %Y")
    receipt = [
        f"🧾 **SyncUp Contribution Receipt**",
        f"📁 *Project:* {chat.title}",
        f"📅 *Generated:* {receipt_date}",
        "═" * 30,
        "📊 **TASK DELIVERY RATE**",
        f"• Total deliverables: `{total_tasks}`",
        f"• Completed items: `{total_completed}` (`{total_completed/total_tasks*100:.1f}%` complete)",
        "",
        "🥇 **CONTRIBUTION SCOREBOARD**"
    ]
    
    for user in leaderboard:
        share = (user['completed_tasks'] / total_completed * 100) if total_completed > 0 else 0
        username_str = f"@{user['username']}" if user["username"] else user['first_name']
        receipt.append(
            f"👤 *{username_str}*:\n"
            f"  └ Complete share: `{share:.1f}%` ({user['completed_tasks']}/{total_completed} tasks) | score: `{user['reliability_points']} RP`"
        )
        
    receipt.extend([
        "",
        "✅ **VERIFIED TASK COMPLETIONS LOG**"
    ])
    
    for t in completed_tasks:
        assignee_name = t["assignee_username"] or t["assignee_first_name"]
        assignee = f"@{assignee_name}" if t["assignee_username"] else assignee_name
        receipt.append(f"• [x] \"{t['description']}\" — Done by *{assignee}*")
        
    open_tasks = [t for t in tasks if t["status"] != "completed"]
    if open_tasks:
        receipt.extend([
            "",
            "⏳ **IN-PROGRESS OR OPEN ITEMS**"
        ])
        for t in open_tasks:
            assignee = "Unassigned"
            if t["assigned_to"]:
                assignee_name = t["assignee_username"] or t["assignee_first_name"]
                assignee = f"@{assignee_name}" if t["assignee_username"] else assignee_name
            receipt.append(f"• [ ] \"{t['description']}\" — Assigned: *{assignee}*")
            
    receipt.extend([
        "═" * 30,
        "🔒 *Signature: SECURE_SYNCUP_VALIDATED_RECEIPT*"
    ])
    await update.message.reply_text("\n".join(receipt), parse_mode="Markdown")
