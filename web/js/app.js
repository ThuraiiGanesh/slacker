// API Server Config
const API_BASE = '/api';

// State Management
let currentGroupId = null;
let currentTasks = [];
let parsedTasks = [];
let currentUser = null;

const BOT_COMMANDS = [
    {
        trigger: '/start',
        type: 'slash',
        scope: 'both',
        desc: 'Displays the welcoming onboarding guide and lists command configurations.',
        example: '/start'
    },
    {
        trigger: '/help',
        type: 'slash',
        scope: 'both',
        desc: 'Shows help resources, bot instructions, and links.',
        example: '/help'
    },
    {
        trigger: '/analyze [rubric_text]',
        type: 'slash',
        scope: 'chat',
        desc: 'Paste assignment text, rubrics, or reply to a message containing a rubric to parse key deliverables using Gemini AI.',
        example: '/analyze Assignment 1: Code a database by Friday.'
    },
    {
        trigger: '/tasks',
        type: 'slash',
        scope: 'chat',
        desc: 'Retrieves all active project deliverables with interactive inline buttons to claim or complete them.',
        example: '/tasks'
    },
    {
        trigger: '/claim [task_id]',
        type: 'slash',
        scope: 'chat',
        desc: 'Claim a task deliverable by ID and assign it to yourself.',
        example: '/claim 3'
    },
    {
        trigger: '/complete [task_id]',
        type: 'slash',
        scope: 'chat',
        desc: 'Mark a claimed task deliverable as completed and receive +10 Reliability Points (XP).',
        example: '/complete 3'
    },
    {
        trigger: '/sos [task_id]',
        type: 'slash',
        scope: 'chat',
        desc: 'Workload backup helper: releases a claimed task back to the team pool when you are overwhelmed.',
        example: '/sos 3'
    },
    {
        trigger: '/nudge [task_id]',
        type: 'slash',
        scope: 'dm',
        desc: 'Sends a gentle, anonymous reminder to a teammate currently assigned to that task. Must be sent in private DM to ensure anonymity.',
        example: '/nudge 2'
    },
    {
        trigger: '/standup',
        type: 'slash',
        scope: 'chat',
        desc: 'Generates a quick, event-driven status summary of the team\'s latest group chat discussion using Gemini.',
        example: '/standup'
    },
    {
        trigger: '/stats',
        type: 'slash',
        scope: 'chat',
        desc: 'Displays the group contribution leaderboard showing teammate reliability points.',
        example: '/stats'
    },
    {
        trigger: '/receipt',
        type: 'slash',
        scope: 'chat',
        desc: 'Generates a secure markdown contribution receipt certifying individual task contributions.',
        example: '/receipt'
    },
    {
        trigger: 'show tasks',
        type: 'nlp',
        scope: 'chat',
        desc: 'Natural Talk trigger to view the active list of project deliverables.',
        example: 'what are the tasks'
    },
    {
        trigger: 'I claim task [id]',
        type: 'nlp',
        scope: 'chat',
        desc: 'Natural Talk trigger to claim a task deliverable by mentioning its ID.',
        example: 'I will do task 3'
    },
    {
        trigger: 'done with task [id]',
        type: 'nlp',
        scope: 'chat',
        desc: 'Natural Talk trigger to mark a task completed.',
        example: 'task 2 is complete'
    },
    {
        trigger: 'I need backup on task [id]',
        type: 'nlp',
        scope: 'chat',
        desc: 'Natural Talk trigger to release a task and trigger an SOS notification to the group.',
        example: 'sos task 3'
    },
    {
        trigger: 'standup summary',
        type: 'nlp',
        scope: 'chat',
        desc: 'Natural Talk trigger to compile a standup log summary of team chat.',
        example: 'brief us'
    },
    {
        trigger: 'show leaderboard',
        type: 'nlp',
        scope: 'chat',
        desc: 'Natural Talk trigger to view the reliability rankings.',
        example: 'show stats'
    },
    {
        trigger: 'project receipt',
        type: 'nlp',
        scope: 'chat',
        desc: 'Natural Talk trigger to retrieve the contribution receipt.',
        example: 'grade receipt'
    },
    {
        trigger: 'nudge task [id]',
        type: 'nlp',
        scope: 'dm',
        desc: 'Natural Talk trigger to send an anonymous peer check-in reminder. Send via DM to preserve anonymity.',
        example: 'nudge teammate on task 3'
    }
];

// DOM Elements
const appWrapper = document.getElementById('app-wrapper');
const loginPage = document.getElementById('login-page');
const groupSelector = document.getElementById('group-selector');
const btnRefresh = document.getElementById('btn-refresh');
const noGroupAlert = document.getElementById('no-group-alert');
const dashboardGrid = document.getElementById('dashboard-grid');

// Login Form Elements
const loginStep1Form = document.getElementById('login-step1-form');
const loginStep2Form = document.getElementById('login-step2-form');
const loginUsername = document.getElementById('login-username');
const loginOtp = document.getElementById('login-otp');
const loginError1 = document.getElementById('login-error-1');
const loginError2 = document.getElementById('login-error-2');
const btnSendOtp = document.getElementById('btn-send-otp');
const btnVerifyOtp = document.getElementById('btn-verify-otp');
const btnBackStep1 = document.getElementById('btn-back-step1');
const btnResendOtp = document.getElementById('btn-resend-otp');
const botUsernameLink = document.getElementById('bot-username-link');
const userProfileDisplay = document.getElementById('user-profile-display');
const btnLogout = document.getElementById('btn-logout');

// Stat Elements
const taskProgressRing = document.getElementById('task-progress-ring');
const taskProgressText = document.getElementById('task-progress-text');
const statTasksRatio = document.getElementById('stat-tasks-ratio');
const vibeOrb = document.getElementById('vibe-orb');
const vibeStatus = document.getElementById('vibe-status');
const vibeDescription = document.getElementById('vibe-description');
const leaderboardList = document.getElementById('leaderboard-list');

