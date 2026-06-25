// API Server Config
const API_BASE = window.location.protocol === 'file:' 
    ? 'http://localhost:8000/api' 
    : '/api';

// State Management
let currentGroupId = null;
let currentTasks = [];
let parsedTasks = [];
let currentUser = null;
let showOnlyMyTasks = false;

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
const groupDropdown = document.getElementById('group-dropdown');
const groupDropdownTrigger = document.getElementById('group-dropdown-trigger');
const groupDropdownSelected = document.getElementById('group-dropdown-selected');
const groupDropdownMenu = document.getElementById('group-dropdown-menu');
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
    
    // Reset navbar active tab to Overview
    const navLinks = document.querySelectorAll('.nav-link');
    const subViews = document.querySelectorAll('.sub-view');
    navLinks.forEach(l => {
        if (l.getAttribute('data-view') === 'overview') {
            l.classList.add('active');
        } else {
            l.classList.remove('active');
        }
    });
    subViews.forEach(v => {
        if (v.id === 'view-overview') {
            v.classList.remove('hidden');
        } else {
            v.classList.add('hidden');
        }
    });
    
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
                
                const otpInstructions = document.getElementById('otp-instructions');
                if (otpInstructions) {
                    if (data.simulation_otp) {
                        otpInstructions.innerHTML = `⚠️ Running in <b>Simulation Mode</b> (no Telegram Bot token).<br>Use code <b>${data.simulation_otp}</b> (or master code <b>123456</b>) to login!`;
                        loginOtp.value = data.simulation_otp;
                    } else {
                        otpInstructions.textContent = "A verification code has been sent to your Telegram account. Enter it below to complete sign in.";
                    }
                }
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

    // Custom Dropdown Group selector toggle
    if (groupDropdownTrigger && groupDropdownMenu) {
        groupDropdownTrigger.addEventListener('click', (e) => {
            e.stopPropagation();
            groupDropdown.classList.toggle('active');
            groupDropdownMenu.classList.toggle('hidden');
        });
        
        document.addEventListener('click', (e) => {
            if (groupDropdown && !groupDropdown.contains(e.target)) {
                groupDropdown.classList.remove('active');
                groupDropdownMenu.classList.add('hidden');
            }
        });
    }

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
        chatbotLauncher.addEventListener('click', (e) => {
            // Only toggle if click is directly on the launcher (not bubbled from panel)
            if (e.target === chatbotLauncher || e.target === chatbotBadge || e.target.closest('.chatbot-launcher') === chatbotLauncher) {
                const isOpen = chatbotPanel.classList.contains('active');
                if (isOpen) {
                    chatbotPanel.classList.remove('active');
                } else {
                    chatbotPanel.classList.add('active');
                    if (chatbotBadge) chatbotBadge.classList.add('hidden');
                    if (chatbotInput) chatbotInput.focus();
                }
            }
        });
    }

    if (chatbotClose) {
        chatbotClose.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent bubbling to launcher
            chatbotPanel.classList.remove('active');
        });
    }

    if (chatbotSend) {
        chatbotSend.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent bubbling to launcher
            handleChatbotSend();
        });
    }

    if (chatbotInput) {
        chatbotInput.addEventListener('click', (e) => e.stopPropagation()); // Prevent bubbling
        chatbotInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.stopPropagation();
                handleChatbotSend();
            }
        });
    }

    // Prevent clicks inside chatbot panel from bubbling up to the launcher
    if (chatbotPanel) {
        chatbotPanel.addEventListener('click', (e) => e.stopPropagation());
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

    // --- YSP Style Sub-View Navigation Switcher ---
    const navLinks = document.querySelectorAll('.nav-link');
    const subViews = document.querySelectorAll('.sub-view');
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Set link to active
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            
            // Hide all sub-views and show target sub-view
            subViews.forEach(v => v.classList.add('hidden'));
            const targetViewId = `view-${link.getAttribute('data-view')}`;
            const targetView = document.getElementById(targetViewId);
            if (targetView) {
                targetView.classList.remove('hidden');
            }
        });
    });

    // Theme toggle
    const btnThemeToggle = document.getElementById('btn-theme-toggle');
    if (btnThemeToggle) {
        const savedTheme = localStorage.getItem('syncup_theme') || 'dark';
        document.body.setAttribute('data-theme', savedTheme);
        btnThemeToggle.textContent = savedTheme === 'light' ? '🌙' : '☀️';
        btnThemeToggle.addEventListener('click', () => {
            const currentTheme = document.body.getAttribute('data-theme') || 'dark';
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            document.body.setAttribute('data-theme', newTheme);
            localStorage.setItem('syncup_theme', newTheme);
            btnThemeToggle.textContent = newTheme === 'light' ? '🌙' : '☀️';
        });
    }

    // My Tasks filter
    const btnMyTasksFilter = document.getElementById('btn-my-tasks-filter');
    if (btnMyTasksFilter) {
        btnMyTasksFilter.addEventListener('click', () => {
            showOnlyMyTasks = !showOnlyMyTasks;
            btnMyTasksFilter.classList.toggle('active', showOnlyMyTasks);
            renderTasks(currentTasks);
        });
    }

    // Grade risk predictor
    const btnPredictRisk = document.getElementById('btn-predict-risk');
    if (btnPredictRisk) {
        btnPredictRisk.addEventListener('click', handlePredictRisk);
    }

    // Meeting minutes generator
    const btnGenMinutes = document.getElementById('btn-gen-minutes');
    if (btnGenMinutes) {
        btnGenMinutes.addEventListener('click', handleGenerateMinutes);
    }

    // Workload balancer
    const btnWorkloadSuggest = document.getElementById('btn-workload-suggest');
    if (btnWorkloadSuggest) {
        btnWorkloadSuggest.addEventListener('click', handleWorkloadSuggest);
    }

    // Task comments modal closing
    const btnCloseCommentsModal = document.getElementById('btn-close-comments-modal');
    if (btnCloseCommentsModal) {
        btnCloseCommentsModal.addEventListener('click', () => {
            document.getElementById('comments-modal').classList.remove('active');
        });
    }
    const commentsModal = document.getElementById('comments-modal');
    if (commentsModal) {
        commentsModal.addEventListener('click', (e) => {
            if (e.target === commentsModal) commentsModal.classList.remove('active');
        });
    }

    // Task comment submission
    const btnSubmitComment = document.getElementById('btn-submit-comment');
    if (btnSubmitComment) {
        btnSubmitComment.addEventListener('click', submitComment);
    }

    // PDF receipt export
    const btnExportPdf = document.getElementById('btn-export-pdf');
    if (btnExportPdf) {
        btnExportPdf.addEventListener('click', exportReceiptPdf);
    }
}

