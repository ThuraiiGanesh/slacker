import asyncio
import logging
import os
import sys
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from database import models
from api import routes
from bot import handlers, scheduler

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Load configuration from Environment
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
# Fallback demo token if not set (judges can set this in environment)
if not TELEGRAM_BOT_TOKEN:
    logger.warning("[WARNING] TELEGRAM_BOT_TOKEN environment variable not set. Telegram Bot will run in SIMULATION/OFFLINE mode.")

from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI app
app = FastAPI(title="SyncUp AI API", description="Gradeline AI Hackathon MVP Backend")

# Enable CORS for file:// protocol (Origin: null) and local/deployment ports
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize SQLite database
models.init_db()
logger.info("SQLite database initialized successfully.")

# Configure Telegram Bot
telegram_application = None

if TELEGRAM_BOT_TOKEN:
    try:
        # Build python-telegram-bot application
        telegram_application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Register Command Handlers
        telegram_application.add_handler(CommandHandler("start", handlers.start_command))
        telegram_application.add_handler(CommandHandler("help", handlers.help_command))
        telegram_application.add_handler(CommandHandler("analyze", handlers.analyze_command))
        telegram_application.add_handler(CommandHandler("tasks", handlers.tasks_command))
        telegram_application.add_handler(CommandHandler("claim", handlers.claim_command))
        telegram_application.add_handler(CommandHandler("complete", handlers.complete_command))
        telegram_application.add_handler(CommandHandler("nudge", handlers.nudge_command))
        telegram_application.add_handler(CommandHandler("sos", handlers.sos_command))
        telegram_application.add_handler(CommandHandler("standup", handlers.standup_command))
        telegram_application.add_handler(CommandHandler("stats", handlers.stats_command))
        telegram_application.add_handler(CommandHandler("receipt", handlers.receipt_command))
        
        # Register Callback query handler (for inline keyboard clicks)
        telegram_application.add_handler(CallbackQueryHandler(handlers.inline_keyboard_handler))
        
        # Register text registration / passive sentiment monitoring middleware
        telegram_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.auto_register_middleware))
        
        # Pass telegram application reference to api router for cross-communication
        routes.telegram_app = telegram_application
        logger.info("Telegram Bot handlers registered successfully.")
    except Exception as e:
        logger.error(f"[ERROR] Failed to initialize Telegram Bot: {e}")
        telegram_application = None

# Connect API Routes
app.include_router(routes.router, prefix="/api")

# Mount Dashboard Static Files at Root
web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
if os.path.exists(web_dir):
    app.mount("/", StaticFiles(directory=web_dir, html=True), name="static")
    logger.info(f"Mounted static web files from {web_dir}")
else:
    logger.error(f"[ERROR] Web directory not found at {web_dir}. Dashboard UI will not be hosted.")

# Hook Bot Lifecycles into FastAPI events for concurrent asyncio running
@app.on_event("startup")
async def startup_event():
    if telegram_application:
        logger.info("Starting Telegram Bot long-polling loop...")
        await telegram_application.initialize()
        await telegram_application.start()
        await telegram_application.updater.start_polling()
        logger.info("Telegram Bot is online and listening!")
        
        # Register command list in Telegram menu button
        try:
            from telegram import BotCommand
            await telegram_application.bot.set_my_commands([
                BotCommand("start", "Register & show welcome guide"),
                BotCommand("tasks", "List active project tasks"),
                BotCommand("stats", "Show team reliability leaderboard"),
                BotCommand("standup", "Generate AI summary of recent chat"),
                BotCommand("receipt", "Export contribution receipt"),
                BotCommand("analyze", "Parse rubric text into tasks")
            ])
            logger.info("Telegram Bot command menu set successfully.")
            
            # Set bot description (shown before starting the bot)
            bot_description = (
                "🔄 Gradeline AI (SyncUp) is the ultimate accountability bot for student group projects!\n\n"
                "I help you:\n"
                "• Parse assignment rubrics & syllabi into tasks (/analyze)\n"
                "• Claim tasks conversational style & earn XP (/claim)\n"
                "• Check team leaderboard scores (/stats)\n"
                "• Get AI standup summaries of chat logs (/standup)\n"
                "• Send anonymous gentle check-ins to slacking peers (/nudge)\n"
                "• Export project receipts for contribution proof (/receipt)\n\n"
                "Add me to your group chat to sync up! 🤝"
            )
            await telegram_application.bot.set_my_description(description=bot_description)
            logger.info("Telegram Bot description set successfully.")
            
            # Set bot short description (shown on bot profile)
            bot_short_desc = "🔄 Gradeline AI (SyncUp) tracks deliverables, parses rubrics, balances workloads, and nudges teammates."
            await telegram_application.bot.set_my_short_description(short_description=bot_short_desc)
            logger.info("Telegram Bot short description set successfully.")
        except Exception as menu_err:
            logger.error(f"[ERROR] Failed to set command menu/descriptions: {menu_err}")
        
        # Start background accountability loop (checks tasks due within 24h)
        asyncio.create_task(scheduler.start_accountability_loop(telegram_application, interval_seconds=3600))
    else:
        logger.warning("[WARNING] Running API and Dashboard in standalone simulation mode (No live Telegram connection).")

@app.on_event("shutdown")
async def shutdown_event():
    if telegram_application:
        logger.info("Stopping Telegram Bot...")
        await telegram_application.updater.stop()
        await telegram_application.stop()
        await telegram_application.shutdown()
        logger.info("Telegram Bot stopped.")

if __name__ == "__main__":
    # Host on all interfaces on the port assigned by the system (fallback to 8000)
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting SyncUp AI FastAPI backend & Web server on http://0.0.0.0:{port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
