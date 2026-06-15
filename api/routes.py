import random
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import List, Optional

from database import models
from bot import ai_helpers

router = APIRouter()

# Global reference to Telegram application to allow sending messages from API requests
telegram_app = None

# --- Schemas ---

class RubricRequest(BaseModel):
    text: str

class TaskItem(BaseModel):
    description: str
    due_date: Optional[str] = None
    blocked_by: Optional[int] = None

class SyncTasksRequest(BaseModel):
    tasks: List[TaskItem]

class TaskCreateRequest(BaseModel):
    description: str
    due_date: Optional[str] = None
    assigned_to: Optional[int] = None
    blocked_by: Optional[int] = None

class SendOtpRequest(BaseModel):
    username: str

class VerifyOtpRequest(BaseModel):
    username: str
    otp_code: str

class PeerReviewRequest(BaseModel):
    reviewee_id: int
    rating: int
    feedback: Optional[str] = ""

class DraftAuditRequest(BaseModel):
    draft_text: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []



# --- Security Dependencies ---

def get_current_user(authorization: Optional[str] = Header(None)):
    """Verifies session token passed as Bearer token in Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication token missing or invalid.")
    token = authorization.split("Bearer ")[1].strip()
    session = models.get_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired or invalid. Please log in again.")
    return session

def verify_group_membership(group_id: int, user_id: int):
    """Verifies that the logged-in user belongs to the requested group."""
    members = models.get_group_members(group_id)
    if not any(m["id"] == user_id for m in members):
        raise HTTPException(status_code=403, detail="You do not have access to this group project.")

# --- Authentication Endpoints ---

@router.post("/auth/send-otp")
async def send_otp(request: SendOtpRequest):
    username = request.username.strip()
    if username.startswith("@"):
        username = username[1:]
    
    if not username:
        raise HTTPException(status_code=400, detail="Username cannot be empty.")
        
    user = models.get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=404, 
            detail="User not registered in Gradeline database. Please interact with the bot in your group chat or private DM first!"
        )
        
    # Generate 6-digit random OTP code
    otp_code = f"{random.randint(100000, 999999)}"
    
    # Save OTP to database
    models.create_otp(username, user["id"], otp_code)
    
    # Try sending via Telegram bot
    if telegram_app:
        try:
            telegram_text = (
                f"🔑 *Gradeline SyncUp Login Code*\n\n"
                f"Your 2FA One-Time Password is: `{otp_code}`\n"
                f"This code will expire in 5 minutes. Do not share it with others! 🛡️"
            )
            await telegram_app.bot.send_message(
                chat_id=user["id"],
                text=telegram_text,
                parse_mode="Markdown"
            )
        except Exception as e:
            # Typically fails if user has not started the bot privately
            raise HTTPException(
                status_code=400,
                detail=f"Unable to send message on Telegram. Please open a private chat with our bot @{telegram_app.bot.username} and click Start first, then try again!"
            )
    else:
        # Simulation mode fallback for testing
        print(f"[SIMULATION] OTP code for @{username} (ID: {user['id']}) is {otp_code}")
        return {
            "status": "success",
            "message": "OTP code sent successfully (Simulation Mode)!",
            "simulation_otp": otp_code
        }
        
    return {"status": "success", "message": "OTP code sent successfully via Telegram!"}

@router.post("/auth/verify-otp")
def verify_otp_endpoint(request: VerifyOtpRequest):
    username = request.username.strip()
    if username.startswith("@"):
        username = username[1:]
        
    # If in simulation mode, allow master bypass '123456'
    if telegram_app is None and request.otp_code.strip() == "123456":
        user = models.get_user_by_username(username)
    else:
        user = models.verify_otp(username, request.otp_code.strip())
        
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP code.")
        
    # Generate user session
    session_token = models.create_session(user["id"], user["username"], user["first_name"])
    
    return {
        "status": "success",
        "session_token": session_token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "first_name": user["first_name"]
        }
    }

@router.post("/auth/logout")
def logout(authorization: Optional[str] = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ")[1].strip()
        models.delete_session(token)
    return {"status": "success"}

@router.get("/auth/me")
def get_me(user = Depends(get_current_user)):
    return user

@router.get("/bot-info")
def get_bot_info():
    if telegram_app and telegram_app.bot:
        return {"username": telegram_app.bot.username}
    return {"username": "gradeline_syncup_bot"}

# --- Group & Task Endpoints (Secured) ---

@router.get("/groups")
def get_groups(user = Depends(get_current_user)):
    """Returns list of all registered groups that the current user belongs to."""
    return models.get_groups_for_user(user["user_id"])

@router.get("/groups/{group_id}/tasks")
def get_tasks(group_id: int, user = Depends(get_current_user)):
    """Returns all tasks for a group if user is a member."""
    verify_group_membership(group_id, user["user_id"])
    return models.get_tasks_for_group(group_id)

@router.get("/groups/{group_id}/stats")
def get_stats(group_id: int, user = Depends(get_current_user)):
    """Returns leaderboard and task completion stats if user is a member."""
    verify_group_membership(group_id, user["user_id"])
    return models.get_group_stats(group_id)

@router.get("/groups/{group_id}/nudges")
def get_nudges(group_id: int, user = Depends(get_current_user)):
    """Returns anonymous nudge log if user is a member."""
    verify_group_membership(group_id, user["user_id"])
    return models.get_nudges_for_group(group_id)

@router.get("/groups/{group_id}/standup")
def get_standup(group_id: int, user = Depends(get_current_user)):
    """Generates an AI standup summary using Gemini based on recent messages if user is a member."""
    verify_group_membership(group_id, user["user_id"])
    messages = models.get_recent_messages(group_id, limit=60)
    if not messages:
        return {"summary": "No recent chat messages found. Chat in your Telegram group first!"}
        
    summary = ai_helpers.generate_standup(messages)
    return {"summary": summary}

@router.post("/analyze-rubric")
def analyze_rubric_api(request: RubricRequest, user = Depends(get_current_user)):
    """Call Gemini to parse raw rubric text and return raw list of deliverables (no DB saving)."""
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Rubric text cannot be empty.")
        
    parsed_tasks = ai_helpers.analyze_rubric(request.text)
    return {"tasks": parsed_tasks}

@router.post("/groups/{group_id}/sync-tasks")
async def sync_tasks(group_id: int, request: SyncTasksRequest, user = Depends(get_current_user)):
    """Saves a batch of tasks to the database and announces them to the Telegram group."""
    verify_group_membership(group_id, user["user_id"])
    if not request.tasks:
        raise HTTPException(status_code=400, detail="Task list cannot be empty.")
        
    added_tasks = []
    announcement_lines = ["📋 *New Deliverables Added from Dashboard:*"]
    
    for task in request.tasks:
        desc = task.description.strip()
        due = task.due_date.strip() if task.due_date else ""
        blocked = task.blocked_by
        if desc:
            task_id = models.create_task(group_id, desc, due, blocked_by=blocked)
            added_tasks.append({"id": task_id, "description": desc, "due_date": due, "blocked_by": blocked})
            due_suffix = f" (Due: {due})" if due else ""
            blocked_suffix = f" (Blocked by Task {blocked})" if blocked else ""
            announcement_lines.append(f"{task_id}. **{desc}**{due_suffix}{blocked_suffix} — `/claim {task_id}`")
            
    announcement_lines.append("\n👉 Click `/tasks` or use `/claim [task_id]` in this chat to claim them!")
    
    # Broadcast to Telegram group if application reference is active
    if telegram_app:
        try:
            await telegram_app.bot.send_message(
                chat_id=group_id,
                text="\n".join(announcement_lines),
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Failed to broadcast API sync message to Telegram: {e}")
            
    return {"status": "success", "tasks": added_tasks}

@router.post("/groups/{group_id}/tasks")
async def add_single_task(group_id: int, request: TaskCreateRequest, user = Depends(get_current_user)):
    """Creates a single task manually from the web UI and announces it in chat."""
    verify_group_membership(group_id, user["user_id"])
    if not request.description.strip():
        raise HTTPException(status_code=400, detail="Task description cannot be empty.")
        
    task_id = models.create_task(group_id, request.description, request.due_date, request.assigned_to, request.blocked_by)
    task_details = models.get_task(task_id)
    
    # Broadcast
    if telegram_app:
        due_suffix = f" (Due: {request.due_date})" if request.due_date else ""
        blocked_suffix = f" (Blocked by Task {request.blocked_by})" if request.blocked_by else ""
        announcement = (
            f"📋 *New Task Added from Dashboard:* \n"
            f"Task {task_id}: **{request.description}**{due_suffix}{blocked_suffix}\n\n"
            f"👉 Use `/claim {task_id}` to take it!"
        )
        try:
            await telegram_app.bot.send_message(
                chat_id=group_id,
                text=announcement,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Failed to broadcast single task: {e}")
            
    return task_details

@router.post("/tasks/{task_id}/complete")
async def complete_task_api(task_id: int, user = Depends(get_current_user)):
    """Marks a task as completed via dashboard and pings the group."""
    task = models.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
        
    verify_group_membership(task["group_id"], user["user_id"])
    
    if models.is_task_blocked(task_id):
        raise HTTPException(status_code=400, detail="This task is blocked by an uncompleted blocker task. Please complete the blocker first!")
        
    success = models.complete_task(task_id)
    if success:
        # Refresh details to get assignee name
        task = models.get_task(task_id)
        if telegram_app:
            assignee_name = task["assignee_username"] or task["assignee_first_name"]
            assignee = f"@{assignee_name}" if task["assignee_username"] else assignee_name
            announcement = (
                f"✅ *Task Completed from Dashboard!* \n"
                f"Task {task_id}: *\"{task['description']}\"* has been marked as completed!\n"
                f"🎉 Congrats to {assignee} for earning +10 Reliability Points! 🏆"
            )
            try:
                await telegram_app.bot.send_message(
                    chat_id=task["group_id"],
                    text=announcement,
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Failed to broadcast completion: {e}")
                
            # Check for newly unblocked tasks
            conn = models.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE blocked_by = ?", (task_id,))
            blocked_tasks = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
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
                    await telegram_app.bot.send_message(
                        chat_id=task["group_id"],
                        text=unblock_msg,
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    print(f"Failed to send unblock message: {e}")
                    
        return {"status": "success", "task": task}
    else:
        raise HTTPException(status_code=400, detail="Task could not be completed (already completed or unassigned).")

# --- New Endpoints ---

@router.post("/groups/{group_id}/peer-reviews")
def submit_peer_review_api(group_id: int, request: PeerReviewRequest, user = Depends(get_current_user)):
    """Submits a peer review rating and feedback for a teammate."""
    verify_group_membership(group_id, user["user_id"])
    
    # Verify reviewee belongs to the same group
    members = models.get_group_members(group_id)
    if not any(m["id"] == request.reviewee_id for m in members):
        raise HTTPException(status_code=400, detail="Teammate is not a member of this group.")
        
    if request.reviewee_id == user["user_id"]:
        raise HTTPException(status_code=400, detail="You cannot submit a peer review for yourself.")
        
    if request.rating < 1 or request.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5.")
        
    models.submit_peer_review(group_id, user["user_id"], request.reviewee_id, request.rating, request.feedback.strip())
    return {"status": "success", "message": "Peer review submitted successfully!"}

@router.get("/groups/{group_id}/peer-reviews")
def get_peer_reviews_api(group_id: int, user = Depends(get_current_user)):
    """Retrieves all peer reviews for a group."""
    verify_group_membership(group_id, user["user_id"])
    return models.get_peer_reviews_for_group(group_id)

@router.post("/groups/{group_id}/audit-draft")
def audit_draft_api(group_id: int, request: DraftAuditRequest, user = Depends(get_current_user)):
    """Audits student project draft text against the parsed rubric tasks using Gemini."""
    verify_group_membership(group_id, user["user_id"])
    tasks = models.get_tasks_for_group(group_id)
    if not tasks:
        raise HTTPException(status_code=400, detail="No deliverables checklist exists for this group project. Parse a rubric first!")
    
    audit_report = ai_helpers.audit_project_draft(request.draft_text, tasks)
    return audit_report

@router.get("/groups/{group_id}/health")
def get_group_health(group_id: int, user = Depends(get_current_user)):
    """Checks group activity health and identifies members at risk of ghosting (inactive 3 days)."""
    verify_group_membership(group_id, user["user_id"])
    inactive_users = models.get_inactive_users_for_group(group_id, inactive_days=3)
    all_members = models.get_group_members(group_id)
    active_count = len(all_members) - len(inactive_users)
    
    return {
        "total_members": len(all_members),
        "active_members_count": active_count,
        "inactive_members": inactive_users
    }

@router.post("/chat")
def chat_endpoint(request: ChatRequest):
    """Answers user queries in the persona of the preppy bunny mascot, Syncie."""
    reply = ai_helpers.chat_with_mascot(request.message, request.history)
    return {"reply": reply}