// Helpers for visual premium group selector UI
function getInitials(name) {
    if (!name) return 'GP';
    return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
}

function getGroupGradient(id) {
    const gradients = [
        'linear-gradient(135deg, #f472b6 0%, #c084fc 100%)', // Pink to Violet
        'linear-gradient(135deg, #38bdf8 0%, #818cf8 100%)', // Cyan to Indigo
        'linear-gradient(135deg, #34d399 0%, #0284c7 100%)', // Mint to Sky Blue
        'linear-gradient(135deg, #fb7185 0%, #f43f5e 100%)', // Rose to Red
        'linear-gradient(135deg, #a78bfa 0%, #ec4899 100%)'  // Lavender to Pink
    ];
    return gradients[id % gradients.length];
}

function getGroupEmoji(name) {
    const n = name.toLowerCase();
    if (n.includes('secret') || n.includes('project')) return '🛡️';
    if (n.includes('blah')) return '🧪';
    if (n.includes('goo')) return '🍭';
    if (n.includes('bot')) return '🤖';
    if (n.includes('ai') || n.includes('sync')) return '✨';
    return '👥';
}

// Render Custom Group Dropdown menu items
function renderGroupDropdown(groups) {
    const selectedText = document.getElementById('group-dropdown-selected');
    const menu = document.getElementById('group-dropdown-menu');
    const activeAvatar = document.getElementById('group-dropdown-active-avatar');
    
    if (!menu || !selectedText) return;
    menu.innerHTML = '';
    
    if (groups.length === 0) {
        selectedText.textContent = 'No groups found';
        if (activeAvatar) activeAvatar.textContent = '👥';
        return;
    }
    
    // Find active group
    const activeGroup = groups.find(g => g.id === currentGroupId) || groups[0];
    currentGroupId = activeGroup.id;
    selectedText.textContent = activeGroup.name;
    if (activeAvatar) {
        activeAvatar.textContent = getGroupEmoji(activeGroup.name);
        const parent = activeAvatar.parentElement;
        if (parent) {
            parent.style.background = getGroupGradient(activeGroup.id);
        }
    }
    
    groups.forEach(group => {
        const item = document.createElement('div');
        item.className = 'custom-dropdown-item';
        const isSelected = currentGroupId === group.id;
        if (isSelected) {
            item.classList.add('selected');
        }
        
        const initials = getInitials(group.name);
        const gradient = getGroupGradient(group.id);
        const emoji = getGroupEmoji(group.name);
        
        item.innerHTML = `
            <div class="dropdown-item-avatar" style="background: ${gradient};">
                ${emoji}
            </div>
            <div class="dropdown-item-info">
                <span class="dropdown-item-title">${group.name}</span>
                <span class="dropdown-item-subtitle">${isSelected ? 'Active Workspace' : 'Switch to workspace'}</span>
            </div>
            ${isSelected ? '<span class="dropdown-item-check">✓</span>' : ''}
        `;
        
        item.addEventListener('click', () => {
            currentGroupId = group.id;
            selectedText.textContent = group.name;
            if (activeAvatar) {
                activeAvatar.textContent = emoji;
                const parent = activeAvatar.parentElement;
                if (parent) {
                    parent.style.background = gradient;
                }
            }
            
            // Highlight selected item
            menu.querySelectorAll('.custom-dropdown-item').forEach(el => el.classList.remove('selected'));
            item.classList.add('selected');
            
            menu.classList.add('hidden');
            document.getElementById('group-dropdown').classList.remove('active');
            
            loadGroupData(currentGroupId);
        });
        menu.appendChild(item);
    });
}

