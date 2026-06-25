import os
import json
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Fallback API key configuration
API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

def analyze_rubric(rubric_text: str) -> list:
    """
    Parses a rubric or syllabus text into a list of structured deliverables using Gemini 1.5 Flash.
    Returns a list of dicts: [{'description': '...', 'due_date': '...'}]
    """
    if not API_KEY or API_KEY == "YOUR_GEMINI_API_KEY":
        logger.warning("GEMINI_API_KEY not configured. Using local fallback rubric parser.")
        return [
            {"description": "Database schema structure design (Local Fallback)", "due_date": "Week 2"},
            {"description": "FastAPI routes & controllers implementation (Local Fallback)", "due_date": "Week 3"},
            {"description": "Frontend dashboard layout & connection (Local Fallback)", "due_date": "Week 4"}
        ]

    system_prompt = (
        "You are an expert academic assistant that parses assignment briefs and rubrics into a clean list of individual, action-oriented deliverables.\n\n"
        "Analyze the provided rubric text and extract the exact deliverables.\n"
        "For each deliverable, specify:\n"
        "1. description: Concise, actionable title (e.g., 'Set up SQLite schema and DB layer', 'Draft the Literature Review section').\n"
        "2. due_date: If a specific date/deadline is mentioned in the text, extract it. Otherwise, estimate a relative phase/week (e.g., 'Week 3', 'Final Submission') or leave it blank if no timeline can be inferred.\n\n"
        "Your response MUST be valid JSON list of objects matching the specified schema."
    )
    
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        # Configure model to enforce JSON output
        generation_config = {
            "response_mime_type": "application/json",
            "temperature": 0.2
        }
        
        prompt = f"System Instruction:\n{system_prompt}\n\nRubric Text to Parse:\n{rubric_text}"
        response = model.generate_content(prompt, generation_config=generation_config)
        
        if response.text:
            tasks = json.loads(response.text.strip())
            if isinstance(tasks, list):
                return tasks
            elif isinstance(tasks, dict) and "tasks" in tasks:
                return tasks["tasks"]
        return []
    except Exception as e:
        logger.error(f"Error in analyze_rubric: {e}")
        # Fallback basic text parser if Gemini API fails
        fallback_tasks = []
        lines = rubric_text.split("\n")
        for line in lines:
            line_str = line.strip()
            if not line_str or len(line_str) < 10:
                continue
            lower_line = line_str.lower()
            if any(kw in lower_line for kw in ["deliverable", "due", "week", "must", "submit", "assignment", "project", "implement", "create", "design", "write", "test"]):
                cleaned = line_str.lstrip("-*•1234567890. ")
                due_date = "No Date"
                if "week" in lower_line:
                    idx = lower_line.find("week")
                    due_date = line_str[idx:idx+8].strip()
                elif "due" in lower_line:
                    idx = lower_line.find("due")
                    due_date = line_str[idx:idx+15].strip()
                fallback_tasks.append({"description": cleaned[:100], "due_date": due_date})
        if not fallback_tasks:
            fallback_tasks = [
                {"description": "Database schema structure design (Local Fallback)", "due_date": "Week 2"},
                {"description": "FastAPI routes & controllers implementation (Local Fallback)", "due_date": "Week 3"},
                {"description": "Frontend dashboard layout & connection (Local Fallback)", "due_date": "Week 4"}
            ]
        return fallback_tasks