// Tasks Board
const tasksTableBody = document.getElementById('tasks-table-body');

// Standup Summary
const btnRefreshStandup = document.getElementById('btn-refresh-standup');
const standupLoader = document.getElementById('standup-loader');
const standupContent = document.getElementById('standup-content');

// Rubric Parser & Pre-Submission Auditor
const rubricInput = document.getElementById('rubric-input');
const btnAnalyzeRubric = document.getElementById('btn-analyze-rubric');
const rubricPreviewSection = document.getElementById('rubric-preview-section');
const parsedTasksList = document.getElementById('parsed-tasks-list');
const btnSyncTasks = document.getElementById('btn-sync-tasks');
const btnAuditDraft = document.getElementById('btn-audit-draft');
const draftInput = document.getElementById('draft-input');
const auditResultsSection = document.getElementById('audit-results-section');
const auditSummaryStatus = document.getElementById('audit-summary-status');
const auditSummaryGuidance = document.getElementById('audit-summary-guidance');
const auditDeliverablesList = document.getElementById('audit-deliverables-list');

// Telemetry, Receipt & Peer Feedback
const tabBtns = document.querySelectorAll('.tab-btn');
const tabPanes = document.querySelectorAll('.tab-pane');
const nudgesTimeline = document.getElementById('nudges-timeline');
const peerReviewsList = document.getElementById('peer-reviews-list');
const receiptContent = document.getElementById('receipt-content');
const btnCopyReceipt = document.getElementById('btn-copy-receipt');

// Modal & Health Elements
const groupHealthBanner = document.getElementById('group-health-banner');
const healthBannerText = document.getElementById('health-banner-text');
const btnAddTaskModal = document.getElementById('btn-add-task-modal');
const taskModal = document.getElementById('task-modal');
const btnCloseModal = document.getElementById('btn-close-modal');
const addTaskForm = document.getElementById('add-task-form');
const taskBlockedBySelect = document.getElementById('task-blocked-by');

const peerReviewModal = document.getElementById('peer-review-modal');
const btnCloseReviewModal = document.getElementById('btn-close-review-modal');
const peerReviewForm = document.getElementById('peer-review-form');

// Chatbot Elements
const chatbotLauncher = document.getElementById('chatbot-launcher');
const chatbotPanel = document.getElementById('chatbot-panel');
const chatbotClose = document.getElementById('chatbot-close');
const chatbotInput = document.getElementById('chatbot-input');
const chatbotSend = document.getElementById('chatbot-send');
const chatbotMessages = document.getElementById('chatbot-messages');
const chatbotBadge = document.getElementById('chatbot-badge');
let chatbotHistory = [];

// --- Helper: Authorized Fetch wrapper ---
async function authorizedFetch(url, options = {}) {
    const token = localStorage.getItem('syncup_session_token');
    if (!options.headers) {
        options.headers = {};
    }
    if (token) {
        options.headers['Authorization'] = `Bearer ${token}`;
    }
    
    const res = await fetch(url, options);
    
    if (res.status === 401) {
        handleUnauthorized();
        throw new Error("Unauthorized");
    }
    return res;
}

function handleUnauthorized() {
    localStorage.removeItem('syncup_session_token');
    localStorage.removeItem('syncup_user_info');
    currentUser = null;
    appWrapper.classList.add('hidden');
    loginPage.classList.remove('hidden');
    loginStep1Form.classList.remove('hidden');
    loginStep2Form.classList.add('hidden');
    loginUsername.value = '';
    loginOtp.value = '';
}

// Initialize App
document.addEventListener('DOMContentLoaded', async () => {
    setupEventListeners();
    renderCommandGuide();
    await fetchBotInfo();
    await checkAuthSession();
});

// Check Session on startup
async function checkAuthSession() {
    const token = localStorage.getItem('syncup_session_token');
    if (!token) {
        handleUnauthorized();
        return;
    }
    
    try {
        const res = await authorizedFetch(`${API_BASE}/auth/me`);
        if (res.ok) {
            const data = await res.json();
            // Session is valid
            currentUser = {
                user_id: data.user_id,
                username: data.username,
                first_name: data.first_name
            };
            localStorage.setItem('syncup_user_info', JSON.stringify(currentUser));
            showDashboard();
        } else {
            handleUnauthorized();
        }
    } catch (err) {
        console.error("Session verification failed:", err);
        handleUnauthorized();
    }
}

function showDashboard() {
    loginPage.classList.add('hidden');
    appWrapper.classList.remove('hidden');
    
    const nameStr = currentUser.first_name + (currentUser.username ? ` (@${currentUser.username})` : '');
    userProfileDisplay.textContent = `👤 Hi, ${nameStr}`;
    
    fetchGroups();
}

// Fetch bot details dynamically for instruction link
async function fetchBotInfo() {
    try {
        const res = await fetch(`${API_BASE}/bot-info`);
        if (res.ok) {
            const data = await res.json();
            botUsernameLink.href = `https://t.me/${data.username}`;
            botUsernameLink.textContent = `@${data.username}`;
        }
    } catch (err) {
        console.error("Error fetching bot info:", err);
    }
}