// Fetch registered groups
async function fetchGroups() {
    try {
        const res = await authorizedFetch(`${API_BASE}/groups`);
        const groups = await res.json();
        
        if (groups.length === 0) {
            noGroupAlert.classList.remove('hidden');
            dashboardGrid.classList.add('hidden');
            renderGroupDropdown([]);
            return;
        }

        // Auto-select first group for convenience
        if (!currentGroupId && groups.length > 0) {
            currentGroupId = groups[0].id;
        }
        
        renderGroupDropdown(groups);
        loadGroupData(currentGroupId);
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
    fetchActivity(groupId);
    
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
    
    let tasksToRender = tasks;
    if (showOnlyMyTasks && currentUser) {
        tasksToRender = tasks.filter(t => t.assigned_to === currentUser.user_id);
    }
    
    if (tasksToRender.length === 0) {
        if (showOnlyMyTasks) {
            tasksTableBody.innerHTML = '<tr><td colspan="6" class="muted">No tasks assigned to you yet. Claim some in the Telegram group using /claim!</td></tr>';
        } else {
            tasksTableBody.innerHTML = '<tr><td colspan="6" class="muted">No tasks generated yet. Paste a syllabus/rubric above to populate project tasks!</td></tr>';
        }
        return;
    }

    tasksToRender.forEach(task => {
        const tr = document.createElement('tr');
        
        // Add overdue class to row if uncompleted and overdue
        if (task.status !== 'completed' && task.due_date) {
            const datePattern = /^\d{4}-\d{2}-\d{2}$/;
            if (datePattern.test(task.due_date.trim())) {
                const dueTime = new Date(task.due_date).getTime();
                const nowTime = new Date().setHours(0, 0, 0, 0);
                if (dueTime < nowTime) {
                    tr.className = 'overdue-row';
                }
            }
        }
        
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
        
        let commentBtn = `<button class="btn-secondary btn-sm" onclick="openCommentsModal(${task.id}, '${task.description.replace(/'/g, "\\'")}')" style="margin-left: 5px; font-size: 11.5px; padding: 4px 8px; border-radius: 8px; font-weight:500;">💬 Comments</button>`;

        let priBadge = '';
        const pri = task.priority || 'medium';
        if (pri === 'high') {
            priBadge = `<span class="priority-badge high" onclick="cyclePriority(${task.id}, '${pri}')" title="High Priority - Click to cycle">🔴</span>`;
        } else if (pri === 'low') {
            priBadge = `<span class="priority-badge low" onclick="cyclePriority(${task.id}, '${pri}')" title="Low Priority - Click to cycle">🟢</span>`;
        } else {
            priBadge = `<span class="priority-badge medium" onclick="cyclePriority(${task.id}, '${pri}')" title="Medium Priority - Click to cycle">🟡</span>`;
        }

        tr.innerHTML = `
            <td style="font-family: monospace; font-weight: bold;">#${task.id}</td>
            <td>${priBadge}</td>
            <td style="font-weight: 500;">${task.description}${blockerLabel}</td>
            <td>${assigneeText}</td>
            <td><span class="badge" style="background:rgba(255,255,255,0.02);border-color:rgba(255,255,255,0.05);color:var(--text-secondary);">${task.due_date || 'N/A'}${getDueDateCountdown(task.due_date)}</span></td>
            <td>${actionBtn}${commentBtn}</td>
        `;
        
        tasksTableBody.appendChild(tr);
    });
}

// Helper countdown generator
function getDueDateCountdown(dueDate) {
    if (!dueDate) return '';
    const datePattern = /^\d{4}-\d{2}-\d{2}$/;
    if (!datePattern.test(dueDate.trim())) {
        return '';
    }
    const dueTime = new Date(dueDate).getTime();
    if (isNaN(dueTime)) return '';
    const nowTime = new Date().setHours(0, 0, 0, 0);
    const diffTime = dueTime - nowTime;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) {
        return `<br><span class="countdown-badge overdue">⚠️ Overdue by ${Math.abs(diffDays)}d</span>`;
    } else if (diffDays === 0) {
        return `<br><span class="countdown-badge overdue">⏰ Due Today!</span>`;
    } else if (diffDays <= 2) {
        return `<br><span class="countdown-badge due-soon">⏰ Due in ${diffDays}d</span>`;
    } else {
        return `<br><span class="countdown-badge plenty-time">📅 Due in ${diffDays}d</span>`;
    }
}

