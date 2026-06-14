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
        return [
            {"description": "Deliverable 1 (Extract failed, verify rubric)", "due_date": "Check rubric"},
            {"description": "Deliverable 2 (Extract failed, verify rubric)", "due_date": "Check rubric"}
        ]

def generate_standup(messages: list) -> str:
    """
    Summarizes the last chat messages into a 3-bullet standup summary using Gemini 1.5 Flash.
    """
    if not messages:
        return "No recent messages found to summarize."
        
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

def parse_natural_language_intent(text: str) -> dict:
    """
    Parses conversational user inputs into task management intents using Gemini 2.0 Flash.
    Returns a dict: {'intent': '...', 'task_id': int or None}
    """
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
        
    return {
        "overall_status": "Audit Failed",
        "overall_guidance": "Could not contact Gemini AI auditor. Please verify connection and try again.",
        "deliverables_audit": [{"task_id": t.get("id"), "description": t.get("description"), "status": "unchecked", "feedback": "Auditor offline"} for t in tasks]
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
        return "Oopsie! 🧸 I'm having trouble connecting to my AI brain right now. Can we try chatting again in a moment? 🎀✨"