// Event Listeners Configuration
function setupEventListeners() {
    // --- Login Step 1: Send OTP ---
    loginStep1Form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = loginUsername.value.trim();
        if (!username) return;
        
        loginError1.classList.add('hidden');
        btnSendOtp.disabled = true;
        btnSendOtp.textContent = "Sending OTP code...";
        
        try {
            const res = await fetch(`${API_BASE}/auth/send-otp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username })
            });
            
            const data = await res.json();
            
            if (res.ok) {
                // OTP sent successfully, move to step 2
                loginStep1Form.classList.add('hidden');
                loginStep2Form.classList.remove('hidden');
                loginError2.classList.add('hidden');
            } else {
                loginError1.textContent = data.detail || "Failed to send verification code.";
                loginError1.classList.remove('hidden');
            }
        } catch (err) {
            loginError1.textContent = "Server connection error. Please try again.";
            loginError1.classList.remove('hidden');
            console.error(err);
        } finally {
            btnSendOtp.disabled = false;
            btnSendOtp.textContent = "Send Verification Code 🔑";
        }
    });
    
    // --- Login Step 2: Verify OTP ---
    loginStep2Form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = loginUsername.value.trim();
        const otp_code = loginOtp.value.trim();
        if (!username || !otp_code) return;
        
        loginError2.classList.add('hidden');
        btnVerifyOtp.disabled = true;
        btnVerifyOtp.textContent = "Verifying code...";
        
        try {
            const res = await fetch(`${API_BASE}/auth/verify-otp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, otp_code })
            });
            
            const data = await res.json();
            
            if (res.ok) {
                // Verification successful
                localStorage.setItem('syncup_session_token', data.session_token);
                currentUser = {
                    user_id: data.user.id,
                    username: data.user.username,
                    first_name: data.user.first_name
                };
                localStorage.setItem('syncup_user_info', JSON.stringify(currentUser));
                
                showDashboard();
            } else {
                loginError2.textContent = data.detail || "Invalid or expired verification code.";
                loginError2.classList.remove('hidden');
            }
        } catch (err) {
            loginError2.textContent = "Server connection error. Please try again.";
            loginError2.classList.remove('hidden');
            console.error(err);
        } finally {
            btnVerifyOtp.disabled = false;
            btnVerifyOtp.textContent = "Verify & Access Dashboard 🔓";
        }
    });
    
    // Back to Username (Step 2 -> Step 1)
    btnBackStep1.addEventListener('click', () => {
        loginStep2Form.classList.add('hidden');
        loginStep1Form.classList.remove('hidden');
        loginOtp.value = '';
        loginError1.classList.add('hidden');
    });
    
    // Resend OTP
    btnResendOtp.addEventListener('click', () => {
        loginStep1Form.dispatchEvent(new Event('submit'));
    });
    
    // Logout
    btnLogout.addEventListener('click', async () => {
        try {
            const token = localStorage.getItem('syncup_session_token');
            if (token) {
                await fetch(`${API_BASE}/auth/logout`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
            }
        } catch (err) {
            console.error("Logout error on server:", err);
        }
        handleUnauthorized();
    });

    // Dropdown Group selector
    groupSelector.addEventListener('change', (e) => {
        currentGroupId = parseInt(e.target.value);
        loadGroupData(currentGroupId);
    });

    // Global refresh
    btnRefresh.addEventListener('click', () => {
        if (currentGroupId) loadGroupData(currentGroupId);
    });

    // Modal Triggers
    btnAddTaskModal.addEventListener('click', () => {
        // Populate blocker dropdown select options with current uncompleted tasks
        taskBlockedBySelect.innerHTML = '<option value="">No blocker (unblocked)</option>';
        currentTasks.forEach(t => {
            if (t.status !== 'completed') {
                const opt = document.createElement('option');
                opt.value = t.id;
                opt.textContent = `Task #${t.id}: ${t.description}`;
                taskBlockedBySelect.appendChild(opt);
            }
        });
        taskModal.classList.add('active');
    });
    btnCloseModal.addEventListener('click', () => {
        taskModal.classList.remove('active');
    });
    taskModal.addEventListener('click', (e) => {
        if (e.target === taskModal) taskModal.classList.remove('active');
    });

    // Peer Review Modal Triggers
    btnCloseReviewModal.addEventListener('click', () => {
        peerReviewModal.classList.remove('active');
    });
    peerReviewModal.addEventListener('click', (e) => {
        if (e.target === peerReviewModal) peerReviewModal.classList.remove('active');
    });
    peerReviewForm.addEventListener('submit', handleAddPeerReview);

    // Form Submit
    addTaskForm.addEventListener('submit', handleAddTask);

    // AI Standup
    btnRefreshStandup.addEventListener('click', handleRefreshStandup);

    // AI Rubric Parser & Auditor
    btnAnalyzeRubric.addEventListener('click', handleAnalyzeRubric);
    btnSyncTasks.addEventListener('click', handleSyncTasks);
    btnAuditDraft.addEventListener('click', handleAuditDraft);

    // Tabs logic (works dynamically for all tabs including the new ones)
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Find parent card to scope the tab switching, so that Telemetry tabs and Rubric tabs don't interfere!
            const parentCard = btn.closest('.card');
            const cardBtns = parentCard.querySelectorAll('.tab-btn');
            const cardPanes = parentCard.querySelectorAll('.tab-pane');
            
            cardBtns.forEach(b => b.classList.remove('active'));
            cardPanes.forEach(p => p.classList.remove('active'));
            
            btn.classList.add('active');
            const targetTab = btn.getAttribute('data-tab');
            parentCard.querySelector(`#tab-${targetTab}`).classList.add('active');
        });
    });


    // Copy receipt
    btnCopyReceipt.addEventListener('click', handleCopyReceipt);

    // Chatbot Event Listeners
    if (chatbotLauncher) {
        chatbotLauncher.addEventListener('click', () => {
            chatbotPanel.classList.add('active');
            if (chatbotBadge) {
                chatbotBadge.classList.add('hidden');
            }
        });
    }

    if (chatbotClose) {
        chatbotClose.addEventListener('click', () => {
            chatbotPanel.classList.remove('active');
        });
    }

    if (chatbotSend) {
        chatbotSend.addEventListener('click', handleChatbotSend);
    }

    if (chatbotInput) {
        chatbotInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                handleChatbotSend();
            }
        });
    }

    // Command Guide Search and Filter
    const commandSearch = document.getElementById('command-search');
    const filterPills = document.querySelectorAll('.filter-pill');
    
    if (commandSearch) {
        commandSearch.addEventListener('input', () => {
            renderCommandGuide();
        });
    }
    
    filterPills.forEach(pill => {
        pill.addEventListener('click', () => {
            filterPills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            renderCommandGuide();
        });
    });
}