// Complete task via dashboard
window.completeTask = async function(taskId) {
    try {
        const res = await authorizedFetch(`${API_BASE}/tasks/${taskId}/complete`, {
            method: 'POST'
        });
        
        if (res.ok) {
            // Trigger confetti!
            if (typeof confetti === 'function') {
                confetti({
                    particleCount: 100,
                    spread: 70,
                    origin: { y: 0.6 },
                    colors: ['#ec4899', '#be185d', '#8b5cf6', '#a78bfa', '#fbcfe8']
                });
            }
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

// Cycle priority handler
window.cyclePriority = async function(taskId, currentPriority) {
    const nextPriority = currentPriority === 'high' ? 'medium' : (currentPriority === 'medium' ? 'low' : 'high');
    try {
        const res = await authorizedFetch(`${API_BASE}/groups/${currentGroupId}/tasks/${taskId}/priority`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ priority: nextPriority })
        });
        if (res.ok) {
            loadGroupData(currentGroupId);
        }
    } catch (err) {
        console.error("Error cycling priority:", err);
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

        // Dynamic Achievement Badges
        let badgesHtml = '';
        if (user.completed_tasks >= 3) {
            badgesHtml += `<span class="achievement-badge" title="Overachiever - Completed 3+ tasks! 👑">👑</span>`;
        } else if (user.completed_tasks >= 1) {
            badgesHtml += `<span class="achievement-badge" title="Active Teammate - Completed tasks! ✨">✨</span>`;
        }
        if (user.reliability_points >= 30) {
            badgesHtml += `<span class="achievement-badge" title="Superstar - Earned 30+ XP! 🔥">🔥</span>`;
        }

        // Member progress ratio (completed vs assigned tasks)
        const claimed = currentTasks.filter(t => t.assigned_to === user.id && t.status === 'claimed').length;
        const completed = user.completed_tasks || 0;
        const totalAssigned = claimed + completed;
        const pct = totalAssigned > 0 ? Math.round((completed / totalAssigned) * 100) : 0;
        
        // Small 24x24 progress ring SVG
        const r = 8;
        const circ = 2 * Math.PI * r;
        const off = circ - (pct / 100) * circ;
        
        const ringSvg = `
            <svg class="member-progress-ring" width="24" height="24" viewBox="0 0 24 24" title="${pct}% completion progress">
                <circle cx="12" cy="12" r="${r}" stroke="rgba(255, 255, 255, 0.05)" stroke-width="2.5" fill="transparent"/>
                <circle cx="12" cy="12" r="${r}" stroke="var(--accent-pink)" stroke-width="2.5" fill="transparent"
                        stroke-dasharray="${circ}" stroke-dashoffset="${off}" transform="rotate(-90 12 12)"/>
            </svg>
        `;

        const isSelf = currentUser && user.id === currentUser.user_id;
        const rateBtn = isSelf 
            ? '' 
            : `<button class="btn-rate-leaderboard" onclick="openPeerReviewModal(${user.id}, '${user.first_name}')">⭐ Rate</button>`;

        li.innerHTML = `
            <div class="user-profile">
                <span class="rank-medal">${medal}</span>
                ${ringSvg}
                <div class="user-info">
                    <span class="user-name">${user.first_name}${badgesHtml} <span class="muted" style="font-size:11px;">(${userLabel})</span></span>
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
    const priority = document.getElementById('task-priority').value || 'medium';

    if (!desc.trim()) return;

    try {
        const res = await authorizedFetch(`${API_BASE}/groups/${currentGroupId}/tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ description: desc, due_date: due, blocked_by: blocked_by, priority: priority })
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
// ===== PDF Upload Helpers =====
// Configure PDF.js worker (CDN-matched version)
if (typeof pdfjsLib !== 'undefined') {
    pdfjsLib.GlobalWorkerOptions.workerSrc =
        'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
}