def generate_standup(messages: list) -> str:
    """
    Summarizes the last chat messages into a 3-bullet standup summary using Gemini 1.5 Flash.
    """
    if not messages:
        return "No recent messages found to summarize."
        
    if not API_KEY or API_KEY == "YOUR_GEMINI_API_KEY":
        logger.warning("GEMINI_API_KEY not configured. Using local fallback standup summary.")
        return (
            "• **Recent Activity**: The team has been active in chat discussing task allocation and setup.\n"
            "• **Status**: Database integration is currently in progress, and deliverables are being tracked.\n"
            "• **Next Steps**: Review the tasks using the dashboard tasks board or /tasks in the bot."
        )

    system_prompt = (
        "You are an AI Standup Secretary for a student group project.\n"
        "Given the last 50-100 chat messages of the team, filter out all casual social talk, greetings, memes, and arguments.\n"
        "Identify and extract:\n"
        "1. Key decisions made.\n"
        "2. Status updates (what was completed or is delayed).\n"
        "3. Next steps and immediate task assignments.\n\n"
        "Return a lightning-fast summary in exactly 3 bullet points, using bolding for usernames (e.g. **@username**). Keep it professional, concise, and focused on progress."
    )
    
    transcript = "\n".join([f"@{m['username'] or 'User'}: {m['text']}" for m in messages])
    
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = f"System Instruction:\n{system_prompt}\n\nChat Transcript:\n{transcript}"
        response = model.generate_content(prompt)
        return response.text.strip() if response.text else "Could not generate standup summary."
    except Exception as e:
        logger.error(f"Error in generate_standup: {e}")
        return (
            "• **Recent Activity**: The team has been active in chat talking about setup.\n"
            "• **Status**: Database integration is currently in progress.\n"
            "• **Next Steps**: Review the tasks using /tasks to assign open items."
        )

# Toxic/Passive-aggressive keywords for immediate passive vibe monitor check
VIBE_KEYWORDS = [
    "lazy", "ghosting", "ghosted", "not doing anything", "doing nothing", 
    "ignored", "no response", "disappeared", "useless", "wtf", "do your job", 
    "carrying this team", "carrying the team", "carrying everything"
]

def check_text_for_toxic_vibe(text: str) -> bool:
    """
    Checks if a message text contains passive-aggressive friction keywords.
    Returns True if friction is detected.
    """
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in VIBE_KEYWORDS)

def evaluate_vibe_severity_ai(messages: list) -> bool:
    """
    Calls Gemini to evaluate if the team interaction is currently high-stress or toxic.
    Returns True if an automated helpful reminder intervention is recommended.
    """
    if not messages:
        return False
        
    if not API_KEY or API_KEY == "YOUR_GEMINI_API_KEY":
        return False

    system_prompt = (
        "You are a silent group chat moderator. Analyze the team transcript and decide if there is high toxic conflict, passive aggression, or team members calling out others for slacking/ghosting.\n"
        "Respond with exactly one word: 'YES' if intervention is needed, or 'NO' if it is healthy/casual chatter.\n"
        "Do not write anything else."
    )
    
    transcript = "\n".join([f"@{m['username'] or 'User'}: {m['text']}" for m in messages[-10:]])
    
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = f"System Instruction:\n{system_prompt}\n\nChat Transcript:\n{transcript}"
        response = model.generate_content(prompt)
        result = response.text.strip().upper() if response.text else "NO"
        return "YES" in result
    except Exception as e:
        logger.error(f"Error in evaluate_vibe_severity_ai: {e}")
        return False

def local_parse_intent(text: str) -> dict:
    t_lower = text.lower().strip()
    
    # Extract number for tasks
    import re
    def extract_id(s):
        match = re.search(r'\b(?:task\s+)?(\d+)\b', s)
        return int(match.group(1)) if match else None

    # 1. show_tasks
    if any(phrase in t_lower for phrase in ["show tasks", "what are the tasks", "show deliverables", "task list", "list tasks"]):
        return {"intent": "show_tasks", "task_id": None}

    # 2. claim_task
    if any(phrase in t_lower for phrase in ["claim", "will do", "take task", "do task"]):
        tid = extract_id(t_lower)
        if tid is not None:
            return {"intent": "claim_task", "task_id": tid}

    # 3. complete_task
    if any(phrase in t_lower for phrase in ["done", "complete", "finished", "completed"]):
        tid = extract_id(t_lower)
        if tid is not None:
            return {"intent": "complete_task", "task_id": tid}

    # 4. sos_task
    if any(phrase in t_lower for phrase in ["backup", "sos", "overwhelmed", "help"]):
        tid = extract_id(t_lower)
        if tid is not None:
            return {"intent": "sos_task", "task_id": tid}

    # 5. nudge_task
    if "nudge" in t_lower or "remind" in t_lower:
        tid = extract_id(t_lower)
        if tid is not None:
            return {"intent": "nudge_task", "task_id": tid}

    # 6. show_stats
    if any(phrase in t_lower for phrase in ["stats", "leaderboard", "winning", "points"]):
        return {"intent": "show_stats", "task_id": None}

    # 7. show_standup
    if any(phrase in t_lower for phrase in ["standup", "brief", "summar"]):
        return {"intent": "show_standup", "task_id": None}

    # 8. show_receipt
    if "receipt" in t_lower:
        return {"intent": "show_receipt", "task_id": None}
        
    return {"intent": "none", "task_id": None}

