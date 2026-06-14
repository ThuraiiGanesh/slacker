# SyncUp AI (Gradeline AI) 🤖🤝📊

SyncUp AI (formerly Gradeline AI) is a smart chat assistant and companion web dashboard designed to resolve student group project friction (ghosting, accountability, and rubric tracking) right inside existing group chats. 

It parses assignment briefs, manages tasks via chat commands, logs anonymous nudges to resolve peer friction, monitors stress levels (vibe check), generates standup summaries, and exports verified contribution receipts for professors.

---

## 🚀 5-Minute Setup Instructions

### 1. Prerequisites
Ensure you have **Python 3.10+** installed on your system.

### 2. Install Dependencies
Open your terminal inside the project directory (`hackton/`) and run:
```bash
pip install -r requirements.txt
```

### 3. Create a Telegram Bot
1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Send `/newbot` and follow the instructions to choose a name and username for your bot.
3. Copy the **HTTP API Token** provided by BotFather.
4. Add your bot to your student group chat. Make sure it has permissions to read messages.

### 4. Configure Environment Variables
Set the following environment variables.

**On Windows (PowerShell):**
```powershell
$env:TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
$env:GEMINI_API_KEY="your_gemini_api_key"
```

**On Linux/macOS:**
```bash
export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
export GEMINI_API_KEY="your_gemini_api_key"
```

*Note: If `TELEGRAM_BOT_TOKEN` is not provided, the server will launch in **Simulation Mode**, allowing you to demo all features via the web dashboard directly.*

### 5. Launch the Application
Run the orchestrator:
```bash
python main.py
```
This single command launches the **Telegram Bot long-polling updater**, the **background accountability checker**, and the **FastAPI web server** on `http://localhost:8000`.

---

## 🎮 How to Demo & Use

### Step 1: Initialize the Group
Add your bot to a group chat and send a message (e.g. "Hi team"). The bot will automatically register the group, the members, and initialize the database.

### Step 2: Open the Dashboard
Open [http://localhost:8000](http://localhost:8000) in your browser. Select your active group from the dropdown in the top-right corner. You will immediately see the custom dark-mode bento dashboard!

### Step 3: Analyze a Rubric
1. **Option A (Web):** In the dashboard's "AI Rubric Task Parser" card, paste a brief/syllabus text and click **Extract Deliverables**. Edit the extracted tasks inline, and click **Sync & Broadcast**.
2. **Option B (Telegram):** Send `/analyze [rubric text]` in your group chat. Or reply to a message containing the rubric with `/analyze`.
*The bot will parse the deliverables using Gemini 1.5 Flash and register them as task items in the database.*

### Step 4: Manage Tasks
* In chat, type `/tasks` to see deliverables. Click the inline buttons (or type `/claim [task_id]`) to claim a task.
* Type `/complete [task_id]` in chat, or click **Complete** next to a task on the web dashboard to mark it done. Assignees receive `+10 Reliability XP`!
* If a teammate is overwhelmed, they can type `/sos [task_id]` to return the task to the open pool and broadcast a request for backup.

### Step 5: Anonymous Nudges (Privacy Safe)
1. Send a private message to the bot on Telegram: `/nudge [task_id]`.
2. The bot logs the nudge anonymously in the database (exposing it on the dashboard timeline) and posts a polite reminder in the group chat: 
   *"Hi @username, a teammate asked me to check in on Task #2... Let the team know if you need help!"*

### Step 6: Vibe check and Standup
* **Vibe Check:** The bot passively logs group text and monitors stress. If terms like *"lazy"*, *"carrying the team"*, or *"not doing anything"* are detected, the bot intercepts with a gentle message. The dashboard's "Group Vibe Index" orb will glow red (Stressed), amber, or green (Active) accordingly.
* **Standup:** In chat, type `/standup` or click **Regenerate** on the dashboard. The bot reads recent messages and generates a 3-bullet-point summary using Gemini.
* **Receipt:** Navigate to the **Receipt Export** tab on the dashboard to copy a Markdown receipt of completed work to share with course professors.