// Fetch registered groups
async function fetchGroups() {
    try {
        const res = await authorizedFetch(`${API_BASE}/groups`);
        const groups = await res.json();
        
        // Clear selector
        groupSelector.innerHTML = '<option value="" disabled selected>Select a group chat...</option>';
        
        if (groups.length === 0) {
            noGroupAlert.classList.remove('hidden');
            dashboardGrid.classList.add('hidden');
            return;
        }

        groups.forEach(group => {
            const opt = document.createElement('option');
            opt.value = group.id;
            opt.textContent = group.name;
            groupSelector.appendChild(opt);
        });

        // Auto-select first group for presentation convenience
        if (groups.length > 0) {
            groupSelector.selectedIndex = 1;
            currentGroupId = groups[0].id;
            loadGroupData(currentGroupId);
        }
    } catch (err) {
        console.error("Error fetching groups:", err);
    }
}

// Global Loader dispatcher for selected Group
function loadGroupData(groupId) {
    noGroupAlert.classList.add('hidden');
    dashboardGrid.classList.remove('hidden');
    
    fetchTasks(groupId);
    fetchStats(groupId);
    fetchNudges(groupId);
    fetchHealth(groupId);
    fetchPeerReviews(groupId);
    // Reset inputs
    rubricPreviewSection.classList.add('hidden');
    rubricInput.value = '';
    standupContent.innerHTML = '<p class="muted">Click "Regenerate" to summarize the last group discussions.</p>';
    
    // Reset Pre-Submission Auditor
    auditResultsSection.classList.add('hidden');
    draftInput.value = '';
}

// Fetch Group tasks
async function fetchTasks(groupId) {
    try {
        const res = await authorizedFetch(`${API_BASE}/groups/${groupId}/tasks`);
        currentTasks = await res.json();
        renderTasks(currentTasks);
        generateReceiptText(currentTasks);
    } catch (err) {
        console.error("Error fetching tasks:", err);
    }
}

// Render tasks list in table
function renderTasks(tasks) {
    tasksTableBody.innerHTML = '';
    
    if (tasks.length === 0) {
        tasksTableBody.innerHTML = '<tr><td colspan="5" class="muted">No tasks generated yet. Paste a syllabus/rubric above to populate project tasks!</td></tr>';
        return;
    }

    tasks.forEach(task => {
        const tr = document.createElement('tr');
        
        let statusBadge = '';
        if (task.status === 'open') {
            statusBadge = '<span class="badge-status open">Open</span>';
        } else if (task.status === 'claimed') {
            statusBadge = '<span class="badge-status claimed">Claimed</span>';
        } else {
            statusBadge = '<span class="badge-status completed">Done</span>';
        }

        const assigneeText = task.assigned_to 
            ? `<span class="assignee-badge">${task.assignee_username ? '@' + task.assignee_username : task.assignee_first_name}</span>`
            : '<span class="muted">Unassigned</span>';

        let blockerLabel = '';
        let isBlocked = false;
        if (task.blocked_by && task.blocker_status !== 'completed') {
            isBlocked = true;
            blockerLabel = `<br><span class="blocker-tag">🔒 Blocked by Task #${task.blocked_by}</span>`;
        } else if (task.blocked_by) {
            blockerLabel = `<br><span class="blocker-status-tag" style="background:rgba(16, 185, 129, 0.15); border-color:rgba(16, 185, 129, 0.3); color:#34d399;">🔓 Task #${task.blocked_by} Done</span>`;
        }

        let actionBtn = '';
        if (task.status === 'claimed') {
            if (isBlocked) {
                actionBtn = `<button class="btn-secondary btn-sm" disabled title="Locked: Complete blocker task first" style="opacity: 0.5; cursor: not-allowed;">Complete</button>`;
            } else {
                actionBtn = `<button class="btn-secondary btn-sm" onclick="completeTask(${task.id})">Complete</button>`;
            }
        } else if (task.status === 'open') {
            if (isBlocked) {
                actionBtn = `<span class="muted" style="font-size:12px; color: var(--text-muted);">🔒 Blocked</span>`;
            } else {
                actionBtn = `<span class="muted" style="font-size:12px;">Claim in Bot</span>`;
            }
        } else {
            actionBtn = '✔️';
        }

        tr.innerHTML = `
            <td style="font-family: monospace; font-weight: bold;">#${task.id}</td>
            <td style="font-weight: 500;">${task.description}${blockerLabel}</td>
            <td>${assigneeText}</td>
            <td><span class="badge" style="background:rgba(255,255,255,0.02);border-color:rgba(255,255,255,0.05);color:var(--text-secondary);">${task.due_date || 'N/A'}</span></td>
            <td>${actionBtn}</td>
        `;
        
        tasksTableBody.appendChild(tr);
    });
}

// Complete task via dashboard
async function completeTask(taskId) {
    try {
        const res = await authorizedFetch(`${API_BASE}/tasks/${taskId}/complete`, {
            method: 'POST'
        });
        
        if (res.ok) {
            // Reload
            loadGroupData(currentGroupId);
        } else {
            const err = await res.json();
            alert(`Error: ${err.detail}`);
        }
    } catch (err) {
        console.error("Error completing task:", err);
    }
}

// Fetch Stats (Leaderboard, circular progress)
async function fetchStats(groupId) {
    try {
        const res = await authorizedFetch(`${API_BASE}/groups/${groupId}/stats`);
        const stats = await res.json();
        
        renderProgress(stats.status_counts);
        renderLeaderboard(stats.leaderboard);
        calculateVibe(stats.status_counts, stats.leaderboard);
    } catch (err) {
        console.error("Error fetching stats:", err);
    }
}

// Render Progress ring
function renderProgress(counts) {
    const open = counts.open || 0;
    const claimed = counts.claimed || 0;
    const completed = counts.completed || 0;
    const total = open + claimed + completed;
    
    const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;
    
    // Animate progress ring (2 * PI * r = 2 * 3.14159 * 50 = 314.16)
    const radius = 50;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (percentage / 100) * circumference;
    
    taskProgressRing.style.strokeDasharray = `${circumference}`;
    taskProgressRing.style.strokeDashoffset = `${offset}`;
    taskProgressText.textContent = `${percentage}%`;
    statTasksRatio.textContent = `${completed} of ${total} tasks completed`;
}