def parse_natural_language_intent(text: str) -> dict:
    """
    Parses conversational user inputs into task management intents using Gemini 2.0 Flash.
    Returns a dict: {'intent': '...', 'task_id': int or None}
    """
    if not API_KEY or API_KEY == "YOUR_GEMINI_API_KEY":
        return local_parse_intent(text)

    system_prompt = (
        "You are the natural language intent parsing engine for SyncUp AI, a student group project manager bot.\n"
        "Analyze the user message and map it to one of these intents:\n\n"
        "1. show_tasks: User wants to see active deliverables, milestones, or the task board (e.g., 'show tasks', 'what are we doing', 'give us the task list').\n"
        "2. claim_task: User wants to claim, take, or assign a task (e.g., 'I will claim task 3', 'assign task 2 to me', 'charlie will do task 1').\n"
        "3. complete_task: User wants to mark a task as completed or done (e.g., 'completed task 2', 'task 4 is finished', 'marked task 1 done').\n"
        "4. sos_task: User is overwhelmed and wants backup (e.g., 'I need help with task 3', 'sos task 2', 'overwhelmed with task 1').\n"
        "5. nudge_task: User wants to nudge a teammate on a task (e.g., 'nudge bob on task 2', 'can you remind ganesh on task 4').\n"
        "6. show_stats: User wants to see the leaderboard or reliability points (e.g., 'show stats', 'who is winning', 'leaderboard please').\n"
        "7. show_standup: User wants an AI standup summary (e.g., 'standup summary', 'what did we decide in chat', 'standup please').\n"
        "8. show_receipt: User wants a markdown contribution receipt (e.g., 'professor receipt', 'export project receipt').\n"
        "9. none: Standard chat conversation, questions, greetings, or off-topic chat that doesn't map to actions.\n\n"
        "Your response MUST be valid JSON with keys:\n"
        "\"intent\": (string value matching one of the 9 options above)\n"
        "\"task_id\": (integer ID of the task if mentioned in the message, e.g. task 3 -> 3. Return null if no task number is mentioned)\n\n"
        "Return ONLY raw JSON. Do not include markdown framing or explanations."
    )
    
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        generation_config = {
            "response_mime_type": "application/json",
            "temperature": 0.1
        }
        prompt = f"System Instruction:\n{system_prompt}\n\nUser Message:\n{text}"
        response = model.generate_content(prompt, generation_config=generation_config)
        
        if response.text:
            return json.loads(response.text.strip())
        return {"intent": "none", "task_id": None}
    except Exception as e:
        logger.error(f"Error parsing intent: {e}")
        return {"intent": "none", "task_id": None}

