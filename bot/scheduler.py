import asyncio
import logging
from datetime import datetime, timedelta
import sqlite3

from database import models
from bot.handlers import get_username_or_name

logger = logging.getLogger(__name__)

# To prevent spamming the group with the same auto-nudge multiple times on the same day
# Key format: (task_id, date_string_of_today)
notified_cache = set()

async def check_due_deadlines(application):
    """
    Checks for tasks due within the next 24 hours and pings their assignees in the respective group.
    """
    conn = models.get_db_connection()
    cursor = conn.cursor()
    
    # Query all active claimed tasks
    cursor.execute(
        """SELECT t.*, u.username as assignee_username, u.first_name as assignee_first_name 
           FROM tasks t 
           JOIN users u ON t.assigned_to = u.id 
           WHERE t.status = 'claimed'"""
    )
    claimed_tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    
    for task in claimed_tasks:
        due_str = task["due_date"]
        if not due_str:
            continue
            
        due_date = None
        # Try parsing common formats
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
            try:
                due_date = datetime.strptime(due_str, fmt)
                break
            except ValueError:
                continue
                
        # If not parseable as date, skip (e.g. "Week 2")
        if not due_date:
            continue
            
        time_left = due_date - now
        
        # Check if due within next 24 hours (and is not already past due)
        if timedelta(seconds=0) < time_left <= timedelta(hours=24):
            cache_key = (task["id"], today_str)
            if cache_key in notified_cache:
                continue
                
            # Trigger notification
            assignee_name = task["assignee_username"] or task["assignee_first_name"]
            assignee = f"@{assignee_name}" if task["assignee_username"] else assignee_name
            
            reminder_text = (
                f"⏰ *Automated Task Deadline Alert!* \n"
                f"Hey {assignee}, this is a system reminder that *Task {task['id']}*:\n"
                f"_\"{task['description']}\"_ \n"
                f"is due in less than 24 hours (*{due_str}*)!\n\n"
                f"Please update the team on your progress or type `/complete {task['id']}` if done. "
                f"If you're blocked or need backup, type `/sos {task['id']}`! 🤝"
            )
            
            try:
                await application.bot.send_message(
                    chat_id=task["group_id"],
                    text=reminder_text,
                    parse_mode="Markdown"
                )
                notified_cache.add(cache_key)
                logger.info(f"Sent auto-deadline nudge for task {task['id']} to {assignee}")
            except Exception as e:
                logger.error(f"Failed to send automated nudge for task {task['id']}: {e}")

# To prevent spamming inactivity alerts multiple times on the same day
# Key format: (group_id, user_id, date_string_of_today)
inactivity_notified_cache = set()

async def check_inactivity_and_alert(application):
    """
    Checks if group members have been inactive for 3 days or more,
    and sends a friendly accountability ping to the group.
    """
    # Get all groups
    groups = models.get_all_groups()
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    
    for g in groups:
        group_id = g["id"]
        # Retrieve inactive users
        inactive_users = models.get_inactive_users_for_group(group_id, inactive_days=3.0)
        
        for user in inactive_users:
            user_id = user["id"]
            cache_key = (group_id, user_id, today_str)
            if cache_key in inactivity_notified_cache:
                continue
                
            username_str = f"@{user['username']}" if user["username"] else user["first_name"]
            
            alert_text = (
                f"🤖 *Active Group Chat Sync Check-In!*\n"
                f"Hey {username_str}, we haven't seen any activity from you in this group chat "
                f"or any completed tasks in the last 3 days! ⏳\n\n"
                f"Please let the team know if you're doing alright, or if you need help "
                f"rebalancing tasks! We are here to support each other! 🤝"
            )
            
            try:
                await application.bot.send_message(
                    chat_id=group_id,
                    text=alert_text,
                    parse_mode="Markdown"
                )
                inactivity_notified_cache.add(cache_key)
                logger.info(f"Sent inactivity alert for user {user_id} in group {group_id}")
            except Exception as e:
                logger.error(f"Failed to send inactivity alert for user {user_id}: {e}")

async def start_accountability_loop(application, interval_seconds: int = 3600):
    """
    Recurring background task runner that sleeps for interval_seconds and executes check_due_deadlines.
    """
    logger.info("Accountability loop scheduler started successfully.")
    # Short wait on startup to allow bot connection to fully initialize
    await asyncio.sleep(10)
    
    while True:
        try:
            await check_due_deadlines(application)
        except Exception as e:
            logger.error(f"Error in check_due_deadlines scheduler: {e}")
            
        try:
            await check_inactivity_and_alert(application)
        except Exception as e:
            logger.error(f"Error in check_inactivity_and_alert scheduler: {e}")
            
        await asyncio.sleep(interval_seconds)