// Render Leaderboard
function renderLeaderboard(leaderboard) {
    leaderboardList.innerHTML = '';
    
    if (leaderboard.length === 0) {
        leaderboardList.innerHTML = '<p class="muted">No registered students yet.</p>';
        return;
    }

    leaderboard.forEach((user, idx) => {
        const li = document.createElement('li');
        li.className = 'leaderboard-item';
        
        const medals = ['🥇', '🥈', '🥉'];
        const medal = idx < medals.length ? medals[idx] : '👤';
        const userLabel = user.username ? `@${user.username}` : user.first_name;

        const isSelf = currentUser && user.id === currentUser.user_id;
        const rateBtn = isSelf 
            ? '' 
            : `<button class="btn-rate-leaderboard" onclick="openPeerReviewModal(${user.id}, '${user.first_name}')">⭐ Rate</button>`;

        li.innerHTML = `
            <div class="user-profile">
                <span class="rank-medal">${medal}</span>
                <div class="user-info">
                    <span class="user-name">${user.first_name} <span class="muted" style="font-size:11px;">(${userLabel})</span></span>
                    <span class="user-tasks-completed">Completed: ${user.completed_tasks} tasks</span>
                </div>
            </div>
            <div class="score-points">${user.reliability_points} XP${rateBtn}</div>
        `;
        leaderboardList.appendChild(li);
    });
}

// Open Peer Review Modal
window.openPeerReviewModal = (userId, firstName) => {
    document.getElementById('review-reviewee-id').value = userId;
    document.getElementById('review-reviewee-name').value = firstName;
    peerReviewForm.reset();
    peerReviewModal.classList.add('active');
};

// Calculate Group Vibe state locally based on active deliverables + leaderboard points
async function calculateVibe(counts, leaderboard) {
    const res = await authorizedFetch(`${API_BASE}/groups/${currentGroupId}/nudges`);
    const nudges = await res.json();
    const nudgeCount = nudges.length;
    
    const claimedCount = counts.claimed || 0;
    const openCount = counts.open || 0;
    const completedCount = counts.completed || 0;
    const totalCount = openCount + claimedCount + completedCount;
    
    // Logic-based stress checks
    if (nudgeCount > 2 && completedCount === 0) {
        // High nudge alerts, low completion
        vibeOrb.className = 'vibe-orb stressed';
        vibeStatus.textContent = 'High Friction Detected ⚠️';
        vibeStatus.style.color = '#f43f5e';
        vibeDescription.textContent = `${nudgeCount} anonymous nudges sent recently. Teammates are waiting for tasks to be processed!`;
    } else if (claimedCount > 3 && completedCount < 2) {
        // High claimed ratio, slow completions
        vibeOrb.className = 'vibe-orb stressed';
        vibeStatus.textContent = 'Workload Stress Warning ⚠️';
        vibeStatus.style.color = '#f59e0b';
        vibeDescription.textContent = "Many items claimed but low delivery rates. Consider rebalancing tasks with /sos.";
    } else if (completedCount > 0 && claimedCount <= 2) {
        // Steady delivery rate
        vibeOrb.className = 'vibe-orb active';
        vibeStatus.textContent = 'Productive & Active 🚀';
        vibeStatus.style.color = '#10b981';
        vibeDescription.textContent = "Great job! Deliverables are moving steadily. Maintain current team alignment.";
    } else {
        // Balanced/Default
        vibeOrb.className = 'vibe-orb idle';
        vibeStatus.textContent = 'Calm / Aligned 🤝';
        vibeStatus.style.color = '#8b5cf6';
        vibeDescription.textContent = "Active team discussion. No toxic alerts or task blockages reported.";
    }
}

// Fetch Nudges Log
async function fetchNudges(groupId) {
    try {
        const res = await authorizedFetch(`${API_BASE}/groups/${groupId}/nudges`);
        const nudges = await res.json();
        renderNudges(nudges);
    } catch (err) {
        console.error("Error fetching nudges:", err);
    }
}