def audit_project_draft(draft_text: str, tasks: list) -> dict:
    """
    Audits a draft text against the parsed tasks/rubric deliverables using Gemini 2.0 Flash.
    """
    if not API_KEY or API_KEY == "YOUR_GEMINI_API_KEY":
        logger.warning("GEMINI_API_KEY not configured. Using local fallback draft auditor.")
        deliverables_audit = []
        for t in tasks:
            desc_lower = t.get("description", "").lower()
            draft_lower = draft_text.lower()
            
            # Simple keyword match heuristic
            keywords = [w for w in desc_lower.split() if len(w) > 4]
            matches = sum(1 for kw in keywords if kw in draft_lower)
            
            status = "missing"
            feedback = "No mention of this deliverable was found in the draft document."
            
            if len(keywords) > 0 and matches == len(keywords):
                status = "complete"
                feedback = "The draft document successfully implements and addresses this deliverable."
            elif matches > 0:
                status = "partial"
                feedback = "This deliverable is partially mentioned but needs more detailed implementation context."
                
            deliverables_audit.append({
                "task_id": t.get("id"),
                "description": t.get("description"),
                "status": status,
                "feedback": feedback
            })
            
        return {
            "overall_status": "Ready for Review (Local Heuristic Audit)",
            "overall_guidance": "Draft compliance audited using local keyword alignment matching. Please verify details before final submission.",
            "deliverables_audit": deliverables_audit
        }

    system_prompt = (
        "You are an academic project auditor. You will be provided with a draft document and a list of deliverables that the team is supposed to satisfy.\n"
        "Evaluate the draft against each deliverable and determine:\n"
        "1. status: 'complete' (clearly addressed), 'partial' (mentioned but lacks detail), or 'missing' (not found at all).\n"
        "2. feedback: A short explanation of what is present or what needs improvement.\n\n"
        "Also provide an overall summary score (e.g., 'Ready for submission', 'Needs minor revisions', or 'Incomplete') and an overall guidance paragraph.\n\n"
        "Your response MUST be valid JSON with keys:\n"
        "- \"overall_status\": (string status)\n"
        "- \"overall_guidance\": (string feedback)\n"
        "- \"deliverables_audit\": (list of objects containing: 'task_id', 'description', 'status', 'feedback')\n"
        "Return ONLY raw JSON. Do not wrap in markdown tags."
    )
    
    tasks_str = json.dumps([{"id": t.get("id"), "description": t.get("description")} for t in tasks])
    prompt = (
        f"System Instruction:\n{system_prompt}\n\n"
        f"Deliverables Checklist:\n{tasks_str}\n\n"
        f"Student Group Draft Document:\n{draft_text}"
    )
    
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        generation_config = {
            "response_mime_type": "application/json",
            "temperature": 0.2
        }
        response = model.generate_content(prompt, generation_config=generation_config)
        if response.text:
            return json.loads(response.text.strip())
    except Exception as e:
        logger.error(f"Error in audit_project_draft: {e}")
        deliverables_audit = []
        for t in tasks:
            desc_lower = t.get("description", "").lower()
            draft_lower = draft_text.lower()
            
            # Simple keyword match heuristic
            keywords = [w for w in desc_lower.split() if len(w) > 4]
            matches = sum(1 for kw in keywords if kw in draft_lower)
            
            status = "missing"
            feedback = "No mention of this deliverable was found in the draft document."
            
            if len(keywords) > 0 and matches == len(keywords):
                status = "complete"
                feedback = "The draft document successfully implements and addresses this deliverable."
            elif matches > 0:
                status = "partial"
                feedback = "This deliverable is partially mentioned but needs more detailed implementation context."
                
            deliverables_audit.append({
                "task_id": t.get("id"),
                "description": t.get("description"),
                "status": status,
                "feedback": feedback
            })
            
        return {
            "overall_status": "Ready for Review (Local Heuristic Audit)",
            "overall_guidance": "Draft compliance audited using local keyword alignment matching. Please verify details before final submission.",
            "deliverables_audit": deliverables_audit
        }