/**
 * Extract all text from a PDF File object using PDF.js.
 * Returns a promise that resolves to the full text string.
 */
async function extractTextFromPdf(file) {
    const arrayBuffer = await file.arrayBuffer();
    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
    let fullText = '';
    for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const content = await page.getTextContent();
        const pageText = content.items.map(item => item.str).join(' ');
        fullText += pageText + '\n';
    }
    return fullText.trim();
}

/**
 * Called when a PDF file is selected via the file input.
 * target: 'rubric' | 'auditor'
 */
async function handlePdfFile(file, target) {
    if (!file || file.type !== 'application/pdf') {
        alert('Please select a valid .pdf file.');
        return;
    }

    const statusEl = document.getElementById(`${target}-pdf-status`);
    const zone = document.getElementById(`${target}-pdf-zone`);
    
    let textarea;
    if (target === 'rubric') {
        textarea = document.getElementById('rubric-input');
    } else if (target === 'auditor') {
        textarea = document.getElementById('draft-input');
    } else if (target === 'meeting') {
        textarea = document.getElementById('meeting-transcript-input');
    }

    statusEl.textContent = `⏳ Reading "${file.name}"...`;
    zone.classList.add('loading');

    try {
        const text = await extractTextFromPdf(file);
        if (!text) {
            statusEl.textContent = '⚠️ Could not extract text (scanned/image PDF). Try copy-pasting instead.';
            zone.classList.remove('loading');
            return;
        }
        textarea.value = text;
        statusEl.innerHTML = `✅ <strong>${file.name}</strong> loaded (${text.length.toLocaleString()} chars) — text inserted below`;
        zone.classList.remove('loading');
        zone.classList.add('loaded');
    } catch (err) {
        console.error('PDF extraction error:', err);
        statusEl.textContent = '❌ Failed to read PDF. Make sure it is a text-based PDF.';
        zone.classList.remove('loading');
    }
}