// Render Nudges timeline
function renderNudges(nudges) {
    nudgesTimeline.innerHTML = '';
    
    if (nudges.length === 0) {
        nudgesTimeline.innerHTML = '<p class="muted">No anonymous checks logged yet. Perfect accountability!</p>';
        return;
    }

    nudges.forEach(nudge => {
        const li = document.createElement('li');
        li.className = 'timeline-item';
        
        // Format relative or neat timestamp
        const timeStr = new Date(nudge.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        const dateStr = new Date(nudge.timestamp).toLocaleDateString([], {month: 'short', day:'numeric'});
        
        const username = nudge.nudged_user_username ? `@${nudge.nudged_user_username}` : nudge.nudged_user_first_name;
        
        li.innerHTML = `
            <strong>${username}</strong> was nudged to check in on task: 
            <i>"${nudge.task_description}"</i>
            <span class="time">${dateStr} at ${timeStr}</span>
        `;
        nudgesTimeline.appendChild(li);
    });
}

// Handle Add Task Manually
async function handleAddTask(e) {
    e.preventDefault();
    const desc = document.getElementById('task-desc').value;
    const due = document.getElementById('task-due').value;
    const blockedByVal = document.getElementById('task-blocked-by').value;
    const blocked_by = blockedByVal ? parseInt(blockedByVal) : null;

    if (!desc.trim()) return;

    try {
        const res = await authorizedFetch(`${API_BASE}/groups/${currentGroupId}/tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ description: desc, due_date: due, blocked_by: blocked_by })
        });

        if (res.ok) {
            // Close modal & reset
            taskModal.classList.remove('active');
            addTaskForm.reset();
            loadGroupData(currentGroupId);
        } else {
            const err = await res.json();
            alert(`Failed to add task: ${err.detail || 'Unknown error'}`);
        }
    } catch (err) {
        console.error("Error adding task:", err);
    }
}

// AI Standup Generation
async function handleRefreshStandup() {
    if (!currentGroupId) return;

    standupLoader.classList.remove('hidden');
    standupContent.innerHTML = '';

    try {
        const res = await authorizedFetch(`${API_BASE}/groups/${currentGroupId}/standup`);
        const data = await res.json();
        
        standupLoader.classList.add('hidden');
        
        // Replace markdown formatting from Gemini to simple HTML highlights
        let formatted = data.summary
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
            .replace(/•\s*(.*?)(<br>|$)/g, '<div class="standup-bullet">$1</div>');
            
        standupContent.innerHTML = formatted;
    } catch (err) {
        standupLoader.classList.add('hidden');
        standupContent.innerHTML = '<p class="muted" style="color:#f43f5e;">Failed to connect to AI summarizer. Try again.</p>';
        console.error("Error fetching standup:", err);
    }
}

// AI Rubric parsing via Gemini
async function handleAnalyzeRubric() {
    const text = rubricInput.value.trim();
    if (!text) {
        alert("Please paste some syllabus/rubric text first.");
        return;
    }

    btnAnalyzeRubric.textContent = "Analyzing... ✨";
    btnAnalyzeRubric.disabled = true;

    try {
        const res = await authorizedFetch(`${API_BASE}/analyze-rubric`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        const data = await res.json();
        
        btnAnalyzeRubric.textContent = "Extract Deliverables 🪄";
        btnAnalyzeRubric.disabled = false;

        if (data.tasks && data.tasks.length > 0) {
            parsedTasks = data.tasks;
            renderRubricPreview(parsedTasks);
        } else {
            alert("No tasks could be parsed. Check rubric content.");
        }
    } catch (err) {
        btnAnalyzeRubric.textContent = "Extract Deliverables 🪄";
        btnAnalyzeRubric.disabled = false;
        alert("Failed to analyze. Check Gemini connection.");
        console.error(err);
    }
}

// Render parsed preview
function renderRubricPreview(tasks) {
    rubricPreviewSection.classList.remove('hidden');
    parsedTasksList.innerHTML = '';

    tasks.forEach((task, idx) => {
        const li = document.createElement('li');
        li.className = 'parsed-task-item';
        
        li.innerHTML = `
            <div>
                <strong>Task ${idx + 1}:</strong> 
                <span class="task-desc-val" contenteditable="true" onblur="updateParsedTaskDesc(${idx}, this.innerText)">${task.description}</span>
            </div>
            <div>
                <span class="task-due" contenteditable="true" onblur="updateParsedTaskDue(${idx}, this.innerText)">${task.due_date || 'No Date'}</span>
            </div>
        `;
        parsedTasksList.appendChild(li);
    });
}

// Edit parsed tasks in-place on UI
window.updateParsedTaskDesc = (index, value) => {
    if (parsedTasks[index]) parsedTasks[index].description = value;
};
window.updateParsedTaskDue = (index, value) => {
    if (parsedTasks[index]) parsedTasks[index].due_date = value;
};

// Sync tasks batch to SQLite & group chat
async function handleSyncTasks() {
    if (parsedTasks.length === 0) return;

    btnSyncTasks.textContent = "Syncing... 🚀";
    btnSyncTasks.disabled = true;

    try {
        const res = await authorizedFetch(`${API_BASE}/groups/${currentGroupId}/sync-tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tasks: parsedTasks })
        });

        if (res.ok) {
            rubricPreviewSection.classList.add('hidden');
            rubricInput.value = '';
            parsedTasks = [];
            loadGroupData(currentGroupId);
        } else {
            alert("Failed to sync tasks.");
        }
    } catch (err) {
        console.error("Error syncing tasks:", err);
    } finally {
        btnSyncTasks.textContent = "Sync & Broadcast to Group Chat 🚀";
        btnSyncTasks.disabled = false;
    }
}

// Generate Markdown contribution receipt
function generateReceiptText(tasks) {
    if (tasks.length === 0) {
        receiptContent.textContent = "No tasks completed to construct a receipt.";
        return;
    }

    const completed = tasks.filter(t => t.status === 'completed');
    const totalCompleted = completed.length;
    
    // Group by assignee
    const statsMap = {};
    tasks.forEach(t => {
        if (t.status === 'completed' && t.assigned_to) {
            const label = t.assignee_username ? `@${t.assignee_username}` : t.assignee_first_name;
            if (!statsMap[label]) statsMap[label] = 0;
            statsMap[label]++;
        }
    });

    const groupName = groupSelector.options[groupSelector.selectedIndex].text;
    const dateStr = new Date().toLocaleDateString([], {year: 'numeric', month: 'long', day: 'numeric'});

    let receiptLines = [
        `🧾 SYNCUP CONTRIBUTION RECEIPT`,
        `📁 Group Project: ${groupName}`,
        `📅 Date Generated: ${dateStr}`,
        `==================================`,
        `🏆 PERFORMANCE METRICS:`,
        `• Total Completed Deliverables: ${totalCompleted}/${tasks.length} (${Math.round(totalCompleted/tasks.length*100)}%)`,
        ``,
        `📊 WORKSHARE CONTRIBUTION RATIOS:`
    ];

    Object.keys(statsMap).forEach(user => {
        const share = Math.round((statsMap[user] / totalCompleted) * 100);
        receiptLines.push(`• ${user}: ${share}% share (${statsMap[user]} tasks completed)`);
    });

    receiptLines.push(
        ``,
        `✅ VERIFIED DELIVERABLES LOG:`
    );

    completed.forEach(t => {
        const label = t.assignee_username ? `@${t.assignee_username}` : t.assignee_first_name;
        receiptLines.push(`- [x] "${t.description}" (Handled by: ${label})`);
    });

    receiptLines.push(
        `==================================`,
        `🔒 Validated by SyncUp Cryptographic Hash`
    );

    receiptContent.textContent = receiptLines.join('\n');
}