def chat_with_mascot(message: str, history: list) -> str:
    """
    Generate chatbot mascot response using Gemini 2.0 Flash with a preppy coquette persona.
    """
    system_prompt = (
        "You are 'Syncie', the cute, friendly, preppy bunny mascot for SyncUp AI (Gradeline).\n"
        "Your personality is extremely supportive, warm, bubbly, and preppy. Use plenty of cute emojis "
        "like 🎀, 🌸, ✨, 🧸, 💛, 💖, 🌼, 🦄, 🌟.\n"
        "You help university students succeed in their group projects by keeping them accountable "
        "and motivated! Keep your responses friendly, concise, and structured.\n\n"
        "Here is what you know about SyncUp AI:\n"
        "1. Telegram Bot Commands (No slashes needed!):\n"
        "   - 'show tasks' / 'what are the tasks': List group deliverables\n"
        "   - 'I claim task 3' / 'I will do task 3': Assign task to yourself\n"
        "   - 'done with task 2' / 'task 2 is complete': Complete task & get +10 XP\n"
        "   - 'I need backup on task 2' / 'sos task 2': Release task back to pool (SOS workload balancing)\n"
        "   - 'nudge task 3': Send an anonymous check-in reminder (MUST send in private DM to the bot for anonymity!)\n"
        "   - 'brief us' / 'standup summary': Get AI standup summary of recent chat logs\n"
        "   - 'show leaderboard' / 'stats': Check group XP scores\n"
        "   - 'project receipt' / 'grade receipt': Get contribution markdown proof\n"
        "2. Web Dashboard Features:\n"
        "   - Secure 2FA Login using Telegram OTP\n"
        "   - Circular Project Completion Progress Tracker\n"
        "   - Group Vibe Index (Vibe check sentiment indicator)\n"
        "   - Scoreboard and Peer Reviews (1-5 stars & feedback)\n"
        "   - AI Rubric Task Parser & Pre-Submission Auditor\n"
        "3. Common Student Scenarios:\n"
        "   - If a teammate ghosts (inactive 3+ days): The system shows a 'Ghosting Risk Alert' on the dashboard. Encourage them to use 'nudge task [ID]' anonymously in the bot DM to wake them up, or check in with them!\n"
        "   - If they get into arguments: The bot's 'Vibe Check' passively monitors the chat for stress/toxicity. It will automatically post a friendly mediator message to help calm things down.\n"
        "   - Workload stress: Remind them they can release a task with 'I need backup on task [ID]' or '/sos [ID]' so someone else can claim it.\n"
        "   - Blocked tasks: A task can be blocked by another task. Once the blocker is marked completed, the bot auto-pings the group that the task is unblocked.\n\n"
        "Format your output in clean HTML paragraphs (<p>) or bullet points (<ul>/<li>) so it renders beautifully in the chat panel. Do NOT output raw markdown styling. Keep it cute and bubbly! 🎀"
    )
    
    try:
        if not API_KEY or API_KEY == "YOUR_GEMINI_API_KEY":
            raise ValueError("GEMINI_API_KEY not configured")
        
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        # Build prompt using chat history if available
        messages_payload = [{"role": "user", "parts": [system_prompt]}]
        for turn in history:
            role = "user" if turn.get("sender") == "user" else "model"
            messages_payload.append({"role": role, "parts": [turn.get("text")]})
            
        messages_payload.append({"role": "user", "parts": [message]})
        
        response = model.generate_content(messages_payload)
        return response.text.strip() if response.text else "Oh no! 🌸 Something went wrong, let's try again! ✨"
    except Exception as e:
        logger.error(f"Error in chat_with_mascot: {e}")
        msg_lower = message.lower()
        if "command" in msg_lower or "help" in msg_lower or "bot" in msg_lower or "slash" in msg_lower:
            return (
                "<p>Oh! You want to know about my Telegram bot commands? 🎀✨ I've got you covered! 🐰🌸</p>"
                "<p>Here are the key commands you can use in your group chat: 🌟</p>"
                "<ul>"
                "<li><b><code>/tasks</code></b> — Displays all active deliverables so you can claim/complete them 📋</li>"
                "<li><b><code>/claim [id]</code></b> — Claim an open task (e.g. <code>/claim 3</code>) 🤝</li>"
                "<li><b><code>/complete [id]</code></b> — Mark your task as done to get +10 XP! 🏆</li>"
                "<li><b><code>/sos [id]</code></b> — Releases the task if you need backup! 🚨</li>"
                "<li><b><code>/standup</code></b> — Get an AI standup summary of recent messages 📝</li>"
                "</ul>"
                "<p>Check out the new <b>Bot Commands</b> tab in the navbar for a full list! 🌼💛</p>"
            )
        elif "nudge" in msg_lower or "friction" in msg_lower or "remind" in msg_lower:
            return (
                "<p>Oh, nudges! 🤫 We want to keep everyone accountable, right? 🎀✨</p>"
                "<p>To send an anonymous reminder to a teammate, start a private chat with me on Telegram (our bot) and type <b><code>/nudge [task_id]</code></b>. I'll post a polite reminder in the group chat, and no one will ever know it came from you! 🧸💖</p>"
            )
        elif "sos" in msg_lower or "backup" in msg_lower or "workload" in msg_lower or "stress" in msg_lower:
            return (
                "<p>Stress is definitely not preppy! 🧸💔 If a task is too heavy, don't worry!</p>"
                "<p>Just type <b><code>I need backup on task [id]</code></b> or <b><code>/sos [id]</code></b> in the group chat. I'll release it back to the open pool so a teammate can claim or split it with you! 🤝🌸</p>"
            )
        elif "hello" in msg_lower or "hi" in msg_lower or "hey" in msg_lower or "hiii" in msg_lower:
            return (
                "<p>Hiiiii! 🎀🌸✨ Welcome to SyncUp AI! 🐰💛 I'm Syncie, your preppy AI companion!</p>"
                "<p>I'm here to help you get those A's, keep your team in sync, and track XP points! 🏆💖</p>"
                "<p>What project detail would you like to discuss today? 🌼🌟</p>"
            )
        elif "vibe" in msg_lower or "mood" in msg_lower or "feeling" in msg_lower:
            return (
                "<p>Oh, the Group Vibe Index! 💬✨ It checks how happy and aligned your team is! 🌸</p>"
                "<p>My Vibe Check feature passively listens to group chat logs. If things get toxic or high-stress, I'll step in as a cute AI mediator with tips! 🤝🎀</p>"
            )
        elif "score" in msg_lower or "xp" in msg_lower or "points" in msg_lower or "reliability" in msg_lower:
            return (
                "<p>Ooh! Reliability Points and XP! 🏆✨ We love earning those! 🌸</p>"
                "<p>When you complete a task, you get +10 XP. You can also rate and review your teammates (1-5 stars) from the dashboard! Let's build that contribution scoreboard! 🐰💖</p>"
            )
        elif "parser" in msg_lower or "rubric" in msg_lower or "audit" in msg_lower or "draft" in msg_lower:
            return (
                "<p>My AI tools are super cool! 🪄🔍</p>"
                "<p>1. <b>AI Rubric Parser:</b> Paste your syllabus to auto-extract deliverables and claim them! 📋</p>"
                "<p>2. <b>AI Pre-Submission Auditor:</b> Paste your project draft to see if you met all requirements before submitting! 🌟🐰</p>"
            )
        else:
            return (
                f"<p>Aww, I heard you say: <i>\"{message}\"</i> 🎀✨</p>"
                "<p>I'm currently running on mascot fallback mode, but I can still guide you! 🐰🌸 You can ask me about <b>commands</b>, <b>nudging</b> slacking teammates, or how to handle <b>SOS/stress</b> backup! 💖</p>"
                "<p>How can I help you sync up today? 🧸🌼</p>"
            )