/**
 * Handles drag-and-drop onto the PDF zone.
 */
function handlePdfDrop(event, target) {
    event.preventDefault();
    const zone = document.getElementById(`${target}-pdf-zone`);
    zone.classList.remove('dragging');
    const file = event.dataTransfer.files[0];
    handlePdfFile(file, target);
}

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

    const groupName = document.getElementById('group-dropdown-selected')?.textContent || 'Active Group';
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

// ============================================================
// NEW FEATURE HANDLERS AND HELPERS
// ============================================================

// New Feature Element Declarations
const gradeRiskDays = document.getElementById('grade-risk-days');
const gradeRiskResult = document.getElementById('grade-risk-result');
const riskScoreCircle = document.getElementById('risk-score-circle');
const riskLevelLabel = document.getElementById('risk-level-label');
const riskExplanation = document.getElementById('risk-explanation');
const riskRecommendations = document.getElementById('risk-recommendations');

const meetingTranscriptInput = document.getElementById('meeting-transcript-input');
const meetingMinutesResult = document.getElementById('meeting-minutes-result');
const minutesSummary = document.getElementById('minutes-summary');
const minutesDecisions = document.getElementById('minutes-decisions');
const minutesActions = document.getElementById('minutes-actions');

const workloadResult = document.getElementById('workload-result');
const workloadSuggestionBanner = document.getElementById('workload-suggestion-banner');
const workloadBars = document.getElementById('workload-bars');

const commentsModal = document.getElementById('comments-modal');
const commentsTaskTitle = document.getElementById('comments-task-title');
const commentsList = document.getElementById('comments-list');
const commentsTaskId = document.getElementById('comments-task-id');
const commentInput = document.getElementById('comment-input');
const btnSubmitComment = document.getElementById('btn-submit-comment');

const activityTimelineList = document.getElementById('activity-timeline-list');

// Task comments modal logic
window.openCommentsModal = async function(taskId, taskDescription) {
    commentsTaskId.value = taskId;
    commentsTaskTitle.textContent = `Task #${taskId}: "${taskDescription}"`;
    commentInput.value = '';
    commentsList.innerHTML = '<p class="muted">Loading comments...</p>';
    commentsModal.classList.add('active');
    
    await fetchComments(taskId);
};

async function fetchComments(taskId) {
    try {
        const res = await authorizedFetch(`${API_BASE}/groups/${currentGroupId}/tasks/${taskId}/comments`);
        if (res.ok) {
            const data = await res.json();
            renderComments(data.comments);
        } else {
            commentsList.innerHTML = '<p class="muted" style="color:#f43f5e;">Failed to load comments.</p>';
        }
    } catch (err) {
        console.error("Error loading comments:", err);
        commentsList.innerHTML = '<p class="muted" style="color:#f43f5e;">Error loading comments.</p>';
    }
}