// Copy Receipt to clipboard
function handleCopyReceipt() {
    const text = receiptContent.textContent;
    if (!text || text.includes("No tasks")) return;

    navigator.clipboard.writeText(text).then(() => {
        const originalText = btnCopyReceipt.textContent;
        btnCopyReceipt.textContent = "Copied! ✓";
        btnCopyReceipt.style.background = "#10b981";
        btnCopyReceipt.style.color = "#fff";
        setTimeout(() => {
            btnCopyReceipt.textContent = originalText;
            btnCopyReceipt.style.background = "";
            btnCopyReceipt.style.color = "";
        }, 2000);
    });
}

// Fetch Group Health status (Inactivity checking)
async function fetchHealth(groupId) {
    try {
        const res = await authorizedFetch(`${API_BASE}/groups/${groupId}/health`);
        const data = await res.json();
        
        if (data.inactive_members && data.inactive_members.length > 0) {
            const names = data.inactive_members.map(u => {
                const label = u.username ? `@${u.username}` : u.first_name;
                return `${u.first_name} (${label})`;
            }).join(', ');
            
            healthBannerText.textContent = `Teammate(s) inactive for 3+ days: ${names}. Send a message or assign a task to sync back up!`;
            groupHealthBanner.classList.remove('hidden');
        } else {
            groupHealthBanner.classList.add('hidden');
        }
    } catch (err) {
        console.error("Error fetching health status:", err);
    }
}

// Fetch Peer Reviews
async function fetchPeerReviews(groupId) {
    try {
        const res = await authorizedFetch(`${API_BASE}/groups/${groupId}/peer-reviews`);
        const reviews = await res.json();
        renderPeerReviews(reviews);
    } catch (err) {
        console.error("Error fetching peer reviews:", err);
    }
}

// Render Peer Reviews Tab content
function renderPeerReviews(reviews) {
    peerReviewsList.innerHTML = '';
    
    if (reviews.length === 0) {
        peerReviewsList.innerHTML = '<p class="muted">No peer feedback submitted yet. Rate teammates via the scoreboard!</p>';
        return;
    }

    reviews.forEach(review => {
        const li = document.createElement('li');
        li.className = 'peer-review-card';
        
        const stars = '★'.repeat(review.rating) + '☆'.repeat(5 - review.rating);
        
        const dateStr = new Date(review.timestamp).toLocaleDateString([], {month: 'short', day: 'numeric'});

        li.innerHTML = `
            <div class="peer-review-meta">
                <span>From: <strong>${review.reviewer_first_name}</strong></span>
                <span>To: <strong>${review.reviewee_first_name}</strong></span>
            </div>
            <div style="margin-bottom: 6px;">
                <span class="peer-review-stars">${stars}</span>
                <span style="font-size: 11px; color: var(--text-muted); margin-left: 6px;">${dateStr}</span>
            </div>
            <div class="peer-review-text peer-review-feedback-bubble">
                "${review.feedback || 'No comments left.'}"
            </div>
        `;
        peerReviewsList.appendChild(li);
    });
}

// Submit Peer Review Form
async function handleAddPeerReview(e) {
    e.preventDefault();
    const revieweeId = parseInt(document.getElementById('review-reviewee-id').value);
    const feedback = document.getElementById('review-feedback').value;
    
    const ratingActive = document.querySelector('input[name="rating"]:checked');
    if (!ratingActive) {
        alert("Please select a rating.");
        return;
    }
    const rating = parseInt(ratingActive.value);

    try {
        const res = await authorizedFetch(`${API_BASE}/groups/${currentGroupId}/peer-reviews`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reviewee_id: revieweeId, rating: rating, feedback: feedback })
        });

        if (res.ok) {
            peerReviewModal.classList.remove('active');
            peerReviewForm.reset();
            loadGroupData(currentGroupId);
        } else {
            const err = await res.json();
            alert(`Failed to submit review: ${err.detail || 'Unknown error'}`);
        }
    } catch (err) {
        console.error("Error submitting peer review:", err);
    }
}

// Call Gemini Draft Auditor
async function handleAuditDraft() {
    const text = draftInput.value.trim();
    if (!text) {
        alert("Please paste your project draft report/code first.");
        return;
    }

    btnAuditDraft.textContent = "Auditing Draft... 🔍";
    btnAuditDraft.disabled = true;

    try {
        const res = await authorizedFetch(`${API_BASE}/groups/${currentGroupId}/audit-draft`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ draft_text: text })
        });
        const data = await res.json();
        
        btnAuditDraft.textContent = "Audit Draft Document 🔍";
        btnAuditDraft.disabled = false;

        auditResultsSection.classList.remove('hidden');
        auditSummaryStatus.textContent = data.overall_status || 'Audit Complete';
        auditSummaryGuidance.textContent = data.overall_guidance || 'No overall advice returned.';
        
        auditDeliverablesList.innerHTML = '';
        if (data.deliverables_audit && data.deliverables_audit.length > 0) {
            data.deliverables_audit.forEach(audit => {
                const li = document.createElement('li');
                li.className = 'parsed-task-item';
                
                let icon = '❌';
                let color = '#f43f5e';
                let statusLabel = 'Missing';
                if (audit.status === 'complete') {
                    icon = '✅';
                    color = '#10b981';
                    statusLabel = 'Complete';
                } else if (audit.status === 'partial') {
                    icon = '🟡';
                    color = '#f59e0b';
                    statusLabel = 'Partial';
                }

                li.innerHTML = `
                    <div style="flex: 1;">
                        <strong>Task #${audit.task_id}:</strong> ${audit.description}
                        <div style="font-size: 12.5px; color: var(--text-secondary); margin-top: 4px; line-height: 1.4;">
                            Feedback: ${audit.feedback || 'None'}
                        </div>
                    </div>
                    <div style="text-align: right; min-width: 90px;">
                        <span style="font-weight: 600; color: ${color}; font-size: 12px; margin-right: 6px;">${statusLabel}</span>
                        <span>${icon}</span>
                    </div>
                `;
                auditDeliverablesList.appendChild(li);
            });
        } else {
            auditDeliverablesList.innerHTML = '<li class="muted">No checklist audited. Make sure tasks are registered first.</li>';
        }
    } catch (err) {
        btnAuditDraft.textContent = "Audit Draft Document 🔍";
        btnAuditDraft.disabled = false;
        alert("Failed to audit draft report. Verify server connection.");
        console.error(err);
    }
}