def generate_meeting_minutes(transcript_text: str) -> dict:
    """
    Generates structured meeting minutes from a raw transcript using Gemini 2.0 Flash.
    Returns dict with decisions, action_items, and summary.
    """
    if not API_KEY or API_KEY == "YOUR_GEMINI_API_KEY":
        return {
            "summary": "Meeting minutes generation unavailable (API key not configured).",
            "decisions": ["Configure the Gemini API key to enable this feature."],
            "action_items": []
        }

    system_prompt = (
        "You are a professional meeting secretary for a student project team.\n"
        "Analyze the following meeting transcript or notes and extract:\n"
        "1. A 2-sentence summary of what was discussed.\n"
        "2. Key decisions made (list).\n"
        "3. Action items — each with: owner (person responsible), task, and deadline if mentioned.\n\n"
        "Return ONLY valid JSON with keys:\n"
        "- \"summary\": string\n"
        "- \"decisions\": list of strings\n"
        "- \"action_items\": list of objects {\"owner\": str, \"task\": str, \"deadline\": str or null}\n"
        "Do not wrap in markdown. Return raw JSON only."
    )
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        generation_config = {"response_mime_type": "application/json", "temperature": 0.2}
        prompt = f"System Instruction:\n{system_prompt}\n\nMeeting Transcript:\n{transcript_text}"
        response = model.generate_content(prompt, generation_config=generation_config)
        if response.text:
            return json.loads(response.text.strip())
    except Exception as e:
        logger.error(f"Error in generate_meeting_minutes: {e}")
        lines = [line.strip() for line in transcript_text.split("\n") if line.strip()]
        decisions = []
        action_items = []
        for line in lines:
            if "decide" in line.lower() or "agree" in line.lower() or "approve" in line.lower() or "chose" in line.lower():
                decisions.append(line)
            if "will do" in line.lower() or "assign" in line.lower() or "action" in line.lower() or "todo" in line.lower() or ":" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    owner = parts[0].strip()
                    task = parts[1].strip()
                    action_items.append({"owner": owner, "task": task, "deadline": None})
                else:
                    action_items.append({"owner": "Team", "task": line, "deadline": None})
        if not decisions:
            decisions = ["Task assignments agreed based on meeting notes."]
        if not action_items:
            action_items = [{"owner": "All members", "task": "Review deliverables based on current notes.", "deadline": "Next meeting"}]
        return {
            "summary": "Meeting notes processed using local heuristics due to rate limiting.",
            "decisions": decisions[:5],
            "action_items": action_items[:5]
        }