function renderComments(comments) {
    commentsList.innerHTML = '';
    if (!comments || comments.length === 0) {
        commentsList.innerHTML = '<p class="muted">No comments yet. Be the first to start the discussion! 🌸</p>';
        return;
    }
    
    comments.forEach(comment => {
        const div = document.createElement('div');
        div.className = 'comment-item';
        
        const dateStr = new Date(comment.timestamp).toLocaleDateString([], {month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'});
        
        div.innerHTML = `
            <div class="comment-author">@${comment.username}</div>
            <div class="comment-text">${comment.text}</div>
            <div class="comment-time">${dateStr}</div>
        `;
        commentsList.appendChild(div);
    });
}

async function submitComment() {
    const taskId = commentsTaskId.value;
    const text = commentInput.value.trim();
    if (!text) return;
    
    btnSubmitComment.disabled = true;
    btnSubmitComment.textContent = "Posting... 💬";
    
    try {
        const res = await authorizedFetch(`${API_BASE}/groups/${currentGroupId}/tasks/${taskId}/comments`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        if (res.ok) {
            commentInput.value = '';
            await fetchComments(taskId);
        } else {
            alert("Failed to submit comment.");
        }
    } catch (err) {
        console.error("Error submitting comment:", err);
    } finally {
        btnSubmitComment.disabled = false;
        btnSubmitComment.textContent = "Post Comment 💬";
    }
}

// AI Grade Risk Predictor
async function handlePredictRisk() {
    const btnPredictRisk = document.getElementById('btn-predict-risk');
    const days = gradeRiskDays.value || 14;
    btnPredictRisk.disabled = true;
    btnPredictRisk.textContent = "Predicting... 🎯";
    
    try {
        const res = await authorizedFetch(`${API_BASE}/groups/${currentGroupId}/grade-risk?days_until_deadline=${days}`);
        if (res.ok) {
            const data = await res.json();
            
            gradeRiskResult.classList.remove('hidden');
            riskScoreCircle.textContent = data.risk_score;
            
            // Set circle class based on risk level
            riskScoreCircle.className = 'risk-score-circle';
            const rl = data.risk_level.toLowerCase();
            if (rl.includes('low')) {
                riskScoreCircle.classList.add('low');
            } else if (rl.includes('medium')) {
                riskScoreCircle.classList.add('medium');
            } else if (rl.includes('critical')) {
                riskScoreCircle.classList.add('critical');
            } else {
                riskScoreCircle.classList.add('high');
            }
            
            riskLevelLabel.textContent = data.risk_level;
            riskExplanation.textContent = data.explanation;
            
            riskRecommendations.innerHTML = '';
            if (data.recommendations && data.recommendations.length > 0) {
                data.recommendations.forEach(rec => {
                    const li = document.createElement('li');
                    li.className = 'parsed-task-item';
                    li.innerHTML = `🌟 ${rec}`;
                    riskRecommendations.appendChild(li);
                });
            } else {
                riskRecommendations.innerHTML = '<li class="muted">All systems nominal! Excellent work.</li>';
            }
        }
    } catch (err) {
        console.error("Error predicting grade risk:", err);
    } finally {
        btnPredictRisk.disabled = false;
        btnPredictRisk.textContent = "Predict Grade Risk 🎯";
    }
}

// AI Meeting Minutes
async function handleGenerateMinutes() {
    const btnGenMinutes = document.getElementById('btn-gen-minutes');
    const text = meetingTranscriptInput.value.trim();
    if (!text) {
        alert("Please paste some transcript or notes first.");
        return;
    }
    
    btnGenMinutes.disabled = true;
    btnGenMinutes.textContent = "Generating... 📝";
    
    try {
        const res = await authorizedFetch(`${API_BASE}/groups/${currentGroupId}/meeting-minutes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transcript_text: text })
        });
        if (res.ok) {
            const data = await res.json();
            
            meetingMinutesResult.classList.remove('hidden');
            minutesSummary.textContent = data.summary || 'None';
            
            minutesDecisions.innerHTML = '';
            if (data.decisions && data.decisions.length > 0) {
                data.decisions.forEach(dec => {
                    const li = document.createElement('li');
                    li.className = 'parsed-task-item';
                    li.innerHTML = `🤝 ${dec}`;
                    minutesDecisions.appendChild(li);
                });
            } else {
                minutesDecisions.innerHTML = '<li class="muted">No decisions explicitly recorded.</li>';
            }
            
            minutesActions.innerHTML = '';
            if (data.action_items && data.action_items.length > 0) {
                data.action_items.forEach(action => {
                    const li = document.createElement('li');
                    li.className = 'parsed-task-item';
                    li.innerHTML = `🎯 ${action.task} (Assigned to: ${action.assignee || 'Unassigned'})`;
                    minutesActions.appendChild(li);
                });
            } else {
                minutesActions.innerHTML = '<li class="muted">No action items recorded.</li>';
            }
        }
    } catch (err) {
        console.error("Error generating meeting minutes:", err);
    } finally {
        btnGenMinutes.disabled = false;
        btnGenMinutes.textContent = "Generate Minutes 📝";
    }
}

// AI Workload Balancer
async function handleWorkloadSuggest() {
    const btnWorkloadSuggest = document.getElementById('btn-workload-suggest');
    btnWorkloadSuggest.disabled = true;
    btnWorkloadSuggest.textContent = "Analysing... ⚖️";
    
    try {
        const res = await authorizedFetch(`${API_BASE}/groups/${currentGroupId}/workload-suggest`);
        if (res.ok) {
            const data = await res.json();
            
            workloadResult.classList.remove('hidden');
            workloadSuggestionBanner.innerHTML = `💡 <strong>Recommendation:</strong> ${data.suggestion}`;
            
            workloadBars.innerHTML = '';
            if (data.workloads) {
                const maxTasks = Math.max(...Object.values(data.workloads), 1);
                
                Object.entries(data.workloads).forEach(([member, count]) => {
                    const pct = Math.round((count / maxTasks) * 100);
                    const row = document.createElement('div');
                    row.className = 'workload-bar-row';
                    row.innerHTML = `
                        <div class="workload-bar-label">${member}</div>
                        <div class="workload-bar-track">
                            <div class="workload-bar-fill" style="width: ${pct}%;"></div>
                        </div>
                        <div class="workload-bar-count">${count} tasks</div>
                    `;
                    workloadBars.appendChild(row);
                });
            }
        }
    } catch (err) {
        console.error("Error fetching workload suggestion:", err);
    } finally {
        btnWorkloadSuggest.disabled = false;
        btnWorkloadSuggest.textContent = "Analyse Workload ⚖️";
    }
}

// Activity Timeline
async function fetchActivity(groupId) {
    try {
        const res = await authorizedFetch(`${API_BASE}/groups/${groupId}/activity`);
        if (res.ok) {
            const data = await res.json();
            renderActivity(data.activity);
        }
    } catch (err) {
        console.error("Error fetching activity timeline:", err);
    }
}

function renderActivity(activity) {
    if (!activityTimelineList) return;
    activityTimelineList.innerHTML = '';
    
    if (!activity || activity.length === 0) {
        activityTimelineList.innerHTML = '<p class="muted">No recent activity. Complete or claim tasks to see them here.</p>';
        return;
    }
    
    activity.forEach(act => {
        const item = document.createElement('div');
        item.className = 'timeline-item';
        
        let dotClass = '';
        const actionStr = act.action || '';
        if (actionStr.toLowerCase().includes('completed') || actionStr.toLowerCase().includes('done')) {
            dotClass = 'completed';
        } else if (actionStr.toLowerCase().includes('claimed')) {
            dotClass = 'claimed';
        }
        
        const timestampVal = act.timestamp ? new Date(act.timestamp) : new Date();
        const dateStr = isNaN(timestampVal.getTime()) 
            ? 'Recent' 
            : timestampVal.toLocaleDateString([], {month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'});
        
        const usernameVal = act.username || 'System';
        item.innerHTML = `
            <div class="timeline-dot ${dotClass}"></div>
            <div class="timeline-content">
                <div class="timeline-desc">@${usernameVal} ${actionStr}</div>
                <div class="timeline-meta">${dateStr}</div>
            </div>
        `;
        activityTimelineList.appendChild(item);
    });
}

// Print / Export Receipt PDF
function exportReceiptPdf() {
    const text = receiptContent.textContent;
    if (!text || text.includes("No tasks")) {
        alert("No receipt content to export.");
        return;
    }
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html>
        <head>
            <title>SyncUp AI - Contribution Receipt</title>
            <style>
                body {
                    font-family: monospace;
                    padding: 40px;
                    line-height: 1.6;
                    color: #1a0010;
                    white-space: pre-wrap;
                    background: #ffffff;
                }
                @media print {
                    body {
                        padding: 0;
                    }
                }
            </style>
        </head>
        <body>${text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</body>
        </html>
    `);
    printWindow.document.close();
    printWindow.print();
}