// Chatbot Event Handlers
async function handleChatbotSend() {
    const text = chatbotInput.value.trim();
    if (!text) return;

    // Clear input
    chatbotInput.value = '';

    // Append user message to list
    appendChatbotMessage('user', text);

    // Add loading indicator from mascot
    const loadingId = appendChatbotMessage('mascot typing', '<div class="chat-dot"></div><div class="chat-dot"></div><div class="chat-dot"></div>');

    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, history: chatbotHistory })
        });
        
        const data = await response.json();
        
        // Remove loading indicator
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) {
            loadingEl.remove();
        }

        if (response.ok) {
            // Append response message
            appendChatbotMessage('mascot', data.reply);
            
            // Add to history
            chatbotHistory.push({ sender: 'user', text: text });
            chatbotHistory.push({ sender: 'mascot', text: data.reply });
        } else {
            appendChatbotMessage('mascot', "Oopsie! 🧸 I'm having trouble connecting to my AI brain right now. Can we try chatting again in a moment? 🎀✨");
        }
    } catch (err) {
        console.error(err);
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) {
            loadingEl.remove();
        }
        appendChatbotMessage('mascot', "Oopsie! 🧸 I'm having trouble connecting to my AI brain right now. Can we try chatting again in a moment? 🎀✨");
    }
}

function appendChatbotMessage(sender, text) {
    const msgEl = document.createElement('div');
    msgEl.className = `chat-msg ${sender}`;
    
    // Generate a unique ID so we can remove loading/typing indicator if needed
    const msgId = 'chat-msg-' + Date.now() + '-' + Math.floor(Math.random() * 1000000);
    msgEl.id = msgId;

    if (sender.includes('mascot')) {
        msgEl.innerHTML = text;
    } else {
        // User messages are plain text to avoid HTML injection
        msgEl.textContent = text;
    }

    chatbotMessages.appendChild(msgEl);
    
    // Scroll to bottom
    chatbotMessages.scrollTop = chatbotMessages.scrollHeight;

    return msgId;
}

function renderCommandGuide() {
    const container = document.getElementById('commands-list-container');
    if (!container) return;
    
    const searchVal = document.getElementById('command-search')?.value.toLowerCase().trim() || '';
    const activeFilter = document.querySelector('.filter-pill.active')?.getAttribute('data-filter') || 'all';
    
    container.innerHTML = '';
    
    const filtered = BOT_COMMANDS.filter(cmd => {
        // Filter by type
        if (activeFilter !== 'all' && cmd.type !== activeFilter) {
            return false;
        }
        // Filter by search text
        if (searchVal) {
            const inTrigger = cmd.trigger.toLowerCase().includes(searchVal);
            const inDesc = cmd.desc.toLowerCase().includes(searchVal);
            const inExample = cmd.example.toLowerCase().includes(searchVal);
            return inTrigger || inDesc || inExample;
        }
        return true;
    });
    
    if (filtered.length === 0) {
        container.innerHTML = '<p class="muted">No commands found matching criteria. 🌸</p>';
        return;
    }
    
    filtered.forEach(cmd => {
        const card = document.createElement('div');
        card.className = 'command-card';
        
        let typeClass = cmd.type === 'slash' ? 'type-slash' : 'type-nlp';
        let typeText = cmd.type === 'slash' ? 'Slash' : 'Natural Talk';
        
        let scopeClass = cmd.scope === 'chat' ? 'scope-chat' : (cmd.scope === 'dm' ? 'scope-dm' : 'scope-both');
        let scopeText = cmd.scope === 'chat' ? '💬 Group' : (cmd.scope === 'dm' ? '🤫 Private DM' : '🌍 Group & DM');
        
        card.innerHTML = `
            <div class="command-card-header">
                <div class="command-trigger-container">
                    <span class="command-trigger" title="Click to copy trigger">${cmd.trigger}</span>
                    <button class="btn-copy-cmd" title="Copy trigger">
                        <svg viewBox="0 0 24 24" width="12" height="12" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round" style="display:block;"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>
                    </button>
                </div>
                <div class="command-badges">
                    <span class="command-badge ${typeClass}">${typeText}</span>
                    <span class="command-badge ${scopeClass}">${scopeText}</span>
                </div>
            </div>
            <p class="command-desc">${cmd.desc}</p>
            <div class="command-example">
                e.g., <span class="copy-example" style="cursor:pointer; text-decoration: underline dotted;" title="Click to copy example">${cmd.example}</span>
            </div>
        `;
        
        // Add copy-to-clipboard functionality
        const triggerEl = card.querySelector('.command-trigger');
        const copyBtn = card.querySelector('.btn-copy-cmd');
        const exampleEl = card.querySelector('.copy-example');
        
        const copyAction = (text, elementToAnimate) => {
            navigator.clipboard.writeText(text).then(() => {
                const originalBg = elementToAnimate.style.background;
                const originalColor = elementToAnimate.style.color;
                elementToAnimate.style.background = 'rgba(16, 185, 129, 0.15)';
                elementToAnimate.style.color = '#10b981';
                setTimeout(() => {
                    elementToAnimate.style.background = originalBg;
                    elementToAnimate.style.color = originalColor;
                }, 1000);
            }).catch(err => console.error(err));
        };
        
        triggerEl.addEventListener('click', () => copyAction(cmd.trigger, triggerEl));
        exampleEl.addEventListener('click', () => copyAction(cmd.example, exampleEl));
        copyBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            copyAction(cmd.trigger, copyBtn);
        });
        
        container.appendChild(card);
    });
}