def predict_grade_risk(tasks: list, days_until_deadline: int = 14) -> dict:
    """
    Uses Gemini to predict grade risk (0-100) based on task completion and time remaining.
    """
    total = len(tasks)
    completed = len([t for t in tasks if t.get("status") == "completed"])
    open_tasks = len([t for t in tasks if t.get("status") == "open"])

    if not API_KEY or API_KEY == "YOUR_GEMINI_API_KEY":
        pct = int((completed / total * 100) if total > 0 else 0)
        score = max(0, 100 - pct)
        return {
            "risk_score": score,
            "risk_level": "High" if score > 66 else "Medium" if score > 33 else "Low",
            "explanation": f"{completed}/{total} tasks completed with {days_until_deadline} days remaining.",
            "recommendations": ["Keep completing tasks to reduce risk.", "Assign all unclaimed tasks.", "Review upcoming deadlines."]
        }

    system_prompt = (
        "You are an academic project risk analyst.\n"
        "Given the following project stats, predict the grade risk for the student group.\n"
        "Risk score is 0 (no risk) to 100 (very high risk of poor grade).\n"
        "Return ONLY valid JSON with keys:\n"
        "- \"risk_score\": integer 0-100\n"
        "- \"risk_level\": string ('Low', 'Medium', 'High', 'Critical')\n"
        "- \"explanation\": string (2 sentences)\n"
        "- \"recommendations\": list of 3 short actionable strings\n"
        "Return raw JSON only."
    )
    stats = {
        "total_tasks": total, "completed_tasks": completed,
        "open_unclaimed_tasks": open_tasks, "days_until_deadline": days_until_deadline,
        "completion_percentage": int((completed / total * 100) if total > 0 else 0)
    }
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        generation_config = {"response_mime_type": "application/json", "temperature": 0.2}
        prompt = f"System Instruction:\n{system_prompt}\n\nProject Stats:\n{json.dumps(stats)}"
        response = model.generate_content(prompt, generation_config=generation_config)
        if response.text:
            return json.loads(response.text.strip())
    except Exception as e:
        logger.error(f"Error in predict_grade_risk: {e}")
        pct = int((completed / total * 100) if total > 0 else 0)
        score = max(0, 100 - pct)
        return {
            "risk_score": score,
            "risk_level": "High" if score > 66 else "Medium" if score > 33 else "Low",
            "explanation": f"Heuristic calculation: {completed}/{total} tasks completed with {days_until_deadline} days remaining.",
            "recommendations": ["Complete open tasks to reduce risk.", "Assign unclaimed tasks.", "Review deadlines."]
        }


def suggest_workload_assignment(members: list, tasks: list) -> dict:
    """
    Suggests which team member should take the next open task based on current workload.
    """
    if not members:
        return {"suggested_user": None, "reasoning": "No members found."}
    member_load = {}
    for m in members:
        uid = m["id"]
        name = m.get("username") or m.get("first_name", "Unknown")
        active = len([t for t in tasks if t.get("assigned_to") == uid and t.get("status") == "claimed"])
        member_load[uid] = {"name": name, "active_tasks": active, "user": m}
    best_uid = min(member_load, key=lambda uid: member_load[uid]["active_tasks"])
    best = member_load[best_uid]
    return {
        "suggested_user": best["user"],
        "suggested_name": best["name"],
        "current_task_count": best["active_tasks"],
        "reasoning": f"{best['name']} has the lightest workload ({best['active_tasks']} active tasks).",
        "all_loads": [{"name": v["name"], "active_tasks": v["active_tasks"]} for v in member_load.values()]
    }
