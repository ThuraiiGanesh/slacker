import sqlite3
from datetime import datetime
import os

DB_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gradeline.db")
)

def get_db_connection():
    """Returns a SQLite connection. Creates the database file if it does not exist."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the SQLite database schema if tables do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS groups (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT NOT NULL,
        last_name TEXT,
        reliability_points INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS group_members (
        group_id INTEGER,
        user_id INTEGER,
        PRIMARY KEY (group_id, user_id),
        FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL,
        assigned_to INTEGER,
        description TEXT NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('open', 'claimed', 'completed')),
        due_date TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        blocked_by INTEGER,
        FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
        FOREIGN KEY (assigned_to) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (blocked_by) REFERENCES tasks(id) ON DELETE SET NULL
    );
    """)
    
    # Try adding blocked_by column to tasks table if it is an existing DB
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN blocked_by INTEGER REFERENCES tasks(id) ON DELETE SET NULL;")
    except sqlite3.OperationalError:
        pass

    # Try adding priority column to tasks table
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT 'medium' CHECK (priority IN ('high', 'medium', 'low'));")
    except sqlite3.OperationalError:
        pass

    # Task comments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS task_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        username TEXT,
        text TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS nudges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL,
        task_id INTEGER NOT NULL,
        nudger_id INTEGER NOT NULL,
        nudged_user_id INTEGER NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
        FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        username TEXT,
        text TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS otps (
        username TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        otp_code TEXT NOT NULL,
        expires_at TIMESTAMP NOT NULL
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_sessions (
        session_token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        username TEXT,
        first_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS peer_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL,
        reviewer_id INTEGER NOT NULL,
        reviewee_id INTEGER NOT NULL,
        rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
        feedback TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
        FOREIGN KEY (reviewer_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (reviewee_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)
    
    # --- Auto-Seeding Demo Data ---
    # Seed default/demo users if they do not exist
    demo_users = [
        (2001, 'peer1', 'Charlie', None, 0),
        (2002, 'peer2', 'Delta', None, 5),
        (11111, 'test_hacker', 'Hacker', 'Evil', 20),
        (99999, 'test_ganesh', 'Ganesh', 'Test', 0),
        (6816114271, 'Doggodestroyer', 'Dogggo', 'Destroyer', 0)
    ]
    for uid, uname, fname, lname, pts in demo_users:
        cursor.execute(
            "INSERT OR IGNORE INTO users (id, username, first_name, last_name, reliability_points) VALUES (?, ?, ?, ?, ?)",
            (uid, uname, fname, lname, pts)
        )
        cursor.execute(
            "UPDATE users SET username = ?, first_name = ?, last_name = ? WHERE id = ?",
            (uname, fname, lname, uid)
        )

    # Seed default/demo groups if they do not exist
    demo_groups = [
        (201, 'Test Peer Review Group'),
        (-100999, 'Secret Group Project'),
        (-5426437660, 'blahetst'),
        (-5293581723, 'googoo')
    ]
    for gid, gname in demo_groups:
        cursor.execute(
            "INSERT OR IGNORE INTO groups (id, name) VALUES (?, ?)",
            (gid, gname)
        )

    # Seed group members
    demo_memberships = [
        (201, 2001),
        (201, 2002),
        (-100999, 99999),
        (-100999, 11111),
        (-100999, 6816114271),
        (-5426437660, 6816114271),
        (-5293581723, 6816114271)
    ]
    for gid, uid in demo_memberships:
        cursor.execute(
            "INSERT OR IGNORE INTO group_members (group_id, user_id) VALUES (?, ?)",
            (gid, uid)
        )

    # Seed a couple of default tasks for testing bento layout and deliverables board
    demo_tasks = [
        (1, -100999, 6816114271, 'Database schema structure and SQLite layers (Demo)', 'completed', 'Week 2', None),
        (2, -100999, 99999, 'FastAPI authentication & OTP verification endpoints (Demo)', 'completed', 'Week 3', None),
        (3, -100999, 6816114271, 'Develop interactive web dashboard and YSP capsule navigation (Demo)', 'claimed', 'Week 4', None),
        (4, -100999, None, 'Integration testing and deployment on Railway (Demo)', 'open', 'Week 4', 3),
        (5, 201, 2001, 'Implement draft peer reviews and logging triggers (Demo)', 'completed', 'Week 2', None)
    ]
    for tid, gid, uid, desc, status, due, blocked_by in demo_tasks:
        cursor.execute(
            "INSERT OR IGNORE INTO tasks (id, group_id, assigned_to, description, status, due_date, blocked_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (tid, gid, uid, desc, status, due, blocked_by)
        )

    # Seed sample peer reviews
    demo_reviews = [
        (2, 201, 2001, 2002, 5, 'Excellent work on API integration!'),
        (3, -100999, 99999, 11111, 5, 'Outstanding work coordinating the backend tasks!'),
        (4, -100999, 99999, 6816114271, 5, 'Super helpful with the Telegram bot connection and persistent database paths!'),
        (5, -100999, 6816114271, 99999, 5, 'Amazing job styling the floating capsule headers and view transitions!')
    ]
    for rid, gid, rev_id, reviewee_id, rating, feedback in demo_reviews:
        cursor.execute(
            "INSERT OR IGNORE INTO peer_reviews (id, group_id, reviewer_id, reviewee_id, rating, feedback) VALUES (?, ?, ?, ?, ?, ?)",
            (rid, gid, rev_id, reviewee_id, rating, feedback)
        )
    
    conn.commit()
    conn.close()


# --- Group & User CRUD Operations ---

def save_group(group_id: int, name: str):
    """Registers or updates a group in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO groups (id, name) VALUES (?, ?)",
        (group_id, name)
    )
    conn.commit()
    conn.close()

def save_user(user_id: int, username: str, first_name: str, last_name: str = None):
    """Registers or updates a user in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO users (id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
        (user_id, username, first_name, last_name)
    )
    # If user already exists, update username, first name and last name just in case they changed
    cursor.execute(
        "UPDATE users SET username = ?, first_name = ?, last_name = ? WHERE id = ?",
        (username, first_name, last_name, user_id)
    )
    conn.commit()
    conn.close()

def add_group_member(group_id: int, user_id: int):
    """Adds a user to a group relationship."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO group_members (group_id, user_id) VALUES (?, ?)",
        (group_id, user_id)
    )
    conn.commit()
    conn.close()

def get_group_members(group_id: int):
    """Returns a list of users in a specific group."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT u.* FROM users u 
           JOIN group_members gm ON u.id = gm.user_id 
           WHERE gm.group_id = ?""",
        (group_id,)
    )
    members = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return members

def get_all_groups():
    """Returns all registered groups."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM groups")
    groups = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return groups

# --- Task CRUD Operations ---

def is_task_blocked(task_id: int):
    """Checks if a task is currently blocked by an uncompleted blocker task."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT bt.status FROM tasks t
           JOIN tasks bt ON t.blocked_by = bt.id
           WHERE t.id = ?""",
        (task_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row and row["status"] != "completed":
        return True
    return False

def create_task(group_id: int, description: str, due_date: str = None, assigned_to: int = None, blocked_by: int = None, priority: str = 'medium'):
    """Creates a new task in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    status = "claimed" if assigned_to else "open"
    cursor.execute(
        "INSERT INTO tasks (group_id, description, due_date, assigned_to, status, blocked_by, priority) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (group_id, description, due_date, assigned_to, status, blocked_by, priority)
    )
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id

def get_tasks_for_group(group_id: int):
    """Returns all tasks for a group, detailing who it is assigned to and blocker info."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT t.*, u.username as assignee_username, u.first_name as assignee_first_name,
                  bt.description as blocker_description, bt.status as blocker_status
           FROM tasks t 
           LEFT JOIN users u ON t.assigned_to = u.id 
           LEFT JOIN tasks bt ON t.blocked_by = bt.id
           WHERE t.group_id = ?""",
        (group_id,)
    )
    tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tasks

def get_task(task_id: int):
    """Returns details of a specific task including blocker info."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT t.*, u.username as assignee_username, u.first_name as assignee_first_name,
                  bt.description as blocker_description, bt.status as blocker_status
           FROM tasks t 
           LEFT JOIN users u ON t.assigned_to = u.id 
           LEFT JOIN tasks bt ON t.blocked_by = bt.id
           WHERE t.id = ?""",
        (task_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def claim_task(task_id: int, user_id: int):
    """Assigns an open task to a user, verifying it is not blocked."""
    if is_task_blocked(task_id):
        return False
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tasks SET assigned_to = ?, status = 'claimed' WHERE id = ? AND status = 'open'",
        (user_id, task_id)
    )
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

def release_task(task_id: int):
    """Unassigns a task, setting its status back to open (e.g. for /sos command)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tasks SET assigned_to = NULL, status = 'open' WHERE id = ?",
        (task_id,)
    )
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

def complete_task(task_id: int):
    """Marks a task as completed, awards reliability points to the assignee, and checks blockers."""
    if is_task_blocked(task_id):
        return False
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Get task details to find who completed it
    cursor.execute("SELECT assigned_to, group_id, status FROM tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()
    if not task or task['status'] == 'completed' or not task['assigned_to']:
        conn.close()
        return False
        
    assignee_id = task['assigned_to']
    
    # 2. Update task status
    now_str = datetime.now().isoformat()
    cursor.execute(
        "UPDATE tasks SET status = 'completed', completed_at = ? WHERE id = ?",
        (now_str, task_id)
    )
    
    # 3. Award 10 reliability points to the assignee
    cursor.execute(
        "UPDATE users SET reliability_points = reliability_points + 10 WHERE id = ?",
        (assignee_id,)
    )
    
    conn.commit()
    conn.close()
    return True

# --- Nudges & Message Logging ---

def record_nudge(group_id: int, task_id: int, nudger_id: int, nudged_user_id: int):
    """Logs an anonymous nudge request."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO nudges (group_id, task_id, nudger_id, nudged_user_id) VALUES (?, ?, ?, ?)",
        (group_id, task_id, nudger_id, nudged_user_id)
    )
    conn.commit()
    conn.close()

def get_nudge_count_for_group(group_id: int):
    """Returns count of total nudges in a group."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM nudges WHERE group_id = ?", (group_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_nudges_for_group(group_id: int):
    """Returns nudges log (without exposing the nudger identity)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT n.id, n.task_id, t.description as task_description, 
                  u.first_name as nudged_user_first_name, u.username as nudged_user_username, 
                  n.timestamp 
           FROM nudges n
           JOIN tasks t ON n.task_id = t.id
           JOIN users u ON n.nudged_user_id = u.id
           WHERE n.group_id = ? 
           ORDER BY n.timestamp DESC""",
        (group_id,)
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def log_message(group_id: int, user_id: int, username: str, text: str):
    """Saves a message text for analysis (/standup and passive vibe check)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_messages (group_id, user_id, username, text) VALUES (?, ?, ?, ?)",
        (group_id, user_id, username, text)
    )
    conn.commit()
    conn.close()

def get_recent_messages(group_id: int, limit: int = 100):
    """Retrieves recent messages from a group."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM chat_messages WHERE group_id = ? ORDER BY timestamp DESC LIMIT ?",
        (group_id, limit)
    )
    # We want messages in chronological order, so reverse the result
    rows = [dict(row) for row in cursor.fetchall()]
    rows.reverse()
    conn.close()
    return rows

def get_group_stats(group_id: int):
    """Generates leaderboard statistics for the group dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Total task counts by status
    cursor.execute(
        "SELECT status, COUNT(*) as count FROM tasks WHERE group_id = ? GROUP BY status",
        (group_id,)
    )
    status_counts = {"open": 0, "claimed": 0, "completed": 0}
    for row in cursor.fetchall():
        status_counts[row['status']] = row['count']
        
    # 2. Leaderboard: users and their points and completed tasks
    cursor.execute(
        """SELECT u.id, u.username, u.first_name, u.reliability_points,
                  COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks
           FROM users u
           JOIN group_members gm ON u.id = gm.user_id
           LEFT JOIN tasks t ON u.id = t.assigned_to AND t.group_id = gm.group_id
           WHERE gm.group_id = ?
           GROUP BY u.id
           ORDER BY u.reliability_points DESC, completed_tasks DESC""",
        (group_id,)
    )
    leaderboard = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {
        "status_counts": status_counts,
        "leaderboard": leaderboard
    }

# --- OTP and Session Management Helpers ---

def create_otp(username: str, user_id: int, otp_code: str):
    """Saves or updates a One-Time Password for a user. Expiring in 5 minutes."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Expiration is 5 minutes from now
    import datetime
    expires_at = (datetime.datetime.now() + datetime.timedelta(minutes=5)).isoformat()
    
    cursor.execute(
        "INSERT OR REPLACE INTO otps (username, user_id, otp_code, expires_at) VALUES (LOWER(?), ?, ?, ?)",
        (username, user_id, otp_code, expires_at)
    )
    conn.commit()
    conn.close()

def verify_otp(username: str, otp_code: str):
    """
    Checks if the OTP matches and hasn't expired.
    Deletes the OTP code on success to prevent reuse.
    Returns user details if valid, else None.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    import datetime
    now_str = datetime.datetime.now().isoformat()
    
    cursor.execute(
        "SELECT * FROM otps WHERE username = LOWER(?) AND otp_code = ? AND expires_at > ?",
        (username, otp_code, now_str)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
        
    user_id = row["user_id"]
    
    # Fetch user details
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user_row = cursor.fetchone()
    user = dict(user_row) if user_row else None
    
    # Delete OTP code so it can't be reused
    cursor.execute("DELETE FROM otps WHERE username = LOWER(?)", (username,))
    conn.commit()
    conn.close()
    
    return user

def create_session(user_id: int, username: str, first_name: str) -> str:
    """Creates a new session token, expiring in 7 days."""
    import secrets
    import datetime
    session_token = secrets.token_hex(32)
    expires_at = (datetime.datetime.now() + datetime.timedelta(days=7)).isoformat()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_sessions (session_token, user_id, username, first_name, expires_at) VALUES (?, ?, ?, ?, ?)",
        (session_token, user_id, username, first_name, expires_at)
    )
    conn.commit()
    conn.close()
    
    return session_token

def get_session(session_token: str):
    """Retrieves and validates a session. Returns session dict or None."""
    conn = get_db_connection()
    cursor = conn.cursor()
    import datetime
    now_str = datetime.datetime.now().isoformat()
    
    cursor.execute(
        "SELECT * FROM user_sessions WHERE session_token = ? AND expires_at > ?",
        (session_token, now_str)
    )
    row = cursor.fetchone()
    session = dict(row) if row else None
    conn.close()
    return session

def delete_session(session_token: str):
    """Deletes a session token (logout)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_sessions WHERE session_token = ?", (session_token,))
    conn.commit()
    conn.close()

def get_user_by_username(username: str):
    """Looks up a user by username (case-insensitive)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (username,))
    row = cursor.fetchone()
    user = dict(row) if row else None
    conn.close()
    return user

def get_groups_for_user(user_id: int):
    """Returns all groups that the user belongs to."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT g.* FROM groups g 
           JOIN group_members gm ON g.id = gm.group_id 
           WHERE gm.user_id = ?""",
        (user_id,)
    )
    groups = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return groups

# --- New Accountability Helpers ---

def submit_peer_review(group_id: int, reviewer_id: int, reviewee_id: int, rating: int, feedback: str):
    """
    Submits a peer review for a teammate.
    Increases/decreases reviewee's reliability points based on rating:
      5 -> +5 points
      4 -> +2 points
      3 -> +0 points
      2 -> -2 points
      1 -> -5 points
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Insert review
    cursor.execute(
        """INSERT INTO peer_reviews (group_id, reviewer_id, reviewee_id, rating, feedback)
           VALUES (?, ?, ?, ?, ?)""",
        (group_id, reviewer_id, reviewee_id, rating, feedback)
    )
    
    # 2. Adjust points
    points_map = {5: 5, 4: 2, 3: 0, 2: -2, 1: -5}
    adjustment = points_map.get(rating, 0)
    
    if adjustment != 0:
        cursor.execute(
            "UPDATE users SET reliability_points = reliability_points + ? WHERE id = ?",
            (adjustment, reviewee_id)
        )
        
    conn.commit()
    conn.close()
    return True

def get_peer_reviews_for_group(group_id: int):
    """Returns all peer reviews in the group, indicating reviewer and reviewee names."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT pr.*, 
                  u1.first_name as reviewer_first_name, u1.username as reviewer_username,
                  u2.first_name as reviewee_first_name, u2.username as reviewee_username
           FROM peer_reviews pr
           JOIN users u1 ON pr.reviewer_id = u1.id
           JOIN users u2 ON pr.reviewee_id = u2.id
           WHERE pr.group_id = ?
           ORDER BY pr.timestamp DESC""",
        (group_id,)
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_inactive_users_for_group(group_id: int, inactive_days: float = 3.0):
    """
    Finds team members who haven't sent messages or completed tasks in the last inactive_days.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all users in the group
    cursor.execute(
        """SELECT u.* FROM users u
           JOIN group_members gm ON u.id = gm.user_id
           WHERE gm.group_id = ?""",
        (group_id,)
    )
    members = [dict(row) for row in cursor.fetchall()]
    
    inactive_members = []
    import datetime
    now = datetime.datetime.now()
    threshold = now - datetime.timedelta(days=inactive_days)
    
    for member in members:
        user_id = member["id"]
        
        # Check last chat message
        cursor.execute(
            "SELECT MAX(timestamp) FROM chat_messages WHERE group_id = ? AND user_id = ?",
            (group_id, user_id)
        )
        last_msg_row = cursor.fetchone()
        last_msg_str = last_msg_row[0] if last_msg_row else None
        
        # Check last completed task
        cursor.execute(
            "SELECT MAX(completed_at) FROM tasks WHERE group_id = ? AND assigned_to = ? AND status = 'completed'",
            (group_id, user_id)
        )
        last_task_row = cursor.fetchone()
        last_task_str = last_task_row[0] if last_task_row else None
        
        # Convert to datetime and evaluate
        is_inactive = True
        
        for ts_str in (last_msg_str, last_task_str):
            if not ts_str:
                continue
            
            ts_dt = None
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
                try:
                    ts_dt = datetime.datetime.strptime(ts_str.split(".")[0], fmt.split(".")[0])
                    break
                except ValueError:
                    continue
            
            if ts_dt and ts_dt > threshold:
                is_inactive = False
                break
                
        if is_inactive:
            member["last_activity"] = last_msg_str or last_task_str or "Never"
            inactive_members.append(member)
            
    conn.close()
    return inactive_members


# --- Task Priority & Comments ---

def set_task_priority(task_id: int, priority: str):
    """Updates the priority of a task ('high', 'medium', 'low')."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET priority = ? WHERE id = ?", (priority, task_id))
    conn.commit()
    conn.close()

def add_task_comment(task_id: int, user_id: int, username: str, text: str):
    """Appends a comment to a task."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO task_comments (task_id, user_id, username, text) VALUES (?, ?, ?, ?)",
        (task_id, user_id, username, text)
    )
    conn.commit()
    conn.close()

def get_task_comments(task_id: int):
    """Returns all comments for a task in chronological order."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM task_comments WHERE task_id = ? ORDER BY timestamp ASC",
        (task_id,)
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_group_activity(group_id: int, limit: int = 30):
    """Returns a chronological activity feed of recent task completions and claims."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT t.id, t.description, t.status, t.completed_at, t.created_at,
                  u.first_name as assignee_first_name, u.username as assignee_username
           FROM tasks t
           LEFT JOIN users u ON t.assigned_to = u.id
           WHERE t.group_id = ?
           ORDER BY COALESCE(t.completed_at, t.created_at, t.created_at) DESC
           LIMIT ?""",
        (group_id, limit)
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    activity = []
    for r in rows:
        status = r.get("status")
        desc = r.get("description", "")
        username = r.get("assignee_username") or r.get("assignee_first_name") or "System"
        
        if status == "completed":
            action = f"completed task: \"{desc}\""
            timestamp = r.get("completed_at") or r.get("created_at")
        elif status == "claimed":
            action = f"claimed task: \"{desc}\""
            timestamp = r.get("created_at")
        else:
            action = f"created task: \"{desc}\""
            timestamp = r.get("created_at")
            username = "System"
            
        activity.append({
            "username": username,
            "action": action,
            "timestamp": timestamp
        })
    return activity
