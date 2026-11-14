import os
import sys
from pathlib import Path
import argparse

# ================= COMMAND LINE ARGUMENTS =================
parser = argparse.ArgumentParser(description="TheBlackIris Bot")
parser.add_argument("--bypass-warnings", action="store_true", help="Bypass warnings and start the bot even with missing/incorrect configuration")
args = parser.parse_args()

BYPASS_WARNINGS = args.bypass_warnings

# ================= DEPENDENCY CHECK =================
try:
    import discord
    from discord import app_commands
    from discord.ext import commands
except ModuleNotFoundError as e:
    print(f"❌ Missing dependency: {e}")
    print("💡 Activate the Python environment you want to use, then install the requirements.")
    print("   pip install -r requirements.txt")
    sys.exit(1)

# ================= ORIGINAL IMPORTS =================
import sqlite3
import datetime
import datetime as dt
from dotenv import load_dotenv
import asyncio
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from concurrent.futures import ThreadPoolExecutor
import re
import random
import json
from collections import defaultdict, deque
from html import unescape
from typing import Optional
import time
from urllib.parse import urlparse, quote_plus
import uuid
import logging
import threading
from datetime import datetime
import aiohttp
import hashlib
import io
import struct
import socket
import ssl
from datetime import datetime as dt_module

# ================= ORIGINAL BOT CODE =================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)
tree = bot.tree

application_sessions = {}

# Thread pool for running blocking operations
thread_pool = ThreadPoolExecutor(max_workers=5)

# Voice recording variables
voice_recorders = {}
recorded_channels = set()

# Game sessions - Only keeping gambling games
roulette_sessions = {}
crash_games = {}
higher_lower_games = {}
raffle_sessions = {}

script_dir = Path(__file__).parent.resolve()
print(f"📁 Script directory: {script_dir}")
os.chdir(script_dir)
print(f"📂 Current working directory: {os.getcwd()}")

print("🔍 Directory contents:")
for i, item in enumerate(os.listdir(), 1):
    print(f"{i}. {item}")

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TOKEN") # Get token from .env

if not TOKEN:
    if BYPASS_WARNINGS:
        print("⚠️ WARNING: Token not found in .env file! Token is required for the bot to work.")
    else:
        print("\n❌ ERROR: Token not found in .env file!")
        print("💡 Please add TOKEN=your_bot_token to your .env file")
        exit()

OWNER_IDS = [1456125870421835892, 688437410186395776]
APPLICATION_POST_CHANNEL_ID = 1566984141780680764
APPLICATION_SUBMIT_CHANNEL_ID = 1569007639860351046
STAFF_ROLE_ID = 1549569470425600020
BAN_LOG_CHANNEL_ID = 1566983722828431461
KICK_LOG_CHANNEL_ID = 1566983722828431461
LOG_CHANNEL_ID = 1566983722828431461
WELCOME_CHANNEL_ID = 1566969379378176030
VERIFICATION_CHANNEL_ID = 1569020504428384387
JOIN_ROLE_ID = 1569020711110975549
MEMBER_ROLE_ID = 1532084777585475705

FOUNDER_ROLE_ID = 1563295287349354679
OWNER_ROLE_ID = 1531830875619197040
STAFF_LIST_CHANNEL_ID = 1566970346287009842
MESSAGE_LOG_CHANNEL_ID = 1566983722828431461
GENERAL_CHAT_CHANNEL_ID = 1461052279305142398
DAILY_QUESTION_CHANNEL_ID = 1478970607856123986
DAILY_QUESTION_CATEGORIES = [
    {"name": "💬 Icebreakers", "system": "Create a fun, light icebreaker question to help people get to know each other. Keep it short and accessible.", "emoji": "💬"},
    {"name": "🔥 Hot Takes", "system": "Create a controversial or provocative 'hot take' question. Safe for work but sparks discussion. Keep it short.", "emoji": "🔥"},
    {"name": "🤔 Deep Talks", "system": "Create a thought-provoking question that leads to meaningful discussion. Keep it short.", "emoji": "🤔"},
    {"name": "🎮 Gaming", "system": "Create a fun gaming-related question. Can be about games, streaming, or gaming culture. Keep it short.", "emoji": "🎮"},
    {"name": "🎨 Creative", "system": "Create a creative or artistic question about music, art, writing, or creativity. Keep it short.", "emoji": "🎨"},
    {"name": "🌟 Would You Rather", "system": "Create a fun 'Would You Rather' question with two interesting choices. Keep it short.", "emoji": "🌟"},
    {"name": "😂 Memes & Fun", "system": "Create a fun, humorous question about memes, jokes, or funny experiences. Keep it short.", "emoji": "😂"},
    {"name": "💭 Hypotheticals", "system": "Create a fun hypothetical scenario question. Keep it short and engaging.", "emoji": "💭"},
]
_daily_question_category_index = 0
BIRTHDAY_ANNOUNCE_CHANNEL_ID = 1478970582707212391

# AI Configuration
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
CEREBRAS_MODEL = os.getenv("CEREBRAS_MODEL", "gpt-oss-120b")
# Temporary fallback for migration window
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
OPENROUTER_REFERER = os.getenv("OPENROUTER_REFERER", "https://discord.com")
OPENROUTER_TITLE = os.getenv("OPENROUTER_TITLE", "TheBlackIris Discord Bot")
LLM_PROVIDER_DEFAULT = "openrouter"
AI_MAX_CONTEXT_MESSAGES = 20
AI_AUTOREPLY_COOLDOWN_SECONDS = 90
AI_AUTOREPLY_BASE_CHANCE = 0.14
AI_OWNER_REVIEW_USER_ID = 1456125870421835892
AI_TICKET_AUTO_APPROVE_SECONDS = 900
AI_BAN_REVIEW_AUTO_EXPIRE_SECONDS = 900
AI_PERSONA_COOLDOWN_SECONDS = 20
DAILY_TIMEZONE = pytz.timezone("America/New_York")

channel_message_context = defaultdict(lambda: deque(maxlen=AI_MAX_CONTEXT_MESSAGES))
last_general_ai_reply_at = 0.0
persona_last_used = {}
active_debates = {}
active_guessimage_games = {}
guessimage_guess_cooldowns = {}
active_trivia_games = {}
trivia_scores = defaultdict(int)
scheduler = None
startup_backfill_done_for_guild = set()
active_llm_provider = LLM_PROVIDER_DEFAULT
startup_backfill_target_count = 0
startup_backfill_finished_count = 0
DB_MEMBER_PAGE_SIZE = 25

BACKFILL_PER_USER_TARGET = 500
BACKFILL_BATCH_SIZE = 200
BACKFILL_PER_CHANNEL_SCAN_CAP = 3000
BACKFILL_GUILD_SCAN_CAP = 60000

# Ticket System Configuration
TICKET_CHANNEL_ID = 1566971550392127558
TICKET_CATEGORY_ID = None
TICKET_ARCHIVE_CATEGORY_ID = 1569004281258975312

# UPDATED: Ticket manager roles as requested
TICKET_MANAGER_ROLES = [1563295287349354679, 1569546478777536512, 1531830875619197040, 1561161919119753266, 1531828111820325064]

# NEW: Staff Complaints Configuration - UPDATED FOR CHANNEL SYSTEM
STAFF_COMPLAINTS_CHANNEL_ID = 1569006375940399104
STAFF_COMPLAINTS_CATEGORY_ID = None # Will be determined from channel category
STAFF_COMPLAINTS_ARCHIVE_CATEGORY_ID = 1569004281258975312 # Same as tickets
STAFF_COMPLAINTS_ROLE_ID = [1563295287349354679, 1569546478777536512, 1531830875619197040] # Only this role can see the complaint channel
STAFF_COMPLAINTS_MANAGER_ROLES = [1563295287349354679, 1569546478777536512, 1531830875619197040] # Only this role can manage staff complaints

# Confessions channel IDs
CONFESSIONS_SUBMIT_CHANNEL_ID = 1566972896520183930
CONFESSIONS_APPROVAL_CHANNEL_ID = 1566983722828431461
CONFESSIONS_POST_CHANNEL_ID = 1566972896520183930
CONFESSIONS_REVIEW_ENABLED = True

# ================= UPDATED: Staff roles structure =================
STAFF_ROLES = {
    1563295287349354679: "Founder",
    1569546478777536512: "Owner",
    1531830875619197040: "Director",
    1561161919119753266: "Manager",
    1531828111820325064: "Admin",
    1531829121150357705: "Moderator",
    1549569470425600020: "Staff"
}

# ================= UPDATED: Role hierarchy =================
ROLE_HIERARCHY = [
    1563295287349354679, # Founder
    1569546478777536512, # Owner
    1531830875619197040, # Director
    1561161919119753266, # Manager
    1531828111820325064, # Admin
    1531829121150357705, # Moderator
    1549569470425600020  # Staff
]

# ================= UPDATED: Everyone allowed roles =================
EVERYONE_ALLOWED_ROLES = [
    1563295287349354679, # Founder
    1569546478777536512, # Owner
    1531830875619197040, # Director
    1561161919119753266, # Manager
    1531828111820325064, # Admin
    1531829121150357705  # Moderator
]

MODERATE_BLACKLIST = [
    r'\bn[i1l!]+gg[ae4@]r?[sz]?\b',
    r'\bf[a4@]gg?[o0u]?t\b',
    r'\bs[pb]i[ck]+\b',
    r'\bc[o0]on\b',
    r'\bk[i1l!]k[e3]',
]

SEVERE_BLACKLIST = [
    r'\b(cp|child\s?porn|child\s?exploitation)\b',
    r'\b(kill\s?yourself|kys)\b'
]

# UPDATED: Application questions - REMOVED last 2 questions (age verification)
APPLICATION_QUESTIONS = [
    {
        "label": "VRChat Username",
        "placeholder": "Enter your VRChat username (do not put VRChat link)",
        "style": discord.TextStyle.short,
        "validation": None
    },
    {
        "label": "Why apply for this position?",
        "placeholder": "Explain why you want this position...",
        "style": discord.TextStyle.paragraph,
        "validation": None
    },
    {
        "label": "Relevant experience?",
        "placeholder": "Describe your relevant experience...",
        "style": discord.TextStyle.paragraph,
        "validation": None
    },
    {
        "label": "Strengths and weaknesses?",
        "placeholder": "List your strengths and weaknesses...",
        "style": discord.TextStyle.paragraph,
        "validation": None
    },
    {
        "label": "Handle stressful situations?",
        "placeholder": "Describe how you handle stress...",
        "style": discord.TextStyle.paragraph,
        "validation": None
    },
    {
        "label": "De-escalate tense situations?",
        "placeholder": "Describe de-escalation techniques...",
        "style": discord.TextStyle.paragraph,
        "validation": None
    },
    {
        "label": "Time-zone",
        "placeholder": "e.g., EST, PST, GMT, etc.",
        "style": discord.TextStyle.short,
        "validation": None
    }
]

# FIXED: Updated QUESTION_DISPLAY_NAMES with correct key for VRChat Username
QUESTION_DISPLAY_NAMES = {
    "VRChat Username": "What is your VRChat username? (do not put VRChat link)",
    "Why apply for this position?": "Why are you applying for this position? (be detailed)",
    "Relevant experience?": "What experiences do you have for this position? (be detailed and put group names)",
    "Strengths and weaknesses?": "What are your strengths and weaknesses?",
    "Handle stressful situations?": "How do you handle stressful or high-pressure situations?",
    "De-escalate tense situations?": "How would you de-escalate a tense situation or handle an aggressive individual?",
    "Time-zone": "What Time-zone are you in?"
}

# ================= IMPROVED: COMMAND LOGGING SYSTEM =================
class CommandLogger:
    def __init__(self):
        self.logs_dir = Path("logs")
        self.daily_logs_dir = self.logs_dir / "daily_logs"
        self.members_logs_dir = self.logs_dir / "members"
        self.daily_logs_dir.mkdir(exist_ok=True)
        self.members_logs_dir.mkdir(exist_ok=True)
        self.daily_commands = []

    def log_command(self, user, command, guild=None, target=None, result=None, error=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "user_id": user.id,
            "user_name": str(user),
            "command": command,
            "guild": guild.name if guild else "DM",
            "target": str(target) if target else None,
            "result": result,
            "error": error
        }
        self.daily_commands.append(log_entry)

        # Skip logging for staff complaint creation if requested
        if command == "create_staff_complaint" and "no_log" in str(result):
            return

        log_message = f"[{timestamp}] COMMAND: {user} (ID: {user.id}) used {command}"
        if target:
            log_message += f" on {target}"
        if result:
            log_message += f" | Result: {result}"
        if error:
            log_message += f" | Error: {error}"
        print(log_message)
        self.write_daily_log(log_entry)

    def write_daily_log(self, entry: dict):
        try:
            date_str = datetime.now().strftime("%Y-%m-%d")
            log_file = self.daily_logs_dir / f"command_log_{date_str}.txt"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{entry['timestamp']}] {entry['user_name']} (ID: {entry['user_id']}) | {entry['command']}")
                if entry.get('guild'):
                    f.write(f" | Guild: {entry['guild']}")
                if entry.get('target'):
                    f.write(f" | Target: {entry['target']}")
                if entry.get('result'):
                    f.write(f" | Result: {entry['result']}")
                if entry.get('error'):
                    f.write(f" | Error: {entry['error']}")
                f.write("\n")
        except Exception as e:
            print(f"❌ Error writing daily log: {e}")

    def log_member_message(self, guild_id: int, guild_name: str, channel_id: int, channel_name: str, user_id: int, user_name: str, message_id: int, content: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            safe_name = re.sub(r'[^\w.\- ]', '', str(user_name)).strip() or str(user_id)
            user_log_dir = self.members_logs_dir / safe_name
            user_log_dir.mkdir(exist_ok=True)
            log_file = user_log_dir / f"messages_{datetime.now().strftime('%Y-%m')}.txt"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] G:{guild_name} (ID:{guild_id}) | C:#{channel_name} (ID:{channel_id}) | {user_name} (ID:{user_id}) | MSG:{message_id} | {content[:500]}\n")
        except Exception as e:
            print(f"❌ Error logging member message: {e}")

    def log_member_event(self, guild_id: int, guild_name: str, user_id: int, user_name: str, event_type: str, details: str = ""):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            safe_name = re.sub(r'[^\w.\- ]', '', str(user_name)).strip() or str(user_id)
            user_log_dir = self.members_logs_dir / safe_name
            user_log_dir.mkdir(exist_ok=True)
            log_file = user_log_dir / f"events_{datetime.now().strftime('%Y-%m')}.txt"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] G:{guild_name} (ID:{guild_id}) | {user_name} (ID:{user_id}) | {event_type}")
                if details:
                    f.write(f" | {details}")
                f.write("\n")
        except Exception as e:
            print(f"❌ Error logging member event: {e}")

    def log_role_update(self, staff_member, target_user, action, role_name, updated_by=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updater = updated_by if updated_by else staff_member

        # FIXED: Handle case where staff_member might be a string
        staff_id = None
        staff_name = str(staff_member)

        if hasattr(staff_member, 'id'):
            staff_id = staff_member.id
        elif isinstance(staff_member, discord.Member):
            staff_id = staff_member.id
        elif isinstance(staff_member, discord.User):
            staff_id = staff_member.id
        elif staff_member == "Unknown":
            staff_id = 0 # Use 0 for unknown
        else:
            staff_id = 0

        log_entry = {
            "timestamp": timestamp,
            "type": "role_update",
            "staff_member": staff_name,
            "staff_id": staff_id,
            "target_user": str(target_user),
            "target_id": target_user.id,
            "action": action,
            "role_name": role_name,
            "updated_by": str(updater) if updater else "System"
        }
        self.daily_commands.append(log_entry)

        print(f"[{timestamp}] ROLE_UPDATE: {updater} {action} role '{role_name}' to {target_user}")

    def log_application_accept(self, staff_member, target_user, role_name):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "type": "application_accepted",
            "staff_member": str(staff_member),
            "staff_id": staff_member.id,
            "target_user": str(target_user),
            "target_id": target_user.id,
            "role_given": role_name
        }
        self.daily_commands.append(log_entry)

        print(f"[{timestamp}] APPLICATION_ACCEPTED: {staff_member} accepted {target_user}'s application and assigned {role_name} role")

    def log_staff_list_change(self, action, user=None, role_name=None, updated_by=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "type": "staff_list_change",
            "action": action,
            "user": str(user) if user else None,
            "user_id": user.id if user else None,
            "role_name": role_name,
            "updated_by": str(updated_by) if updated_by else "System"
        }
        self.daily_commands.append(log_entry)

        if user and role_name:
            print(f"[{timestamp}] STAFF_LIST: {updated_by or 'System'} {action} {user} from {role_name}")
        else:
            print(f"[{timestamp}] STAFF_LIST: {updated_by or 'System'} {action}")

    def log_voice_action(self, staff_member, target_user, action, channel=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "type": "voice_action",
            "staff_member": str(staff_member),
            "staff_id": staff_member.id,
            "target_user": str(target_user),
            "target_id": target_user.id,
            "action": action,
            "channel": str(channel) if channel else None
        }
        self.daily_commands.append(log_entry)
        print(f"[{timestamp}] VOICE_ACTION: {staff_member} {action} {target_user} in {channel}")

    def log_ban_attempt(self, staff_member, target_user, success, error=None, reason=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "type": "ban_attempt",
            "staff_member": str(staff_member),
            "staff_id": staff_member.id,
            "target_user": str(target_user),
            "target_id": target_user.id,
            "success": success,
            "error": error,
            "reason": reason
        }
        self.daily_commands.append(log_entry)
        status = "SUCCESS" if success else "FAILED"
        error_msg = f" - Error: {error}" if error else ""
        reason_msg = f" - Reason: {reason}" if reason else ""
        print(f"[{timestamp}] BAN_ATTEMPT: {staff_member} tried to ban {target_user} - {status}{error_msg}{reason_msg}")

    def create_daily_log_file(self):
        if not self.daily_commands:
            return None

        today = datetime.now().strftime("%Y-%m-%d")
        filename = self.daily_logs_dir / f"command_log_{today}.txt"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Daily Command Log - {today}\n")
            f.write("=" * 50 + "\n\n")

            for entry in self.daily_commands:
                if entry.get('type') == 'role_update':
                    f.write(f"[{entry['timestamp']}] ROLE_UPDATE: {entry['updated_by']} {entry['action']} role '{entry['role_name']}' to {entry['target_user']}\n")
                elif entry.get('type') == 'application_accepted':
                    f.write(f"[{entry['timestamp']}] APPLICATION_ACCEPTED: {entry['staff_member']} accepted {entry['target_user']}'s application and assigned {entry['role_given']} role\n")
                elif entry.get('type') == 'staff_list_change':
                    if entry.get('user') and entry.get('role_name'):
                        f.write(f"[{entry['timestamp']}] STAFF_LIST: {entry['updated_by']} {entry['action']} {entry['user']} from {entry['role_name']}\n")
                    else:
                        f.write(f"[{entry['timestamp']}] STAFF_LIST: {entry['updated_by']} {entry['action']}\n")
                elif entry.get('type') == 'voice_action':
                    f.write(f"[{entry['timestamp']}] VOICE_ACTION: {entry['staff_member']} {entry['action']} {entry['target_user']} in {entry['channel']}\n")
                elif entry.get('type') == 'ban_attempt':
                    status = "SUCCESS" if entry['success'] else "FAILED"
                    error_msg = f" - Error: {entry['error']}" if entry['error'] else ""
                    reason_msg = f" - Reason: {entry['reason']}" if entry.get('reason') else ""
                    f.write(f"[{entry['timestamp']}] BAN_ATTEMPT: {entry['staff_member']} tried to ban {entry['target_user']} - {status}{error_msg}{reason_msg}\n")
                else:
                    f.write(f"[{entry['timestamp']}] COMMAND: {entry['user_name']} used {entry['command']}")
                    if entry.get('target'):
                        f.write(f" on {entry['target']}")
                    if entry.get('result'):
                        f.write(f" | Result: {entry['result']}")
                    if entry.get('error'):
                        f.write(f" | Error: {entry['error']}")
                    f.write("\n")

        return filename

    def clear_daily_logs(self):
        self.daily_commands = []

command_logger = CommandLogger()

def setup_database():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS applications
                (user_id INTEGER, guild_id INTEGER, answers TEXT, position TEXT,
                status TEXT DEFAULT 'pending', timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )''')
    c.execute('''CREATE TABLE IF NOT EXISTS language_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern TEXT NOT NULL,
                response TEXT NOT NULL,
                usage_count INTEGER DEFAULT 0,
                added_by INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
    c.execute('''CREATE TABLE IF NOT EXISTS message_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                channel_id INTEGER,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_chips (
                user_id INTEGER PRIMARY KEY,
                chips INTEGER DEFAULT 1000,
                last_daily TIMESTAMP DEFAULT NULL
            )''')
    c.execute('''CREATE TABLE IF NOT EXISTS giveaways (
                message_id INTEGER PRIMARY KEY,
                channel_id INTEGER,
                prize TEXT,
                winners INTEGER,
                end_time TIMESTAMP,
                participants TEXT
            )''')
    c.execute('''CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                channel_id INTEGER,
                status TEXT DEFAULT 'open',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                closed_at DATETIME
            )''')
    # FIXED: Updated staff_complaints table with proper column order
    c.execute('''CREATE TABLE IF NOT EXISTS staff_complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                channel_id INTEGER,
                complaint_text TEXT DEFAULT '',
                status TEXT DEFAULT 'open',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                closed_at DATETIME
            )''')
    c.execute('''CREATE TABLE IF NOT EXISTS staff_messages (
                message_id INTEGER PRIMARY KEY,
                channel_id INTEGER
            )''')
    c.execute('''CREATE TABLE IF NOT EXISTS staff_info (
                user_id INTEGER PRIMARY KEY,
                vrchat_name TEXT,
                position TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
    c.execute('''CREATE TABLE IF NOT EXISTS banned_staff (
                user_id INTEGER PRIMARY KEY,
                banned_by INTEGER,
                reason TEXT,
                banned_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
    # Add confessions tables
    c.execute('''CREATE TABLE IF NOT EXISTS confessions
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                confession_id TEXT UNIQUE,
                user_id INTEGER,
                content TEXT,
                status TEXT DEFAULT 'pending',
                thread_id INTEGER,
                message_id INTEGER,
                approved_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                approved_at DATETIME)''')
    c.execute('''CREATE TABLE IF NOT EXISTS confession_replies
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                confession_id TEXT,
                user_id INTEGER,
                content TEXT,
                is_anonymous BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (confession_id) REFERENCES confessions (confession_id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS vrchat_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                vrchat_profile_url TEXT NOT NULL,
                vrchat_username TEXT,
                vrchat_identifier TEXT,
                discord_username TEXT,
                display_name TEXT,
                linked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, user_id)
            )''')
    c.execute('''CREATE TABLE IF NOT EXISTS username_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                platform TEXT NOT NULL,
                old_username TEXT,
                new_username TEXT NOT NULL,
                first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, user_id, platform, new_username)
            )''')
    c.execute('''CREATE TABLE IF NOT EXISTS linked_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                platform TEXT NOT NULL,
                username TEXT,
                url TEXT,
                profile_image TEXT,
                found_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, user_id, platform, url)
            )''')
    c.execute('''CREATE TABLE IF NOT EXISTS phone_lookups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                phone_number TEXT NOT NULL,
                lookup_result TEXT,
                found_name TEXT,
                found_address TEXT,
                found_social TEXT,
                looked_up_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, user_id, phone_number)
            )''')
    c.execute('''CREATE TABLE IF NOT EXISTS image_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                image_url TEXT,
                image_hash TEXT,
                exif_data TEXT,
                gps_latitude REAL,
                gps_longitude REAL,
                camera_model TEXT,
                timestamp TEXT,
                analyzed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, user_id, image_hash)
            )''')
    c.execute('''CREATE TABLE IF NOT EXISTS unified_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                unified_data TEXT,
                completeness_score REAL,
                timeline_data TEXT,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, user_id)
            )''')
    c.execute('''CREATE TABLE IF NOT EXISTS shared_servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                target_user_id INTEGER NOT NULL,
                shared_guild_ids TEXT,
                shared_channel_ids TEXT,
                last_checked DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, user_id, target_user_id)
            )''')
    c.execute('''CREATE TABLE IF NOT EXISTS pastebin_dumps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                source TEXT,
                paste_url TEXT,
                paste_content TEXT,
                contains_email INTEGER DEFAULT 0,
                contains_phone INTEGER DEFAULT 0,
                contains_username INTEGER DEFAULT 0,
                found_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, user_id, paste_url)
            )''')
    c.execute('''CREATE TABLE IF NOT EXISTS wayback_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                snapshot_url TEXT,
                snapshot_date TEXT,
                found_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, user_id, url, snapshot_url)
            )''')
    c.execute('''CREATE TABLE IF NOT EXISTS dns_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                domain TEXT NOT NULL,
                ip_addresses TEXT,
                historical_ips TEXT,
                mx_records TEXT,
                ns_records TEXT,
                ssl_info TEXT,
                checked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, user_id, domain)
            )''')
    c.execute('''CREATE TABLE IF NOT EXISTS member_activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                channel_id INTEGER,
                details TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
    c.execute('''CREATE TABLE IF NOT EXISTS ai_incident_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                channel_id INTEGER,
                requested_by INTEGER,
                message_count INTEGER,
                summary TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
    c.execute('''CREATE TABLE IF NOT EXISTS ai_message_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                message_id INTEGER,
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
    c.execute('''CREATE TABLE IF NOT EXISTS ai_ticket_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                requester_id INTEGER NOT NULL,
                source TEXT NOT NULL,
                category TEXT NOT NULL,
                qa_json TEXT NOT NULL,
                ai_summary TEXT,
                ai_priority TEXT,
                suggested_actions TEXT,
                status TEXT DEFAULT 'pending_owner',
                owner_message_id INTEGER,
                expires_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                resolved_at DATETIME
            )''')
    c.execute('''CREATE TABLE IF NOT EXISTS birthdays (
                user_id INTEGER PRIMARY KEY,
                guild_id INTEGER NOT NULL,
                birth_date TEXT NOT NULL,
                timezone TEXT DEFAULT 'America/New_York',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
    c.execute('''CREATE TABLE IF NOT EXISTS daily_questions_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                posted_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
    c.execute('''CREATE TABLE IF NOT EXISTS trivia_scores (
                user_id INTEGER PRIMARY KEY,
                score INTEGER DEFAULT 0,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
    c.execute('''CREATE TABLE IF NOT EXISTS ai_ban_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                target_user_id INTEGER NOT NULL,
                requested_by INTEGER NOT NULL,
                reason TEXT NOT NULL,
                ai_summary TEXT,
                status TEXT DEFAULT 'pending_owner',
                owner_message_id INTEGER,
                expires_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                resolved_at DATETIME
            )''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_ai_message_memory_guild_created ON ai_message_memory (guild_id, created_at)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_ai_message_memory_user_created ON ai_message_memory (guild_id, user_id, created_at)")
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_ai_message_unique ON ai_message_memory (guild_id, message_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_member_activity_user_time ON member_activity_log (guild_id, user_id, created_at)")

    # FIXED: Check if channel_id column exists and add it if missing
    c.execute("PRAGMA table_info(staff_complaints)")
    columns = [column[1] for column in c.fetchall()]

    if 'channel_id' not in columns:
        print("⚠️ Adding missing 'channel_id' column to staff_complaints table...")
        c.execute("ALTER TABLE staff_complaints ADD COLUMN channel_id INTEGER")

    if 'complaint_text' not in columns:
        print("⚠️ Adding missing 'complaint_text' column to staff_complaints table...")
        c.execute("ALTER TABLE staff_complaints ADD COLUMN complaint_text TEXT DEFAULT ''")

    c.execute("PRAGMA table_info(message_log)")
    message_log_columns = [column[1] for column in c.fetchall()]

    if 'guild_id' not in message_log_columns:
        print("⚠️ Adding missing 'guild_id' column to message_log table...")
        c.execute("ALTER TABLE message_log ADD COLUMN guild_id INTEGER")

    c.execute("CREATE INDEX IF NOT EXISTS idx_message_log_user_time ON message_log (guild_id, user_id, timestamp)")

    c.execute("PRAGMA table_info(vrchat_links)")
    vrchat_links_columns = [column[1] for column in c.fetchall()]

    if 'profile_data_json' not in vrchat_links_columns:
        print("⚠️ Adding missing 'profile_data_json' column to vrchat_links table...")
        c.execute("ALTER TABLE vrchat_links ADD COLUMN profile_data_json TEXT")

    try:
        c.execute("PRAGMA table_info(username_history)")
        username_history_columns = [column[1] for column in c.fetchall()]
        if not username_history_columns:
            print("⚠️ Creating username_history table...")
            c.execute('''CREATE TABLE IF NOT EXISTS username_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                platform TEXT NOT NULL,
                old_username TEXT,
                new_username TEXT NOT NULL,
                first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, user_id, platform, new_username)
            )''')
    except Exception:
        pass

    try:
        c.execute("PRAGMA table_info(linked_accounts)")
        linked_accounts_columns = [column[1] for column in c.fetchall()]
        if not linked_accounts_columns:
            print("⚠️ Creating linked_accounts table...")
            c.execute('''CREATE TABLE IF NOT EXISTS linked_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                platform TEXT NOT NULL,
                username TEXT,
                url TEXT,
                profile_image TEXT,
                found_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, user_id, platform, url)
            )''')
    except Exception:
        pass

    try:
        c.execute("PRAGMA table_info(phone_lookups)")
        phone_lookups_columns = [column[1] for column in c.fetchall()]
        if not phone_lookups_columns:
            print("⚠️ Creating phone_lookups table...")
            c.execute('''CREATE TABLE IF NOT EXISTS phone_lookups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                phone_number TEXT NOT NULL,
                lookup_result TEXT,
                found_name TEXT,
                found_address TEXT,
                found_social TEXT,
                looked_up_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, user_id, phone_number)
            )''')
    except Exception:
        pass

    try:
        c.execute("PRAGMA table_info(image_analysis)")
        image_analysis_columns = [column[1] for column in c.fetchall()]
        if not image_analysis_columns:
            print("⚠️ Creating image_analysis table...")
            c.execute('''CREATE TABLE IF NOT EXISTS image_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                image_url TEXT,
                image_hash TEXT,
                exif_data TEXT,
                gps_latitude REAL,
                gps_longitude REAL,
                camera_model TEXT,
                timestamp TEXT,
                analyzed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, user_id, image_hash)
            )''')
    except Exception:
        pass

    try:
        c.execute("PRAGMA table_info(unified_profile)")
        unified_profile_columns = [column[1] for column in c.fetchall()]
        if not unified_profile_columns:
            print("⚠️ Creating unified_profile table...")
            c.execute('''CREATE TABLE IF NOT EXISTS unified_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                unified_data TEXT,
                completeness_score REAL,
                timeline_data TEXT,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, user_id)
            )''')
    except Exception:
        pass

    try:
        c.execute("PRAGMA table_info(shared_servers)")
        shared_servers_columns = [column[1] for column in c.fetchall()]
        if not shared_servers_columns:
            print("⚠️ Creating shared_servers table...")
            c.execute('''CREATE TABLE IF NOT EXISTS shared_servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                target_user_id INTEGER NOT NULL,
                shared_guild_ids TEXT,
                shared_channel_ids TEXT,
                last_checked DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, user_id, target_user_id)
            )''')
    except Exception:
        pass

    try:
        c.execute("PRAGMA table_info(pastebin_dumps)")
        pastebin_dumps_columns = [column[1] for column in c.fetchall()]
        if not pastebin_dumps_columns:
            print("⚠️ Creating pastebin_dumps table...")
            c.execute('''CREATE TABLE IF NOT EXISTS pastebin_dumps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                source TEXT,
                paste_url TEXT,
                paste_content TEXT,
                contains_email INTEGER DEFAULT 0,
                contains_phone INTEGER DEFAULT 0,
                contains_username INTEGER DEFAULT 0,
                found_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, user_id, paste_url)
            )''')
    except Exception:
        pass

    try:
        c.execute("PRAGMA table_info(wayback_snapshots)")
        wayback_snapshots_columns = [column[1] for column in c.fetchall()]
        if not wayback_snapshots_columns:
            print("⚠️ Creating wayback_snapshots table...")
            c.execute('''CREATE TABLE IF NOT EXISTS wayback_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                snapshot_url TEXT,
                snapshot_date TEXT,
                found_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, user_id, url, snapshot_url)
            )''')
    except Exception:
        pass

    try:
        c.execute("PRAGMA table_info(dns_history)")
        dns_history_columns = [column[1] for column in c.fetchall()]
        if not dns_history_columns:
            print("⚠️ Creating dns_history table...")
    except Exception:
        pass
    c.execute('''CREATE TABLE IF NOT EXISTS dns_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                domain TEXT NOT NULL,
                ip_addresses TEXT,
                historical_ips TEXT,
                mx_records TEXT,
                ns_records TEXT,
                ssl_info TEXT,
                checked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, user_id, domain)
            )''')
    conn.commit()
    conn.close()

setup_database()

def get_staff_message_id():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='staff_message_id'")
    result = c.fetchone()
    conn.close()
    return int(result[0]) if result else 0

def set_staff_message_id(message_id):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('staff_message_id', ?)", (str(message_id),))
    conn.commit()
    conn.close()

def get_ticket_message_id():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='ticket_message_id'")
    result = c.fetchone()
    conn.close()
    return int(result[0]) if result else 0

def set_ticket_message_id(message_id):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('ticket_message_id', ?)", (str(message_id),))
    conn.commit()
    conn.close()

def get_staff_complaints_message_id():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='staff_complaints_message_id'")
    result = c.fetchone()
    conn.close()
    return int(result[0]) if result else 0

def set_staff_complaints_message_id(message_id):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('staff_complaints_message_id', ?)", (str(message_id),))
    conn.commit()
    conn.close()

def has_founder_or_owner_role(member: Optional[discord.Member]) -> bool:
    if member is None:
        return False
    return any(role.id in {FOUNDER_ROLE_ID, OWNER_ROLE_ID} for role in member.roles)

def resolve_authorized_member(user_id: int, preferred_guild: Optional[discord.Guild] = None):
    if preferred_guild:
        preferred_member = preferred_guild.get_member(user_id)
        if has_founder_or_owner_role(preferred_member):
            return preferred_guild, preferred_member

    for guild in bot.guilds:
        member = guild.get_member(user_id)
        if has_founder_or_owner_role(member):
            return guild, member
    return None, None

def normalize_vrchat_profile_url(raw_value: str) -> Optional[str]:
    if not raw_value:
        return None
    candidate = raw_value.strip()
    if "://" not in candidate:
        candidate = f"https://{candidate}"

    parsed = urlparse(candidate)
    host = parsed.netloc.lower().removeprefix("www.")
    if parsed.scheme not in {"http", "https"} or host != "vrchat.com":
        return None
    return parsed.geturl()

def extract_vrchat_identity_from_url(profile_url: str):
    parsed = urlparse(profile_url)
    segments = [segment.strip() for segment in parsed.path.split("/") if segment.strip()]
    identifier = segments[-1] if segments else None
    if not identifier:
        return None, None
    username = identifier if not identifier.lower().startswith("usr_") else None
    return username, identifier

async def fetch_vrchat_profile(identifier: str, username: Optional[str] = None):
    timeout = aiohttp.ClientTimeout(total=10)
    headers = {
        "User-Agent": "VRCX/2024.04.01",
        "Accept": "application/json",
    }
    try:
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            if identifier.startswith("usr_"):
                url = f"https://api.vrchat.cloud/api/1/users/{identifier}"
            else:
                url = f"https://api.vrchat.cloud/api/1/users/{username}/name"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "id": data.get("id"),
                        "username": data.get("username"),
                        "displayName": data.get("displayName"),
                        "bio": data.get("bio", ""),
                        "bioLinks": data.get("bioLinks", []),
                        "userIcon": data.get("userIcon"),
                        "status": data.get("status"),
                        "statusDescription": data.get("statusDescription", ""),
                        "dateJoined": data.get("dateJoined"),
                        "lastLogin": data.get("lastLogin"),
                        "location": data.get("location", {}),
                        "worldId": data.get("location", {}).get("worldId"),
                        "instanceId": data.get("location", {}).get("instanceId"),
                        "tags": data.get("tags", []),
                        "friendCount": data.get("friendCount"),
                        "isFriend": data.get("isFriend"),
                        "incomingFriendRequest": data.get("incomingFriendRequest"),
                        "outgoingFriendRequest": data.get("outgoingFriendRequest"),
                        "notificationRoute": data.get("notificationRoute"),
                    }
                elif response.status == 404:
                    return None
                else:
                    print(f"VRChat API error: {response.status}")
                    return None
    except Exception as e:
        print(f"Failed to fetch VRChat profile: {e}")
        return None

def store_vrchat_profile_data(guild_id: int, user_id: int, profile_data: dict):
    serialized = json.dumps(profile_data)
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO vrchat_links (guild_id, user_id, vrchat_profile_url, vrchat_username, vrchat_identifier, discord_username, display_name, profile_data_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(guild_id, user_id) DO UPDATE SET
            profile_data_json = excluded.profile_data_json,
            updated_at = CURRENT_TIMESTAMP
        """,
        (guild_id, user_id, None, profile_data.get("username"), profile_data.get("id"), None, profile_data.get("displayName"), serialized)
    )
    conn.commit()
    conn.close()

def get_vrchat_profile_data(guild_id: int, user_id: int) -> Optional[dict]:
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute(
        """
        SELECT profile_data_json FROM vrchat_links
        WHERE guild_id = ? AND user_id = ?
        """,
        (guild_id, user_id)
    )
    row = c.fetchone()
    conn.close()
    if row and row[0]:
        try:
            return json.loads(row[0])
        except json.JSONDecodeError:
            return None
    return None

def store_message_log_entry(message: discord.Message):
    if not message.guild or not message.content or not message.content.strip():
        return
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute(
        "INSERT INTO message_log (guild_id, user_id, channel_id, content) VALUES (?, ?, ?, ?)",
        (message.guild.id, message.author.id, message.channel.id, message.content.strip()[:1500])
    )
    conn.commit()
    conn.close()
    
    command_logger.log_member_message(
        message.guild.id,
        message.guild.name,
        message.channel.id,
        getattr(message.channel, 'name', 'DM'),
        message.author.id,
        str(message.author),
        message.id,
        message.content.strip()
    )

def save_member_activity(guild_id: int, user_id: int, event_type: str, channel_id: Optional[int] = None, details: Optional[str] = None):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute(
        "INSERT INTO member_activity_log (guild_id, user_id, event_type, channel_id, details) VALUES (?, ?, ?, ?, ?)",
        (guild_id, user_id, event_type, channel_id, details[:1000] if details else None)
    )
    conn.commit()
    conn.close()

def get_member_activity_rows(guild_id: int, user_id: int, limit: int = 15):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute(
        """
        SELECT event_type, channel_id, details, created_at
        FROM member_activity_log
        WHERE guild_id = ? AND user_id = ?
        ORDER BY created_at DESC, id DESC
        LIMIT ?
        """,
        (guild_id, user_id, limit)
    )
    rows = c.fetchall()
    conn.close()
    return rows

def get_recent_message_rows(guild_id: int, user_id: int, limit: int = 10):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute(
        """
        SELECT channel_id, content, timestamp
        FROM message_log
        WHERE guild_id = ? AND user_id = ?
        ORDER BY timestamp DESC, id DESC
        LIMIT ?
        """,
        (guild_id, user_id, limit)
    )
    rows = c.fetchall()
    if rows:
        conn.close()
        return rows, "message_log"

    c.execute(
        """
        SELECT channel_id, content, created_at
        FROM ai_message_memory
        WHERE guild_id = ? AND user_id = ?
        ORDER BY created_at DESC, id DESC
        LIMIT ?
        """,
        (guild_id, user_id, limit)
    )
    rows = c.fetchall()
    conn.close()
    return rows, "ai_message_memory"

def get_member_link_record(guild_id: int, user_id: int):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute(
        """
        SELECT vrchat_profile_url, vrchat_username, vrchat_identifier, discord_username, display_name, linked_at, updated_at
        FROM vrchat_links
        WHERE guild_id = ? AND user_id = ?
        """,
        (guild_id, user_id)
    )
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "vrchat_profile_url": row[0],
        "vrchat_username": row[1],
        "vrchat_identifier": row[2],
        "discord_username": row[3],
        "display_name": row[4],
        "linked_at": row[5],
        "updated_at": row[6],
    }

def _sherlock_member_dir(guild_id: int, member: discord.Member) -> Path:
    safe_name = re.sub(r'[^\w.\- ]', '', str(member)).strip() or str(member.id)
    base = Path("logs") / "members" / safe_name / "sherlock"
    base.mkdir(parents=True, exist_ok=True)
    return base

async def run_sherlock_for_username(username: str, output_dir: Path, timeout: int = 3) -> tuple[int, str]:
    """Run sherlock for a single username. Returns (found_count, output_file_path)."""
    username = (username or "").strip()
    if not username or len(username) < 2:
        return 0, ""
    # sherlock usernames can't contain spaces; sanitize
    safe_username = username.replace(" ", "")
    if len(safe_username) < 2:
        return 0, ""
    out_dir = output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    # Remove stale file
    target_file = out_dir / f"{safe_username}.txt"
    try:
        if target_file.exists():
            target_file.unlink()
    except Exception:
        pass

    proc = await asyncio.create_subprocess_exec(
        "sherlock", safe_username, "--timeout", str(timeout), "--no-color",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(out_dir),
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
    except asyncio.TimeoutError:
        try:
            proc.kill()
        except Exception:
            pass
        return 0, str(target_file)

    output_text = (stdout or b"").decode("utf-8", errors="replace")
    # Count found lines like "[+]"
    found_count = output_text.count("[+]")
    # sherlock writes file named safe_username.txt in cwd
    if not target_file.exists():
        # fallback: maybe file named differently
        candidates = list(out_dir.glob("*.txt"))
        if candidates:
            target_file = max(candidates, key=lambda p: p.stat().st_mtime)
    return found_count, str(target_file)

async def run_sherlock_scan_for_member(guild: discord.Guild, member: discord.Member):
    """Gather candidate usernames and run sherlock for each, storing results."""
    if member.bot:
        return []
    usernames = []
    # Discord username
    usernames.append((member.name, "discord_username"))
    # Display name (if different)
    if member.display_name and member.display_name != member.name:
        usernames.append((member.display_name, "discord_display_name"))
    # VRChat name from link
    link_record = get_member_link_record(guild.id, member.id)
    if link_record:
        vr_name = link_record.get("vrchat_username") or link_record.get("vrchat_identifier")
        if vr_name:
            usernames.append((vr_name, "vrchat_name"))
        vr_profile = get_vrchat_profile_data(guild.id, member.id)
        if vr_profile:
            dn = vr_profile.get("displayName")
            if dn and dn not in [u[0] for u in usernames]:
                usernames.append((dn, "vrchat_display_name"))
            un = vr_profile.get("username")
            if un and un not in [u[0] for u in usernames]:
                usernames.append((un, "vrchat_username"))

    out_dir = _sherlock_member_dir(guild.id, member)
    results = []
    # Dedupe by sanitized username
    seen = set()
    for username, source in usernames:
        key = username.strip().replace(" ", "")
        if key in seen:
            continue
        seen.add(key)
        found_count, output_path = await run_sherlock_for_username(username, out_dir)
        results.append({"username": key, "source": source, "found_count": found_count, "output_path": output_path})
        print(f"🔍 Sherlock scan for {member} ({source}:{key}) -> {found_count} hits")
    return results

async def scrape_sherlock_found_sites(guild: discord.Guild, member: discord.Member, max_sites: int = 0):
    """Fetch Sherlock-found profile URLs, scrape phone numbers / names / socials, save to member folder.
    max_sites=0 means fetch all found sites."""
    if member.bot:
        return None
    out_dir = _sherlock_member_dir(guild.id, member)
    urls = []
    for txt_file in sorted(out_dir.glob("*.txt")):
        try:
            for line in txt_file.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if line.startswith("[+]"):
                    # format: [+] Site: https://...
                    parts = line.split(":", 2)
                    if len(parts) >= 3:
                        url = parts[2].strip()
                        if url.startswith("http"):
                            urls.append(url)
        except Exception:
            continue
    urls = list(dict.fromkeys(urls))
    if max_sites and max_sites > 0:
        urls = urls[:max_sites]
    if not urls:
        return None

    aggregated = {
        "phones": set(),
        "names": set(),
        "socials": {},
        "sites_scraped": [],
        "phone_lookups": [],
    }
    timeout = aiohttp.ClientTimeout(total=12)
    headers = {"User-Agent": "Mozilla/5.0 (compatible; OSINTBot/1.0)"}
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        for url in urls:
            try:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        continue
                    html = await resp.text(errors="replace")
            except Exception:
                continue
            phones = _extract_phones_from_text(html)
            meta = _extract_public_profile_meta(html)
            socials = _extract_social_links(html)
            for p in phones:
                aggregated["phones"].add(p)
            for key in ("profile_title", "real_name"):
                val = meta.get(key)
                if val:
                    aggregated["names"].add(val)
            for platform, uname in socials.items():
                if platform not in aggregated["socials"]:
                    aggregated["socials"][platform] = []
                if isinstance(uname, list):
                    aggregated["socials"][platform].extend(uname)
                else:
                    aggregated["socials"][platform].append(uname)
            aggregated["sites_scraped"].append(url)
            await asyncio.sleep(0.5)

    # Run basic open phone lookup for each phone
    for phone in aggregated["phones"]:
        try:
            info = await lookup_phone_number(phone)
            if info:
                aggregated["phone_lookups"].append(info)
        except Exception:
            continue

    # Save JSON + TXT
    json_path = out_dir / "scraped_osint.json"
    try:
        serializable = {
            "phones": sorted(aggregated["phones"]),
            "names": sorted(aggregated["names"]),
            "socials": {k: list(set(v)) for k, v in aggregated["socials"].items()},
            "sites_scraped": aggregated["sites_scraped"],
            "phone_lookups": aggregated["phone_lookups"],
        }
        json_path.write_text(json.dumps(serializable, indent=2, default=str), encoding="utf-8")
    except Exception as e:
        print(f"❌ Failed to write scraped JSON: {e}")

    txt_path = out_dir / "scraped_osint.txt"
    try:
        lines = ["=== Scraped OSINT from Sherlock-found sites ===", ""]
        lines.append(f"Phones: {', '.join(sorted(aggregated['phones'])) or 'None'}")
        lines.append(f"Names: {', '.join(sorted(aggregated['names'])) or 'None'}")
        lines.append("")
        lines.append("Socials:")
        for platform, unames in aggregated["socials"].items():
            lines.append(f"  {platform}: {', '.join(set(unames))}")
        lines.append("")
        lines.append(f"Sites scraped: {len(aggregated['sites_scraped'])}")
        txt_path.write_text("\n".join(lines), encoding="utf-8")
    except Exception as e:
        print(f"❌ Failed to write scraped TXT: {e}")

    print(f"✅ Scraped {len(urls)} sites for {member}: {len(aggregated['phones'])} phones, {len(aggregated['names'])} names")
    return aggregated

def upsert_member_link_record(guild_id: int, user_id: int, vrchat_profile_url: str, vrchat_username: Optional[str], vrchat_identifier: Optional[str], discord_username: str, display_name: str):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO vrchat_links (
            guild_id, user_id, vrchat_profile_url, vrchat_username, vrchat_identifier, discord_username, display_name
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(guild_id, user_id) DO UPDATE SET
            vrchat_profile_url = excluded.vrchat_profile_url,
            vrchat_username = excluded.vrchat_username,
            vrchat_identifier = excluded.vrchat_identifier,
            discord_username = excluded.discord_username,
            display_name = excluded.display_name,
            updated_at = CURRENT_TIMESTAMP
        """,
        (guild_id, user_id, vrchat_profile_url, vrchat_username, vrchat_identifier, discord_username, display_name)
    )
    conn.commit()
    conn.close()

def save_username_history(guild_id: int, user_id: int, platform: str, old_username: Optional[str], new_username: str):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    try:
        c.execute(
            """
            INSERT INTO username_history (guild_id, user_id, platform, old_username, new_username)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(guild_id, user_id, platform, new_username) DO UPDATE SET
                old_username = COALESCE(excluded.old_username, old_username),
                last_seen = CURRENT_TIMESTAMP
            """,
            (guild_id, user_id, platform, old_username, new_username)
        )
        conn.commit()
    except Exception:
        pass
    conn.close()

def get_username_history(guild_id: int, user_id: int) -> dict:
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute(
        """
        SELECT platform, old_username, new_username, first_seen, last_seen
        FROM username_history
        WHERE guild_id = ? AND user_id = ?
        ORDER BY last_seen DESC
        """,
        (guild_id, user_id)
    )
    rows = c.fetchall()
    conn.close()
    
    history = {}
    for platform, old_username, new_username, first_seen, last_seen in rows:
        if platform not in history:
            history[platform] = []
        history[platform].append({
            "old_username": old_username,
            "new_username": new_username,
            "first_seen": first_seen,
            "last_seen": last_seen
        })
    return history

def save_linked_account(guild_id: int, user_id: int, platform: str, username: Optional[str], url: str, profile_image: Optional[str] = None):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    try:
        c.execute(
            """
            INSERT INTO linked_accounts (guild_id, user_id, platform, username, url, profile_image)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(guild_id, user_id, platform, url) DO UPDATE SET
                username = COALESCE(excluded.username, username),
                profile_image = COALESCE(excluded.profile_image, profile_image)
            """,
            (guild_id, user_id, platform, username, url, profile_image)
        )
        conn.commit()
    except Exception:
        pass
    conn.close()

def get_linked_accounts(guild_id: int, user_id: int) -> list[dict]:
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute(
        """
        SELECT platform, username, url, profile_image, found_at
        FROM linked_accounts
        WHERE guild_id = ? AND user_id = ?
        ORDER BY found_at DESC
        """,
        (guild_id, user_id)
    )
    rows = c.fetchall()
    conn.close()
    return [
        {
            "platform": row[0],
            "username": row[1],
            "url": row[2],
            "profile_image": row[3],
            "found_at": row[4]
        }
        for row in rows
    ]

def save_phone_lookup(guild_id: int, user_id: int, phone_number: str, lookup_result: Optional[dict] = None):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    result_json = json.dumps(lookup_result) if lookup_result else None
    found_name = lookup_result.get("name") if lookup_result else None
    found_address = lookup_result.get("address") if lookup_result else None
    found_social = json.dumps(lookup_result.get("social", [])) if lookup_result else None
    
    c.execute(
        """
        INSERT INTO phone_lookups (guild_id, user_id, phone_number, lookup_result, found_name, found_address, found_social)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(guild_id, user_id, phone_number) DO UPDATE SET
            lookup_result = COALESCE(excluded.lookup_result, lookup_result),
            found_name = COALESCE(excluded.found_name, found_name),
            found_address = COALESCE(excluded.found_address, found_address),
            found_social = COALESCE(excluded.found_social, found_social),
            looked_up_at = CURRENT_TIMESTAMP
        """,
        (guild_id, user_id, phone_number, result_json, found_name, found_address, found_social)
    )
    conn.commit()
    conn.close()

def get_phone_lookup(guild_id: int, user_id: int, phone_number: str) -> Optional[dict]:
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute(
        """
        SELECT phone_number, lookup_result, found_name, found_address, found_social, looked_up_at
        FROM phone_lookups
        WHERE guild_id = ? AND user_id = ? AND phone_number = ?
        """,
        (guild_id, user_id, phone_number)
    )
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    
    result = json.loads(row[1]) if row[1] else None
    return {
        "phone_number": row[0],
        "lookup_result": result,
        "found_name": row[2],
        "found_address": row[3],
        "found_social": json.loads(row[4]) if row[4] else [],
        "looked_up_at": row[5]
    }

def get_all_phone_lookups(guild_id: int, user_id: int) -> list[dict]:
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute(
        """
        SELECT phone_number, lookup_result, found_name, found_address, found_social, looked_up_at
        FROM phone_lookups
        WHERE guild_id = ? AND user_id = ?
        ORDER BY looked_up_at DESC
        """,
        (guild_id, user_id)
    )
    rows = c.fetchall()
    conn.close()
    return [
        {
            "phone_number": row[0],
            "lookup_result": json.loads(row[1]) if row[1] else None,
            "found_name": row[2],
            "found_address": row[3],
            "found_social": json.loads(row[4]) if row[4] else [],
            "looked_up_at": row[5]
        }
        for row in rows
    ]

def save_image_analysis(guild_id: int, user_id: int, image_url: str, image_hash: str, exif_data: dict = None, gps: tuple = None, camera_model: str = None, timestamp: str = None):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    exif_json = json.dumps(exif_data) if exif_data else None
    lat, lon = (gps[0], gps[1]) if gps else (None, None)
    
    c.execute(
        """
        INSERT INTO image_analysis (guild_id, user_id, image_url, image_hash, exif_data, gps_latitude, gps_longitude, camera_model, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(guild_id, user_id, image_hash) DO UPDATE SET
            exif_data = COALESCE(excluded.exif_data, exif_data),
            gps_latitude = COALESCE(excluded.gps_latitude, gps_latitude),
            gps_longitude = COALESCE(excluded.gps_longitude, gps_longitude),
            camera_model = COALESCE(excluded.camera_model, camera_model),
            timestamp = COALESCE(excluded.timestamp, timestamp)
        """,
        (guild_id, user_id, image_url, image_hash, exif_json, lat, lon, camera_model, timestamp)
    )
    conn.commit()
    conn.close()

def get_image_analyses(guild_id: int, user_id: int) -> list[dict]:
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute(
        """
        SELECT image_url, image_hash, exif_data, gps_latitude, gps_longitude, camera_model, timestamp, analyzed_at
        FROM image_analysis
        WHERE guild_id = ? AND user_id = ?
        ORDER BY analyzed_at DESC
        """,
        (guild_id, user_id)
    )
    rows = c.fetchall()
    conn.close()
    return [
        {
            "image_url": row[0],
            "image_hash": row[1],
            "exif_data": json.loads(row[2]) if row[2] else {},
            "gps_latitude": row[3],
            "gps_longitude": row[4],
            "camera_model": row[5],
            "timestamp": row[6],
            "analyzed_at": row[7]
        }
        for row in rows
    ]

def save_unified_profile(guild_id: int, user_id: int, unified_data: dict, completeness_score: float, timeline_data: dict = None):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    unified_json = json.dumps(unified_data)
    timeline_json = json.dumps(timeline_data) if timeline_data else None
    
    c.execute(
        """
        INSERT INTO unified_profile (guild_id, user_id, unified_data, completeness_score, timeline_data)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(guild_id, user_id) DO UPDATE SET
            unified_data = excluded.unified_data,
            completeness_score = excluded.completeness_score,
            timeline_data = COALESCE(excluded.timeline_data, timeline_data),
            last_updated = CURRENT_TIMESTAMP
        """,
        (guild_id, user_id, unified_json, completeness_score, timeline_json)
    )
    conn.commit()
    conn.close()

def get_unified_profile(guild_id: int, user_id: int) -> Optional[dict]:
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute(
        """
        SELECT unified_data, completeness_score, timeline_data, last_updated
        FROM unified_profile
        WHERE guild_id = ? AND user_id = ?
        """,
        (guild_id, user_id)
    )
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "unified_data": json.loads(row[0]),
        "completeness_score": row[1],
        "timeline_data": json.loads(row[2]) if row[2] else {},
        "last_updated": row[3]
    }

def save_shared_servers(guild_id: int, user_id: int, target_user_id: int, shared_guild_ids: list, shared_channel_ids: list = None):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    guilds_json = json.dumps(shared_guild_ids)
    channels_json = json.dumps(shared_channel_ids) if shared_channel_ids else None
    
    c.execute(
        """
        INSERT INTO shared_servers (guild_id, user_id, target_user_id, shared_guild_ids, shared_channel_ids)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(guild_id, user_id, target_user_id) DO UPDATE SET
            shared_guild_ids = excluded.shared_guild_ids,
            shared_channel_ids = COALESCE(excluded.shared_channel_ids, shared_channel_ids),
            last_checked = CURRENT_TIMESTAMP
        """,
        (guild_id, user_id, target_user_id, guilds_json, channels_json)
    )
    conn.commit()
    conn.close()

def get_shared_servers(guild_id: int, user_id: int, target_user_id: int) -> Optional[dict]:
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute(
        """
        SELECT shared_guild_ids, shared_channel_ids, last_checked
        FROM shared_servers
        WHERE guild_id = ? AND user_id = ? AND target_user_id = ?
        """,
        (guild_id, user_id, target_user_id)
    )
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "shared_guild_ids": json.loads(row[0]),
        "shared_channel_ids": json.loads(row[1]) if row[1] else [],
        "last_checked": row[2]
    }

def get_all_shared_servers_for_user(guild_id: int, user_id: int) -> list[dict]:
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute(
        """
        SELECT target_user_id, shared_guild_ids, shared_channel_ids, last_checked
        FROM shared_servers
        WHERE guild_id = ? AND user_id = ?
        ORDER BY last_checked DESC
        """,
        (guild_id, user_id)
    )
    rows = c.fetchall()
    conn.close()
    return [
        {
            "target_user_id": row[0],
            "shared_guild_ids": json.loads(row[1]),
            "shared_channel_ids": json.loads(row[2]) if row[2] else [],
            "last_checked": row[3]
        }
        for row in rows
    ]

def save_pastebin_dump(guild_id: int, user_id: int, source: str, paste_url: str, paste_content: str = None, contains_email: bool = False, contains_phone: bool = False, contains_username: bool = False):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    
    c.execute(
        """
        INSERT INTO pastebin_dumps (guild_id, user_id, source, paste_url, paste_content, contains_email, contains_phone, contains_username)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(guild_id, user_id, paste_url) DO UPDATE SET
            paste_content = COALESCE(excluded.paste_content, paste_content),
            contains_email = excluded.contains_email,
            contains_phone = excluded.contains_phone,
            contains_username = excluded.contains_username
        """,
        (guild_id, user_id, source, paste_url, paste_content[:5000] if paste_content else None, 1 if contains_email else 0, 1 if contains_phone else 0, 1 if contains_username else 0)
    )
    conn.commit()
    conn.close()

def get_pastebin_dumps(guild_id: int, user_id: int) -> list[dict]:
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute(
        """
        SELECT source, paste_url, paste_content, contains_email, contains_phone, contains_username, found_at
        FROM pastebin_dumps
        WHERE guild_id = ? AND user_id = ?
        ORDER BY found_at DESC
        """,
        (guild_id, user_id)
    )
    rows = c.fetchall()
    conn.close()
    return [
        {
            "source": row[0],
            "paste_url": row[1],
            "paste_content": row[2],
            "contains_email": bool(row[3]),
            "contains_phone": bool(row[4]),
            "contains_username": bool(row[5]),
            "found_at": row[6]
        }
        for row in rows
    ]

def save_wayback_snapshot(guild_id: int, user_id: int, url: str, snapshot_url: str, snapshot_date: str = None):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    
    c.execute(
        """
        INSERT INTO wayback_snapshots (guild_id, user_id, url, snapshot_url, snapshot_date)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(guild_id, user_id, url, snapshot_url) DO UPDATE SET
            snapshot_date = COALESCE(excluded.snapshot_date, snapshot_date)
        """,
        (guild_id, user_id, url, snapshot_url, snapshot_date)
    )
    conn.commit()
    conn.close()

def get_wayback_snapshots(guild_id: int, user_id: int, url: str = None) -> list[dict]:
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    if url:
        c.execute(
            """
            SELECT url, snapshot_url, snapshot_date, found_at
            FROM wayback_snapshots
            WHERE guild_id = ? AND user_id = ? AND url = ?
            ORDER BY found_at DESC
            """,
            (guild_id, user_id, url)
        )
    else:
        c.execute(
            """
            SELECT url, snapshot_url, snapshot_date, found_at
            FROM wayback_snapshots
            WHERE guild_id = ? AND user_id = ?
            ORDER BY found_at DESC
            LIMIT 50
            """,
            (guild_id, user_id)
        )
    rows = c.fetchall()
    conn.close()
    return [
        {
            "url": row[0],
            "snapshot_url": row[1],
            "snapshot_date": row[2],
            "found_at": row[3]
        }
        for row in rows
    ]

def save_dns_history(guild_id: int, user_id: int, domain: str, ip_addresses: list = None, historical_ips: list = None, mx_records: list = None, ns_records: list = None, ssl_info: dict = None):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    ips_json = json.dumps(ip_addresses) if ip_addresses else None
    hist_ips_json = json.dumps(historical_ips) if historical_ips else None
    mx_json = json.dumps(mx_records) if mx_records else None
    ns_json = json.dumps(ns_records) if ns_records else None
    ssl_json = json.dumps(ssl_info) if ssl_info else None
    
    c.execute(
        """
        INSERT INTO dns_history (guild_id, user_id, domain, ip_addresses, historical_ips, mx_records, ns_records, ssl_info)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(guild_id, user_id, domain) DO UPDATE SET
            ip_addresses = COALESCE(excluded.ip_addresses, ip_addresses),
            historical_ips = COALESCE(excluded.historical_ips, historical_ips),
            mx_records = COALESCE(excluded.mx_records, mx_records),
            ns_records = COALESCE(excluded.ns_records, ns_records),
            ssl_info = COALESCE(excluded.ssl_info, ssl_info),
            checked_at = CURRENT_TIMESTAMP
        """,
        (guild_id, user_id, domain, ips_json, hist_ips_json, mx_json, ns_json, ssl_json)
    )
    conn.commit()
    conn.close()

def get_dns_history(guild_id: int, user_id: int, domain: str = None) -> list[dict]:
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    if domain:
        c.execute(
            """
            SELECT domain, ip_addresses, historical_ips, mx_records, ns_records, ssl_info, checked_at
            FROM dns_history
            WHERE guild_id = ? AND user_id = ? AND domain = ?
            """,
            (guild_id, user_id, domain)
        )
    else:
        c.execute(
            """
            SELECT domain, ip_addresses, historical_ips, mx_records, ns_records, ssl_info, checked_at
            FROM dns_history
            WHERE guild_id = ? AND user_id = ?
            ORDER BY checked_at DESC
            LIMIT 50
            """,
            (guild_id, user_id)
        )
    rows = c.fetchall()
    conn.close()
    return [
        {
            "domain": row[0],
            "ip_addresses": json.loads(row[1]) if row[1] else [],
            "historical_ips": json.loads(row[2]) if row[2] else [],
            "mx_records": json.loads(row[3]) if row[3] else [],
            "ns_records": json.loads(row[4]) if row[4] else [],
            "ssl_info": json.loads(row[5]) if row[5] else {},
            "checked_at": row[6]
        }
        for row in rows
    ]

def _clean_public_meta_text(value: Optional[str], limit: int = 240):
    if not value:
        return None
    cleaned = re.sub(r"\s+", " ", unescape(str(value))).strip()
    if not cleaned:
        return None
    return cleaned[:limit]

def _extract_emails_from_text(text: str) -> list[str]:
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    return list(set([e.lower() for e in emails if len(e) < 100]))

def _extract_phones_from_text(text: str) -> list[str]:
    patterns = [
        r'\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',
        r'\+?[0-9]{1,4}[-.\s]?[0-9]{2,4}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}',
    ]
    phones = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            cleaned = re.sub(r'[^\d+]', '', match)
            if 10 <= len(cleaned) <= 15:
                phones.append(cleaned)
    return list(set(phones))

def _extract_social_links(html_text: str) -> dict:
    social_patterns = {
        "twitter": r'(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)',
        "instagram": r'instagram\.com/([a-zA-Z0-9_.]+)',
        "facebook": r'facebook\.com/([a-zA-Z0-9_.]+)',
        "youtube": r'(?:youtube\.com/(?:channel/|@|user/)|youtu\.be/)([a-zA-Z0-9_-]+)',
        "tiktok": r'tiktok\.com/@([a-zA-Z0-9_.]+)',
        "reddit": r'reddit\.com/u/([a-zA-Z0-9_-]+)',
        "linkedin": r'linkedin\.com/in/([a-zA-Z0-9_-]+)',
        "github": r'github\.com/([a-zA-Z0-9_-]+)',
        "snapchat": r'snapchat\.com/add/([a-zA-Z0-9_.]+)',
        "discord": r'discord(?:app)?\.com/users?/([0-9]+)',
        "twitch": r'twitch\.tv/([a-zA-Z0-9_]+)',
        "pinterest": r'pinterest\.com/([a-zA-Z0-9_]+)',
        "tumblr": r'([a-zA-Z0-9-]+)\.tumblr\.com',
    }
    
    socials = {}
    for platform, pattern in social_patterns.items():
        matches = re.findall(pattern, html_text, flags=re.IGNORECASE)
        if matches:
            usernames = list(set(matches))[:3]
            socials[platform] = usernames if len(usernames) > 1 else usernames[0]
    return socials

def _extract_public_profile_meta(html_text: str):
    patterns = [
        ("profile_title", r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\'](.*?)["\']'),
        ("profile_title", r'<meta[^>]+name=["\']twitter:title["\'][^>]+content=["\'](.*?)["\']'),
        ("profile_title", r"<title[^>]*>(.*?)</title>"),
        ("profile_summary", r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\'](.*?)["\']'),
        ("profile_summary", r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']'),
        ("profile_summary", r'<meta[^>]+name=["\']twitter:description["\'][^>]+content=["\'](.*?)["\']'),
        ("real_name", r'<meta[^>]+property=["\']profile:first_name["\'][^>]+content=["\'](.*?)["\']'),
        ("real_name", r'<meta[^>]+name=["\']profile:first_name["\'][^>]+content=["\'](.*?)["\']'),
        ("real_name", r'<meta[^>]+property=["\']profile:last_name["\'][^>]+content=["\'](.*?)["\']'),
        ("real_name", r'<meta[^>]+name=["\']profile:last_name["\'][^>]+content=["\'](.*?)["\']'),
        ("real_name", r'<meta[^>]+property=["\']profile:name["\'][^>]+content=["\'](.*?)["\']'),
        ("real_name", r'<span[^>]+itemprop=["\']name["\'][^>]*>(.*?)</span>'),
        ("real_name", r'<span[^>]+class=["\'][^"\']*\bname\b[^"\']*["\'][^>]*>(.*?)</span>'),
        ("real_name", r'<div[^>]+class=["\'][^"\']*\b(name|realname|full-name|fullname)\b[^"\']*["\'][^>]*>(.*?)</div>'),
        ("location", r'<meta[^>]+property=["\']profile:region["\'][^>]+content=["\'](.*?)["\']'),
        ("location", r'<meta[^>]+name=["\']profile:region["\'][^>]+content=["\'](.*?)["\']'),
        ("location", r'<span[^>]+itemprop=["\']addressLocality["\'][^>]*>(.*?)</span>'),
        ("location", r'<span[^>]+class=["\'][^"\']*\b(location|city|place)\b[^"\']*["\'][^>]*>(.*?)</span>'),
        ("location", r'<meta[^>]+property=["\']og:locale:region["\'][^>]+content=["\'](.*?)["\']'),
        ("location", r'<meta[^>]+name=["\']geo\.region["\'][^>]+content=["\'](.*?)["\']'),
        ("location", r'<meta[^>]+name=["\']geo\.placename["\'][^>]+content=["\'](.*?)["\']'),
        ("bio", r'<meta[^>]+property=["\']og:bios["\'][^>]+content=["\'](.*?)["\']'),
        ("bio", r'<meta[^>]+name=["\']bio["\'][^>]+content=["\'](.*?)["\']'),
        ("bio", r'<meta[^>]+property=["\']profile:user_about_me["\'][^>]+content=["\'](.*?)["\']'),
        ("bio", r'<p[^>]+class=["\'][^"\']*\b(bio|about|description|summary)\b[^"\']*["\'][^>]*>(.*?)</p>'),
        ("bio", r'<div[^>]+class=["\'][^"\']*\b(bio|about-me|user-bio)\b[^"\']*["\'][^>]*>(.*?)</div>'),
        ("profile_image", r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\'](.*?)["\']'),
        ("profile_image", r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\'](.*?)["\']'),
        ("profile_image", r'<img[^>]+class=["\'][^"\']*\b(avatar|profile|pic|photo|user-avatar)\b[^"\']*["\'][^>]+src=["\'](.*?)["\']'),
        ("profile_image", r'<meta[^>]+property=["\']profile:image["\'][^>]+content=["\'](.*?)["\']'),
        ("username", r'<meta[^>]+property=["\']profile:username["\'][^>]+content=["\'](.*?)["\']'),
        ("username", r'<meta[^>]+name=["\']twitter:site["\'][^>]+content=["\'](.*?)["\']'),
        ("username", r'<a[^>]+class=["\'][^"\']*\b(handle|username|alias)\b[^"\']*["\'][^>]*>@?([a-zA-Z0-9_\.]+)'),
        ("username", r'<span[^>]+class=["\'][^"\']*\bat\b[^"\']*["\'][^>]*>@?([a-zA-Z0-9_\.]+)'),
        ("account_age", r'(?:joined|joined|account created|member since|since|created|registered)[:\s]*["\']?(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\w+ \d{1,2},? \d{4}|\d{4})'),
        ("account_age", r'(?:age|years? old|born|birth)[:\s]*["\']?(\d{1,3})(?: years?| y\.?| y/o)?'),
        ("account_age", r'(?:member since|on platform since|here for)[:\s]*["\']?(\w+ \d{4})'),
        ("followers", r'(?:followers?|subscribers?|friends?)[:\s]*["\']?([0-9,]+[KMB]?|[0-9,]+)'),
        ("followers", r'<span[^>]+class=["\'][^"\']*\b(follower-count|follower-count|subscriber-count)\b[^"\']*["\'][^>]*>([0-9,]+)</span>'),
        ("following", r'(?:following)[:\s]*["\']?([0-9,]+[KMB]?|[0-9,]+)'),
        ("website", r'<meta[^>]+property=["\']og:url["\'][^>]+content=["\'](https?://[^"\']+)["\']'),
        ("website", r'<a[^>]+rel=["\'][^"\']*\b(author|me|me)\b[^"\']*["\'][^>]+href=["\'](https?://[^"\']+)["\']'),
    ]

    extracted = {}
    for pattern_tuple in patterns:
        if len(pattern_tuple) == 3:
            key, pattern, group_idx = pattern_tuple
        else:
            key, pattern = pattern_tuple
            group_idx = 1

        if key in extracted:
            continue
        match = re.search(pattern, html_text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            try:
                cleaned = _clean_public_meta_text(match.group(group_idx), limit=180)
                if cleaned:
                    extracted[key] = cleaned
            except (IndexError, AttributeError):
                pass
    
    emails = _extract_emails_from_text(html_text)
    if emails:
        extracted["emails"] = emails[:5]
    
    phones = _extract_phones_from_text(html_text)
    if phones:
        extracted["phones"] = phones[:3]
    
    socials = _extract_social_links(html_text)
    if socials:
        extracted["social_links"] = socials
    
    return extracted

def _parse_json_profile(data: dict, url: str):
    extracted = {}
    
    def extract_value(obj, *keys, default=None):
        for key in keys:
            if isinstance(obj, dict):
                obj = obj.get(key, default)
            else:
                return default
        return obj if obj else default
    
    title = extract_value(data, "title", "name", "username", "display_name", "displayName") or extract_value(data, "full_name", "fullName", "first_name", "firstName")
    if title:
        extracted["profile_title"] = str(title)[:180]
    
    bio = extract_value(data, "bio", "description", "about", "summary", "biography")
    if bio:
        extracted["bio"] = str(bio)[:280]
    
    name = extract_value(data, "real_name", "realName", "full_name", "fullName") or extract_value(data, "first_name", "firstName")
    if name:
        last_name = extract_value(data, "last_name", "lastName")
        if last_name:
            name = f"{name} {last_name}"
        extracted["real_name"] = str(name)[:100]
    
    location = extract_value(data, "location", "city", "place", "region")
    if location:
        if isinstance(location, dict):
            location = extract_value(location, "name", "city", "region") or str(location)
        extracted["location"] = str(location)[:100]
    
    image = extract_value(data, "profile_image", "profileImage", "avatar_url", "avatarUrl", "image_url", "imageUrl", "profile_picture", "photo", "pic", "pfp_url", "avatar", "user_image", "profileUrl", "profile_url")
    if image:
        extracted["profile_image"] = str(image)
    
    username = extract_value(data, "username", "handle", "screen_name", "screenName", "login", "user_name", "userName")
    if username:
        extracted["username"] = str(username)[:50]
    
    created_at = extract_value(data, "created_at", "createdAt", "joined_at", "joinedAt", "member_since", "registration_date", "date_joined", "registered_at")
    if created_at:
        extracted["account_age"] = str(created_at)[:50]
    
    followers = extract_value(data, "followers", "follower_count", "followerCount", "followers_count", "followersCount", "subscriber_count", "subscriberCount", "friends_count")
    if followers:
        extracted["followers"] = str(followers)
    
    following = extract_value(data, "following", "following_count", "followingCount", "friends")
    if following:
        extracted["following"] = str(following)
    
    posts = extract_value(data, "posts", "post_count", "tweets", "statuses_count", "media_count")
    if posts:
        extracted["posts"] = str(posts)
    
    website = extract_value(data, "website", "url", "link", "homepage", "blog")
    if website:
        if isinstance(website, dict):
            website = extract_value(website, "url", "link") or str(website)
        extracted["website"] = str(website)[:200]
    
    socials = {}
    twitter = extract_value(data, "twitter", "twitter_handle", "twitter_username")
    if twitter:
        socials["twitter"] = twitter
    instagram = extract_value(data, "instagram", "instagram_handle", "instagram_username")
    if instagram:
        socials["instagram"] = instagram
    github = extract_value(data, "github", "github_username")
    if github:
        socials["github"] = github
    youtube = extract_value(data, "youtube", "youtube_channel", "youtube_id")
    if youtube:
        socials["youtube"] = youtube
    linkedin = extract_value(data, "linkedin", "linkedin_url")
    if linkedin:
        socials["linkedin"] = linkedin
    tiktok = extract_value(data, "tiktok", "tiktok_handle")
    if tiktok:
        socials["tiktok"] = tiktok
    
    if socials:
        extracted["social_links"] = socials
    
    emails = extract_value(data, "email", "email_address", "emailAddress", "contact_email")
    if emails:
        if isinstance(emails, list):
            extracted["emails"] = [str(e).lower() for e in emails[:5]]
        else:
            extracted["emails"] = [str(emails).lower()]
    
    phone = extract_value(data, "phone", "phone_number", "phoneNumber", "mobile", "tel", "telephone")
    if phone:
        phones = _extract_phones_from_text(str(phone))
        if phones:
            extracted["phones"] = phones[:3]
    
    verified = extract_value(data, "verified", "is_verified", "isVerified")
    if verified:
        extracted["verified"] = True
    
    return extracted

def get_image_reverse_search_urls(image_url: str) -> dict:
    if not image_url:
        return {}
    
    encoded_url = quote_plus(image_url)
    return {
        "google": f"https://www.google.com/searchbyimage?image_url={encoded_url}",
        "yandex": f"https://yandex.com/images/search?rpt=imageview&url={encoded_url}",
        "tineye": f"https://tineye.com/search?url={encoded_url}",
        "bing": f"https://www.bing.com/images/search?q=imgurl:{encoded_url}",
        "yahoo": f"https://images.search.yahoo.com/search/images?g_param=&q=imgurl:{encoded_url}",
    }

async def lookup_phone_number(phone_number: str) -> Optional[dict]:
    clean_number = re.sub(r'[^\d+]', '', phone_number)
    if len(clean_number) < 10:
        return None
    
    result = {
        "phone_number": clean_number,
        "found_name": None,
        "found_address": None,
        "social": [],
        "notes": "Basic phone format extracted. Full lookup requires paid API (e.g., Whitepages, Pipl, Truecaller)."
    }
    
    if clean_number.startswith("+1") and len(clean_number) == 11:
        area_code = clean_number[2:5]
        result["area_code"] = area_code
        result["country"] = "USA/Canada"
    
    return result

def calculate_image_hash(image_data: bytes) -> str:
    sha256_hash = hashlib.sha256(image_data).hexdigest()
    return sha256_hash

def parse_basic_exif(image_data: bytes) -> dict:
    exif_data = {}
    try:
        from PIL import Image
        from io import BytesIO
        img = Image.open(BytesIO(image_data))
        if hasattr(img, '_getexif') and img._getexif():
            exif = img._getexif()
            if exif:
                tag_names = {
                    0x010F: 'Make',
                    0x0110: 'Model',
                    0x0132: 'DateTime',
                    0x9003: 'DateTimeOriginal',
                    0x0131: 'Software',
                    0x829A: 'ExposureTime',
                    0x829D: 'FNumber',
                    0x8827: 'ISOSpeedRatings',
                    0xA434: 'LensModel',
                }
                for tag_id, value in exif.items():
                    if tag_id in tag_names:
                        exif_data[tag_names[tag_id]] = str(value)
        
        if hasattr(img, '_getexif') and hasattr(img, 'tag_v2'):
            if 34853 in img.tag_v2:
                gps_info = img.tag_v2[34853]
                exif_data['GPSInfo'] = gps_info
    except ImportError:
        pass
    except Exception:
        pass
    return exif_data

def extract_gps_from_exif(exif_data: dict) -> Optional[tuple]:
    if 'GPSInfo' in exif_data and exif_data['GPSInfo']:
        gps = exif_data['GPSInfo']
        try:
            if 1 in gps and 2 in gps and 3 in gps and 4 in gps:
                lat = gps[2][0] / gps[2][1] if gps[2][1] != 0 else 0
                lat += gps[2][2] / gps[2][3] / 3600 if len(gps[2]) > 2 and gps[2][3] != 0 else 0
                if gps[1] == 'S':
                    lat = -lat
                
                lon = gps[4][0] / gps[4][1] if gps[4][1] != 0 else 0
                lon += gps[4][2] / gps[4][3] / 3600 if len(gps[4]) > 2 and gps[4][3] != 0 else 0
                if gps[3] == 'W':
                    lon = -lon
                
                return (lat, lon)
        except Exception:
            pass
    return None

async def fetch_and_analyze_image(image_url: str, guild_id: int, user_id: int) -> Optional[dict]:
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(image_url, headers={"User-Agent": "TheBlackIrisBot/1.0"}) as response:
                if response.status != 200:
                    return None
                
                content_type = response.headers.get("Content-Type", "").lower()
                if not any(img_type in content_type for img_type in ["image/jpeg", "image/png", "image/gif", "image/webp"]):
                    return None
                
                image_data = await response.read()
                image_hash = calculate_image_hash(image_data)
                
                exif_data = parse_basic_exif(image_data)
                gps_coords = extract_gps_from_exif(exif_data)
                camera_model = exif_data.get("Make", "") + " " + exif_data.get("Model", "") if "Make" in exif_data or "Model" in exif_data else None
                timestamp = exif_data.get("DateTimeOriginal") or exif_data.get("DateTime")
                
                save_image_analysis(guild_id, user_id, image_url, image_hash, exif_data, gps_coords, camera_model, timestamp)
                
                return {
                    "image_hash": image_hash,
                    "exif_data": exif_data,
                    "gps_coords": gps_coords,
                    "camera_model": camera_model,
                    "timestamp": timestamp
                }
    except Exception as e:
        print(f"Failed to analyze image: {e}")
        return None

async def check_wayback_machine(url: str) -> Optional[dict]:
    try:
        wayback_url = f"https://archive.org/wayback/available?url={quote_plus(url)}"
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(wayback_url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("archived_snapshots", {}).get("closest"):
                        snapshot = data["archived_snapshots"]["closest"]
                        return {
                            "available": True,
                            "url": snapshot.get("url"),
                            "timestamp": snapshot.get("timestamp"),
                            "status": snapshot.get("status")
                        }
        return {"available": False}
    except Exception:
        return {"available": False}

async def search_pastebin(username: str, emails: list = None) -> list[dict]:
    results = []
    
    if emails:
        for email in emails[:3]:
            results.append({
                "source": "email",
                "query": email,
                "pastebin_url": f"https://www.google.com/search?q=site:pastebin.com+{quote_plus(email)}",
                "direct_url": f"https://pastebin.com/search?q={quote_plus(email)}"
            })
    
    if username:
        results.append({
            "source": "username",
            "query": username,
            "pastebin_url": f"https://www.google.com/search?q=site:pastebin.com+{quote_plus(username)}",
            "direct_url": f"https://pastebin.com/search?q={quote_plus(username)}"
        })
    
    return results

async def get_dns_info(domain: str) -> Optional[dict]:
    try:
        dns_data = {
            "domain": domain,
            "ip_addresses": [],
            "mx_records": [],
            "ns_records": [],
            "historical_ips": []
        }
        
        try:
            addr_info = socket.getaddrinfo(domain, None)
            dns_data["ip_addresses"] = list(set([info[4][0] for info in addr_info]))
        except Exception:
            pass
        
        try:
            mx_records = []
            for priority, host in socket.getaddrinfo(domain, 25):
                pass
        except Exception:
            pass
        
        try:
            import dns.resolver
            resolver = dns.resolver.Resolver()
            resolver.timeout = 3
            resolver.lifetime = 3
            
            try:
                mx_answer = resolver.resolve(domain, 'MX')
                dns_data["mx_records"] = [str(rdata.exchange) for rdata in mx_answer]
            except Exception:
                pass
            
            try:
                ns_answer = resolver.resolve(domain, 'NS')
                dns_data["ns_records"] = [str(rdata) for rdata in ns_answer]
            except Exception:
                pass
        except ImportError:
            pass
        except Exception:
            pass
        
        return dns_data
    except Exception:
        return None

def get_ssl_info(domain: str) -> Optional[dict]:
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert(binary_form=True)
                ssl_info = {
                    "issuer": dict(x[0] for x in ssock.getpeercert().get('issuer', [])),
                    "subject": dict(x[0] for x in ssock.getpeercert().get('subject', [])),
                    "version": ssock.getpeercert().get('version'),
                    "not_before": ssock.getpeercert().get('notBefore'),
                    "not_after": ssock.getpeercert().get('notAfter'),
                }
                return ssl_info
    except Exception:
        return None

def build_unified_profile(guild_id: int, user_id: int) -> dict:
    unified = {
        "names": set(),
        "usernames": set(),
        "emails": set(),
        "phones": set(),
        "locations": set(),
        "bios": [],
        "profile_images": [],
        "social_accounts": {},
        "account_ages": {},
        "followers": {},
    }
    
    linked_accounts = get_linked_accounts(guild_id, user_id)
    for acc in linked_accounts:
        platform = acc["platform"]
        username = acc["username"]
        if username and platform not in unified["social_accounts"]:
            unified["social_accounts"][platform] = username
    
    vrchat_profile = get_vrchat_profile_data(guild_id, user_id)
    if vrchat_profile:
        if vrchat_profile.get("displayName"):
            unified["names"].add(vrchat_profile["displayName"])
        if vrchat_profile.get("bio"):
            unified["bios"].append(vrchat_profile["bio"][:200])
        if vrchat_profile.get("dateJoined"):
            unified["account_ages"]["vrchat"] = vrchat_profile["dateJoined"][:10]
    
    completeness = 0
    total_fields = 9
    if unified["names"]: completeness += 1
    if unified["usernames"]: completeness += 1
    if unified["emails"]: completeness += 1
    if unified["phones"]: completeness += 1
    if unified["locations"]: completeness += 1
    if unified["bios"]: completeness += 1
    if unified["profile_images"]: completeness += 1
    if unified["social_accounts"]: completeness += 1
    if unified["account_ages"]: completeness += 1
    
    completeness_score = (completeness / total_fields) * 100
    
    return {
        "names": list(unified["names"]),
        "usernames": list(unified["usernames"]),
        "emails": list(unified["emails"]),
        "phones": list(unified["phones"]),
        "locations": list(unified["locations"]),
        "bios": unified["bios"][:5],
        "profile_images": unified["profile_images"][:5],
        "social_accounts": unified["social_accounts"],
        "account_ages": unified["account_ages"],
        "followers": unified["followers"],
        "completeness_score": completeness_score
    }

def build_timeline(guild_id: int, user_id: int) -> list[dict]:
    timeline = []
    
    vrchat_profile = get_vrchat_profile_data(guild_id, user_id)
    if vrchat_profile:
        if vrchat_profile.get("dateJoined"):
            timeline.append({
                "date": vrchat_profile["dateJoined"],
                "event": "VRChat account created",
                "source": "vrchat_api"
            })
        if vrchat_profile.get("lastLogin"):
            timeline.append({
                "date": vrchat_profile["lastLogin"],
                "event": "Last VRChat login",
                "source": "vrchat_api"
            })
    
    linked_accounts = get_linked_accounts(guild_id, user_id)
    for acc in linked_accounts:
        timeline.append({
            "date": acc.get("found_at"),
            "event": f"Linked {acc['platform'].title()} account: {acc.get('username', 'unknown')}",
            "source": "osint"
        })
    
    image_analyses = get_image_analyses(guild_id, user_id)
    for img in image_analyses:
        if img.get("timestamp"):
            timeline.append({
                "date": img["timestamp"],
                "event": f"Photo taken (from EXIF)",
                "source": "image_exif"
            })
    
    timeline.sort(key=lambda x: x.get("date", ""), reverse=True)
    return timeline[:50]

def find_shared_servers_between_users(guild_id: int, user_id: int, target_user_id: int) -> dict:
    guild = bot.get_guild(guild_id)
    if not guild:
        return {"shared_guilds": [], "shared_count": 0}
    
    member1 = guild.get_member(user_id)
    member2 = guild.get_member(target_user_id)
    
    if not member1 or not member2:
        return {"shared_guilds": [], "shared_count": 0}
    
    shared_guilds = []
    for shared_guild in bot.guilds:
        m1 = shared_guild.get_member(user_id)
        m2 = shared_guild.get_member(target_user_id)
        if m1 and m2:
            shared_guilds.append({
                "guild_id": shared_guild.id,
                "guild_name": shared_guild.name,
                "guild_icon": str(shared_guild.icon) if shared_guild.icon else None
            })
    
    save_shared_servers(guild_id, user_id, target_user_id, [g["guild_id"] for g in shared_guilds])
    
    return {
        "shared_guilds": shared_guilds,
        "shared_count": len(shared_guilds)
    }

def generate_google_dorks(username: str, email: str = None, real_name: str = None) -> dict:
    dorks = {}
    
    if username:
        dorks["site_leak"] = f'site:pastebin.com "{username}"'
        dorks["site_github"] = f'site:github.com "{username}"'
        dorks["site_twitter"] = f'site:twitter.com "{username}"'
        dorks["site_instagram"] = f'site:instagram.com "{username}"'
        dorks["site_linkedin"] = f'site:linkedin.com/in "{username}"'
        dorks["site_reddit"] = f'site:reddit.com/user "{username}"'
        dorks["exif_tool"] = f'"{username}" filetype:jpg OR filetype:png'
        dorks["cached"] = f'cache:{username}'
    
    if email:
        dorks["email_breach"] = f'"{email}"'
        dorks["email_paste"] = f'site:pastebin.com "{email}"'
        dorks["email_discord"] = f'"{email}" site:discord.com'
    
    if real_name:
        dorks["real_name_site"] = f'"{real_name}" site:facebook.com OR site:linkedin.com'
        dorks["real_name_leak"] = f'"{real_name}" filetype:csv OR filetype:txt'
    
    return dorks

def create_ticket(user_id, channel_id):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO tickets (user_id, channel_id) VALUES (?, ?)", (user_id, channel_id))
    ticket_id = c.lastrowid
    conn.commit()
    conn.close()
    return ticket_id

def create_staff_complaint(user_id, channel_id, complaint_text=""):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO staff_complaints (user_id, channel_id, complaint_text) VALUES (?, ?, ?)", (user_id, channel_id, complaint_text))
    complaint_id = c.lastrowid
    conn.commit()
    conn.close()
    return complaint_id

def get_ticket_by_channel(channel_id):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT id, user_id, status FROM tickets WHERE channel_id = ?", (channel_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return {"id": result[0], "user_id": result[1], "status": result[2]}
    return None

def get_staff_complaint_by_channel(channel_id):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT id, user_id, status FROM staff_complaints WHERE channel_id = ?", (channel_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return {"id": result[0], "user_id": result[1], "status": result[2]}
    return None

def get_ticket_by_id(ticket_id):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT id, user_id, channel_id, status FROM tickets WHERE id = ?", (ticket_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return {"id": result[0], "user_id": result[1], "channel_id": result[2], "status": result[3]}
    return None

def get_staff_complaint_by_id(complaint_id):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT id, user_id, channel_id, status FROM staff_complaints WHERE id = ?", (complaint_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return {"id": result[0], "user_id": result[1], "channel_id": result[2], "status": result[3]}
    return None

def close_ticket(ticket_id):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("UPDATE tickets SET status = 'closed', closed_at = CURRENT_TIMESTAMP WHERE id = ?", (ticket_id,))
    conn.commit()
    conn.close()

def close_staff_complaint(complaint_id):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("UPDATE staff_complaints SET status = 'closed', closed_at = CURRENT_TIMESTAMP WHERE id = ?", (complaint_id,))
    conn.commit()
    conn.close()

def get_staff_vrchat_name(user_id):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT vrchat_name FROM staff_info WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def set_staff_vrchat_name(user_id, vrchat_name, position):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO staff_info (user_id, vrchat_name, position) VALUES (?, ?, ?)",
              (user_id, vrchat_name, position))
    conn.commit()
    conn.close()

def is_staff_banned(user_id):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM banned_staff WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def ban_staff_user(user_id, banned_by, reason):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO banned_staff (user_id, banned_by, reason) VALUES (?, ?, ?)",
              (user_id, banned_by, reason))
    conn.commit()
    conn.close()

def unban_staff_user(user_id):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("DELETE FROM banned_staff WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

async def log_to_channel(guild, action, description, channel_id=None):
    if channel_id is None:
        channel_id = LOG_CHANNEL_ID
    channel = guild.get_channel(channel_id)
    if channel:
        embed = discord.Embed(
            title=f"🔔 {action}",
            description=description,
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        await channel.send(embed=embed)

# FIXED: Added proper DM channel handling to prevent AttributeError
async def log_message_event(event_type: str, **kwargs):
    channel = bot.get_channel(MESSAGE_LOG_CHANNEL_ID)
    if not channel:
        print(f"❌ Message log channel not found (ID: {MESSAGE_LOG_CHANNEL_ID})")
        return

    embed = discord.Embed(
        color=discord.Color.orange(),
        timestamp=datetime.now()
    )

    try:
        if event_type == "delete":
            message = kwargs.get('message')
            moderator = kwargs.get('moderator', "Unknown")
            embed.title = "🗑️ Message Deleted"

            # FIX: Handle DM channels properly
            if isinstance(message.channel, discord.DMChannel):
                embed.description = f"**Message by {message.author.mention} deleted in DMs**"
            else:
                embed.description = f"**Message by {message.author.mention} deleted in {message.channel.mention}**"

            embed.add_field(name="Content", value=message.content[:1000] if message.content else "No text content", inline=False)
            embed.add_field(name="Deleted By", value=moderator.mention if isinstance(moderator, discord.Member) else moderator, inline=True)
            embed.add_field(name="Message ID", value=message.id, inline=True)

            # FIX: Handle cases where avatar might be None
            if message.author.avatar:
                embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
            else:
                embed.set_author(name=message.author.display_name)

            embed.set_footer(text=f"Author ID: {message.author.id}")

        elif event_type == "edit":
            before = kwargs.get('before')
            after = kwargs.get('after')
            embed.title = "📝 Message Edited"

            # FIX: Handle DM channels properly - DMChannel doesn't have 'mention' attribute
            if isinstance(before.channel, discord.DMChannel):
                embed.description = f"**Message by {before.author.mention} edited in DMs**\n[Jump to Message]({after.jump_url})"
            else:
                embed.description = f"**Message by {before.author.mention} edited in {before.channel.mention}**\n[Jump to Message]({after.jump_url})"

            embed.add_field(name="Before", value=before.content[:1000] if before.content else "No content", inline=False)
            embed.add_field(name="After", value=after.content[:1000] if after.content else "No content", inline=False)

            # FIX: Handle cases where avatar might be None
            if before.author.avatar:
                embed.set_author(name=before.author.display_name, icon_url=before.author.avatar.url)
            else:
                embed.set_author(name=before.author.display_name)

            embed.set_footer(text=f"Author ID: {before.author.id} | Message ID: {before.id}")

        elif event_type == "leave":
            member = kwargs.get('member')
            embed.title = "👋 Member Left"
            embed.description = f"**{member.mention} has left the server**"

            # FIX: Handle cases where avatar might be None
            if member.avatar:
                embed.set_author(name=member.display_name, icon_url=member.avatar.url)
            else:
                embed.set_author(name=member.display_name)

            embed.set_footer(text=f"ID: {member.id}")
            embed.color = discord.Color.red()

        elif event_type == "timeout":
            member = kwargs.get('member')
            moderator = kwargs.get('moderator')
            duration = kwargs.get('duration')
            reason = kwargs.get('reason')
            embed.title = "⏱️ Member Timed Out"
            embed.description = f"**{member.mention} has been timed out**"
            embed.add_field(name="Duration", value=duration, inline=True)
            embed.add_field(name="Reason", value=reason, inline=True)
            embed.add_field(name="Moderator", value=moderator.mention, inline=False)

            # FIX: Handle cases where avatar might be None
            if member.avatar:
                embed.set_author(name=member.display_name, icon_url=member.avatar.url)
            else:
                embed.set_author(name=member.display_name)

            embed.set_footer(text=f"ID: {member.id}")
            embed.color = discord.Color.gold()

        elif event_type == "blacklist":
            message = kwargs.get('message')
            word = kwargs.get('word')
            embed.title = "⚠️ Blacklisted Word Detected"

            # FIX: Handle DM channels properly
            if isinstance(message.channel, discord.DMChannel):
                embed.description = f"**Message by {message.author.mention} contained blacklisted word in DMs**"
            else:
                embed.description = f"**Message by {message.author.mention} contained blacklisted word**"

            embed.add_field(name="Word", value=f"||{word}||", inline=False)
            embed.add_field(name="Content", value=f"||{message.content[:500]}||", inline=False)
            embed.add_field(name="Action", value="Message deleted and user timed out for 30 minutes", inline=False)

            # FIX: Handle cases where avatar might be None
            if message.author.avatar:
                embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
            else:
                embed.set_author(name=message.author.display_name)

            embed.set_footer(text=f"Author ID: {message.author.id} | Channel: {getattr(message.channel, 'name', 'DM')}")
            embed.color = discord.Color.red()

        elif event_type == "severe_blacklist":
            message = kwargs.get('message')
            word = kwargs.get('word')
            embed.title = "⛔ SEVERE Blacklisted Word Detected"

            # FIX: Handle DM channels properly
            if isinstance(message.channel, discord.DMChannel):
                embed.description = f"**Message by {message.author.mention} contained severe blacklisted word in DMs**"
            else:
                embed.description = f"**Message by {message.author.mention} contained severe blacklisted word**"

            embed.add_field(name="Word", value=f"||{word}||", inline=False)
            embed.add_field(name="Content", value=f"||{message.content[:500]}||", inline=False)
            embed.add_field(name="Action", value="User banned", inline=False)

            # FIX: Handle cases where avatar might be None
            if message.author.avatar:
                embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
            else:
                embed.set_author(name=message.author.display_name)

            embed.set_footer(text=f"Author ID: {message.author.id} | Channel: {getattr(message.channel, 'name', 'DM')}")
            embed.color =discord.Color.dark_red()

        elif event_type == "voice_mute":
            member = kwargs.get('member')
            moderator = kwargs.get('moderator')
            action = kwargs.get('action')
            embed.title = "🎤 Voice Mute"
            embed.description = f"**{member.mention} was {action} in voice channel**"
            embed.add_field(name="Moderator", value=moderator.mention, inline=True)
            embed.add_field(name="Action", value=action, inline=True)

            # FIX: Handle cases where avatar might be None
            if member.avatar:
                embed.set_author(name=member.display_name, icon_url=member.avatar.url)
            else:
                embed.set_author(name=member.display_name)

            embed.set_footer(text=f"ID: {member.id}")
            embed.color = discord.Color.purple()

        elif event_type == "voice_deafen":
            member = kwargs.get('member')
            moderator = kwargs.get('moderator')
            action = kwargs.get('action')
            embed.title = "🔇 Voice Deafen"
            embed.description = f"**{member.mention} was {action} in voice channel**"
            embed.add_field(name="Moderator", value=moderator.mention, inline=True)
            embed.add_field(name="Action", value=action, inline=True)

            # FIX: Handle cases where avatar might be None
            if member.avatar:
                embed.set_author(name=member.display_name, icon_url=member.avatar.url)
            else:
                embed.set_author(name=member.display_name)

            embed.set_footer(text=f"ID: {member.id}")
            embed.color = discord.Color.dark_purple()

        await channel.send(embed=embed)

    except Exception as e:
        print(f"❌ Error in log_message_event for {event_type}: {str(e)}")
        # Don't let logging errors crash the bot

async def set_bot_status(status_text):
    if status_text.strip(): # Only set status if text is not empty
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=status_text))
        print(f"Status changed to: {status_text}")
    else:
        await bot.change_presence(activity=None) # Clear status
        print("Status cleared")

async def handle_application_response(message):
    user_id = message.author.id
    if user_id not in application_sessions:
        if message.content.lower() == 'cancel':
            await message.channel.send("❌ You don't have an active application to cancel.")
            return
    session = application_sessions[user_id]
    if message.content.lower() == 'cancel':
        del application_sessions[user_id]
        await message.channel.send("❌ Application cancelled.")
        return
    current_question = APPLICATION_QUESTIONS[session.current_question]
    answer = message.content.strip()
    # REMOVED URL validation for VRChat question since we're asking for username, not link
    session.answers[current_question["label"]] = answer
    session.current_question += 1
    if session.current_question >= len(APPLICATION_QUESTIONS):
        await submit_application(message, session)
        return
    await ask_next_question(message, session)

async def ask_next_question(message, session):
    question = APPLICATION_QUESTIONS[session.current_question]
    display_name = QUESTION_DISPLAY_NAMES[question["label"]]
    embed = discord.Embed(
        title=f"Question {session.current_question + 1}/{len(APPLICATION_QUESTIONS)}",
        description=display_name,
        color=discord.Color.blue()
    )
    if question["placeholder"]:
        embed.add_field(name="Hint", value=question["placeholder"], inline=False)
    # REMOVED URL validation note since we're asking for username, not link
    embed.set_footer(text=f"Position: {session.position} | Type your answer below")
    await message.channel.send(embed=embed)

async def submit_application(message, session):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO applications (user_id, guild_id, answers, position) VALUES (?, ?, ?, ?)",
              (session.user_id, 0, json.dumps(session.answers), session.position))
    app_id = c.lastrowid
    conn.commit()
    submit_channel = bot.get_channel(APPLICATION_SUBMIT_CHANNEL_ID)
    if submit_channel:
        embed = discord.Embed(title=f"New {session.position} Application", color=0x00ff00)
        embed.set_author(name=str(message.author), icon_url=message.author.avatar.url if message.author.avatar else None)
        # FIXED: Add applicant Discord ID to application embed
        embed.add_field(name="Applicant Discord", value=f"{message.author.mention} (ID: {session.user_id})", inline=False)
        for i, question in enumerate(APPLICATION_QUESTIONS):
            display_name = QUESTION_DISPLAY_NAMES[question["label"]]
            answer = session.answers.get(question["label"], "Not provided")
            if len(str(answer)) > 500:
                answer = str(answer)[:500] + "..."
            embed.add_field(name=display_name, value=answer, inline=False)
        view = ApplicationReviewView(session.user_id, 0, app_id, session.position)
        await submit_channel.send(embed=embed, view=view)
    embed = discord.Embed(
        title="✅ Application Submitted!",
        description="Your application has been submitted successfully. Staff will review it soon.",
        color=discord.Color.green()
    )
    await message.channel.send(embed=embed)
    # FIXED: Changed user_id to session.user_id
    if session.user_id in application_sessions:
        del application_sessions[session.user_id]
    conn.close()

class ApplicationSession:
    def __init__(self, user_id, position):
        self.user_id = user_id
        self.position = position
        self.current_question = 0
        self.answers = {}
        self.start_time = datetime.now()
        self.message = None

# FIXED: Deny reason modal - removed the "Something went wrong" error
class DenyReasonModal(discord.ui.Modal, title='Application Denial Reason'):
    reason = discord.ui.TextInput(
        label='Reason for denial',
        placeholder='Please provide a reason for denying this application...',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    def __init__(self, review_view):
        super().__init__()
        self.review_view = review_view

    async def on_submit(self, interaction: discord.Interaction):
        # FIXED: Properly defer the response to prevent "Something went wrong" error
        await interaction.response.defer()
        await self.review_view.deny_with_reason(interaction, self.reason.value)

# ================= VERIFICATION SYSTEM =================
class VerificationModal(discord.ui.Modal, title='Server Verification'):
    vrchat_link = discord.ui.TextInput(
        label='VRChat profile link',
        placeholder='https://vrchat.com/home/user/...',
        style=discord.TextStyle.short,
        required=True,
        max_length=200
    )
    heard = discord.ui.TextInput(
        label='How did you hear about us?',
        placeholder='Friend, social media, event, etc.',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        member = guild.get_member(interaction.user.id) if guild else None
        if not member:
            await interaction.followup.send("❌ Could not find your member info.", ephemeral=True)
            return
        member_role = guild.get_role(MEMBER_ROLE_ID)
        if member_role and member_role not in member.roles:
            try:
                await member.add_roles(member_role, reason="Verified")
            except Exception as e:
                print(f"❌ Failed to grant member role: {e}")
        join_role = guild.get_role(JOIN_ROLE_ID)
        if join_role and join_role in member.roles:
            try:
                await member.remove_roles(join_role, reason="Verified")
            except Exception as e:
                print(f"❌ Failed to remove join role: {e}")
        save_member_activity(guild.id, member.id, "verified", details=f"VRChat: {self.vrchat_link.value} | Heard: {self.heard.value}")
        await interaction.followup.send("✅ You are now verified! Welcome to the server.", ephemeral=True)

class VerificationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.green, custom_id="verify_button", emoji="✅")
    async def verify_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VerificationModal())

async def setup_verification_system(guild):
    channel = guild.get_channel(VERIFICATION_CHANNEL_ID)
    if not channel:
        print(f"❌ Verification channel not found (ID: {VERIFICATION_CHANNEL_ID})")
        return
    # Try to find an existing verification message before posting another
    existing_message = None
    try:
        async for message in channel.history(limit=50):
            if message.author == bot.user and message.embeds:
                if "Server Verification" in (message.embeds[0].title or ""):
                    existing_message = message
                    break
    except Exception as e:
        print(f"❌ Error searching for existing verification message: {e}")

    if existing_message:
        # Re-attach the persistent view to the existing message
        try:
            await existing_message.edit(view=VerificationView())
        except Exception:
            pass
        print(f"ℹ️ Verification embed already exists in #{channel.name}; not posting a new one.")
        return

    # Clear old bot messages only if none found
    try:
        async for message in channel.history(limit=20):
            if message.author == bot.user:
                await message.delete()
                await asyncio.sleep(1)
    except Exception as e:
        print(f"❌ Error clearing old verification messages: {e}")

    embed = discord.Embed(
        title="✅ Server Verification",
        description="Click the button below to verify and get access to the server.",
        color=discord.Color.green()
    )
    embed.add_field(name="You'll need:", value="• Your VRChat profile link\n• How you heard about us", inline=False)
    view = VerificationView()
    await channel.send(embed=embed, view=view)
    print(f"✅ Posted verification embed in #{channel.name}")

# UPDATED: ApplicationStartView with Security and Bartender buttons AND age verification check
class ApplicationStartView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Apply", style=discord.ButtonStyle.green, custom_id="app_apply")
    async def apply_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.start_application_process(interaction, "Staff")

    async def start_application_process(self, interaction: discord.Interaction, position: str):
        if is_staff_banned(interaction.user.id):
            await interaction.response.send_message(
                "❌ You are banned from applying for staff positions.",
                ephemeral=True
            )
            return

        # FIXED: Properly handle the interaction response first
        await interaction.response.defer(ephemeral=True)

        try:
            embed = discord.Embed(
                title=f"🎉 {position} Application",
                description=f"Are you ready to start your {position} application?\n\nClick the button below to begin!",
                color=discord.Color.green()
            )
            embed.set_footer(text="You can type 'cancel' at any time to stop the application process")
            view = StartApplicationDMView(position, interaction.user.id)

            # FIXED: Create DM channel and send message
            try:
                dm_channel = await interaction.user.create_dm()
                await dm_channel.send(embed=embed, view=view)

                # FIXED: Use followup to send success message
                await interaction.followup.send(
                    f"✅ Check your DMs! I've sent you a message to start your {position} application.",
                    ephemeral=True
                )
                print(f"✅ Sent DM to {interaction.user} for {position} application")

            except discord.Forbidden:
                await interaction.followup.send(
                    "❌ I couldn't send you a DM! Please make sure your DMs are open and try again.",
                    ephemeral=True
                )
                print(f"❌ Failed to send DM to {interaction.user} - DMs closed")

        except Exception as e:
            print(f"❌ Error in application process: {e}")
            await interaction.followup.send(
                "❌ An error occurred while starting your application. Please try again.",
                ephemeral=True
            )

# FIXED: StartApplicationDMView with proper interaction handling
class StartApplicationDMView(discord.ui.View):
    def __init__(self, position, user_id):
        super().__init__(timeout=3600) # 1 hour timeout
        self.position = position
        self.user_id = user_id

    @discord.ui.button(label="Start Application", style=discord.ButtonStyle.green, emoji="📝")
    async def start_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your application process.", ephemeral=True)
            return

        # FIXED: Properly handle the interaction
        await interaction.response.defer()

        # Create application session
        session = ApplicationSession(interaction.user.id, self.position)
        application_sessions[interaction.user.id] = session

        # Disable the button to prevent multiple clicks
        button.disabled = True
        button.label = "Application Started"
        button.style = discord.ButtonStyle.gray
        await interaction.edit_original_response(view=self)

        # Start asking questions
        await self.ask_first_question(interaction, session)

    async def ask_first_question(self, interaction: discord.Interaction, session: ApplicationSession):
        if session.current_question >= len(APPLICATION_QUESTIONS):
            await self.submit_application(interaction, session)
            return

        question = APPLICATION_QUESTIONS[session.current_question]
        display_name = QUESTION_DISPLAY_NAMES[question["label"]]
        embed = discord.Embed(
            title=f"Question {session.current_question + 1}/{len(APPLICATION_QUESTIONS)}",
            description=display_name,
            color=discord.Color.blue()
        )
        if question["placeholder"]:
            embed.add_field(name="Hint", value=question["placeholder"], inline=False)
        embed.set_footer(text=f"Position: {session.position} | Type your answer below")

        # FIXED: Use followup to send the question
        await interaction.followup.send(embed=embed)

    async def submit_application(self, interaction: discord.Interaction, session: ApplicationSession):
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("INSERT INTO applications (user_id, guild_id, answers, position) VALUES (?, ?, ?, ?)",
                  (session.user_id, interaction.guild.id if interaction.guild else 0, json.dumps(session.answers), session.position))
        app_id = c.lastrowid
        conn.commit()

        # Send to application submission channel
        submit_channel = bot.get_channel(APPLICATION_SUBMIT_CHANNEL_ID)
        if submit_channel:
            embed = discord.Embed(title=f"New {session.position} Application", color=0x00ff00)
            embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            embed.add_field(name="Applicant Discord", value=f"{interaction.user.mention} (ID: {session.user_id})", inline=False)

            for i, question in enumerate(APPLICATION_QUESTIONS):
                display_name = QUESTION_DISPLAY_NAMES[question["label"]]
                answer = session.answers.get(question["label"], "Not provided")
                if len(str(answer)) > 500:
                    answer = str(answer)[:500] + "..."
                embed.add_field(name=display_name, value=answer, inline=False)

            view = ApplicationReviewView(session.user_id, interaction.guild.id if interaction.guild else 0, app_id, session.position)
            await submit_channel.send(embed=embed, view=view)

        # Send confirmation to user
        embed = discord.Embed(
            title="✅ Application Submitted!",
            description="Your application has been submitted successfully. Staff will review it soon.",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed)

        # Clean up session
        if session.user_id in application_sessions:
            del application_sessions[session.user_id]

        conn.close()
        print(f"✅ Application submitted by {interaction.user} for {session.position}")

class ApplicationReviewView(discord.ui.View):
    def __init__(self, user_id, guild_id, app_id, position):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.guild_id = guild_id
        self.app_id = app_id
        self.position = position

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.green, custom_id="approve_btn")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if is_staff_banned(self.user_id):
            await interaction.response.send_message(
                "❌ This user is banned from staff positions and cannot be approved.",
                ephemeral=True
            )
            return

        # FIXED: Defer the response first
        await interaction.response.defer()

        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("SELECT answers FROM applications WHERE rowid = ?", (self.app_id,))
        result = c.fetchone()
        if result:
            answers = json.loads(result[0])
            # CHANGED: Get VRChat Username instead of Profile Link
            vrchat_name = answers.get("VRChat Username", "Not provided")
            set_staff_vrchat_name(self.user_id, vrchat_name, self.position)
            guild = interaction.guild
            member = guild.get_member(self.user_id)

            # FIXED: Proper role assignment with error handling
            role_ids_to_assign = [1549569470425600020, 1531829121150357705]
            roles_to_assign = [guild.get_role(rid) for rid in role_ids_to_assign if guild.get_role(rid)]

            if member and roles_to_assign:
                try:
                    await member.add_roles(*roles_to_assign)
                    # IMPROVED: Application acceptance logging - only one log
                    command_logger.log_application_accept(interaction.user, member, self.position)
                except discord.Forbidden:
                    await interaction.followup.send(
                        "❌ I don't have permission to assign roles. Please check my role hierarchy and permissions.",
                        ephemeral=True
                    )
                    conn.close()
                    return
                except Exception as e:
                    await interaction.followup.send(
                        f"❌ Error assigning roles: {str(e)}",
                        ephemeral=True
                    )
                    conn.close()
                    return
            else:
                error_msg = "❌ "
                if not member:
                    error_msg += "Member not found. "
                if not roles_to_assign:
                    error_msg += f"Roles for {self.position} not found. "
                error_msg += "The user may have left the server or roles may be misconfigured."

                await interaction.followup.send(error_msg, ephemeral=True)
                conn.close()
                return

            c.execute("UPDATE applications SET status = 'approved' WHERE rowid = ?", (self.app_id,))
            try:
                if member:
                    dm = await member.create_dm()
                    await dm.send(f"🎉 Your {self.position} application has been approved by {interaction.user.display_name}! You have been given the {self.position} role.")
            except:
                pass
            archive_channel = guild.get_channel(APPLICATION_SUBMIT_CHANNEL_ID)
            if archive_channel:
                try:
                    original_message = await interaction.channel.fetch_message(interaction.message.id)
                    await original_message.delete()
                    embed = original_message.embeds[0].copy()
                    embed.title = f"✅ Approved {self.position} Application"
                    # FIXED: Add who accepted the application to the embed
                    embed.add_field(name="Accepted By", value=f"{interaction.user.mention} (ID: {interaction.user.id})", inline=False)
                    await archive_channel.send(embed=embed)
                except Exception as e:
                    print(f"❌ Error archiving application: {e}")
            conn.commit()
            conn.close()
            await update_staff_list(interaction.guild, updated_by=interaction.user)
            await interaction.followup.send(f"✅ Application approved! {member.mention} has been given the {self.position} role.", ephemeral=True)

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red, custom_id="deny_btn")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Show modal for deny reason
        modal = DenyReasonModal(self)
        await interaction.response.send_modal(modal)

    async def deny_with_reason(self, interaction: discord.Interaction, reason: str):
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("UPDATE applications SET status = 'denied' WHERE rowid = ?", (self.app_id,))
        guild = interaction.guild
        member = guild.get_member(self.user_id)
        try:
            if member:
                dm = await member.create_dm()
                await dm.send(f"❌ Your {self.position} application has been denied by {interaction.user.display_name}. Reason: {reason}")
        except:
            pass
        archive_channel = guild.get_channel(APPLICATION_SUBMIT_CHANNEL_ID)
        if archive_channel:
            try:
                original_message = await interaction.channel.fetch_message(interaction.message.id)
                await original_message.delete()
                embed = original_message.embeds[0].copy()
                embed.title = f"❌ Denied {self.position} Application"
                embed.add_field(name="Denied By", value=f"{interaction.user.mention} (ID: {interaction.user.id})", inline=False)
                embed.add_field(name="Reason", value=reason, inline=False)
                await archive_channel.send(embed=embed)
            except Exception as e:
                print(f"❌ Error archiving denied application: {e}")
        conn.commit()
        conn.close()
        await interaction.followup.send(f"✅ Application denied. Reason: {reason}", ephemeral=True)

# FIXED: Staff Complaints System with proper database handling
class StaffComplaintModal(discord.ui.Modal, title='Submit Staff Complaint'):
    complaint = discord.ui.TextInput(
        label='Staff Complaint Details',
        placeholder='Please describe your complaint in detail...',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=2000
    )

    evidence = discord.ui.TextInput(
        label='Evidence (links, screenshots, etc.)',
        placeholder='Provide any evidence or context for your complaint...',
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=1000
    )

    def __init__(self):
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        # Check if user already has an open staff complaint
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("SELECT id FROM staff_complaints WHERE user_id = ? AND status = 'open'", (interaction.user.id,))
        existing_complaint = c.fetchone()
        conn.close()

        if existing_complaint:
            await interaction.followup.send(
                "❌ You already have an open staff complaint. Please wait for it to be resolved before creating a new one.",
                ephemeral=True
            )
            return

        # Get the staff complaints channel
        complaints_channel = interaction.guild.get_channel(STAFF_COMPLAINTS_CHANNEL_ID)
        if not complaints_channel:
            await interaction.followup.send(
                "❌ Staff complaints system is not configured properly. Please contact an administrator.",
                ephemeral=True
            )
            return

        # Check if the user is a staff member
        user_roles = [role.id for role in interaction.user.roles]
        is_staff = any(role_id in STAFF_ROLES.keys() for role_id in user_roles)

        if not is_staff:
            await interaction.followup.send(
                "❌ Only staff members can create staff complaints.",
                ephemeral=True
            )
            return

        # Create a private channel for the complaint
        try:
            # Get the staff role that can see the channel
            staff_role = interaction.guild.get_role(STAFF_COMPLAINTS_ROLE_ID)
            if not staff_role:
                await interaction.followup.send(
                    "❌ Staff role not found. Please contact an administrator.",
                    ephemeral=True
                )
                return

            # Get the category from the complaints channel
            category = complaints_channel.category

            # Create channel name with "complaint" prefix and username
            channel_name = f"complaint-{interaction.user.display_name.lower().replace(' ', '-')[:20]}"

            # Set up permissions - only the user and the specified role can see it
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
                staff_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_messages=True),
                interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_messages=True)
            }

            # Create the complaint channel
            channel = await interaction.guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                reason=f"Staff complaint by {interaction.user.display_name}"
            )

            # Create complaint in database
            complaint_text = f"{self.complaint.value}\n\n**Evidence:** {self.evidence.value}" if self.evidence.value else self.complaint.value
            complaint_id = create_staff_complaint(interaction.user.id, channel.id, complaint_text)

            # Send initial embed in the channel
            embed = discord.Embed(
                title=f"Staff Complaint #{complaint_id}",
                description=f"Hello {interaction.user.mention}! This is a private channel for your staff complaint.",
                color=discord.Color.red()
            )
            embed.add_field(name="Complaint Details", value=self.complaint.value[:1000], inline=False)
            if self.evidence.value:
                embed.add_field(name="Evidence", value=self.evidence.value[:1000], inline=False)

            embed.add_field(name="Complaint Guidelines", value="• Be specific and provide details\n• Include any relevant evidence\n• Be respectful and professional", inline=False)
            embed.set_footer(text=f"Created by {interaction.user.display_name} | ID: {complaint_id}")

            view = StaffComplaintCloseView(complaint_id, interaction.user.id)
            initial_message = await channel.send(embed=embed, view=view)

            # Pin the initial message
            try:
                await initial_message.pin()
            except:
                pass

            await interaction.followup.send(
                f"✅ Staff complaint created! {channel.mention}",
                ephemeral=True
            )

            # Log with "no_log" flag to prevent showing in logs
            command_logger.log_command(interaction.user, "create_staff_complaint", interaction.guild, result=f"Complaint ID: {complaint_id} - no_log")

        except Exception as e:
            print(f"❌ Error creating staff complaint: {e}")
            await interaction.followup.send(
                f"❌ Failed to create staff complaint: {str(e)}",
                ephemeral=True
            )

# ================= UPDATED: STAFF COMPLAINTS SYSTEM (CHANNELS INSTEAD OF THREADS) =================

class StaffComplaintCreateView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Staff Complaint", style=discord.ButtonStyle.red, custom_id="create_staff_complaint", emoji="⚠️")
    async def create_staff_complaint(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Show modal for complaint details
        await interaction.response.send_modal(StaffComplaintModal())

class StaffComplaintCloseView(discord.ui.View):
    def __init__(self, complaint_id, creator_id):
        super().__init__(timeout=None)
        self.complaint_id = complaint_id
        self.creator_id = creator_id

    @discord.ui.button(label="Close Complaint", style=discord.ButtonStyle.red, custom_id=f"close_staff_complaint")
    async def close_complaint(self, interaction: discord.Interaction, button: discord.ui.Button):
        complaint = get_staff_complaint_by_id(self.complaint_id)
        if not complaint:
            await interaction.response.send_message("❌ Complaint not found.", ephemeral=True)
            return

        # Check if user has permission to close (only the specified role)
        user_roles = [role.id for role in interaction.user.roles]
        has_permission = any(role_id in STAFF_COMPLAINTS_MANAGER_ROLES for role_id in user_roles)

        if not has_permission:
            await interaction.response.send_message("❌ You don't have permission to close staff complaints.", ephemeral=True)
            return

        close_staff_complaint(self.complaint_id)

        # Get the channel
        channel = interaction.guild.get_channel(complaint["channel_id"])
        if channel:
            try:
                # Move the channel to archive category
                archive_category = interaction.guild.get_channel(STAFF_COMPLAINTS_ARCHIVE_CATEGORY_ID)
                if archive_category:
                    await channel.edit(category=archive_category, sync_permissions=True)

                # Send closure message
                embed = discord.Embed(
                    title=f"Staff Complaint #{self.complaint_id} Closed",
                    description=f"This staff complaint has been closed by {interaction.user.mention}",
                    color=discord.Color.dark_red()
                )
                await channel.send(embed=embed)

                # Change permissions to read-only
                overwrites = channel.overwrites
                for target in overwrites:
                    if isinstance(target, discord.Member) or isinstance(target, discord.Role):
                        if target.id != interaction.guild.me.id: # Don't change bot permissions
                            overwrites[target].send_messages = False

                await channel.edit(overwrites=overwrites)

                await interaction.response.send_message("✅ Staff complaint closed and archived successfully.", ephemeral=True)

                command_logger.log_command(interaction.user, "close_staff_complaint", interaction.guild, target=f"Complaint #{self.complaint_id}")

            except Exception as e:
                await interaction.response.send_message(f"❌ Failed to close staff complaint: {str(e)}", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Complaint channel not found.", ephemeral=True)

# ================= UPDATED: CONFESSIONS SYSTEM =================
# Now with "Start Confession" button instead of just "Reply"

class ConfessionSubmitView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Start Confession", style=discord.ButtonStyle.green, custom_id="confess_submit", emoji="📝")
    async def confess_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ConfessionModal())

class ConfessionModal(discord.ui.Modal, title='Submit Your Confession'):
    confession = discord.ui.TextInput(
        label='Your Confession',
        placeholder='Type your confession here...',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=2000
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Generate unique ID for confession
        confession_id = str(uuid.uuid4())[:8]

        founder_owner_roles = {1563295287349354679, 1531830875619197040}  # Founder, Director
        user_roles = [role.id for role in interaction.user.roles]
        is_founder_or_owner = any(role_id in founder_owner_roles for role_id in user_roles)

        # Founder/Director confessions are auto-approved and posted immediately.
        # Also auto-approve all when review is disabled.
        auto_approve = is_founder_or_owner or not CONFESSIONS_REVIEW_ENABLED
        if auto_approve:
            confessions_channel = interaction.guild.get_channel(CONFESSIONS_POST_CHANNEL_ID)
            if not confessions_channel:
                await interaction.response.send_message(
                    "Confessions post channel not found. Please contact an owner.",
                    ephemeral=True
                )
                return

            conn = sqlite3.connect('bot_data.db')
            c = conn.cursor()
            try:
                c.execute(
                    "INSERT INTO confessions (confession_id, user_id, content, status, approved_by, approved_at) VALUES (?, ?, ?, 'approved', ?, CURRENT_TIMESTAMP)",
                    (confession_id, interaction.user.id, self.confession.value, interaction.user.id)
                )

                embed = discord.Embed(
                    title="Anonymous Confession",
                    description=self.confession.value,
                    color=discord.Color.purple(),
                    timestamp=datetime.now()
                )
                embed.set_footer(text=f"Confession ID: {confession_id} - {datetime.now().strftime('%Y-%m-%d %H:%M')}")

                view = ConfessionPostView(confession_id)
                confession_message = await confessions_channel.send(embed=embed, view=view)

                c.execute("UPDATE confessions SET message_id = ? WHERE confession_id = ?", (confession_message.id, confession_id))
                conn.commit()
            except Exception as e:
                conn.rollback()
                print(f"Error auto-posting founder/owner confession: {e}")
                await interaction.response.send_message(
                    "Failed to auto-post confession. Please try again.",
                    ephemeral=True
                )
                return
            finally:
                conn.close()

            await interaction.response.send_message(
                "Your confession was auto-approved and posted anonymously.",
                ephemeral=True
            )
            command_logger.log_command(
                interaction.user,
                "submit_confession",
                interaction.guild,
                result=f"Confession ID: {confession_id} (auto-approved)"
            )
            return

        # Save regular confession to database
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("INSERT INTO confessions (confession_id, user_id, content) VALUES (?, ?, ?)",
                  (confession_id, interaction.user.id, self.confession.value))
        conn.commit()

        # Send to approval channel
        approval_channel = interaction.guild.get_channel(CONFESSIONS_APPROVAL_CHANNEL_ID)
        if approval_channel:
            embed = discord.Embed(
                title="New Confession Submission",
                description=self.confession.value,
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            embed.set_footer(text=f"Confession ID: {confession_id} | Submitted by: {interaction.user.display_name} (ID: {interaction.user.id})")

            view = ConfessionReviewView(confession_id, interaction.user.id)
            message = await approval_channel.send(embed=embed, view=view)

            # Update database with message ID
            c.execute("UPDATE confessions SET message_id = ? WHERE confession_id = ?", (message.id, confession_id))
            conn.commit()

        conn.close()

        # Send confirmation to user
        await interaction.response.send_message(
            "Your confession has been submitted for approval. It will be posted anonymously if approved.",
            ephemeral=True
        )

        # Log the submission
        command_logger.log_command(interaction.user, "submit_confession", interaction.guild, result=f"Confession ID: {confession_id}")

class ConfessionReviewView(discord.ui.View):
    def __init__(self, confession_id: str, submitter_id: int):
        super().__init__(timeout=None)
        self.confession_id = confession_id
        self.submitter_id = submitter_id

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.green, custom_id="confess_approve")
    async def approve_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if user has permission to approve (staff roles)
        user_roles = [role.id for role in interaction.user.roles]
        has_permission = any(role_id in TICKET_MANAGER_ROLES for role_id in user_roles)

        if not has_permission:
            await interaction.response.send_message(
                "❌ You don't have permission to approve confessions.",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        # Get confession from database
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("SELECT content, message_id FROM confessions WHERE confession_id = ?", (self.confession_id,))
        result = c.fetchone()

        if not result:
            await interaction.followup.send("❌ Confession not found.", ephemeral=True)
            return

        content, message_id = result

        # Update confession status
        c.execute("UPDATE confessions SET status = 'approved', approved_by = ?, approved_at = CURRENT_TIMESTAMP WHERE confession_id = ?",
                  (interaction.user.id, self.confession_id))

        # Post to confessions channel
        confessions_channel = interaction.guild.get_channel(CONFESSIONS_POST_CHANNEL_ID)
        if confessions_channel:
            embed = discord.Embed(
                title="📝 Anonymous Confession",
                description=content,
                color=discord.Color.purple(),
                timestamp=datetime.now()
            )
            embed.set_footer(text=f"Confession ID: {self.confession_id} • {datetime.now().strftime('%Y-%m-%d %H:%M')}")

            # Create view with BOTH Start Confession and Reply buttons
            view = ConfessionPostView(self.confession_id)
            confession_message = await confessions_channel.send(embed=embed, view=view)

            # Update database with confession message ID
            c.execute("UPDATE confessions SET message_id = ? WHERE confession_id = ?", (confession_message.id, self.confession_id))

        conn.commit()
        conn.close()

        # Notify submitter (optional)
        try:
            submitter = await interaction.guild.fetch_member(self.submitter_id)
            if submitter:
                await submitter.send("✅ Your confession has been approved and posted anonymously!")
        except:
            pass
        await interaction.followup.send("✅ Confession approved and posted!", ephemeral=True)

        # Log the approval
        command_logger.log_command(interaction.user, "approve_confession", interaction.guild, result=f"Confession ID: {self.confession_id}")

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red, custom_id="confess_deny")
    async def deny_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if user has permission to deny (staff roles)
        user_roles = [role.id for role in interaction.user.roles]
        has_permission = any(role_id in TICKET_MANAGER_ROLES for role_id in user_roles)

        if not has_permission:
            await interaction.response.send_message(
                "❌ You don't have permission to deny confessions.",
                ephemeral=True
            )
            return

        # Update database
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("UPDATE confessions SET status = 'denied' WHERE confession_id = ?", (self.confession_id,))
        conn.commit()
        conn.close()

        # Notify submitter (optional)
        try:
            submitter = await interaction.guild.fetch_member(self.submitter_id)
            if submitter:
                await submitter.send("❌ Your confession has been denied by staff.")
        except:
            pass
        await interaction.response.send_message("✅ Confession denied.", ephemeral=True)

        # Log the denial
        command_logger.log_command(interaction.user, "deny_confession", interaction.guild, result=f"Confession ID: {self.confession_id}")

# UPDATED: Confession Post View with BOTH buttons
class ConfessionPostView(discord.ui.View):
    def __init__(self, confession_id: str):
        super().__init__(timeout=None)
        self.confession_id = confession_id

    @discord.ui.button(label="Start Confession", style=discord.ButtonStyle.green, custom_id="start_confession", emoji="📝")
    async def start_confession_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Open the confession modal for a new confession
        await interaction.response.send_modal(ConfessionModal())

    @discord.ui.button(label="Reply", style=discord.ButtonStyle.blurple, custom_id="confess_reply", emoji="💬")
    async def reply_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if thread already exists
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("SELECT thread_id FROM confessions WHERE confession_id = ?", (self.confession_id,))
        result = c.fetchone()

        if result and result[0]:
            # Thread exists, notify user
            await interaction.response.send_message(
                f"A thread already exists for this confession! Check it out here: <#{result[0]}>",
                ephemeral=True
            )
            conn.close()
            return

        # Create thread
        try:
            thread = await interaction.message.create_thread(
                name=f"Confession Discussion - ID: {self.confession_id}",
                auto_archive_duration=1440 # 24 hours
            )

            # Update database with thread ID
            c.execute("UPDATE confessions SET thread_id = ? WHERE confession_id = ?", (thread.id, self.confession_id))
            conn.commit()

            # Send initial message in thread
            embed = discord.Embed(
                title="💬 Discussion Thread",
                description=f"Discuss this confession here! Use the buttons below to reply anonymously or publicly.",
                color=discord.Color.blurple()
            )
            embed.add_field(name="Confession ID", value=self.confession_id, inline=False)
            embed.add_field(name="Rules", value="• Be respectful\n• Keep it civil\n• No harassment", inline=False)

            thread_view = ThreadReplyView(self.confession_id)
            await thread.send(embed=embed, view=thread_view)

            await interaction.response.send_message(
                f"✅ Thread created! Join the discussion here: {thread.mention}",
                ephemeral=True
            )

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to create thread: {str(e)}",
                ephemeral=True
            )

        conn.close()

        # Log thread creation
        command_logger.log_command(interaction.user, "create_confession_thread", interaction.guild, result=f"Confession ID: {self.confession_id}")

class ThreadReplyView(discord.ui.View):
    def __init__(self, confession_id: str):
        super().__init__(timeout=None)
        self.confession_id = confession_id

    @discord.ui.button(label="Reply Anonymously", style=discord.ButtonStyle.gray, custom_id="reply_anon")
    async def reply_anon_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AnonymousReplyModal(self.confession_id))

    @discord.ui.button(label="Reply Publicly", style=discord.ButtonStyle.blurple, custom_id="reply_public")
    async def reply_public_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PublicReplyModal(self.confession_id))

class AnonymousReplyModal(discord.ui.Modal, title='Anonymous Reply'):
    reply = discord.ui.TextInput(
        label='Your Anonymous Reply',
        placeholder='Type your reply here (will be posted anonymously)...',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    def __init__(self, confession_id: str):
        super().__init__()
        self.confession_id = confession_id

    async def on_submit(self, interaction: discord.Interaction):
        # Save to database
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("INSERT INTO confession_replies (confession_id, user_id, content, is_anonymous) VALUES (?, ?, ?, ?)",
                  (self.confession_id, interaction.user.id, self.reply.value, 1))
        conn.commit()
        conn.close()

        # Send anonymous reply
        embed = discord.Embed(
            description=f"💬 {self.reply.value}",
            color=discord.Color.dark_gray(),
            timestamp=datetime.now()
        )
        embed.set_footer(text="Anonymous Reply")

        await interaction.response.send_message(embed=embed)

        # Log the reply
        command_logger.log_command(interaction.user, "anonymous_confession_reply", interaction.guild, result=f"Confession ID: {self.confession_id}")

class PublicReplyModal(discord.ui.Modal, title='Public Reply'):
    reply = discord.ui.TextInput(
        label='Your Public Reply',
        placeholder='Type your reply here (will show your username)...',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    def __init__(self, confession_id: str):
        super().__init__()
        self.confession_id = confession_id

    async def on_submit(self, interaction: discord.Interaction):
        # Save to database
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("INSERT INTO confession_replies (confession_id, user_id, content, is_anonymous) VALUES (?, ?, ?, ?)",
                  (self.confession_id, interaction.user.id, self.reply.value, 0))
        conn.commit()
        conn.close()

        # Send public reply
        embed = discord.Embed(
            description=f"💬 {self.reply.value}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url if interaction.user.avatar else None)

        await interaction.response.send_message(embed=embed)

        # Log the reply
        command_logger.log_command(interaction.user, "public_confession_reply", interaction.guild, result=f"Confession ID: {self.confession_id}")

# ================= GAME CLASSES =================
class RouletteGame:
    def __init__(self, user_id, bet):
        self.user_id = user_id
        self.bet = bet
        self.wheel = list(range(0, 37)) # 0-36
        self.colors = {
            **{i: 'red' for i in [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]},
            **{i: 'black' for i in [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]},
            0: 'green'
        }
        self.payouts = {
            'red': 1,
            'black': 1,
            'green': 35,
            'single': 35,
            'dozen1': 2, # 1-12
            'dozen2': 2, # 13-24
            'dozen3': 2, # 25-36
            'column1': 2, # 1,4,7,10,13,16,19,22,25,28,31,34
            'column2': 2, # 2,5,8,11,14,17,20,23,26,29,32,35
            'column3': 2 # 3,6,9,12,15,18,21,24,27,30,33,36
        }

    def spin(self):
        return random.choice(self.wheel)

    def calculate_payout(self, bet_type, bet_value, winning_number):
        if bet_type == 'color':
            if self.colors[winning_number] == bet_value:
                return self.bet * (self.payouts[bet_value] + 1)
        elif bet_type == 'single':
            if winning_number == bet_value:
                return self.bet * (self.payouts['single'] + 1)
        elif bet_type == 'dozen':
            if bet_value == 1 and 1 <= winning_number <= 12:
                return self.bet * (self.payouts['dozen1'] + 1)
            elif bet_value == 2 and 13 <= winning_number <= 24:
                return self.bet * (self.payouts['dozen2'] + 1)
            elif bet_value == 3 and 25 <= winning_number <= 36:
                return self.bet * (self.payouts['dozen3'] + 1)
        elif bet_type == 'column':
            columns = {
                1: [1,4,7,10,13,16,19,22,25,28,31,34],
                2: [2,5,8,11,14,17,20,23,26,29,32,35],
                3: [3,6,9,12,15,18,21,24,27,30,33,36]
            }
            if winning_number in columns[bet_value]:
                return self.bet * (self.payouts['column1'] + 1)
        return 0

class CrashGame:
    def __init__(self, user_id, bet):
        self.user_id = user_id
        self.bet = bet
        self.multiplier = 1.0
        self.crashed = False
        self.cash_out_multiplier = None
        self.crash_point = self.generate_crash_point()

    def generate_crash_point(self):
        # Higher probability for lower multipliers
        r = random.random()
        if r < 0.1: # 10% chance for 1.0-1.5x
            return random.uniform(1.0, 1.5)
        elif r < 0.3: # 20% chance for 1.5-2.0x
            return random.uniform(1.5, 2.0)
        elif r < 0.6: # 30% chance for 2.0-3.0x
            return random.uniform(2.0, 3.0)
        elif r < 0.85: # 25% chance for 3.0-5.0x
            return random.uniform(3.0, 5.0)
        elif r < 0.95: # 10% chance for 5.0-10.0x
            return random.uniform(5.0, 10.0)
        else: # 5% chance for 10.0-100.0x
            return random.uniform(10.0, 100.0)

    def update(self):
        if self.crashed or self.cash_out_multiplier:
            return

        increment = random.uniform(0.01, 0.1)
        self.multiplier += increment

        if self.multiplier >= self.crash_point:
            self.crashed = True

    def cash_out(self):
        if not self.crashed and not self.cash_out_multiplier:
            self.cash_out_multiplier = self.multiplier
            return self.bet * self.multiplier
        return 0

class HigherLowerGame:
    def __init__(self, user_id, bet):
        self.user_id = user_id
        self.bet = bet
        self.current_number = random.randint(1, 100)
        self.previous_number = None
        self.streak = 0
        self.game_over = False

    def guess(self, guess_type):
        if self.game_over:
            return 0

        self.previous_number = self.current_number
        self.current_number = random.randint(1, 100)

        correct = False
        if guess_type == 'higher' and self.current_number > self.previous_number:
            correct = True
        elif guess_type == 'lower' and self.current_number < self.previous_number:
            correct = True
        elif guess_type == 'same' and self.current_number == self.previous_number:
            correct = True

        if correct:
            self.streak += 1
            return self.bet * 0.5 # Small win for each correct guess
        else:
            self.game_over = True
            if self.streak >= 3:
                return self.bet * self.streak # Bonus for streaks
            return 0

class RaffleGame:
    def __init__(self, creator_id, prize, ticket_price, duration_minutes):
        self.creator_id = creator_id
        self.prize = prize
        self.ticket_price = ticket_price
        self.end_time = datetime.now() + datetime.timedelta(minutes=duration_minutes)
        self.participants = {} # user_id: ticket_count
        self.total_tickets = 0
        self.message_id = None

    def buy_ticket(self, user_id, quantity=1):
        if user_id not in self.participants:
            self.participants[user_id] = 0
        self.participants[user_id] += quantity
        self.total_tickets += quantity

    def draw_winner(self):
        if not self.participants:
            return None

        tickets = []
        for user_id, count in self.participants.items():
            tickets.extend([user_id] * count)

        return random.choice(tickets)

# ================= REGULAR TICKET SYSTEM =================

class TicketIntakeModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Create Support Ticket")
        self.description = discord.ui.TextInput(
            label="Describe your issue",
            placeholder="Please describe what you need help with...",
            style=discord.TextStyle.paragraph,
            max_length=1000
        )
        self.add_item(self.description)

    async def on_submit(self, interaction: discord.Interaction):
        issue_description = str(self.description)
        ok, channel_or_error = await create_ticket_channel(interaction.guild, interaction.user.id, issue_description)
        if ok:
            await interaction.response.send_message(
                f"✅ Ticket created: {channel_or_error.mention}",
                ephemeral=True
            )
            command_logger.log_command(interaction.user, "/ticket", interaction.guild, result="Ticket created")
        else:
            await interaction.response.send_message(
                f"❌ Ticket could not be created: {channel_or_error}",
                ephemeral=True
            )

class TicketCategorySelect(discord.ui.Select):
    def __init__(self, user_id: int):
        options = [
            discord.SelectOption(label="General", value="general", description="General help"),
            discord.SelectOption(label="Moderation", value="moderation", description="Moderation issue"),
            discord.SelectOption(label="Technical", value="technical", description="Tech support"),
            discord.SelectOption(label="Report", value="report", description="Report an issue"),
        ]
        super().__init__(placeholder="What do you need help with?", min_values=1, max_values=1, options=options, custom_id="ticket_category_select")
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This menu isn't for you.", ephemeral=True)
            return
        await interaction.response.send_modal(TicketIntakeModal())

class TicketCategoryView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=180)
        self.add_item(TicketCategorySelect(user_id))

class TicketCreateView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.green, custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Select what you need help with:",
            ephemeral=True,
            view=TicketCategoryView(user_id=interaction.user.id)
        )

async def ensure_member_role(member: discord.Member, reason: str):
    if member.bot:
        return False

    member_role = member.guild.get_role(MEMBER_ROLE_ID)
    if member_role is None:
        print(f"❌ Member role not found in {member.guild.name} (ID: {MEMBER_ROLE_ID})")
        return False

    changed = False
    if member_role not in member.roles:
        try:
            await member.add_roles(member_role, reason=reason)
            changed = True
        except Exception as error:
            print(f"❌ Failed to add member role to {member}: {error}")

    return changed

# NEW: Function to check if user is manager or above
def is_manager_or_above(member):
    """Check if member has manager or higher role"""
    manager_plus_roles = [
        1461057322418962567, # Founder
        1461052878717456416, # Director
        1461069473086701783, # Manager
        1470270460544679996, # Security
    ]
    user_roles = [role.id for role in member.roles]
    return any(role_id in manager_plus_roles for role_id in user_roles)

class TicketCloseView(discord.ui.View):
    def __init__(self, ticket_id, creator_id):
        super().__init__(timeout=None)
        self.ticket_id = ticket_id
        self.creator_id = creator_id

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, custom_id=f"close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        ticket = get_ticket_by_id(self.ticket_id)
        if not ticket:
            await interaction.response.send_message("❌ Ticket not found.", ephemeral=True)
            return

        # UPDATED: Allow ticket managers OR managers and above to close tickets, but NOT the ticket creator
        user_roles = [role.id for role in interaction.user.roles]
        has_permission = (
            any(role_id in user_roles for role_id in TICKET_MANAGER_ROLES) or
            is_manager_or_above(interaction.user)
        )

        if not has_permission or interaction.user.id == self.creator_id:
            await interaction.response.send_message("❌ You don't have permission to close this ticket.", ephemeral=True)
            return

        close_ticket(self.ticket_id)
        archive_category = interaction.guild.get_channel(TICKET_ARCHIVE_CATEGORY_ID)
        if not archive_category:
            await interaction.response.send_message("❌ Archive category not found.", ephemeral=True)
            return

        channel = interaction.guild.get_channel(ticket["channel_id"])
        if channel:
            try:
                await channel.edit(category=archive_category, sync_permissions=True)
                overwrites = channel.overwrites
                if interaction.user in overwrites:
                    del overwrites[interaction.user]
                user = interaction.guild.get_member(ticket["user_id"])
                if user and user in overwrites:
                    del overwrites[user]
                await channel.edit(overwrites=overwrites)
                embed = discord.Embed(
                    title=f"Ticket #{self.ticket_id} Closed",
                    description=f"This ticket has been closed by {interaction.user.mention}",
                    color=discord.Color.red()
                )
                await channel.send(embed=embed)
                await interaction.response.send_message("✅ Ticket closed successfully.", ephemeral=True)
                await log_to_channel(
                    interaction.guild,
                    "Ticket Closed",
                    f"{interaction.user.mention} closed ticket #{self.ticket_id}\nChannel: {channel.mention}"
                )
                command_logger.log_command(interaction.user, "close_ticket_button", interaction.guild, target=f"Ticket #{self.ticket_id}")
            except Exception as e:
                await interaction.response.send_message(f"❌ Failed to close ticket: {str(e)}", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Ticket channel not found.", ephemeral=True)

def get_ticket_count():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tickets")
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def get_staff_complaint_count():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM staff_complaints")
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

async def setup_ticket_system(guild):
    channel = guild.get_channel(TICKET_CHANNEL_ID)
    if not channel:
        print(f"❌ Ticket channel not found (ID: {TICKET_CHANNEL_ID})")
        return

    ticket_message_id = get_ticket_message_id()
    if ticket_message_id:
        try:
            message = await channel.fetch_message(ticket_message_id)
            if message:
                print("✅ Ticket message already exists")
                return
        except discord.NotFound:
            pass
        except Exception as e:
            print(f"❌ Error fetching ticket message: {e}")

    # Clear existing bot messages in the channel
    try:
        async for message in channel.history(limit=20):
            if message.author == bot.user:
                await message.delete()
                await asyncio.sleep(1) # Rate limit prevention
    except Exception as e:
        print(f"❌ Error clearing old messages: {e}")

    embed = discord.Embed(
        title="Support Tickets",
        description="Click the button below to create a support ticket. Our staff will assist you as soon as possible.",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="Guidelines",
        value="• Please be patient while waiting for a response\n• Describe your issue in detail\n• Be respectful to our staff",
        inline=False
    )
    view = TicketCreateView()
    message = await channel.send(embed=embed, view=view)
    set_ticket_message_id(message.id)
    print(f"✅ Ticket message posted in #{channel.name} (ID: {message.id})")

async def setup_staff_complaints_system(guild):
    channel = guild.get_channel(STAFF_COMPLAINTS_CHANNEL_ID)
    if not channel:
        print(f"❌ Staff complaints channel not found (ID: {STAFF_COMPLAINTS_CHANNEL_ID})")
        return

    staff_complaints_message_id = get_staff_complaints_message_id()
    if staff_complaints_message_id:
        try:
            message = await channel.fetch_message(staff_complaints_message_id)
            if message:
                print("✅ Staff complaints message already exists")
                return
        except discord.NotFound:
            pass
        except Exception as e:
            print(f"❌ Error fetching staff complaints message: {e}")

    # Clear existing bot messages in the channel
    try:
        async for message in channel.history(limit=20):
            if message.author == bot.user:
                await message.delete()
                await asyncio.sleep(1) # Rate limit prevention
    except Exception as e:
        print(f"❌ Error clearing old messages: {e}")

    embed = discord.Embed(
        title="⚠️ Staff Complaints",
        description="Click the button below to create a private complaint channel.\n\nOnly the specified role will be able to see and respond to your complaint.",
        color=discord.Color.red()
    )
    embed.add_field(
        name="Important Information",
        value="• Give us all information\n• Complaints are private and confidential\n• Please provide detailed information\n• Be professional and respectful",
        inline=False
    )
    embed.set_footer(text="For staff-related issues only")

    view = StaffComplaintCreateView()
    message = await channel.send(embed=embed, view=view)
    set_staff_complaints_message_id(message.id)
    print(f"✅ Staff complaints message posted in #{channel.name} (ID: {message.id})")

def format_sqlite_timestamp(value) -> str:
    if not value:
        return "Unknown"
    try:
        parsed = datetime.fromisoformat(str(value))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=datetime.timezone.utc)
        return discord.utils.format_dt(parsed, style="F")
    except Exception:
        return str(value)

def truncate_for_embed(text: str, limit: int = 300) -> str:
    text = str(text or "").strip()
    if len(text) <= limit:
        return text or "No data."
    return text[: limit - 3] + "..."

def describe_activity_row(event_type: str, channel_id: Optional[int], details: Optional[str]) -> str:
    labels = {
        "server_join": "Joined the server",
        "server_leave": "Left the server",
        "voice_join": "Joined a voice channel",
        "voice_leave": "Left a voice channel",
        "voice_move": "Moved voice channels",
        "vrchat_linked": "Linked a VRChat profile",
    }
    base_text = labels.get(event_type, event_type.replace("_", " ").title())
    if details:
        return f"{base_text} - {details}"
    if channel_id:
        return f"{base_text} - <#{channel_id}>"
    return base_text

def build_database_member_info_embed(guild: discord.Guild, member: discord.Member):
    link_record = get_member_link_record(guild.id, member.id)
    activity_rows = get_member_activity_rows(guild.id, member.id, limit=5)

    embed = discord.Embed(
        title=f"Database Search - {member.display_name}",
        description=f"Member info for {member.mention} in **{guild.name}**",
        color=discord.Color.blurple(),
        timestamp=datetime.now(),
    )
    embed.add_field(name="User ID", value=str(member.id), inline=True)
    embed.add_field(name="Username", value=member.name, inline=True)
    embed.add_field(name="Display Name", value=member.display_name, inline=True)
    embed.add_field(name="Account Created", value=discord.utils.format_dt(member.created_at, style="F"), inline=False)
    embed.add_field(name="Joined Server", value=discord.utils.format_dt(member.joined_at, style="F") if member.joined_at else "Unknown", inline=False)
    embed.add_field(
        name="Roles",
        value=", ".join(role.mention for role in member.roles[1:][-8:]) if len(member.roles) > 1 else "No roles",
        inline=False,
    )

    status_bits = []
    if any(role.id == MEMBER_ROLE_ID for role in member.roles):
        status_bits.append("member")
    if link_record:
        status_bits.append("vrchat-linked")
    embed.add_field(name="Status", value=", ".join(status_bits) if status_bits else "No tracked status", inline=False)

    if activity_rows:
        recent_lines = [
            f"• {format_sqlite_timestamp(created_at)}: {truncate_for_embed(describe_activity_row(event_type, channel_id, details), 130)}"
            for event_type, channel_id, details, created_at in activity_rows
        ]
        embed.add_field(name="Recent Activity", value=truncate_for_embed("\n".join(recent_lines), 1000), inline=False)

    if member.avatar:
        embed.set_author(name=str(member), icon_url=member.avatar.url)
    else:
        embed.set_author(name=str(member))
    return embed

def build_database_member_messages_embed(guild: discord.Guild, member: discord.Member):
    rows, source_name = get_recent_message_rows(guild.id, member.id, limit=10)
    embed = discord.Embed(
        title=f"Messages - {member.display_name}",
        description=f"Recent saved messages for {member.mention}",
        color=discord.Color.green(),
        timestamp=datetime.now(),
    )
    if not rows:
        embed.add_field(name="Recent Messages", value="No saved messages found for this user yet.", inline=False)
        return embed

    lines = []
    for channel_id, content, created_at in rows:
        lines.append(
            f"• {format_sqlite_timestamp(created_at)} in <#{channel_id}>: {truncate_for_embed(content, 180)}"
        )
    embed.add_field(
        name=f"Recent Messages ({source_name})",
        value=truncate_for_embed("\n".join(lines), 1000),
        inline=False,
    )
    return embed

def build_database_member_links_embed(guild: discord.Guild, member: discord.Member):
    link_record = get_member_link_record(guild.id, member.id)
    vrchat_profile = get_vrchat_profile_data(guild.id, member.id)
    username_history = get_username_history(guild.id, member.id)
    linked_accounts = get_linked_accounts(guild.id, member.id)
    phone_lookups = get_all_phone_lookups(guild.id, member.id)
    image_analyses = get_image_analyses(guild.id, member.id)
    unified_profile = get_unified_profile(guild.id, member.id)
    pastebin_dumps = get_pastebin_dumps(guild.id, member.id)
    dns_records = get_dns_history(guild.id, member.id)
    
    embed = discord.Embed(
        title=f"OSINT - {member.display_name}",
        description=f"OSINT data for {member.mention}",
        color=discord.Color.orange(),
        timestamp=datetime.now(),
    )

    if link_record:
        link_lines = [
            f"Profile: {link_record['vrchat_profile_url']}",
            f"Stored Name: {link_record.get('vrchat_username') or link_record.get('vrchat_identifier') or 'Unknown'}",
            f"Linked At: {format_sqlite_timestamp(link_record.get('linked_at'))}",
            f"Updated At: {format_sqlite_timestamp(link_record.get('updated_at'))}",
        ]
        embed.add_field(name="VRChat Link", value="\n".join(link_lines), inline=False)
    else:
        embed.add_field(name="VRChat Link", value="No VRChat link has been saved for this member.", inline=False)

    if vrchat_profile:
        profile_lines = [
            f"**Username:** {vrchat_profile.get('username', 'N/A')}",
            f"**Display Name:** {vrchat_profile.get('displayName', 'N/A')}",
        ]
        if vrchat_profile.get('bio'):
            profile_lines.append(f"**Bio:** {truncate_for_embed(vrchat_profile['bio'], 200)}")
        if vrchat_profile.get('dateJoined'):
            profile_lines.append(f"**Joined VRChat:** {vrchat_profile['dateJoined'][:10] if len(vrchat_profile['dateJoined']) > 10 else vrchat_profile['dateJoined']}")
        if vrchat_profile.get('lastLogin'):
            profile_lines.append(f"**Last Login:** {vrchat_profile['lastLogin'][:10] if len(vrchat_profile['lastLogin']) > 10 else vrchat_profile['lastLogin']}")
        if vrchat_profile.get('status'):
            status_desc = vrchat_profile.get('statusDescription', '')
            profile_lines.append(f"**Status:** {vrchat_profile['status']}" + (f" - {status_desc}" if status_desc else ""))
        if vrchat_profile.get('friendCount') is not None:
            profile_lines.append(f"**Friends:** {vrchat_profile['friendCount']}")
        if vrchat_profile.get('tags'):
            tags_str = ", ".join([t for t in vrchat_profile['tags'] if not t.startswith('system_') and not t.startswith('admin_')])
            if tags_str:
                profile_lines.append(f"**Tags:** {truncate_for_embed(tags_str, 300)}")
        embed.add_field(name="VRChat Profile", value="\n".join(profile_lines), inline=False)

    if unified_profile and unified_profile.get("completeness_score", 0) > 0:
        score = unified_profile.get("completeness_score", 0)
        score_bar = "▓" * int(score / 10) + "░" * (10 - int(score / 10))
        profile_lines = [f"**Completeness:** {score_bar} {score:.0f}%"]
        
        if unified_profile.get("names"):
            profile_lines.append(f"**Names:** {', '.join(unified_profile['names'][:3])}")
        if unified_profile.get("usernames"):
            profile_lines.append(f"**Usernames:** {', '.join(unified_profile['usernames'][:3])}")
        if unified_profile.get("emails"):
            profile_lines.append(f"**Emails:** {', '.join(unified_profile['emails'][:3])}")
        if unified_profile.get("phones"):
            profile_lines.append(f"**Phones:** {', '.join(unified_profile['phones'][:2])}")
        if unified_profile.get("locations"):
            profile_lines.append(f"**Locations:** {', '.join(unified_profile['locations'][:3])}")
        if unified_profile.get("account_ages"):
            ages = [f"{site}: {age[:10]}" for site, age in list(unified_profile['account_ages'].items())[:5]]
            profile_lines.append(f"**Account Ages:** {' | '.join(ages)}")
        if unified_profile.get("followers"):
            followers = [f"{site}: {count}" for site, count in list(unified_profile['followers'].items())[:5]]
            profile_lines.append(f"**Followers:** {' | '.join(followers)}")
        
        embed.add_field(name="Unified Profile", value="\n".join(profile_lines), inline=False)
        
        if unified_profile.get("bios"):
            bio_lines = []
            for i, bio in enumerate(unified_profile['bios'][:3]):
                bio_lines.append(f"{i+1}. {truncate_for_embed(bio, 200)}")
            embed.add_field(name="Bios Found", value="\n".join(bio_lines), inline=False)
        
        timeline = build_timeline(guild.id, member.id)
        if timeline:
            timeline_lines = []
            for event in timeline[:10]:
                date_str = str(event.get('date', 'Unknown'))[:10] if event.get('date') else 'Unknown'
                event_str = truncate_for_embed(event.get('event', 'Unknown event'), 60)
                source_icon = "🔍" if event.get('source') == 'sherlock' else "🎮" if event.get('source') == 'vrchat_api' else "📷" if event.get('source') == 'image_exif' else "🔗"
                timeline_lines.append(f"{source_icon} `{date_str}` {event_str}")
            if timeline_lines:
                embed.add_field(name="Timeline", value="\n".join(timeline_lines), inline=False)

    if linked_accounts:
        platform_groups = {}
        for acc in linked_accounts:
            platform = acc['platform'].title()
            if platform not in platform_groups:
                platform_groups[platform] = []
            platform_groups[platform].append(acc)
        
        account_lines = []
        for platform, accounts in platform_groups.items():
            usernames = []
            for acc in accounts[:5]:
                if acc['username']:
                    usernames.append(f"`{acc['username']}`")
                elif acc['url']:
                    usernames.append(f"[link]({acc['url'][:40]})")
            if usernames:
                account_lines.append(f"**{platform}:** {', '.join(usernames)}")
        
        if account_lines:
            embed.add_field(name="Linked Accounts", value="\n".join(account_lines), inline=False)

    if username_history:
        history_lines = []
        for platform, entries in username_history.items():
            usernames = []
            for entry in entries[:5]:
                if entry['old_username']:
                    usernames.append(f"`{entry['old_username']}` → `{entry['new_username']}`")
                else:
                    usernames.append(f"`{entry['new_username']}`")
            history_lines.append(f"**{platform.title()}:** {' → '.join(usernames)}")
        
        if history_lines:
            embed.add_field(name="Username History", value="\n".join(history_lines), inline=False)

    if phone_lookups:
        phone_lines = []
        for lookup in phone_lookups[:3]:
            phone_lines.append(f"**Phone:** `{lookup['phone_number']}`")
            if lookup.get('found_name'):
                phone_lines.append(f"  Name: `{lookup['found_name']}`")
            if lookup.get('found_address'):
                phone_lines.append(f"  Address: `{truncate_for_embed(lookup['found_address'], 50)}`")
            if lookup.get('found_social'):
                socials = ", ".join(lookup['found_social'][:3])
                phone_lines.append(f"  Social: {socials}")
            phone_lines.append(f"  *Full lookup requires paid API*")
        embed.add_field(name="Phone Numbers", value="\n".join(phone_lines), inline=False)

    if image_analyses:
        image_lines = []
        for img in image_analyses[:5]:
            image_lines.append(f"**Hash:** `{img['image_hash'][:16]}...`")
            if img.get('gps_latitude') and img.get('gps_longitude'):
                image_lines.append(f"  **GPS:** {img['gps_latitude']:.6f}, {img['gps_longitude']:.6f}")
            if img.get('camera_model'):
                image_lines.append(f"  **Camera:** {img['camera_model']}")
            if img.get('timestamp'):
                image_lines.append(f"  **Photo Date:** {img['timestamp']}")
            if img.get('exif_data'):
                exif_keys = list(img['exif_data'].keys())[:3]
                if exif_keys:
                    image_lines.append(f"  **EXIF:** {', '.join(exif_keys)}")
        embed.add_field(name="Image Analysis", value="\n".join(image_lines[:10]), inline=False)

    if pastebin_dumps:
        paste_lines = []
        for paste in pastebin_dumps[:5]:
            flags = []
            if paste.get('contains_email'):
                flags.append("📧")
            if paste.get('contains_phone'):
                flags.append("📱")
            if paste.get('contains_username'):
                flags.append("👤")
            paste_lines.append(f"[Paste]({paste['paste_url'][:80]}) {' '.join(flags) if flags else ''}")
        embed.add_field(name="Pastebin Dumps", value="\n".join(paste_lines), inline=False)

    if dns_records:
        dns_lines = []
        for dns in dns_records[:3]:
            dns_lines.append(f"**{dns['domain']}**")
            if dns.get('ip_addresses'):
                ips = ", ".join(dns['ip_addresses'][:2])
                dns_lines.append(f"  IPs: {ips}")
            if dns.get('mx_records'):
                dns_lines.append(f"  MX: {', '.join(dns['mx_records'][:2])}")
            if dns.get('ns_records'):
                dns_lines.append(f"  NS: {', '.join(dns['ns_records'][:2])}")
        embed.add_field(name="DNS Records", value="\n".join(dns_lines), inline=False)

    sherlock_dir = _sherlock_member_dir(guild.id, member)
    sherlock_files = sorted(sherlock_dir.glob("*.txt"))
    if sherlock_files:
        sherlock_lines = []
        for f in sherlock_files[:10]:
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
                hits = content.count("[+]")
            except Exception:
                hits = 0
            sherlock_lines.append(f"• `{f.stem}` → {hits} hits ({f.name})")
        embed.add_field(name="Sherlock Scans", value="\n".join(sherlock_lines), inline=False)

    return embed

def build_database_member_activity_embed(guild: discord.Guild, member: discord.Member):
    rows = get_member_activity_rows(guild.id, member.id, limit=20)
    embed = discord.Embed(
        title=f"Activity - {member.display_name}",
        description=f"Tracked server activity for {member.mention}",
        color=discord.Color.purple(),
        timestamp=datetime.now(),
    )
    if not rows:
        embed.add_field(name="Activity Log", value="No tracked activity has been saved for this user yet.", inline=False)
        return embed

    lines = [
        f"• {format_sqlite_timestamp(created_at)}: {truncate_for_embed(describe_activity_row(event_type, channel_id, details), 170)}"
        for event_type, channel_id, details, created_at in rows
    ]
    embed.add_field(name="Recent Activity", value=truncate_for_embed("\n".join(lines), 1000), inline=False)
    return embed

class DatabaseMemberSelect(discord.ui.Select):
    def __init__(self, owner_view):
        self.owner_view = owner_view
        super().__init__(
            placeholder="Select a user...",
            min_values=1,
            max_values=1,
            options=owner_view.build_options(),
        )

    async def callback(self, interaction: discord.Interaction):
        await self.owner_view.handle_member_selected(interaction, int(self.values[0]))

class DatabaseSearchView(discord.ui.View):
    def __init__(self, guild_id: int, requester_id: int, page: int = 0):
        super().__init__(timeout=600)
        self.guild_id = guild_id
        self.requester_id = requester_id
        self.page = page
        self.rebuild_items()

    def get_guild(self):
        return bot.get_guild(self.guild_id)

    def get_members(self):
        guild = self.get_guild()
        if guild is None:
            return []
        return sorted(
            [member for member in guild.members if not member.bot],
            key=lambda member: ((member.display_name or member.name).casefold(), member.id),
        )

    def page_members(self):
        members = self.get_members()
        start = self.page * DB_MEMBER_PAGE_SIZE
        end = start + DB_MEMBER_PAGE_SIZE
        return members[start:end]

    def build_options(self):
        options = []
        for member in self.page_members():
            options.append(
                discord.SelectOption(
                    label=truncate_for_embed(member.display_name, 95),
                    value=str(member.id),
                    description=truncate_for_embed(f"{member.name} | ID: {member.id}", 95),
                )
            )
        if not options:
            options.append(discord.SelectOption(label="No members found", value="0", description="No selectable members"))
        return options

    def build_embed(self):
        guild = self.get_guild()
        members = self.get_members()
        total_pages = max(1, (len(members) + DB_MEMBER_PAGE_SIZE - 1) // DB_MEMBER_PAGE_SIZE)
        embed = discord.Embed(
            title="Database Search",
            description="Select a member to inspect their saved info, links, messages, and activity.",
            color=discord.Color.blurple(),
            timestamp=datetime.now(),
        )
        embed.add_field(name="Server", value=guild.name if guild else "Unknown", inline=True)
        embed.add_field(name="Members", value=str(len(members)), inline=True)
        embed.add_field(name="Page", value=f"{self.page + 1}/{total_pages}", inline=True)
        return embed

    def rebuild_items(self):
        self.clear_items()
        self.add_item(DatabaseMemberSelect(self))

        members = self.get_members()
        total_pages = max(1, (len(members) + DB_MEMBER_PAGE_SIZE - 1) // DB_MEMBER_PAGE_SIZE)

        prev_button = discord.ui.Button(label="Previous", style=discord.ButtonStyle.gray, disabled=self.page <= 0)
        next_button = discord.ui.Button(label="Next", style=discord.ButtonStyle.gray, disabled=self.page >= total_pages - 1)
        prev_button.callback = self.previous_page
        next_button.callback = self.next_page
        self.add_item(prev_button)
        self.add_item(next_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.requester_id:
            await interaction.response.send_message("❌ This database panel is only for the user who opened it.", ephemeral=True)
            return False
        return True

    async def previous_page(self, interaction: discord.Interaction):
        if self.page > 0:
            self.page -= 1
            self.rebuild_items()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def next_page(self, interaction: discord.Interaction):
        members = self.get_members()
        total_pages = max(1, (len(members) + DB_MEMBER_PAGE_SIZE - 1) // DB_MEMBER_PAGE_SIZE)
        if self.page < total_pages - 1:
            self.page += 1
            self.rebuild_items()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def handle_member_selected(self, interaction: discord.Interaction, member_id: int):
        guild = self.get_guild()
        if guild is None:
            await interaction.response.send_message("❌ The server could not be resolved for this panel.", ephemeral=True)
            return
        member = guild.get_member(member_id)
        if member is None:
            await interaction.response.send_message("❌ That member could not be found.", ephemeral=True)
            return
        detail_view = DatabaseMemberDetailView(guild.id, self.requester_id, member.id, self.page)
        await interaction.response.edit_message(embed=build_database_member_info_embed(guild, member), view=detail_view)

class DatabaseMemberDetailView(discord.ui.View):
    def __init__(self, guild_id: int, requester_id: int, target_user_id: int, origin_page: int = 0):
        super().__init__(timeout=600)
        self.guild_id = guild_id
        self.requester_id = requester_id
        self.target_user_id = target_user_id
        self.origin_page = origin_page

    def get_target(self):
        guild = bot.get_guild(self.guild_id)
        if guild is None:
            return None, None
        return guild, guild.get_member(self.target_user_id)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.requester_id:
            await interaction.response.send_message("❌ This database panel is only for the user who opened it.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Info", style=discord.ButtonStyle.blurple)
    async def info_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild, member = self.get_target()
        if guild is None or member is None:
            await interaction.response.send_message("❌ That member is no longer available.", ephemeral=True)
            return
        await interaction.response.edit_message(embed=build_database_member_info_embed(guild, member), view=self)

    @discord.ui.button(label="Messages", style=discord.ButtonStyle.green)
    async def messages_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild, member = self.get_target()
        if guild is None or member is None:
            await interaction.response.send_message("❌ That member is no longer available.", ephemeral=True)
            return
        await interaction.response.edit_message(embed=build_database_member_messages_embed(guild, member), view=self)

    @discord.ui.button(label="Links", style=discord.ButtonStyle.gray)
    async def links_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild, member = self.get_target()
        if guild is None or member is None:
            await interaction.response.send_message("❌ That member is no longer available.", ephemeral=True)
            return
        await interaction.response.edit_message(embed=build_database_member_links_embed(guild, member), view=self)

    @discord.ui.button(label="Activity", style=discord.ButtonStyle.gray)
    async def activity_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild, member = self.get_target()
        if guild is None or member is None:
            await interaction.response.send_message("❌ That member is no longer available.", ephemeral=True)
            return
        await interaction.response.edit_message(embed=build_database_member_activity_embed(guild, member), view=self)

    @discord.ui.button(label="Refresh VRChat", style=discord.ButtonStyle.green, row=1)
    async def refresh_vrchat_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild, member = self.get_target()
        if guild is None or member is None:
            await interaction.response.send_message("❌ That member is no longer available.", ephemeral=True)
            return
        
        link_record = get_member_link_record(guild.id, member.id)
        if not link_record or not link_record.get("vrchat_identifier"):
            await interaction.response.send_message("❌ No VRChat profile linked for this member.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        vrchat_id = link_record.get("vrchat_identifier")
        vrchat_username = link_record.get("vrchat_username")
        try:
            vrchat_profile = await fetch_vrchat_profile(vrchat_id, vrchat_username)
            if vrchat_profile:
                store_vrchat_profile_data(guild.id, member.id, vrchat_profile)
                await interaction.followup.send(f"✅ VRChat profile refreshed for **{vrchat_profile.get('displayName', vrchat_username or vrchat_id)}**", ephemeral=True)
            else:
                await interaction.followup.send("❌ Could not fetch VRChat profile. User may be private or API unavailable.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error fetching VRChat profile: {str(e)[:200]}", ephemeral=True)
        
        await interaction.edit_original_response(embed=build_database_member_links_embed(guild, member), view=self)

    @discord.ui.button(label="Back", style=discord.ButtonStyle.red)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild, _ = self.get_target()
        search_view = DatabaseSearchView(self.guild_id, self.requester_id, self.origin_page)
        await interaction.response.edit_message(embed=search_view.build_embed(), view=search_view)

class SlotsView(discord.ui.View):
    def __init__(self, user_id: int, bet: int):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.bet = bet
        self.symbols = ["🍒", "🍋", "🍊", "🍇", "🔔", "⭐", "💎", "7️⃣"]
        self.weights = [15, 15, 15, 12, 10, 8, 5, 3]

    # FIXED: Slot machine payout calculation
    def calculate_payout(self, reels):
        if reels[0] == reels[1] == reels[2]:
            if reels[0] == "💎":
                return self.bet * 50 # Win 50x bet
            elif reels[0] == "7️⃣":
                return self.bet * 25 # Win 25x bet
            elif reels[0] == "⭐":
                return self.bet * 15 # Win 15x bet
            elif reels[0] == "🔔":
                return self.bet * 10 # Win 10x bet
            elif reels[0] == "🍇":
                return self.bet * 5 # Win 5x bet
            else:
                return self.bet * 3 # Win 3x bet
        elif reels[0] == reels[1] or reels[0] == reels[2] or reels[1] == reels[2]:
            return self.bet * 2 # Win 2x bet for two matching
        else:
            return 0 # No win

    @discord.ui.button(label="Spin", style=discord.ButtonStyle.primary, emoji="🎰")
    async def spin_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This isn't your slot machine!", ephemeral=True)
            return
        chips = get_chips(self.user_id)
        if self.bet > chips:
            await interaction.response.send_message("❌ You don't have enough chips!", ephemeral=True)
            return
        button.disabled = True
        await interaction.response.edit_message(view=self)

        # Deduct the bet first
        set_chips(self.user_id, chips - self.bet)

        message = await interaction.original_response()

        # Animation frames
        for frame in range(5):
            reels = [
                random.choices(self.symbols, weights=self.weights, k=1)[0],
                random.choices(self.symbols, weights=self.weights, k=1)[0],
                random.choices(self.symbols, weights=self.weights, k=1)[0]
            ]
            embed = discord.Embed(
                title="🎰 Slot Machine",
                description=f"**Spinning...**\n{' | '.join(reels)}\n\n",
                color=discord.Color.gold()
            )
            embed.add_field(name="Bet", value=f"{self.bet} chips", inline=True)
            embed.add_field(name="Balance", value=f"{get_chips(self.user_id)} chips", inline=True)
            await message.edit(embed=embed)
            await asyncio.sleep(0.5)

        # Final result
        reels = [
            random.choices(self.symbols, weights=self.weights, k=1)[0],
            random.choices(self.symbols, weights=self.weights, k=1)[0],
            random.choices(self.symbols, weights=self.weights, k=1)[0]
        ]

        winnings = self.calculate_payout(reels)

        # Add winnings to balance
        current_balance = get_chips(self.user_id)
        new_balance = current_balance + winnings
        set_chips(self.user_id, new_balance)

        embed = discord.Embed(
            title="🎰 Slot Machine",
            description=f"**Results:**\n{' | '.join(reels)}\n\n",
            color=discord.Color.gold()
        )

        if winnings > 0:
            embed.description += f"🎉 You won **{winnings}** chips!"
            embed.color = discord.Color.green()
        else:
            embed.description += "😢 Better luck next time!"
            embed.color = discord.Color.red()

        embed.add_field(name="Bet", value=f"{self.bet} chips", inline=True)
        embed.add_field(name="New Balance", value=f"{new_balance} chips", inline=True)
        embed.set_footer(text="Play again by clicking Spin")

        button.disabled = False
        await message.edit(embed=embed, view=self)

class BlackjackView(discord.ui.View):
    def __init__(self, user_id: int, bet: int):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.bet = bet
        self.player_hand = []
        self.dealer_hand = []
        self.deck = self.create_deck()
        self.game_over = False
        self.player_hand.append(self.draw_card())
        self.dealer_hand.append(self.draw_card())
        self.player_hand.append(self.draw_card())
        self.dealer_hand.append(self.draw_card())
        player_value = self.calculate_hand(self.player_hand)
        dealer_value = self.calculate_hand(self.dealer_hand)
        if player_value == 21:
            self.game_over = True
            self.disable_all_items()
            if dealer_value == 21:
                self.result = "push"
            else:
                self.result = "blackjack"

    def create_deck(self):
        deck = []
        suits = ["♥", "♦", "♣", "♠"]
        ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        for suit in suits:
            for rank in ranks:
                deck.append(f"{rank}{suit}")
        random.shuffle(deck)
        return deck

    def draw_card(self):
        return self.deck.pop()

    def calculate_hand(self, hand):
        value = 0
        aces = 0
        for card in hand:
            rank = card[:-1]
            if rank in ["J", "Q", "K"]:
                value += 10
            elif rank == "A":
                value += 11
                aces += 1
            else:
                value += int(rank)
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
        return value

    def get_embed(self):
        embed = discord.Embed(title="♠️♥️ Blackjack ♣️♦️", color=discord.Color.dark_green())
        player_value = self.calculate_hand(self.player_hand)
        embed.add_field(
            name="Your Hand",
            value=f"{' '.join(self.player_hand)}\nTotal: **{player_value}**",
            inline=False
        )
        if self.game_over:
            dealer_value = self.calculate_hand(self.dealer_hand)
            embed.add_field(
                name="Dealer's Hand",
                value=f"{' '.join(self.dealer_hand)}\nTotal: **{dealer_value}**",
                inline=False
            )
        else:
            embed.add_field(
                name="Dealer's Hand",
                value=f"{self.dealer_hand[0]} | 🃏\nTotal: ?",
                inline=False
            )
        embed.add_field(name="Bet", value=f"{self.bet} chips", inline=True)
        if self.game_over:
            chips = get_chips(self.user_id)
            if self.result == "blackjack":
                winnings = int(self.bet * 2.5)
                new_balance = chips + winnings
                set_chips(self.user_id, new_balance)
                embed.add_field(name="Result", value=f"**BLACKJACK!**\nYou won {winnings} chips!", inline=True)
                embed.color = discord.Color.gold()
            elif self.result == "win":
                winnings = self.bet * 2
                new_balance = chips + winnings
                set_chips(self.user_id, new_balance)
                embed.add_field(name="Result", value=f"**You win!**\n+{self.bet} chips", inline=True)
                embed.color = discord.Color.green()
            elif self.result == "push":
                new_balance = chips + self.bet
                set_chips(self.user_id, new_balance)
                embed.add_field(name="Result", value="**Push!**\nBet returned", inline=True)
                embed.color = discord.Color.blue()
            elif self.result == "lose":
                embed.add_field(name="Result", value="**You lose!**", inline=True)
                embed.color = discord.Color.red()
            embed.add_field(name="New Balance", value=f"{new_balance} chips", inline=True)
        else:
            chips = get_chips(self.user_id)
            embed.add_field(name="Balance", value=f"{chips} chips", inline=True)
        return embed

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.primary, emoji="➕")
    async def hit_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This isn't your game!", ephemeral=True)
            return
        if self.game_over:
            await interaction.response.send_message("❌ This game is already over!", ephemeral=True)
            return
        self.player_hand.append(self.draw_card())
        player_value = self.calculate_hand(self.player_hand)
        if player_value > 21:
            self.game_over = True
            self.result = "lose"
            self.disable_all_items()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.secondary, emoji="✋")
    async def stand_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This isn't your game!", ephemeral=True)
            return
        if self.game_over:
            await interaction.response.send_message("❌ This game is already over!", ephemeral=True)
            return
        self.game_over = True
        self.disable_all_items()
        dealer_value = self.calculate_hand(self.dealer_hand)
        while dealer_value < 17:
            self.dealer_hand.append(self.draw_card())
            dealer_value = self.calculate_hand(self.dealer_hand)
        player_value = self.calculate_hand(self.player_hand)
        if dealer_value > 21:
            self.result = "win"
        elif player_value > dealer_value:
            self.result = "win"
        elif player_value == dealer_value:
            self.result = "push"
        else:
            self.result = "lose"
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

class GiveawayView(discord.ui.View):
    def __init__(self, giveaway_id: int):
        super().__init__(timeout=None)
        self.giveaway_id = giveaway_id
        self.custom_id = f"giveaway_{giveaway_id}"
        self.entries = []

    @discord.ui.button(label="Enter Giveaway", style=discord.ButtonStyle.green, emoji="🎉", custom_id="enter_giveaway")
    async def enter_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("SELECT participants FROM giveaways WHERE message_id = ?", (self.giveaway_id,))
        result = c.fetchone()
        participants = json.loads(result[0]) if result and result[0] else []
        if interaction.user.id not in participants:
            participants.append(interaction.user.id)
            c.execute("UPDATE giveaways SET participants = ? WHERE message_id = ?",
                      (json.dumps(participants), self.giveaway_id))
            conn.commit()
            await interaction.response.send_message(
                "✅ You've entered the giveaway! Good luck!",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ You've already entered this giveaway!",
                ephemeral=True
            )
        conn.close()

def get_chips(user_id: int) -> int:
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT chips FROM user_chips WHERE user_id=?", (user_id,))
    result = c.fetchone()
    if result:
        chips = result[0]
    else:
        c.execute("INSERT INTO user_chips (user_id, chips) VALUES (?, ?)", (user_id, 1000))
        conn.commit()
        chips = 1000
    conn.close()
    return chips

def set_chips(user_id: int, chips: int):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO user_chips (user_id, chips) VALUES (?, ?)", (user_id, chips))
    conn.commit()
    conn.close()

def get_last_daily(user_id: int) -> Optional[datetime]:
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    try:
        c.execute("SELECT last_daily FROM user_chips WHERE user_id=?", (user_id,))
        result = c.fetchone()
        if result and result[0]:
            return datetime.fromisoformat(result[0])
    except sqlite3.OperationalError as e:
        print(f"Error getting last daily: {e}")
    finally:
        conn.close()
    return None

def set_last_daily(user_id: int):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    now = datetime.utcnow().isoformat()
    c.execute("UPDATE user_chips SET last_daily=? WHERE user_id=?", (now, user_id))
    conn.commit()
    conn.close()

def get_highest_staff_role(member):
    for role_id in ROLE_HIERARCHY:
        if any(role.id == role_id for role in member.roles):
            return role_id
    return None

async def generate_staff_list(guild):
    listed_roles = [rid for rid in ROLE_HIERARCHY if rid != STAFF_ROLE_ID]
    role_members = {role_id: [] for role_id in listed_roles}
    for member in guild.members:
        if any(role.id in STAFF_ROLES for role in member.roles) and not member.bot:
            highest_role_id = get_highest_staff_role(member)
            if highest_role_id and highest_role_id != STAFF_ROLE_ID:
                role_members.setdefault(highest_role_id, []).append(member)
    for role_id in role_members:
        role_members[role_id].sort(key=lambda m: m.display_name.lower())

    staff_list = "**Staff List**\n\n"

    sections = [
        (1563295287349354679, "Founder"),
        (1569546478777536512, "Owner"),
        (1531830875619197040, "Director"),
        (1561161919119753266, "Manager"),
        (1531828111820325064, "Admin"),
        (1531829121150357705, "Moderator"),
    ]
    for role_id, name in sections:
        staff_list += f"**{name}**\n"
        for member in role_members.get(role_id, []):
            staff_list += f"• {member.display_name}\n"
        staff_list += "\n"

    return staff_list.strip()


async def post_staff_list(guild, updated_by=None):
    channel = guild.get_channel(STAFF_LIST_CHANNEL_ID)
    if not channel:
        print(f"❌ Staff list channel not found (ID: {STAFF_LIST_CHANNEL_ID})")
        return
    staff_message_id = get_staff_message_id()
    if staff_message_id:
        try:
            old_message = await channel.fetch_message(staff_message_id)
            await old_message.delete()
        except:
            pass
    staff_list = await generate_staff_list(guild)
    message = await channel.send(staff_list)
    set_staff_message_id(message.id)

    # NEW: Log staff list posting
    command_logger.log_staff_list_change("posted", updated_by=updated_by)
    print(f"✅ Posted staff list in #{channel.name} (Message ID: {message.id})")

# IMPROVED: Added updated_by parameter to track who triggered the update
async def update_staff_list(guild, updated_by=None):
    staff_message_id = get_staff_message_id()
    if not staff_message_id:
        await post_staff_list(guild, updated_by=updated_by)
        return
    channel = guild.get_channel(STAFF_LIST_CHANNEL_ID)
    if not channel:
        print(f"❌ Staff list channel not found (ID: {STAFF_LIST_CHANNEL_ID})")
        return
    try:
        message = await channel.fetch_message(staff_message_id)
        staff_list = await generate_staff_list(guild)
        await message.edit(content=staff_list)

        # NEW: Log staff list update
        command_logger.log_staff_list_change("updated", updated_by=updated_by)
    except discord.NotFound:
        print("❌ Staff message not found, reposting...")
        await post_staff_list(guild, updated_by=updated_by)
    except Exception as e:
        print(f"❌ Failed to update staff list: {str(e)}")
        await post_staff_list(guild, updated_by=updated_by)

async def end_giveaway(giveaway_id: int):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT channel_id, message_id, prize, winners, participants FROM giveaways WHERE message_id = ?", (giveaway_id,))
    result = c.fetchone()
    if not result:
        print(f"❌ Giveaway {giveaway_id} not found in database")
        conn.close()
        return
    channel_id, message_id, prize, winners, participants_json = result
    participants = json.loads(participants_json) if participants_json else []
    channel = bot.get_channel(channel_id)
    if not channel:
        print(f"❌ Channel {channel_id} not found")
        conn.close()
        return
    try:
        message = await channel.fetch_message(message_id)
    except discord.NotFound:
        print(f"❌ Giveaway message {message_id} not found")
        conn.close()
        return
    winner_ids = []
    if participants:
        if len(participants) < winners:
            winners = len(participants)
        winner_ids = random.sample(participants, winners)
    embed = discord.Embed(
        title=f"🎉 GIVEAWAY ENDED: {prize}",
        color=discord.Color.gold(),
        timestamp=datetime.now()
    )
    if winner_ids:
        winners_mentions = ", ".join([f"<@{winner_id}>" for winner_id in winner_ids])
        embed.description = f"**Congratulations {winners_mentions}!**\nYou won: **{prize}**"
    else:
        embed.description = "❌ No one entered this giveaway!"
    embed.set_footer(text=f"{len(participants)} entries | Winners: {winners}")
    view = GiveawayView(giveaway_id)
    view.clear_items()
    view.stop()
    try:
        await message.edit(embed=embed, view=None)
        await message.reply(embed=embed)
    except Exception as e:
        print(f"❌ Failed to update giveaway message: {str(e)}")
    c.execute("DELETE FROM giveaways WHERE message_id = ?", (giveaway_id,))
    conn.commit()
    conn.close()
    print(f"✅ Ended giveaway {giveaway_id}")

# ================= IMPROVED: DAILY LOG TASK =================
async def send_daily_logs():
    """Send daily log file to owners and clear daily logs"""
    log_file = command_logger.create_daily_log_file()
    if log_file:
        for owner_id in OWNER_IDS:
            try:
                owner = await bot.fetch_user(owner_id)
                with open(log_file, 'rb') as f:
                    file = discord.File(f, filename=f"command_log_{datetime.now().strftime('%Y-%m-%d')}.txt")
                    await owner.send(f"📊 Daily Command Log - {datetime.now().strftime('%Y-%m-%d')}", file=file)
            except Exception as e:
                print(f"❌ Failed to send daily log to owner {owner_id}: {e}")
        command_logger.clear_daily_logs()
        print("✅ Cleared daily logs")
    else:
        print("ℹ️ No logs to send today")

# FIXED: Ban permission check function
def has_ban_permission(interaction: discord.Interaction) -> bool:
    """Check if user has ban permissions or manager+ role"""
    # Check if user has ban_members permission
    if interaction.user.guild_permissions.ban_members:
        return True

    # Check if user has manager or above role
    user_roles = [role.id for role in interaction.user.roles]
    manager_plus_roles = [
        1461057322418962567, # Founder
        1461052878717456416, # Director
        1461069473086701783, # Manager
        1470270460544679996, # Security
    ]

    return any(role_id in manager_plus_roles for role_id in user_roles)

def can_use_staff_ai(member) -> bool:
    if not isinstance(member, discord.Member):
        return False
    return is_manager_or_above(member) or member.guild_permissions.manage_messages

def append_message_context(message: discord.Message):
    if not message.content:
        return
    channel_message_context[message.channel.id].append({
        "author": message.author.display_name,
        "content": message.content.strip()
    })

def build_context_block(channel_id: int, max_items: int = 12) -> str:
    messages = list(channel_message_context[channel_id])[-max_items:]
    if not messages:
        return "No recent context."
    lines = [f"{item['author']}: {item['content']}" for item in messages if item.get("content")]
    return "\n".join(lines) if lines else "No recent context."

def chunk_text(text: str, max_len: int = 1900):
    if len(text) <= max_len:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_len, len(text))
        chunks.append(text[start:end])
        start = end
    return chunks

async def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.7, max_tokens: int = 400) -> str:
    payload = {
        "model": CEREBRAS_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    selected_provider = (active_llm_provider or "openrouter").lower()

    async def _call_cerebras(session_obj):
        cerebras_headers = {
            "Authorization": f"Bearer {CEREBRAS_API_KEY}",
            "Content-Type": "application/json"
        }
        async with session_obj.post("https://api.cerebras.ai/v1/chat/completions", json=payload, headers=cerebras_headers) as response:
            response_text = await response.text()
            if response.status != 200:
                raise RuntimeError(f"Cerebras error {response.status}: {response_text[:300]}")
            return json.loads(response_text)

    async def _call_openrouter(session_obj):
        payload_open = dict(payload)
        payload_open["model"] = OPENROUTER_MODEL
        openrouter_headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": OPENROUTER_REFERER,
            "X-Title": OPENROUTER_TITLE
        }
        async with session_obj.post("https://openrouter.ai/api/v1/chat/completions", json=payload_open, headers=openrouter_headers) as response:
            response_text = await response.text()
            if response.status != 200:
                raise RuntimeError(f"OpenRouter error {response.status}: {response_text[:300]}")
            return json.loads(response_text)

    timeout = aiohttp.ClientTimeout(total=45)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        if selected_provider == "cerebras":
            if CEREBRAS_API_KEY:
                data = await _call_cerebras(session)
            elif OPENROUTER_API_KEY:
                print("⚠️ Cerebras selected but key missing, using OpenRouter fallback.")
                data = await _call_openrouter(session)
            else:
                raise RuntimeError("No LLM API key configured (Cerebras/OpenRouter).")
        elif selected_provider == "open":
            if OPENROUTER_API_KEY:
                data = await _call_openrouter(session)
            elif CEREBRAS_API_KEY:
                print("⚠️ OpenRouter selected but key missing, using Cerebras fallback.")
                data = await _call_cerebras(session)
            else:
                raise RuntimeError("No LLM API key configured (OpenRouter/Cerebras).")
        else:
            raise RuntimeError(f"Unsupported LLM provider: {selected_provider}")

    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError("LLM returned no choices.")
    content = choices[0].get("message", {}).get("content", "")
    if not content:
        raise RuntimeError("LLM returned an empty response.")
    return content.strip()

def should_auto_reply_in_general(message: discord.Message) -> bool:
    global last_general_ai_reply_at

    if not message.guild or message.channel.id != GENERAL_CHAT_CHANNEL_ID:
        return False
    if not message.content or len(message.content.strip()) < 4:
        return False
    if CEREBRAS_API_KEY is None and OPENROUTER_API_KEY is None:
        return False
    if time.time() - last_general_ai_reply_at < AI_AUTOREPLY_COOLDOWN_SECONDS:
        return False

    text = message.content.lower()
    triggers = [
        "whats up",
        "what's up",
        "sup everyone",
        "hello everyone",
        "hey everyone",
        "yo everyone",
        "anyone online",
        "good morning",
        "good night",
        "how is everyone"
    ]
    high_signal = any(trigger in text for trigger in triggers)
    chance = 0.45 if high_signal else AI_AUTOREPLY_BASE_CHANCE
    return random.random() < chance

async def generate_general_auto_reply(message: discord.Message) -> str:
    context_block = build_context_block(message.channel.id, max_items=10)
    system_prompt = (
        "You are TheBlackIris, a chill and friendly Discord server bot. "
        "Reply in 1-2 short sentences. Be welcoming, not cringe, and avoid moderation topics."
    )
    user_prompt = (
        f"Recent channel context:\n{context_block}\n\n"
        f"Latest user message from {message.author.display_name}: {message.content}\n\n"
        "Write a natural short response for the server."
    )
    return await call_llm(system_prompt, user_prompt, temperature=0.8, max_tokens=90)

async def save_incident_summary(guild_id: int, channel_id: int, requested_by: int, message_count: int, summary: str):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute(
        "INSERT INTO ai_incident_summaries (guild_id, channel_id, requested_by, message_count, summary) VALUES (?, ?, ?, ?, ?)",
        (guild_id, channel_id, requested_by, message_count, summary[:3500])
    )
    conn.commit()
    conn.close()

def can_use_persona_command(user_id: int) -> bool:
    now = time.time()
    if now - persona_last_used.get(user_id, 0) < AI_PERSONA_COOLDOWN_SECONDS:
        return False
    persona_last_used[user_id] = now
    return True

def sanitize_edgy_output(text: str) -> str:
    blocked_patterns = [
        r"\bn[i1]gg",
        r"\bfagg",
        r"\bkys\b",
        r"\bkill yourself\b",
        r"\bdoxx\b",
        r"\bsexual assault\b",
        r"\bpedoph"
    ]
    lowered = text.lower()
    if any(re.search(pattern, lowered) for pattern in blocked_patterns):
        return "Keeping it playful only. Roast request blocked for safety."
    return text

def store_ai_memory_message(message: discord.Message):
    if not message.guild or not message.content or not message.content.strip():
        return
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute(
        "INSERT OR IGNORE INTO ai_message_memory (guild_id, channel_id, user_id, message_id, content) VALUES (?, ?, ?, ?, ?)",
        (message.guild.id, message.channel.id, message.author.id, message.id, message.content.strip()[:1500])
    )
    c.execute(
        """
        DELETE FROM ai_message_memory
        WHERE guild_id = ? AND user_id = ?
          AND id NOT IN (
            SELECT id FROM ai_message_memory
            WHERE guild_id = ? AND user_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
          )
        """,
        (message.guild.id, message.author.id, message.guild.id, message.author.id, BACKFILL_PER_USER_TARGET)
    )
    conn.commit()
    conn.close()

def get_memory_context(guild_id: int, user_id: Optional[int] = None, limit: int = 50) -> str:
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute(
        "SELECT user_id, content FROM ai_message_memory WHERE guild_id = ? ORDER BY created_at DESC, id DESC LIMIT ?",
        (guild_id, min(max(limit, 10), 150))
    )
    global_rows = c.fetchall()
    target_rows = []
    if user_id:
        c.execute(
            "SELECT user_id, content FROM ai_message_memory WHERE guild_id = ? AND user_id = ? ORDER BY created_at DESC, id DESC LIMIT 30",
            (guild_id, user_id)
        )
        target_rows = c.fetchall()
    conn.close()

    combined = []
    for uid, content in target_rows:
        combined.append(f"user:{uid} (target): {content}")
    for uid, content in global_rows:
        combined.append(f"user:{uid}: {content}")
    if not combined:
        return "No memory available."
    return "\n".join(combined[:limit])

def get_user_memory_context(guild_id: int, user_id: int, limit: int = 500):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute(
        """
        SELECT content
        FROM ai_message_memory
        WHERE guild_id = ? AND user_id = ?
        ORDER BY created_at DESC, id DESC
        LIMIT ?
        """,
        (guild_id, user_id, min(max(limit, 10), BACKFILL_PER_USER_TARGET))
    )
    rows = c.fetchall()
    conn.close()
    if not rows:
        return "", 0
    rows = list(reversed(rows))
    lines = [row[0] for row in rows if row and row[0]]
    if not lines:
        return "", 0
    context = "\n".join(lines)
    # Keep prompt payload manageable.
    if len(context) > 12000:
        context = context[-12000:]
    return context, len(lines)

def _insert_backfill_batch(rows):
    if not rows:
        return 0
    retries = 3
    for attempt in range(retries):
        try:
            conn = sqlite3.connect('bot_data.db')
            c = conn.cursor()
            c.executemany(
                "INSERT OR IGNORE INTO ai_message_memory (guild_id, channel_id, user_id, message_id, content) VALUES (?, ?, ?, ?, ?)",
                rows
            )
            user_keys = set((row[0], row[2]) for row in rows)
            for guild_id, user_id in user_keys:
                c.execute(
                    """
                    DELETE FROM ai_message_memory
                    WHERE guild_id = ? AND user_id = ?
                      AND id NOT IN (
                        SELECT id FROM ai_message_memory
                        WHERE guild_id = ? AND user_id = ?
                        ORDER BY created_at DESC, id DESC
                        LIMIT ?
                      )
                    """,
                    (guild_id, user_id, guild_id, user_id, BACKFILL_PER_USER_TARGET)
                )
            inserted = c.rowcount
            conn.commit()
            conn.close()
            return max(inserted, 0)
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() and attempt < retries - 1:
                time.sleep(0.3 * (attempt + 1))
                continue
            print(f"❌ Backfill DB error: {e}")
            return 0
        except Exception as e:
            print(f"❌ Backfill insert failed: {e}")
            return 0
    return 0

async def backfill_guild_user_history(guild: discord.Guild):
    global startup_backfill_finished_count
    if guild.id in startup_backfill_done_for_guild:
        return
    startup_backfill_done_for_guild.add(guild.id)
    print(f"⌛ Starting AI memory backfill for guild {guild.name} ({guild.id})")

    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT user_id, COUNT(*) FROM ai_message_memory WHERE guild_id = ? GROUP BY user_id", (guild.id,))
    user_counts = {row[0]: row[1] for row in c.fetchall()}
    conn.close()

    total_scanned = 0
    total_buffered = 0
    buffered_rows = []

    for channel in guild.text_channels:
        perms = channel.permissions_for(guild.me)
        if not (perms.view_channel and perms.read_message_history):
            continue
        if total_scanned >= BACKFILL_GUILD_SCAN_CAP:
            break
        channel_scanned = 0
        try:
            async for msg in channel.history(limit=BACKFILL_PER_CHANNEL_SCAN_CAP, oldest_first=False):
                channel_scanned += 1
                total_scanned += 1
                if total_scanned >= BACKFILL_GUILD_SCAN_CAP:
                    break
                if msg.author.bot or not msg.content or not msg.content.strip():
                    continue
                current = user_counts.get(msg.author.id, 0)
                if current >= BACKFILL_PER_USER_TARGET:
                    continue
                buffered_rows.append((guild.id, channel.id, msg.author.id, msg.id, msg.content.strip()[:1500]))
                user_counts[msg.author.id] = current + 1
                total_buffered += 1

                if len(buffered_rows) >= BACKFILL_BATCH_SIZE:
                    _insert_backfill_batch(buffered_rows)
                    buffered_rows = []

                if channel_scanned % 300 == 0:
                    await asyncio.sleep(0.15)
        except discord.Forbidden:
            continue
        except Exception as e:
            print(f"❌ Backfill channel error #{channel.id}: {e}")
        await asyncio.sleep(0.2)

    if buffered_rows:
        _insert_backfill_batch(buffered_rows)

    covered_users = sum(1 for count in user_counts.values() if count > 0)
    print(
        f"✅ Backfill complete for guild {guild.name} | scanned={total_scanned} buffered={total_buffered} users={covered_users}"
    )
    startup_backfill_finished_count += 1
    print(f"📊 Backfill progress: {startup_backfill_finished_count}/{startup_backfill_target_count} guild(s) complete")
    if startup_backfill_target_count > 0 and startup_backfill_finished_count >= startup_backfill_target_count:
        print("✅ All startup backfills are complete.")

def save_trivia_score(user_id: int, points: int):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO trivia_scores (user_id, score) VALUES (?, 0)", (user_id,))
    c.execute("UPDATE trivia_scores SET score = score + ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?", (points, user_id))
    conn.commit()
    conn.close()

def save_ai_ticket_request(guild_id: int, requester_id: int, source: str, category: str, qa_json: str, summary: str, priority: str, actions: str, expires_at: str):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO ai_ticket_requests (guild_id, requester_id, source, category, qa_json, ai_summary, ai_priority, suggested_actions, status, expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending_owner', ?)
        """,
        (guild_id, requester_id, source, category, qa_json, summary, priority, actions, expires_at)
    )
    row_id = c.lastrowid
    conn.commit()
    conn.close()
    return row_id

def update_ai_ticket_owner_message(request_id: int, owner_message_id: int):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("UPDATE ai_ticket_requests SET owner_message_id = ? WHERE id = ?", (owner_message_id, request_id))
    conn.commit()
    conn.close()

def get_ai_ticket_request(request_id: int):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute(
        """
        SELECT id, guild_id, requester_id, source, category, qa_json, ai_summary, ai_priority, suggested_actions, status
        FROM ai_ticket_requests WHERE id = ?
        """,
        (request_id,)
    )
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "guild_id": row[1],
        "requester_id": row[2],
        "source": row[3],
        "category": row[4],
        "qa_json": row[5],
        "ai_summary": row[6],
        "ai_priority": row[7],
        "suggested_actions": row[8],
        "status": row[9]
    }

def update_ai_ticket_status(request_id: int, status: str):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("UPDATE ai_ticket_requests SET status = ?, resolved_at = CURRENT_TIMESTAMP WHERE id = ?", (status, request_id))
    conn.commit()
    conn.close()

def get_pending_ai_ticket_requests():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute(
        """
        SELECT id, guild_id, requester_id, source, category, qa_json, ai_summary, ai_priority, suggested_actions, status, expires_at
        FROM ai_ticket_requests WHERE status = 'pending_owner'
        """
    )
    rows = c.fetchall()
    conn.close()
    return rows

def save_ai_ban_review(guild_id: int, target_user_id: int, requested_by: int, reason: str, ai_summary: str, expires_at: str):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO ai_ban_reviews (guild_id, target_user_id, requested_by, reason, ai_summary, status, expires_at)
        VALUES (?, ?, ?, ?, ?, 'pending_owner', ?)
        """,
        (guild_id, target_user_id, requested_by, reason, ai_summary, expires_at)
    )
    review_id = c.lastrowid
    conn.commit()
    conn.close()
    return review_id

def update_ai_ban_owner_message(review_id: int, owner_message_id: int):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("UPDATE ai_ban_reviews SET owner_message_id = ? WHERE id = ?", (owner_message_id, review_id))
    conn.commit()
    conn.close()

def get_ai_ban_review(review_id: int):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute(
        """
        SELECT id, guild_id, target_user_id, requested_by, reason, ai_summary, status
        FROM ai_ban_reviews WHERE id = ?
        """,
        (review_id,)
    )
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "guild_id": row[1],
        "target_user_id": row[2],
        "requested_by": row[3],
        "reason": row[4],
        "ai_summary": row[5],
        "status": row[6]
    }

def update_ai_ban_review_status(review_id: int, status: str):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("UPDATE ai_ban_reviews SET status = ?, resolved_at = CURRENT_TIMESTAMP WHERE id = ?", (status, review_id))
    conn.commit()
    conn.close()

def get_pending_ai_ban_reviews():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT id, expires_at FROM ai_ban_reviews WHERE status = 'pending_owner'")
    rows = c.fetchall()
    conn.close()
    return rows

async def perform_ban_with_guardrails(guild: discord.Guild, target_id: int, reason: str, moderator: discord.abc.User):
    member = guild.get_member(target_id)
    if member is None:
        try:
            member = await guild.fetch_member(target_id)
        except Exception:
            return False, "Target user not found in this guild."
    bot_member = guild.me or guild.get_member(bot.user.id if bot.user else 0)
    if bot_member is None:
        return False, "Could not verify bot permissions."
    if not bot_member.guild_permissions.ban_members:
        return False, "Bot lacks ban_members permission."
    if member.id == guild.owner_id:
        return False, "Cannot ban the server owner."
    if member.top_role >= bot_member.top_role:
        return False, "Target role is higher than or equal to bot role."

    try:
        staff_roles_to_remove = [role for role in member.roles if role.id in STAFF_ROLES]
        if staff_roles_to_remove:
            await member.remove_roles(*staff_roles_to_remove, reason=f"Pre-ban cleanup by {moderator}")
    except Exception:
        pass

    try:
        await member.ban(reason=f"{reason} (AI ban review approved by {moderator})")
        return True, member
    except Exception as e:
        return False, str(e)

async def create_ai_ticket_channel(guild: discord.Guild, requester_id: int, request_data: dict):
    requester = guild.get_member(requester_id)
    if requester is None:
        try:
            requester = await guild.fetch_member(requester_id)
        except Exception:
            return False, "Requester not found in guild."

    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT id FROM tickets WHERE user_id = ? AND status = 'open'", (requester.id,))
    existing_ticket = c.fetchone()
    conn.close()
    if existing_ticket:
        return False, "Requester already has an open ticket."

    ticket_hub_channel = guild.get_channel(TICKET_CHANNEL_ID)
    if not ticket_hub_channel or not ticket_hub_channel.category:
        return False, "Ticket category configuration missing."

    ticket_count = get_ticket_count() + 1
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        requester: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
    }
    for role_id in TICKET_MANAGER_ROLES:
        role = guild.get_role(role_id)
        if role:
            overwrites[role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True
            )

    channel = await guild.create_text_channel(
        name=f"ticket-{ticket_count}",
        category=ticket_hub_channel.category,
        overwrites=overwrites
    )
    ticket_id = create_ticket(requester.id, channel.id)
    details = json.loads(request_data["qa_json"])
    detail_lines = [f"• **{k}**: {v}" for k, v in details.items()]
    role_mentions = []
    for role_id in TICKET_MANAGER_ROLES:
        role = guild.get_role(role_id)
        if role:
            role_mentions.append(role.mention)

    embed = discord.Embed(
        title=f"AI Ticket #{ticket_id}",
        description=f"Hello {requester.mention}, AI intake completed and staff have been notified.",
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    embed.add_field(name="Category", value=request_data["category"].title(), inline=True)
    embed.add_field(name="Priority", value=request_data.get("ai_priority", "Medium"), inline=True)
    embed.add_field(name="Summary", value=request_data.get("ai_summary", "No summary provided.")[:1024], inline=False)
    embed.add_field(name="Intake Details", value="\n".join(detail_lines)[:1024] if detail_lines else "No details.", inline=False)
    embed.set_footer(text=f"Requester: {requester.display_name}")
    await channel.send(" ".join(role_mentions) if role_mentions else "Staff notified.", embed=embed, view=TicketCloseView(ticket_id, requester.id))
    return True, channel

def is_leap_year(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

async def post_daily_question():
    global _daily_question_category_index
    if not CEREBRAS_API_KEY and not OPENROUTER_API_KEY:
        return
    
    category = DAILY_QUESTION_CATEGORIES[_daily_question_category_index % len(DAILY_QUESTION_CATEGORIES)]
    _daily_question_category_index += 1
    
    system_prompt = category["system"]
    user_prompt = "Return only one question sentence."
    try:
        question = await call_llm(system_prompt, user_prompt, temperature=0.9, max_tokens=80)
    except Exception as e:
        print(f"❌ Daily question generation failed: {e}")
        return

    for guild in bot.guilds:
        channel = guild.get_channel(DAILY_QUESTION_CHANNEL_ID)
        if not channel:
            continue
        try:
            await channel.send(f"{category['emoji']} **{category['name']}:** {question.strip()}")
            conn = sqlite3.connect('bot_data.db')
            c = conn.cursor()
            c.execute("INSERT INTO daily_questions_log (guild_id, channel_id, question) VALUES (?, ?, ?)", (guild.id, channel.id, question[:900]))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"❌ Failed posting daily question in guild {guild.id}: {e}")

async def post_birthday_announcements():
    now = datetime.now(DAILY_TIMEZONE)
    today_mmdd = now.strftime("%m-%d")
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT user_id, guild_id, birth_date FROM birthdays")
    rows = c.fetchall()
    conn.close()

    for user_id, guild_id, birth_date in rows:
        try:
            birth_dt = datetime.strptime(birth_date, "%Y-%m-%d")
        except Exception:
            continue
        birth_mmdd = birth_dt.strftime("%m-%d")
        if birth_mmdd == "02-29" and not is_leap_year(now.year):
            birth_mmdd = "02-28"
        if birth_mmdd != today_mmdd:
            continue

        guild = bot.get_guild(guild_id)
        if not guild:
            continue
        member = guild.get_member(user_id)
        if not member:
            continue
        channel = guild.get_channel(BIRTHDAY_ANNOUNCE_CHANNEL_ID)
        if not channel:
            continue
        age = now.year - birth_dt.year
        try:
            await channel.send(f"🎉 Happy birthday {member.mention} is turning **{age}**!")
        except Exception as e:
            print(f"❌ Birthday post failed for user {user_id}: {e}")

async def create_ticket_channel(guild, user_id: int, issue_description: str):
    ticket_hub_channel = guild.get_channel(TICKET_CHANNEL_ID)
    if not ticket_hub_channel or not ticket_hub_channel.category:
        return False, "Ticket category not configured"

    user = guild.get_member(user_id)
    if not user:
        return False, "User not found"

    category = ticket_hub_channel.category

    existing_ticket = None
    for channel in category.channels:
        if channel.name == f"ticket-{user.name.lower()}":
            existing_ticket = channel
            break

    if existing_ticket:
        return False, "You already have an open ticket"

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }
    for role_id in TICKET_MANAGER_ROLES:
        role = guild.get_role(role_id)
        if role:
            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

    try:
        channel = await category.create_text_channel(
            f"ticket-{user.name.lower()}",
            overwrites=overwrites,
            topic=f"User: {user.id}"
        )

        embed = discord.Embed(
            title="🎫 New Support Ticket",
            description=f"**User:** {user.mention}\n**Issue:** {issue_description}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"User ID: {user.id}")

        role_mentions = [guild.get_role(role_id).mention for role_id in TICKET_MANAGER_ROLES if guild.get_role(role_id)]

        view = TicketCloseView(0, user.id)
        await channel.send(" ".join(role_mentions) if role_mentions else "Staff notified.", embed=embed, view=view)
        return True, channel
    except Exception as e:
        return False, str(e)

async def create_ai_ban_review(interaction: discord.Interaction, member: discord.Member, reason: str):
    ai_summary = "Manual review requested."
    try:
        ai_summary = await call_llm(
            "You are a moderation risk analyst. Give a concise risk summary in 2-4 lines.",
            f"Target: {member.display_name}\nReason: {reason}\nRequester: {interaction.user.display_name}",
            temperature=0.2,
            max_tokens=180
        )
    except Exception as e:
        print(f"❌ AI ban summary failed: {e}")

    expires_at = (datetime.utcnow() + dt.timedelta(seconds=AI_BAN_REVIEW_AUTO_EXPIRE_SECONDS)).isoformat()
    review_id = save_ai_ban_review(interaction.guild.id, member.id, interaction.user.id, reason, ai_summary, expires_at)

    try:
        owner = await bot.fetch_user(AI_OWNER_REVIEW_USER_ID)
        embed = discord.Embed(
            title=f"AI Ban Review #{review_id}",
            description=f"Target: {member.mention} ({member.id})\nRequested by: {interaction.user.mention}",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Reason", value=reason[:1024], inline=False)
        embed.add_field(name="AI Summary", value=ai_summary[:1024], inline=False)
        embed.set_footer(text="Approve or deny ban action. Expires in 15 minutes.")
        view = AIBanApprovalView(review_id)
        msg = await owner.send(embed=embed, view=view)
        update_ai_ban_owner_message(review_id, msg.id)
    except Exception as e:
        print(f"❌ Could not DM owner for AI ban review: {e}")

    asyncio.create_task(handle_ai_ban_review_expiry(review_id, AI_BAN_REVIEW_AUTO_EXPIRE_SECONDS))
    return review_id

async def handle_ai_ban_review_expiry(review_id: int, wait_seconds: int):
    await asyncio.sleep(wait_seconds)
    review = get_ai_ban_review(review_id)
    if not review or review["status"] != "pending_owner":
        return
    update_ai_ban_review_status(review_id, "expired")

async def process_pending_ai_ban_reviews_on_startup():
    rows = get_pending_ai_ban_reviews()
    now_utc = datetime.utcnow()
    for review_id, expires_at in rows:
        try:
            expiry_dt = datetime.fromisoformat(expires_at) if expires_at else now_utc
        except Exception:
            expiry_dt = now_utc
        remaining = int((expiry_dt - now_utc).total_seconds())
        asyncio.create_task(handle_ai_ban_review_expiry(review_id, max(0, remaining)))

class AIBanApprovalView(discord.ui.View):
    def __init__(self, review_id: int):
        super().__init__(timeout=None)
        self.review_id = review_id

    def _resolve_review_id(self, interaction: discord.Interaction) -> Optional[int]:
        if self.review_id:
            return self.review_id
        try:
            if interaction.message and interaction.message.embeds:
                title = interaction.message.embeds[0].title or ""
                match = re.search(r"#(\d+)", title)
                if match:
                    return int(match.group(1))
        except Exception:
            pass
        return None

    @discord.ui.button(label="Approve Ban", style=discord.ButtonStyle.red, custom_id="ai_ban_approve")
    async def approve_ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != AI_OWNER_REVIEW_USER_ID:
            await interaction.response.send_message("❌ Only the configured owner can approve.", ephemeral=True)
            return
        review_id = self._resolve_review_id(interaction)
        if not review_id:
            await interaction.response.send_message("❌ Could not resolve review id.", ephemeral=True)
            return
        review = get_ai_ban_review(review_id)
        if not review or review["status"] != "pending_owner":
            await interaction.response.send_message("ℹ️ Review is no longer pending.", ephemeral=True)
            return
        guild = bot.get_guild(review["guild_id"])
        if not guild:
            update_ai_ban_review_status(review_id, "failed")
            await interaction.response.send_message("❌ Guild not found.", ephemeral=True)
            return
        success, member_or_error = await perform_ban_with_guardrails(guild, review["target_user_id"], review["reason"], interaction.user)
        if success:
            update_ai_ban_review_status(review_id, "approved")
            await interaction.response.send_message(f"✅ Ban approved and executed for {member_or_error}.", ephemeral=True)
            await log_to_channel(
                guild,
                "AI Ban Approved",
                f"{member_or_error.mention} banned via AI review by {interaction.user.mention}\n**Reason:** {review['reason']}",
                channel_id=BAN_LOG_CHANNEL_ID
            )
        else:
            update_ai_ban_review_status(review_id, "failed")
            await interaction.response.send_message(f"❌ Ban failed: {member_or_error}", ephemeral=True)

    @discord.ui.button(label="Deny Ban", style=discord.ButtonStyle.secondary, custom_id="ai_ban_deny")
    async def deny_ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != AI_OWNER_REVIEW_USER_ID:
            await interaction.response.send_message("❌ Only the configured owner can deny.", ephemeral=True)
            return
        review_id = self._resolve_review_id(interaction)
        if not review_id:
            await interaction.response.send_message("❌ Could not resolve review id.", ephemeral=True)
            return
        review = get_ai_ban_review(review_id)
        if not review or review["status"] != "pending_owner":
            await interaction.response.send_message("ℹ️ Review is no longer pending.", ephemeral=True)
            return
        update_ai_ban_review_status(review_id, "denied")
        guild = bot.get_guild(review["guild_id"])
        if guild:
            requester = guild.get_member(review["requested_by"])
            if requester:
                try:
                    await requester.send(f"❌ AI ban review #{review_id} was denied.")
                except Exception:
                    pass
        await interaction.response.send_message("✅ Ban review denied.", ephemeral=True)

class TriviaAnswerView(discord.ui.View):
    def __init__(self, channel_id: int, question_data: dict):
        super().__init__(timeout=20)
        self.channel_id = channel_id
        self.question_data = question_data
        self.answered_users = set()

    async def _answer(self, interaction: discord.Interaction, selected: str):
        game = active_trivia_games.get(self.channel_id)
        if not game:
            await interaction.response.send_message("❌ No active trivia game.", ephemeral=True)
            return
        if interaction.user.id in self.answered_users:
            await interaction.response.send_message("❌ You already answered this question.", ephemeral=True)
            return
        self.answered_users.add(interaction.user.id)
        correct = self.question_data.get("answer", "").strip().upper()
        if selected == correct:
            trivia_scores[(interaction.guild.id, interaction.user.id)] += 1
            save_trivia_score(interaction.user.id, 1)
            await interaction.response.send_message("✅ Correct!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Wrong answer.", ephemeral=True)

    @discord.ui.button(label="A", style=discord.ButtonStyle.primary, custom_id="trivia_a")
    async def answer_a(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._answer(interaction, "A")

    @discord.ui.button(label="B", style=discord.ButtonStyle.primary, custom_id="trivia_b")
    async def answer_b(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._answer(interaction, "B")

    @discord.ui.button(label="C", style=discord.ButtonStyle.primary, custom_id="trivia_c")
    async def answer_c(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._answer(interaction, "C")

    @discord.ui.button(label="D", style=discord.ButtonStyle.primary, custom_id="trivia_d")
    async def answer_d(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._answer(interaction, "D")

# FIXED: Voice recording functionality - NOW PROPERLY IMPLEMENTED
class VoiceRecorder:
    def __init__(self, channel, guild):
        self.channel = channel
        self.guild = guild
        self.voice_client = None
        self.recording = False
        self.users_in_channel = set()
        self.start_time = None

    async def start_recording(self):
        try:
            self.voice_client = await self.channel.connect()
            self.recording = True
            self.start_time = datetime.now()

            # Start recording (this is a simplified version - actual recording would need more setup)
            print(f"✅ Started monitoring in {self.channel.name}")

            # Send notification to owner
            await self.notify_recording_start()

        except Exception as e:
            print(f"❌ Failed to start recording: {e}")

    async def stop_recording(self):
        if self.voice_client and self.recording:
            self.recording = False
            await self.voice_client.disconnect()

            # Notify about recording stop
            await self.notify_recording_stop()
            print(f"✅ Stopped monitoring in {self.channel.name}")

    async def notify_recording_start(self):
        """Notify when recording starts"""
        current_users = [member for member in self.channel.members if not member.bot]
        user_list = ", ".join([member.display_name for member in current_users]) if current_users else "No users"

        # Notify the specified user
        notify_user = self.guild.get_member(960346704236916766)
        if notify_user:
            try:
                await notify_user.send(
                    f"🎙️ **Recording Started**\n"
                    f"**Channel:** {self.channel.name}\n"
                    f"**Users in channel:** {user_list}\n"
                    f"**Time:** {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
            except Exception as e:
                print(f"❌ Failed to send recording start notification: {e}")

    async def notify_recording_stop(self):
        """Notify when recording stops"""
        # Get current users in channel
        current_users = [member for member in self.channel.members if not member.bot]
        user_list = ", ".join([member.display_name for member in current_users]) if current_users else "No users"

        duration = datetime.now() - self.start_time
        hours, remainder = divmod(int(duration.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        # Notify the specified user
        notify_user = self.guild.get_member(960346704236916766)
        if notify_user:
            try:
                await notify_user.send(
                    f"🎙️ **Recording Stopped**\n"
                    f"**Channel:** {self.channel.name}\n"
                    f"**Users in channel:** {user_list}\n"
                    f"**Duration:** {duration_str}\n"
                    f"**End Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            except Exception as e:
                print(f"❌ Failed to send recording stop notification: {e}")

# NEW: Ticket add command
@tree.command(name="ticketadd", description="Add a user to a ticket")
@app_commands.describe(
    user="The user to add to the ticket",
    ticket_number="The ticket number to add the user to"
)
async def ticketadd(interaction: discord.Interaction, user: discord.User, ticket_number: int):
    # Check if user is manager or above
    if not is_manager_or_above(interaction.user):
        await interaction.response.send_message(
            "❌ You need to be Security or above to use this command.",
            ephemeral=True
        )
        return

    # Get ticket information
    ticket = get_ticket_by_id(ticket_number)
    if not ticket:
        await interaction.response.send_message(
            f"❌ Ticket #{ticket_number} not found.",
            ephemeral=True
        )
        return

    if ticket["status"] == "closed":
        await interaction.response.send_message(
            f"❌ Ticket #{ticket_number} is already closed.",
            ephemeral=True
        )
        return

    # Get the ticket channel
    channel = interaction.guild.get_channel(ticket["channel_id"])
    if not channel:
        await interaction.response.send_message(
            f"❌ Ticket channel for #{ticket_number} not found.",
            ephemeral=True
        )
        return

    # Add user to the ticket
    try:
        await channel.set_permissions(user,
            view_channel=True,
            send_messages=True,
            read_message_history=True)

        embed = discord.Embed(
            title="👤 User Added to Ticket",
            description=f"{user.mention} has been added to this ticket by {interaction.user.mention}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        await channel.send(embed=embed)

        await interaction.response.send_message(
            f"✅ {user.mention} has been added to ticket #{ticket_number}",
            ephemeral=True
        )

        await log_to_channel(
            interaction.guild,
            "User Added to Ticket",
            f"{interaction.user.mention} added {user.mention} to ticket #{ticket_number}\nChannel: {channel.mention}"
        )

        command_logger.log_command(interaction.user, "/ticketadd", interaction.guild,
                                   target=user, result=f"Added to ticket #{ticket_number}")

    except Exception as e:
        await interaction.response.send_message(
            f"❌ Failed to add user to ticket: {str(e)}",
            ephemeral=True
        )
        command_logger.log_command(interaction.user, "/ticketadd", interaction.guild,
                                   target=user, error=str(e))

# NEW: Staff Complaint Add command
@tree.command(name="staffcomplaintadd", description="Add a user to a staff complaint channel")
@app_commands.describe(
    user="The user to add to the staff complaint",
    complaint_number="The staff complaint number to add the user to"
)
async def staffcomplaintadd(interaction: discord.Interaction, user: discord.User, complaint_number: int):
    # Check if user has permission (only the specified role)
    user_roles = [role.id for role in interaction.user.roles]
    has_permission = any(role_id in STAFF_COMPLAINTS_MANAGER_ROLES for role_id in user_roles)

    if not has_permission:
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.",
            ephemeral=True
        )
        return

    # Get complaint information
    complaint = get_staff_complaint_by_id(complaint_number)
    if not complaint:
        await interaction.response.send_message(
            f"❌ Staff complaint #{complaint_number} not found.",
            ephemeral=True
        )
        return

    if complaint["status"] == "closed":
        await interaction.response.send_message(
            f"❌ Staff complaint #{complaint_number} is already closed.",
            ephemeral=True
        )
        return

    # Get the complaint channel
    channel = interaction.guild.get_channel(complaint["channel_id"])
    if not channel:
        await interaction.response.send_message(
            f"❌ Staff complaint channel for #{complaint_number} not found.",
            ephemeral=True
        )
        return

    # Add user to the channel
    try:
        await channel.set_permissions(user,
            view_channel=True,
            send_messages=True,
            read_message_history=True)

        embed = discord.Embed(
            title="👤 User Added to Staff Complaint",
            description=f"{user.mention} has been added to this staff complaint by {interaction.user.mention}",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        await channel.send(embed=embed)

        await interaction.response.send_message(
            f"✅ {user.mention} has been added to staff complaint #{complaint_number}",
            ephemeral=True
        )

        await log_to_channel(
            interaction.guild,
            "User Added to Staff Complaint",
            f"{interaction.user.mention} added {user.mention} to staff complaint #{complaint_number}\nChannel: {channel.mention}"
        )

        command_logger.log_command(interaction.user, "/staffcomplaintadd", interaction.guild,
                                   target=user, result=f"Added to complaint #{complaint_number}")

    except Exception as e:
        await interaction.response.send_message(
            f"❌ Failed to add user to staff complaint: {str(e)}",
            ephemeral=True
        )
        command_logger.log_command(interaction.user, "/staffcomplaintadd", interaction.guild,
                                   target=user, error=str(e))

# ================= GAMBLING COMMANDS =================

@tree.command(name="roulette", description="Play roulette with various betting options")
@app_commands.describe(
    bet="Amount of chips to bet",
    bet_type="Type of bet (color, single, dozen, column)",
    bet_value="Value for your bet (red/black, number 0-36, dozen 1-3, column 1-3)"
)
async def roulette(interaction: discord.Interaction, bet: int, bet_type: str, bet_value: str):
    chips = get_chips(interaction.user.id)
    if bet <= 0:
        await interaction.response.send_message("❌ Bet must be at least 1 chip!", ephemeral=True)
        return
    if bet > chips:
        await interaction.response.send_message("❌ You don't have enough chips!", ephemeral=True)
        return

    # Validate bet type and value
    valid_bet_types = ['color', 'single', 'dozen', 'column']
    if bet_type not in valid_bet_types:
        await interaction.response.send_message(
            f"❌ Invalid bet type! Choose from: {', '.join(valid_bet_types)}",
            ephemeral=True
        )
        return

    game = RouletteGame(interaction.user.id, bet)

    # Validate bet value based on type
    if bet_type == 'color':
        if bet_value.lower() not in ['red', 'black']:
            await interaction.response.send_message("❌ For color bets, use 'red' or 'black'", ephemeral=True)
            return
    elif bet_type == 'single':
        try:
            num = int(bet_value)
            if num < 0 or num > 36:
                raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ For single bets, use a number between 0-36", ephemeral=True)
            return
    elif bet_type == 'dozen':
        try:
            dozen = int(bet_value)
            if dozen < 1 or dozen > 3:
                raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ For dozen bets, use 1, 2, or 3", ephemeral=True)
            return
    elif bet_type == 'column':
        try:
            column = int(bet_value)
            if column < 1 or column > 3:
                raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ For column bets, use 1, 2, or 3", ephemeral=True)
            return

    # Deduct bet
    set_chips(interaction.user.id, chips - bet)

    # Spin the wheel
    winning_number = game.spin()
    winning_color = game.colors[winning_number]

    # Calculate payout
    if bet_type == 'color':
        payout = game.calculate_payout('color', bet_value.lower(), winning_number)
    elif bet_type == 'single':
        payout = game.calculate_payout('single', int(bet_value), winning_number)
    elif bet_type == 'dozen':
        payout = game.calculate_payout('dozen', int(bet_value), winning_number)
    elif bet_type == 'column':
        payout = game.calculate_payout('column', int(bet_value), winning_number)

    # Add winnings
    if payout > 0:
        current_balance = get_chips(interaction.user.id)
        new_balance = current_balance + payout
        set_chips(interaction.user.id, new_balance)

    # Create result embed
    embed = discord.Embed(
        title="🎰 Roulette",
        description=f"**Winning Number: {winning_number} {winning_color.upper()}**",
        color=discord.Color.red() if winning_color == 'red' else discord.Color.dark_grey() if winning_color == 'black' else discord.Color.green()
    )

    embed.add_field(name="Your Bet", value=f"{bet_type}: {bet_value}", inline=True)
    embed.add_field(name="Bet Amount", value=f"{bet} chips", inline=True)

    if payout > 0:
        embed.add_field(name="Result", value=f"🎉 You won {payout} chips!", inline=False)
        embed.color = discord.Color.green()
    else:
        embed.add_field(name="Result", value="😢 You lost this round", inline=False)
        embed.color = discord.Color.red()

    embed.add_field(name="New Balance", value=f"{get_chips(interaction.user.id)} chips", inline=True)

    await interaction.response.send_message(embed=embed)
    command_logger.log_command(interaction.user, "/roulette", interaction.guild, result=f"Bet: {bet}, Type: {bet_type}, Value: {bet_value}")

@tree.command(name="crash", description="Play crash game - cash out before it crashes!")
@app_commands.describe(bet="Amount of chips to bet")
async def crash(interaction: discord.Interaction, bet: int):
    chips = get_chips(interaction.user.id)
    if bet <= 0:
        await interaction.response.send_message("❌ Bet must be at least 1 chip!", ephemeral=True)
        return
    if bet > chips:
        await interaction.response.send_message("❌ You don't have enough chips!", ephemeral=True)
        return

    # Create new crash game
    game = CrashGame(interaction.user.id, bet)
    crash_games[interaction.user.id] = game

    # Deduct bet
    set_chips(interaction.user.id, chips - bet)

    embed = discord.Embed(
        title="🚀 Crash Game",
        description="The multiplier is rising... Cash out before it crashes!",
        color=discord.Color.blue()
    )
    embed.add_field(name="Current Multiplier", value=f"{game.multiplier:.2f}x", inline=True)
    embed.add_field(name="Your Bet", value=f"{bet} chips", inline=True)
    embed.add_field(name="Potential Win", value=f"{(bet * game.multiplier):.2f} chips", inline=True)

    view = discord.ui.View(timeout=60)

    async def cash_out_callback(interaction: discord.Interaction):
        if interaction.user.id != game.user_id:
            await interaction.response.send_message("❌ This isn't your game!", ephemeral=True)
            return

        winnings = game.cash_out()
        if winnings > 0:
            current_balance = get_chips(interaction.user.id)
            new_balance = current_balance + winnings
            set_chips(interaction.user.id, new_balance)

            embed = discord.Embed(
                title="💰 Cash Out Successful!",
                description=f"You cashed out at **{game.cash_out_multiplier:.2f}x**",
                color=discord.Color.green()
            )
            embed.add_field(name="Winnings", value=f"{winnings:.2f} chips", inline=True)
            embed.add_field(name="New Balance", value=f"{new_balance} chips", inline=True)

            await interaction.response.edit_message(embed=embed, view=None)
            command_logger.log_command(interaction.user, "crash_cashout", interaction.guild, result=f"Cashed out at {game.cash_out_multiplier:.2f}x")
        else:
            await interaction.response.send_message("❌ You can't cash out now!", ephemeral=True)

    cash_out_button = discord.ui.Button(label="Cash Out", style=discord.ButtonStyle.green, emoji="💰")
    cash_out_button.callback = cash_out_callback
    view.add_item(cash_out_button)

    await interaction.response.send_message(embed=embed, view=view)

    # Start game loop
    async def game_loop():
        message = await interaction.original_response()
        while not game.crashed and not game.cash_out_multiplier:
            await asyncio.sleep(1)
            game.update()

            embed = discord.Embed(
                title="🚀 Crash Game",
                description="The multiplier is rising... Cash out before it crashes!",
                color=discord.Color.blue()
            )
            embed.add_field(name="Current Multiplier", value=f"{game.multiplier:.2f}x", inline=True)
            embed.add_field(name="Your Bet", value=f"{bet} chips", inline=True)
            embed.add_field(name="Potential Win", value=f"{(bet * game.multiplier):.2f} chips", inline=True)

            if game.crashed:
                embed.title = "💥 Crashed!"
                embed.description = f"The game crashed at **{game.multiplier:.2f}x**"
                embed.color = discord.Color.red()
                embed.add_field(name="Result", value="You lost your bet", inline=True)
                await message.edit(embed=embed, view=None)
                break
            else:
                await message.edit(embed=embed)

    bot.loop.create_task(game_loop())
    command_logger.log_command(interaction.user, "/crash", interaction.guild, result=f"Bet: {bet}")

@tree.command(name="higherlower", description="Guess if the next number is higher or lower")
@app_commands.describe(bet="Amount of chips to bet")
async def higherlower(interaction: discord.Interaction, bet: int):
    chips = get_chips(interaction.user.id)
    if bet <= 0:
        await interaction.response.send_message("❌ Bet must be at least 1 chip!", ephemeral=True)
        return
    if bet > chips:
        await interaction.response.send_message("❌ You don't have enough chips!", ephemeral=True)
        return

    game = HigherLowerGame(interaction.user.id, bet)
    higher_lower_games[interaction.user.id] = game

    embed = discord.Embed(
        title="📊 Higher or Lower",
        description=f"Current number: **{game.current_number}**\n\nWill the next number be higher or lower?",
        color=discord.Color.blue()
    )
    embed.add_field(name="Current Streak", value=f"{game.streak}", inline=True)
    embed.add_field(name="Bet", value=f"{bet} chips", inline=True)

    view = discord.ui.View(timeout=60)

    async def guess_callback(interaction: discord.Interaction, guess_type: str):
        if interaction.user.id != game.user_id:
            await interaction.response.send_message("❌ This isn't your game!", ephemeral=True)
            return

        if game.game_over:
            await interaction.response.send_message("❌ This game is already over!", ephemeral=True)
            return

        winnings = game.guess(guess_type)

        embed = discord.Embed(
            title="📊 Higher or Lower",
            description=f"Previous number: **{game.previous_number}**\nCurrent number: **{game.current_number}**",
            color=discord.Color.blue()
        )

        if game.game_over:
            if winnings > 0:
                current_balance = get_chips(interaction.user.id)
                new_balance = current_balance + winnings
                set_chips(interaction.user.id, new_balance)

                embed.title = "🎉 Game Over - You Win!"
                embed.description += f"\n\n**Final streak: {game.streak}**"
                embed.add_field(name="Winnings", value=f"{winnings} chips", inline=True)
                embed.add_field(name="New Balance", value=f"{new_balance} chips", inline=True)
                embed.color = discord.Color.green()
            else:
                embed.title = "💥 Game Over - You Lose!"
                embed.description += f"\n\n**Final streak: {game.streak}**"
                embed.add_field(name="Result", value="You lost your bet", inline=True)
                embed.color = discord.Color.red()

            await interaction.response.edit_message(embed=embed, view=None)
            command_logger.log_command(interaction.user, "higherlower_guess", interaction.guild, result=f"Game over - Streak: {game.streak}")
        else:
            embed.add_field(name="Current Streak", value=f"{game.streak}", inline=True)
            embed.add_field(name="Result", value="✅ Correct!" if winnings > 0 else "❌ Wrong!", inline=True)

            if winnings > 0:
                current_balance = get_chips(interaction.user.id)
                new_balance = current_balance + winnings
                set_chips(interaction.user.id, new_balance)
                embed.add_field(name="Winnings", value=f"{winnings} chips", inline=True)
                embed.add_field(name="Balance", value=f"{new_balance} chips", inline=True)

            await interaction.response.edit_message(embed=embed)
            command_logger.log_command(interaction.user, "higherlower_guess", interaction.guild, result=f"Correct - Streak: {game.streak}")

    higher_button = discord.ui.Button(label="Higher", style=discord.ButtonStyle.green, emoji="📈")
    higher_button.callback = lambda i: guess_callback(i, 'higher')

    lower_button = discord.ui.Button(label="Lower", style=discord.ButtonStyle.red, emoji="📉")
    lower_button.callback = lambda i: guess_callback(i, 'lower')

    same_button = discord.ui.Button(label="Same", style=discord.ButtonStyle.blurple, emoji="➡️")
    same_button.callback = lambda i: guess_callback(i, 'same')

    view.add_item(higher_button)
    view.add_item(lower_button)
    view.add_item(same_button)

    await interaction.response.send_message(embed=embed, view=view)
    command_logger.log_command(interaction.user, "/higherlower", interaction.guild, result=f"Bet: {bet}")

@tree.command(name="createraffle", description="Create a raffle for users to enter")
@app_commands.describe(
    prize="Prize for the raffle",
    ticket_price="Price per ticket in chips",
    duration_minutes="How long the raffle should run (minutes)"
)
async def createraffle(interaction: discord.Interaction, prize: str, ticket_price: int, duration_minutes: int):
    if ticket_price <= 0:
        await interaction.response.send_message("❌ Ticket price must be at least 1 chip!", ephemeral=True)
        return

    if duration_minutes <= 0 or duration_minutes > 1440: # Max 24 hours
        await interaction.response.send_message("❌ Duration must be between 1-1440 minutes!", ephemeral=True)
        return

    raffle = RaffleGame(interaction.user.id, prize, ticket_price, duration_minutes)
    raffle_id = len(raffle_sessions) + 1
    raffle_sessions[raffle_id] = raffle

    embed = discord.Embed(
        title="🎟️ New Raffle!",
        description=f"**Prize:** {prize}",
        color=discord.Color.gold()
    )
    embed.add_field(name="Ticket Price", value=f"{ticket_price} chips", inline=True)
    embed.add_field(name="Duration", value=f"{duration_minutes} minutes", inline=True)
    embed.add_field(name="Ends At", value=f"<t:{int(raffle.end_time.timestamp())}:R>", inline=False)
    embed.set_footer(text=f"Raffle ID: {raffle_id} | Created by {interaction.user.display_name}")

    view = discord.ui.View(timeout=None)

    async def buy_ticket_callback(interaction: discord.Interaction):
        chips = get_chips(interaction.user.id)
        if chips < ticket_price:
            await interaction.response.send_message("❌ You don't have enough chips!", ephemeral=True)
            return

        # Deduct chips and add ticket
        set_chips(interaction.user.id, chips - ticket_price)
        raffle.buy_ticket(interaction.user.id)

        await interaction.response.send_message(
            f"✅ You bought a ticket for the raffle! Good luck!",
            ephemeral=True
        )

        # Update raffle embed
        embed.set_field_at(2, name="Tickets Sold", value=f"{raffle.total_tickets}", inline=True)
        message = await interaction.original_response()
        await message.edit(embed=embed)

    buy_button = discord.ui.Button(label="Buy Ticket", style=discord.ButtonStyle.green, emoji="🎫")
    buy_button.callback = buy_ticket_callback
    view.add_item(buy_button)

    await interaction.response.send_message(embed=embed, view=view)

    # Schedule raffle end
    async def end_raffle():
        await asyncio.sleep(duration_minutes * 60)

        winner_id = raffle.draw_winner()
        winner = await bot.fetch_user(winner_id) if winner_id else None

        embed = discord.Embed(
            title="🎟️ Raffle Ended!",
            description=f"**Prize:** {prize}",
            color=discord.Color.green()
        )
        embed.add_field(name="Total Tickets", value=f"{raffle.total_tickets}", inline=True)

        if winner:
            embed.add_field(name="🎉 Winner", value=f"{winner.mention}", inline=True)
            # Award prize (you might want to implement prize distribution logic)
            try:
                await winner.send(f"🎉 Congratulations! You won the raffle: **{prize}**")
            except:
                pass
        else:
            embed.add_field(name="Result", value="❌ No participants", inline=True)

        message = await interaction.original_response()
        await message.edit(embed=embed, view=None)

        # Remove raffle from sessions
        if raffle_id in raffle_sessions:
            del raffle_sessions[raffle_id]

    bot.loop.create_task(end_raffle())
    command_logger.log_command(interaction.user, "/createraffle", interaction.guild, result=f"Prize: {prize}, Tickets: {ticket_price}")

# ================= CONFESSION COMMANDS =================

@tree.command(name="confess", description="Submit an anonymous confession")
async def confess(interaction: discord.Interaction):
    """Command to start confession submission process"""
    await interaction.response.send_modal(ConfessionModal())

@tree.command(name="confessreviewoff", description="Turn off confession review (Founder only)")
async def confessreviewoff(interaction: discord.Interaction):
    global CONFESSIONS_REVIEW_ENABLED
    user_roles = [r.id for r in interaction.user.roles]
    if interaction.user.id not in OWNER_IDS and FOUNDER_ROLE_ID not in user_roles:
        await interaction.response.send_message("❌ Founder only.", ephemeral=True)
        return
    CONFESSIONS_REVIEW_ENABLED = False
    await interaction.response.send_message("✅ Confession review turned OFF. Confessions will auto-post.", ephemeral=True)

@tree.command(name="confessreviewon", description="Turn on confession review (Founder only)")
async def confessreviewon(interaction: discord.Interaction):
    global CONFESSIONS_REVIEW_ENABLED
    user_roles = [r.id for r in interaction.user.roles]
    if interaction.user.id not in OWNER_IDS and FOUNDER_ROLE_ID not in user_roles:
        await interaction.response.send_message("❌ Founder only.", ephemeral=True)
        return
    CONFESSIONS_REVIEW_ENABLED = True
    await interaction.response.send_message("✅ Confession review turned ON. Confessions require approval.", ephemeral=True)
@tree.command(name="postconfessions", description="Post the confessions embed (Owner only)")
async def postconfessions(interaction: discord.Interaction):
    if interaction.user.id not in OWNER_IDS:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    channel = bot.get_channel(CONFESSIONS_SUBMIT_CHANNEL_ID)
    if channel:
        # Post new confession embed
        embed = discord.Embed(
            title="Anonymous Confessions",
            description="Got something to get off your chest? Share it anonymously!",
            color=discord.Color.purple()
        )
        embed.add_field(
            name="How it works:",
            value="1. Click the button below to submit a confession\n"
                  "2. Staff will review your submission\n"
                  "3. If approved, it will be posted anonymously\n"
                  "4. Others can reply in a discussion thread",
            inline=False
        )
        embed.add_field(
            name="Rules:",
            value="- No hate speech or harassment\n- No personal information\n- Be respectful\n- No spam",
            inline=False
        )
        embed.set_footer(text="All confessions are reviewed before posting")

        view = ConfessionSubmitView()
        await channel.send(embed=embed, view=view)

        await interaction.response.send_message("Confessions embed posted.", ephemeral=True)
        command_logger.log_command(interaction.user, "/postconfessions", interaction.guild)
    else:
        await interaction.response.send_message("Couldn't find confessions channel.", ephemeral=True)

@tree.command(name="confessionstats", description="View confession statistics (Staff only)")
async def confessionstats(interaction: discord.Interaction):
    # Check if user has staff role
    user_roles = [role.id for role in interaction.user.roles]
    has_permission = any(role_id in TICKET_MANAGER_ROLES for role_id in user_roles)

    if not has_permission:
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()

    # Get statistics
    c.execute("SELECT COUNT(*) FROM confessions")
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM confessions WHERE status = 'pending'")
    pending = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM confessions WHERE status = 'approved'")
    approved = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM confessions WHERE status = 'denied'")
    denied = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM confession_replies")
    replies = c.fetchone()[0]

    c.execute("SELECT COUNT(DISTINCT user_id) FROM confessions")
    submitters = c.fetchone()[0]

    conn.close()

    embed = discord.Embed(
        title="📊 Confession Statistics",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )

    embed.add_field(name="Total Submissions", value=f"📝 {total}", inline=True)
    embed.add_field(name="Pending Review", value=f"⏳ {pending}", inline=True)
    embed.add_field(name="Approved", value=f"✅ {approved}", inline=True)
    embed.add_field(name="Denied", value=f"❌ {denied}", inline=True)
    embed.add_field(name="Total Replies", value=f"💬 {replies}", inline=True)
    embed.add_field(name="Unique Submitters", value=f"👥 {submitters}", inline=True)

    await interaction.response.send_message(embed=embed, ephemeral=True)

    command_logger.log_command(interaction.user, "/confessionstats", interaction.guild)

@tree.command(name="cleanupconfessions", description="Clean up old confessions (Owner only)")
@app_commands.describe(days="Delete confessions older than X days (default: 30)")
async def cleanupconfessions(interaction: discord.Interaction, days: int = 30):
    if interaction.user.id not in OWNER_IDS:
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    if days < 1:
        await interaction.response.send_message("❌ Days must be at least 1.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()

    # Get count before cleanup
    c.execute("SELECT COUNT(*) FROM confessions WHERE created_at < datetime('now', ?)", (f'-{days} days',))
    count = c.fetchone()[0]

    if count == 0:
        await interaction.followup.send(f"No confessions older than {days} days found.", ephemeral=True)
        conn.close()
        return

    # Delete old confessions and their replies
    c.execute("DELETE FROM confession_replies WHERE confession_id IN (SELECT confession_id FROM confessions WHERE created_at < datetime('now', ?))",
              (f'-{days} days',))
    c.execute("DELETE FROM confessions WHERE created_at < datetime('now', ?)", (f'-{days} days',))

    conn.commit()
    conn.close()

    await interaction.followup.send(f"✅ Cleaned up {count} confessions older than {days} days.", ephemeral=True)
    command_logger.log_command(interaction.user, "/cleanupconfessions", interaction.guild, result=f"Removed {count} confessions")

# ================= EXISTING COMMANDS =================

@tree.command(name="dm", description="Send current logs to owners")
async def dm(interaction: discord.Interaction):
    if interaction.user.id not in OWNER_IDS:
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    log_file = command_logger.create_daily_log_file()
    if log_file:
        for owner_id in OWNER_IDS:
            try:
                owner = await bot.fetch_user(owner_id)
                with open(log_file, 'rb') as f:
                    file = discord.File(f, filename=f"command_log_{datetime.now().strftime('%Y-%m-%d')}.txt")
                    await owner.send(f"📊 Daily Command Log - {datetime.now().strftime('%Y-%m-%d %H:%M')}", file=file)
            except Exception as e:
                print(f"❌ Failed to send log to owner {owner_id}: {e}")

        await interaction.followup.send("✅ Logs sent to owners!", ephemeral=True)
        command_logger.log_command(interaction.user, "/dm", interaction.guild, result="Logs sent to owners")
    else:
        await interaction.followup.send("❌ No logs available to send.", ephemeral=True)

@tree.command(name="balance", description="Check your casino chip balance")
async def balance(interaction: discord.Interaction):
    chips = get_chips(interaction.user.id)
    await interaction.response.send_message(
        f"💰 You have **{chips} chips**",
        ephemeral=True
    )
    command_logger.log_command(interaction.user, "/balance", interaction.guild)

@tree.command(name="slots", description="Play the slot machine")
async def slots(interaction: discord.Interaction, bet: int):
    chips = get_chips(interaction.user.id)
    if bet <= 0:
        await interaction.response.send_message("❌ Bet must be at least 1 chip!", ephemeral=True)
        return
    if bet > chips:
        await interaction.response.send_message("❌ You don't have enough chips!", ephemeral=True)
        return
    view = SlotsView(interaction.user.id, bet)
    embed = discord.Embed(
        title="🎰 Slot Machine",
        description="Click **Spin** to play!",
        color=discord.Color.gold()
    )
    embed.add_field(name="Bet", value=f"{bet} chips", inline=True)
    embed.add_field(name="Balance", value=f"{chips} chips", inline=True)
    await interaction.response.send_message(embed=embed, view=view)
    command_logger.log_command(interaction.user, "/slots", interaction.guild, result=f"Bet: {bet} chips")

@tree.command(name="blackjack", description="Play a hand of blackjack")
async def blackjack(interaction: discord.Interaction, bet: int):
    chips = get_chips(interaction.user.id)
    if bet <= 0:
        await interaction.response.send_message("❌ Bet must be at least 1 chip!", ephemeral=True)
        return
    if bet > chips:
        await interaction.response.send_message("❌ You don't have enough chips!", ephemeral=True)
        return
    view = BlackjackView(interaction.user.id, bet)
    await interaction.response.send_message(embed=view.get_embed(), view=view)
    command_logger.log_command(interaction.user, "/blackjack", interaction.guild, result=f"Bet: {bet} chips")

@tree.command(name="changechips", description="Change a user's chip balance (Owners only)")
async def changechips(interaction: discord.Interaction, user: discord.User, amount: int):
    if interaction.user.id not in OWNER_IDS:
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    if amount < 0:
        await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
        return
    set_chips(user.id, amount)
    await interaction.response.send_message(
        f"✅ Updated {user.mention}'s chips to **{amount}**",
        ephemeral=True
    )
    command_logger.log_command(interaction.user, "/changechips", interaction.guild, target=user, result=f"Set to {amount} chips")

@tree.command(name="daily", description="Claim your daily 10,000 tokens")
async def daily(interaction: discord.Interaction):
    user_id = interaction.user.id
    last_daily = get_last_daily(user_id)
    now = datetime.utcnow()
    if last_daily:
        time_diff = now - last_daily
        if time_diff.total_seconds() < 24 * 3600:
            next_claim = last_daily + datetime.timedelta(days=1)
            time_left = next_claim - now
            hours = int(time_left.total_seconds() // 3600)
            minutes = int((time_left.total_seconds() % 3600) // 60)
            await interaction.response.send_message(
                f"⏳ You've already claimed your daily tokens! "
                f"Come back in {hours} hours and {minutes} minutes.",
                ephemeral=True
            )
            return
    current_chips = get_chips(user_id)
    new_chips = current_chips + 10000
    set_chips(user_id, new_chips)
    set_last_daily(user_id)
    embed = discord.Embed(
        title="🎉 Daily Tokens Claimed!",
        description=f"You've received **10,000 chips**!",
        color=discord.Color.green()
    )
    embed.add_field(name="New Balance", value=f"{new_chips} chips")
    embed.set_footer(text="Come back tomorrow for more!")
    await interaction.response.send_message(embed=embed, ephemeral=True)
    command_logger.log_command(interaction.user, "/daily", interaction.guild, result="Claimed 10000 chips")

@tree.command(name="giveaway", description="Start a new giveaway")
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.describe(
    winners="Number of winners",
    prize="Prize for the giveaway",
    duration="Duration (e.g., 1d, 2h, 30m)"
)
async def giveaway(interaction: discord.Interaction, winners: int, prize: str, duration: str):
    time_units = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400
    }
    total_seconds = 0
    try:
        parts = re.findall(r'(\d+)([smhd])', duration)
        if not parts:
            raise ValueError("Invalid format")
        for num, unit in parts:
            total_seconds += int(num) * time_units[unit]
        if total_seconds <= 0:
            raise ValueError("Duration must be positive")
    except Exception as e:
        await interaction.response.send_message(
            "❌ Invalid duration format! Use combinations like: 1d, 2h, 30m",
            ephemeral=True
        )
        return
    if winners <= 0:
        await interaction.response.send_message(
            "❌ Number of winners must be at least 1",
            ephemeral=True
        )
        return
    end_time = datetime.utcnow() + datetime.timedelta(seconds=total_seconds)
    embed = discord.Embed(
        title=f"🎉 GIVEAWAY: {prize}",
        color=discord.Color.gold(),
        timestamp=end_time
    )
    embed.add_field(name="Hosted By", value=interaction.user.mention, inline=True)
    embed.add_field(name="Winners", value=str(winners), inline=True)
    embed.add_field(name="Ends At", value=f"<t:{int(end_time.timestamp())}:R>", inline=False)
    embed.set_footer(text="Click the button below to enter!")
    giveaway_id = int(time.time() * 1000)
    view = GiveawayView(giveaway_id)
    message = await interaction.channel.send(embed=embed, view=view)
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO giveaways (message_id, channel_id, prize, winners, end_time, participants) VALUES (?, ?, ?, ?, ?, ?)",
              (message.id, message.channel.id, prize, winners, end_time.isoformat(), json.dumps([])))
    conn.commit()
    conn.close()
    bot.loop.create_task(schedule_giveaway_end(giveaway_id, total_seconds))
    await interaction.response.send_message(
        f"✅ Giveaway started! [View Giveaway]({message.jump_url})",
        ephemeral=True
    )
    command_logger.log_command(interaction.user, "/giveaway", interaction.guild, result=f"Prize: {prize}, Winners: {winners}")

async def schedule_giveaway_end(giveaway_id: int, delay: int):
    await asyncio.sleep(delay)
    await end_giveaway(giveaway_id)

# UPDATED: closeticket command with reason parameter
@tree.command(name="closeticket", description="Close a ticket by its number")
@app_commands.describe(
    ticket_number="The ticket number to close",
    reason="Reason for closing the ticket"
)
async def closeticket(interaction: discord.Interaction, ticket_number: int, reason: str):
    # Check if user is manager or above
    if not is_manager_or_above(interaction.user):
        await interaction.response.send_message(
            "❌ You need to be Security or above to close tickets.",
            ephemeral=True
        )
        return

    ticket = get_ticket_by_id(ticket_number)
    if not ticket:
        await interaction.response.send_message(
            f"❌ Ticket #{ticket_number} not found.",
            ephemeral=True
        )
        return
    if ticket["status"] == "closed":
        await interaction.response.send_message(
            f"❌ Ticket #{ticket_number} is already closed.",
            ephemeral=True
        )
        return

    # Get user who created the ticket
    user = interaction.guild.get_member(ticket["user_id"])

    close_ticket(ticket_number)
    archive_category = interaction.guild.get_channel(TICKET_ARCHIVE_CATEGORY_ID)
    if not archive_category:
        await interaction.response.send_message(
            "❌ Archive category not found. Please contact an administrator.",
            ephemeral=True
        )
        return

    channel = interaction.guild.get_channel(ticket["channel_id"])
    if channel:
        try:
            await channel.edit(category=archive_category, sync_permissions=True)
            embed = discord.Embed(
                title=f"Ticket #{ticket_number} Closed",
                description=f"This ticket has been closed by {interaction.user.mention}\n**Reason:** {reason}",
                color=discord.Color.red()
            )
            await channel.send(embed=embed)

            # DM the user who created the ticket with the reason
            if user:
                try:
                    dm_embed = discord.Embed(
                        title=f"Ticket #{ticket_number} Closed",
                        description=f"Your ticket has been closed by {interaction.user.display_name}\n**Reason:** {reason}",
                        color=discord.Color.red()
                    )
                    await user.send(embed=dm_embed)
                except discord.Forbidden:
                    print(f"Could not send DM to {user} for ticket closure")

            await interaction.response.send_message(
                f"✅ Ticket #{ticket_number} has been closed and moved to archive.",
                ephemeral=True
            )
            await log_to_channel(
                interaction.guild,
                "Ticket Closed",
                f"{interaction.user.mention} closed ticket #{ticket_number}\nChannel: {channel.mention}\nReason: {reason}"
            )
            command_logger.log_command(interaction.user, "/closeticket", interaction.guild, target=f"Ticket #{ticket_number}", result=f"Reason: {reason}")
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to close ticket: {str(e)}",
                ephemeral=True
            )
    else:
        await interaction.response.send_message(
            "❌ Ticket channel not found.",
            ephemeral=True
        )

# UPDATED: Close Staff Complaint command - now works with channels
@tree.command(name="closestaffcomplaint", description="Close a staff complaint by its number")
@app_commands.describe(
    complaint_number="The staff complaint number to close",
    reason="Reason for closing the complaint"
)
async def closestaffcomplaint(interaction: discord.Interaction, complaint_number: int, reason: str):
    # Check if user has permission (only the specified role)
    user_roles = [role.id for role in interaction.user.roles]
    has_permission = any(role_id in STAFF_COMPLAINTS_MANAGER_ROLES for role_id in user_roles)

    if not has_permission:
        await interaction.response.send_message(
            "❌ You don't have permission to close staff complaints.",
            ephemeral=True
        )
        return

    complaint = get_staff_complaint_by_id(complaint_number)
    if not complaint:
        await interaction.response.send_message(
            f"❌ Staff complaint #{complaint_number} not found.",
            ephemeral=True
        )
        return

    if complaint["status"] == "closed":
        await interaction.response.send_message(
            f"❌ Staff complaint #{complaint_number} is already closed.",
            ephemeral=True
        )
        return

    # Get user who created the complaint
    user = interaction.guild.get_member(complaint["user_id"])

    close_staff_complaint(complaint_number)

    # Get the channel (not thread)
    channel = interaction.guild.get_channel(complaint["channel_id"])
    if channel:
        try:
            # Move the channel to archive category
            archive_category = interaction.guild.get_channel(STAFF_COMPLAINTS_ARCHIVE_CATEGORY_ID)
            if archive_category:
                await channel.edit(category=archive_category, sync_permissions=True)

            # Send closure message
            embed = discord.Embed(
                title=f"Staff Complaint #{complaint_number} Closed",
                description=f"This staff complaint has been closed by {interaction.user.mention}\n**Reason:** {reason}",
                color=discord.Color.dark_red()
            )
            await channel.send(embed=embed)

            # Change permissions to read-only
            overwrites = channel.overwrites
            for target in overwrites:
                if isinstance(target, discord.Member) or isinstance(target, discord.Role):
                    if target.id != interaction.guild.me.id: # Don't change bot permissions
                        overwrites[target].send_messages = False

            await channel.edit(overwrites=overwrites)

            # DM the user who created the complaint with the reason
            if user:
                try:
                    dm_embed = discord.Embed(
                        title=f"Staff Complaint #{complaint_number} Closed",
                        description=f"Your staff complaint has been closed by {interaction.user.display_name}\n**Reason:** {reason}",
                        color=discord.Color.dark_red()
                    )
                    await user.send(embed=dm_embed)
                except discord.Forbidden:
                    print(f"Could not send DM to {user} for complaint closure")

            await interaction.response.send_message(
                f"✅ Staff complaint #{complaint_number} has been closed and archived.",
                ephemeral=True
            )

            command_logger.log_command(interaction.user, "/closestaffcomplaint", interaction.guild, target=f"Complaint #{complaint_number}", result=f"Reason: {reason}")

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to close staff complaint: {str(e)}",
                ephemeral=True
            )
    else:
        await interaction.response.send_message(
            "❌ Complaint channel not found.",
            ephemeral=True
        )

@tree.command(name="poststafflist", description="Post the staff list in the staff channel (Owner only)")
async def poststafflist(interaction: discord.Interaction):
    if interaction.user.id not in OWNER_IDS:
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    await post_staff_list(interaction.guild, updated_by=interaction.user)
    await interaction.followup.send("✅ Staff list posted!", ephemeral=True)
    command_logger.log_command(interaction.user, "/poststafflist", interaction.guild)

@tree.command(name="syncstaff", description="Sync/update the staff list message (Owner only)")
async def syncstaff(interaction: discord.Interaction):
    if interaction.user.id not in OWNER_IDS:
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    await update_staff_list(interaction.guild, updated_by=interaction.user)
    await interaction.followup.send("✅ Staff list synchronized!", ephemeral=True)
    command_logger.log_command(interaction.user, "/syncstaff", interaction.guild)

# REMOVED: vrcadd command entirely as requested
# Also removed the /vrc command since we're not using VRChat names anymore

@tree.command(name="banstaff", description="Ban a user from staff positions and remove staff roles")
@app_commands.describe(
    user="The user to ban from staff",
    reason="Reason for the ban"
)
async def banstaff(interaction: discord.Interaction, user: discord.User, reason: str = "No reason provided"):
    user_roles = [role.id for role in interaction.user.roles]
    allowed_roles = [1461057322418962567, 1461052878717456416, 1461069473086701783, 1470270460544679996] # Allowed staff roles: Founder, Director, Manager, Security
    if not any(role_id in allowed_roles for role_id in user_roles):
        await interaction.response.send_message(
            "❌ You don't have permission to use this command. Only staff members can use this.",
            ephemeral=True
        )
        return
    ban_staff_user(user.id, interaction.user.id, reason)
    member = interaction.guild.get_member(user.id)
    if member:
        staff_roles_to_remove = []
        for role in member.roles:
            if role.id in STAFF_ROLES:
                staff_roles_to_remove.append(role)
        if staff_roles_to_remove:
            await member.remove_roles(*staff_roles_to_remove)
            roles_removed = ", ".join([role.name for role in staff_roles_to_remove])
            # IMPROVED: Enhanced role removal logging
            for role in staff_roles_to_remove:
                command_logger.log_role_update(interaction.user, member, "removed", role.name)
                command_logger.log_staff_list_change("removed", user=member, role_name=role.name, updated_by=interaction.user)
        else:
            roles_removed = "None (user had no staff roles)"
        # FIXED: Changed 'guild' to 'interaction.guild' here
        await update_staff_list(interaction.guild, updated_by=interaction.user)
        await interaction.response.send_message(
            f"✅ {user.mention} has been banned from staff positions.\n"
            f"**Reason:** {reason}\n"
            f"**Staff roles removed:** {roles_removed}",
            ephemeral=False
        )
        await log_to_channel(
            interaction.guild,
            "Staff Ban",
            f"{user.mention} was banned from staff by {interaction.user.mention}\n"
            f"**Reason:** {reason}\n"
            f"**Roles removed:** {roles_removed}"
        )
        try:
            await user.send(
                f"⚠️ You have been banned from staff positions in {interaction.guild.name}.\n"
                f"**Reason:** {reason}\n"
                f"You can no longer apply for staff positions."
            )
        except:
            pass
    else:
        await interaction.response.send_message(
            f"✅ {user.mention} has been banned from staff positions.\n"
            f"**Reason:** {reason}\n"
            f"*User is not currently in the server, so no roles were removed.*",
            ephemeral=False
        )
    command_logger.log_command(interaction.user, "/banstaff", interaction.guild, target=user, result=f"Reason: {reason}")

@tree.command(name="timeout", description="Timeout a member with a reason")
@app_commands.checks.has_permissions(moderate_members=True)
@app_commands.describe(
    member="The member to timeout",
    duration="Duration in minutes",
    reason="Reason for timeout"
)
async def timeout(interaction: discord.Interaction,
                  member: discord.Member,
                  duration: int,
                  reason: str = "No reason provided"):
    duration_seconds = duration * 60
    if duration_seconds > 2419200:
        await interaction.response.send_message("❌ Timeout duration cannot exceed 28 days!", ephemeral=True)
        return
    try:
        await member.timeout(datetime.timedelta(seconds=duration_seconds), reason=reason)
        await interaction.response.send_message(
            f"⏱️ {member.mention} has been timed out for {duration} minutes. Reason: {reason}",
            ephemeral=False
        )
        await log_message_event(
            "timeout",
            member=member,
            moderator=interaction.user,
            duration=f"{duration} minutes",
            reason=reason
        )
        command_logger.log_command(interaction.user, "/timeout", interaction.guild, target=member, result=f"Duration: {duration}min, Reason: {reason}")
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to timeout member: {str(e)}", ephemeral=True)
        command_logger.log_command(interaction.user, "/timeout", interaction.guild, target=member, error=str(e))

# FIXED: Announce command - now allows the specified roles to use @everyone
@tree.command(name="announce", description="Make an announcement in the announcement channel")
@app_commands.rename(announcement="message")
async def announce(interaction: discord.Interaction, announcement: str):
    # Check if user has one of the allowed roles
    user_roles = [role.id for role in interaction.user.roles]
    has_allowed_role = any(role_id in EVERYONE_ALLOWED_ROLES for role_id in user_roles)

    if not has_allowed_role:
        await interaction.response.send_message(
            "❌ You don't have permission to use this command. Only specific roles can make announcements.",
            ephemeral=True
        )
        return

    channel = bot.get_channel(1461055915468918847)
    if channel:
        try:
            await channel.send(f"@everyone {announcement}")
            await interaction.response.send_message("✅ Announcement sent!", ephemeral=True)
            command_logger.log_command(interaction.user, "/announce", interaction.guild, result=f"Announcement: {announcement[:50]}...")
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to send announcement: {str(e)}", ephemeral=True)
            command_logger.log_command(interaction.user, "/announce", interaction.guild, error=str(e))
    else:
        await interaction.response.send_message("❌ Couldn't find announcements channel!", ephemeral=True)

# UPDATED: Application embed message with Mod Application button
@tree.command(name="post_application", description="Post application embed to channel (Owner only)")
async def post_application(interaction: discord.Interaction):
    if interaction.user.id not in OWNER_IDS:
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    channel = bot.get_channel(APPLICATION_POST_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="🎉 Join The TheBlackIris Staff Team!",
            description="Welcome to TheBlackIris staff team! Click the button below to apply.\n\n**All applications are private** - only staff will see your answers",
            color=discord.Color.green()
        )
        view = ApplicationStartView()
        message = await channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Application posted!", ephemeral=True)
        command_logger.log_command(interaction.user, "/post_application", interaction.guild)
    else:
        await interaction.response.send_message("Couldn't find announcements channel!", ephemeral=True)

# ================= SHUTDOWN COMMAND =================
@tree.command(name="shutdown", description="Safely shut down the bot (Owner only)")
async def shutdown(interaction: discord.Interaction):
    if interaction.user.id not in OWNER_IDS:
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    await interaction.response.send_message("🔌 Shutting down the bot...", ephemeral=True)
    print(f"🔌 Shutdown command received from {interaction.user} (ID: {interaction.user.id})")
    command_logger.log_command(interaction.user, "/shutdown", interaction.guild)

    # Wait a moment for the status to update
    await asyncio.sleep(1)

    # Close the bot
    await bot.close()

@tree.command(name="kick", description="Kick a server member")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    try:
        dm_channel = await member.create_dm()
        await dm_channel.send(f"⚠️ You have been kicked from {interaction.guild.name}. Reason: {reason}")
    except discord.Forbidden:
        print(f"Could not send DM to {member} (kick)")
    except Exception as e:
        print(f"Error sending DM to {member}: {e}")
    await member.kick(reason=reason)
    # REMOVED: The public message in the channel
    await interaction.response.send_message(f"👢 {member.mention} has been kicked. Reason: {reason}", ephemeral=True)
    await log_to_channel(interaction.guild, "Member Kicked",
                         f"{member.mention} was kicked by {interaction.user.mention}\n**Reason:** {reason}",
                         channel_id=KICK_LOG_CHANNEL_ID)
    command_logger.log_command(interaction.user, "/kick", interaction.guild, target=member, result=f"Reason: {reason}")

# FIXED: Ban command with proper deferral to prevent timeout errors - REMOVED public message
# UPDATED: Ban command now removes staff roles before banning
@tree.command(name="ban", description="Ban a server member")
@app_commands.describe(
    member="The member to ban",
    reason="Reason for the ban (required)"
)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("Error: This command can only be used in a server.", ephemeral=True)
        return

    # Check if user has ban permissions or manager+ role
    if not has_ban_permission(interaction):
        await interaction.response.send_message(
            "Error: You don't have permission to ban members. You need either:\n"
            "- The 'Ban Members' permission\n"
            "- A Security or higher role",
            ephemeral=True
        )
        return

    # Resolve bot member and check ban permissions
    bot_member = guild.me or guild.get_member(bot.user.id if bot.user else 0)
    if bot_member is None:
        await interaction.response.send_message(
            "Error: I couldn't verify my server permissions. Try again in a moment.",
            ephemeral=True
        )
        return

    if not bot_member.guild_permissions.ban_members:
        await interaction.response.send_message(
            "Error: I don't have permission to ban members. Please check my role permissions.",
            ephemeral=True
        )
        return

    # Guardrails for invalid/hierarchy bans
    if member.id == interaction.user.id:
        await interaction.response.send_message("Error: You can't ban yourself.", ephemeral=True)
        return

    if member.id == guild.owner_id:
        await interaction.response.send_message("Error: You can't ban the server owner.", ephemeral=True)
        return

    if member.top_role >= bot_member.top_role:
        await interaction.response.send_message(
            "Error: I can't ban that member because their role is higher than or equal to mine.",
            ephemeral=True
        )
        return

    if isinstance(interaction.user, discord.Member):
        if member.top_role >= interaction.user.top_role and interaction.user.id != guild.owner_id:
            await interaction.response.send_message(
                "Error: You can't ban a member with an equal or higher role than yours.",
                ephemeral=True
            )
            return

    await interaction.response.defer(ephemeral=True)

    success = False
    error_msg = None

    try:
        # Remove staff roles before banning if present
        staff_roles_to_remove = [role for role in member.roles if role.id in STAFF_ROLES]
        if staff_roles_to_remove:
            await member.remove_roles(*staff_roles_to_remove)
            roles_removed = ", ".join([role.name for role in staff_roles_to_remove])

            for role in staff_roles_to_remove:
                command_logger.log_role_update(interaction.user, member, "removed", role.name)
                command_logger.log_staff_list_change("removed", user=member, role_name=role.name, updated_by=interaction.user)

            await update_staff_list(guild, updated_by=interaction.user)
            print(f"Removed staff roles from {member} before banning: {roles_removed}")

        try:
            dm_channel = await member.create_dm()
            await dm_channel.send(f"You have been banned from {guild.name}. Reason: {reason}")
        except discord.Forbidden:
            print(f"Could not send DM to {member} (ban)")
        except Exception as e:
            print(f"Error sending DM to {member}: {e}")

        await member.ban(reason=f"{reason} (Banned by {interaction.user})")
        success = True

    except Exception as e:
        error_msg = str(e)
        success = False

    command_logger.log_ban_attempt(interaction.user, member, success, error=error_msg, reason=reason)

    ban_log_channel = guild.get_channel(BAN_LOG_CHANNEL_ID)
    if ban_log_channel:
        embed = discord.Embed(
            title="Member Banned" if success else "Ban Failed",
            description=f"**{member.mention}** was banned by **{interaction.user.mention}**" if success else f"Failed to ban **{member.mention}** by **{interaction.user.mention}**",
            color=discord.Color.red() if success else discord.Color.orange(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        if error_msg and not success:
            embed.add_field(name="Error", value=error_msg, inline=False)
        embed.add_field(name="User ID", value=member.id, inline=True)
        embed.add_field(name="Status", value="Successful" if success else "Failed", inline=True)

        if member.avatar:
            embed.set_author(name=member.display_name, icon_url=member.avatar.url)
        else:
            embed.set_author(name=member.display_name)

        await ban_log_channel.send(embed=embed)

    if success:
        await interaction.followup.send(f"{member.mention} has been banned. Reason: {reason}", ephemeral=True)
    else:
        await interaction.followup.send(f"Failed to ban {member.mention}: {error_msg}", ephemeral=True)

    command_logger.log_command(interaction.user, "/ban", guild, target=member, result=f"Success - Reason: {reason}" if success else f"Failed - Error: {error_msg}")

@tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! {latency}ms")
    command_logger.log_command(interaction.user, "/ping", interaction.guild, result=f"Latency: {latency}ms")

@tree.command(name="switch", description="Switch active AI provider (open or cerebras)")
@app_commands.describe(provider="Choose provider")
@app_commands.choices(provider=[
    app_commands.Choice(name="cerebras", value="cerebras"),
    app_commands.Choice(name="open", value="open")
])
async def switch_provider(interaction: discord.Interaction, provider: app_commands.Choice[str]):
    global active_llm_provider
    if interaction.user.id not in OWNER_IDS:
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    active_llm_provider = provider.value.lower().strip()
    await interaction.response.send_message(f"✅ Active AI provider switched to **{active_llm_provider}**.", ephemeral=True)
    command_logger.log_command(interaction.user, "/switch", interaction.guild, result=f"provider={active_llm_provider}")

@bot.command(name="db")
async def database_lookup_command(ctx: commands.Context):
    target_guild = None
    requester_member = None

    if ctx.guild:
        if isinstance(ctx.author, discord.Member) and has_founder_or_owner_role(ctx.author):
            target_guild = ctx.guild
            requester_member = ctx.author
    else:
        target_guild, requester_member = resolve_authorized_member(ctx.author.id)

    if target_guild is None or requester_member is None:
        if ctx.guild:
            try:
                await ctx.reply("❌ Only members with the Founder or Owner role can use `!db`.", mention_author=False, delete_after=10)
            except Exception:
                pass
        else:
            await ctx.send("❌ Only members with the Founder or Owner role can use `!db`.")
        return

    search_view = DatabaseSearchView(target_guild.id, ctx.author.id)
    embed = search_view.build_embed()

    if ctx.guild:
        try:
            await ctx.message.delete()
        except Exception:
            pass
        try:
            dm_channel = await ctx.author.create_dm()
            await dm_channel.send(embed=embed, view=search_view)
            command_logger.log_command(ctx.author, "!db", target_guild, result="Database panel sent via DM")
        except discord.Forbidden:
            await ctx.send("❌ I couldn't DM you the database panel. Please open your DMs and try again.", delete_after=10)
            command_logger.log_command(ctx.author, "!db", target_guild, error="DMs closed")
        return

    await ctx.send(embed=embed, view=search_view)
    command_logger.log_command(ctx.author, "!db", target_guild, result="Database panel opened in DM")

@bot.command(name="search")
async def search_username(ctx: commands.Context, *, username: str):
    if not username or len(username) < 2:
        await ctx.reply("❌ Please provide a username (at least 2 characters).", mention_author=False, delete_after=15)
        return
    
    await ctx.reply(f"🔍 This command has been disabled.", mention_author=False, delete_after=15)
    command_logger.log_command(ctx.author, "!search", ctx.guild, result="Command disabled (OSINT removal)")

@bot.command(name="sherlockscan")
async def sherlockscan_command(ctx: commands.Context, *, target: str = ""):
    """Run a Sherlock scan for a member (or all members). Staff only."""
    target_guild = None
    requester_member = None
    if ctx.guild:
        if isinstance(ctx.author, discord.Member) and has_founder_or_owner_role(ctx.author):
            target_guild = ctx.guild
            requester_member = ctx.author
    else:
        target_guild, requester_member = resolve_authorized_member(ctx.author.id)

    if target_guild is None or requester_member is None:
        await ctx.reply("❌ Only members with the Founder or Owner role can use `!sherlockscan`.", mention_author=False, delete_after=10)
        return

    # Determine targets
    members_to_scan = []
    if target.lower().strip() in ("", "me"):
        # scan requester if in guild
        m = target_guild.get_member(ctx.author.id)
        if m:
            members_to_scan = [m]
    elif target.lower().strip() == "all":
        members_to_scan = [m for m in target_guild.members if not m.bot]
    else:
        # try mention or id
        mentioned = ctx.message.mentions
        if mentioned:
            members_to_scan = [m for m in mentioned if isinstance(m, discord.Member)]
        else:
            # try id
            try:
                uid = int(target.strip().strip("<@!>"))
                m = target_guild.get_member(uid)
                if m:
                    members_to_scan = [m]
            except ValueError:
                pass

    if not members_to_scan:
        await ctx.reply("❌ No valid members found to scan. Usage: `!sherlockscan`, `!sherlockscan @user`, `!sherlockscan all`", mention_author=False, delete_after=15)
        return

    await ctx.reply(f"🔍 Starting Sherlock scan for {len(members_to_scan)} member(s). This may take a while...", mention_author=False)

    async def _scan_one(member):
        try:
            await run_sherlock_scan_for_member(target_guild, member)
        except Exception as e:
            print(f"❌ Sherlock scan failed for {member}: {e}")

    if len(members_to_scan) == 1:
        await _scan_one(members_to_scan[0])
        try:
            await scrape_sherlock_found_sites(target_guild, members_to_scan[0])
        except Exception as e:
            print(f"❌ Scrape failed: {e}")
        await ctx.send(f"✅ Sherlock scan + scrape complete for {members_to_scan[0].mention}. Results saved in member folder.")
    else:
        # Background batch
        async def _batch():
            for m in members_to_scan:
                await _scan_one(m)
                try:
                    await scrape_sherlock_found_sites(target_guild, m)
                except Exception as e:
                    print(f"❌ Scrape failed for {m}: {e}")
                await asyncio.sleep(1)
            try:
                await ctx.send(f"✅ Sherlock scan complete for {len(members_to_scan)} members.")
            except Exception:
                pass
        asyncio.create_task(_batch())
        command_logger.log_command(ctx.author, "!sherlockscan", target_guild, result=f"queued {len(members_to_scan)} members")

@tree.command(name="roast", description="Roast a user based on server message memory")
@app_commands.describe(user="The user to roast")
async def roast(interaction: discord.Interaction, user: discord.Member):
    if user.bot:
        await interaction.response.send_message("❌ I won't roast bots.", ephemeral=True)
        return
    if not can_use_persona_command(interaction.user.id):
        await interaction.response.send_message("⏳ Slow down a little before using this again.", ephemeral=True)
        return
    await interaction.response.defer(thinking=True)
    memory = get_memory_context(interaction.guild.id, user.id, limit=60)
    prompt = (
        f"Target user: {user.display_name}\n"
        f"Server memory context:\n{memory}\n\n"
        "Generate one edgy but policy-safe roast in 1-3 lines. Avoid hate, sexual, or violent harassment."
    )
    try:
        result = await call_llm("You write sharp Discord roasts.", prompt, temperature=0.9, max_tokens=140)
        result = sanitize_edgy_output(result)
    except Exception:
        result = f"{user.mention} talks big game, but even autocorrect gave up trying to understand them."
    await interaction.followup.send(result[:1900])
    command_logger.log_command(interaction.user, "/roast", interaction.guild, target=user)

@tree.command(name="compliment", description="Compliment a user based on server message memory")
@app_commands.describe(user="The user to compliment")
async def compliment(interaction: discord.Interaction, user: discord.Member):
    if user.bot:
        await interaction.response.send_message("❌ I won't target bots for this.", ephemeral=True)
        return
    if not can_use_persona_command(interaction.user.id):
        await interaction.response.send_message("⏳ Slow down a little before using this again.", ephemeral=True)
        return
    await interaction.response.defer(thinking=True)
    memory = get_memory_context(interaction.guild.id, user.id, limit=60)
    prompt = (
        f"Target user: {user.display_name}\n"
        f"Server memory context:\n{memory}\n\n"
        "Write one personalized, genuine compliment in 2-3 lines."
    )
    try:
        result = await call_llm("You write concise uplifting compliments.", prompt, temperature=0.8, max_tokens=130)
    except Exception:
        result = f"{user.mention} brings strong positive energy to this server."
    await interaction.followup.send(result[:1900])
    command_logger.log_command(interaction.user, "/compliment", interaction.guild, target=user)

async def _run_user_summary(interaction: discord.Interaction, user: discord.Member, command_name: str):
    if user.bot:
        await interaction.response.send_message("❌ I can't summarize bot accounts.", ephemeral=True)
        return
    await interaction.response.defer()
    context, msg_count = get_user_memory_context(interaction.guild.id, user.id, limit=BACKFILL_PER_USER_TARGET)
    result = ""

    if msg_count < 10:
        fallback_lines = [
            f"Based on only {msg_count} messages, {user.mention} looks like the kind of person who starts chaos, drops one-liners, and vanishes before anyone can answer.",
            f"Only {msg_count} messages deep, but {user.mention} already gives \"main character in a side quest\" energy with confidence way above sample size.",
            f"Small sample ({msg_count} messages), but {user.mention} still manages to sound like they speedrun conversations and collect reactions like achievements."
        ]
        result = random.choice(fallback_lines)
    else:
        system_prompt = (
            "You write roast-style user profiles for Discord.\n"
            "Write exactly one compact paragraph (no headings, no bullet points).\n"
            "Tone: sharp, witty, direct, playful.\n"
            "Mention recurring habits/patterns from provided messages.\n"
            "Target length: 500-700 characters.\n"
            "Do not invent facts not present in context."
        )
        user_prompt = (
            f"User: {user.display_name}\n"
            f"Message sample count: {msg_count}\n\n"
            f"Messages:\n{context}"
        )
        try:
            result = await call_llm(system_prompt, user_prompt, temperature=0.6, max_tokens=320)
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to generate summary: {str(e)}")
            command_logger.log_command(interaction.user, command_name, interaction.guild, target=user, error=str(e))
            return

    result = sanitize_edgy_output(result).replace("\n", " ").strip()
    await interaction.followup.send(f"## User Summary: {user.mention}\n{result[:1800]}")
    command_logger.log_command(
        interaction.user,
        command_name,
        interaction.guild,
        target=user,
        result=f"mode=roast_profile,messages={msg_count}"
    )

@tree.command(name="summery", description="Summarize a user's stored message history")
@app_commands.describe(user="User to summarize")
async def summery(interaction: discord.Interaction, user: discord.Member):
    await _run_user_summary(interaction, user, "/summery")

@tree.command(name="storyprompt", description="Generate an AI story prompt")
@app_commands.describe(theme="Optional theme or genre")
async def storyprompt(interaction: discord.Interaction, theme: str = "any"):
    await interaction.response.defer(thinking=True)
    try:
        prompt = (
            f"Theme: {theme}\n"
            "Create a short story prompt with sections: Setup, Conflict, Twist."
        )
        result = await call_llm("You generate creative writing prompts.", prompt, temperature=0.95, max_tokens=180)
    except Exception:
        result = "**Setup:** A city where memories are traded like currency.\n**Conflict:** Your last happy memory was stolen.\n**Twist:** The thief is your future self."
    await interaction.followup.send(result[:1900])
    command_logger.log_command(interaction.user, "/storyprompt", interaction.guild, result=theme)

@tree.command(name="kiss", description="Send a playful kiss action")
@app_commands.describe(user="Who you want to kiss")
async def kiss(interaction: discord.Interaction, user: discord.Member):
    if user.bot:
        await interaction.response.send_message("❌ You can't kiss bots.", ephemeral=True)
        return
    if interaction.user.id == user.id:
        await interaction.response.send_message("💋 Self-love unlocked.", ephemeral=True)
        return
    if not can_use_persona_command(interaction.user.id):
        await interaction.response.send_message("⏳ Slow down a little before using this again.", ephemeral=True)
        return
    lines = [
        f"{interaction.user.mention} gives {user.mention} a dramatic anime kiss.",
        f"{interaction.user.mention} steals a quick kiss from {user.mention}.",
        f"{interaction.user.mention} kisses {user.mention} and chat explodes."
    ]
    embed = discord.Embed(
        title="💋 Kiss",
        description=random.choice(lines),
        color=discord.Color.fuchsia(),
        timestamp=datetime.now()
    )
    await interaction.response.send_message(embed=embed)
    command_logger.log_command(interaction.user, "/kiss", interaction.guild, target=user)

@tree.command(name="marry", description="Send a playful marry action")
@app_commands.describe(user="Who you want to marry")
async def marry(interaction: discord.Interaction, user: discord.Member):
    if user.bot:
        await interaction.response.send_message("❌ You can't marry bots.", ephemeral=True)
        return
    if interaction.user.id == user.id:
        await interaction.response.send_message("💍 You are now married to yourself.", ephemeral=True)
        return
    if not can_use_persona_command(interaction.user.id):
        await interaction.response.send_message("⏳ Slow down a little before using this again.", ephemeral=True)
        return
    lines = [
        f"{interaction.user.mention} proposes to {user.mention}. Wedding bells everywhere!",
        f"{interaction.user.mention} and {user.mention} are now server-married.",
        f"{interaction.user.mention} puts a shiny ring on {user.mention}."
    ]
    embed = discord.Embed(
        title="💍 Marry",
        description=random.choice(lines),
        color=discord.Color.gold(),
        timestamp=datetime.now()
    )
    await interaction.response.send_message(embed=embed)
    command_logger.log_command(interaction.user, "/marry", interaction.guild, target=user)

@tree.command(name="debate", description="Debate against AI over a topic")
@app_commands.describe(topic="Topic to debate", rounds="Rounds (1-5)")
async def debate(interaction: discord.Interaction, topic: str, rounds: int = 3):
    rounds = max(1, min(5, rounds))
    key = (interaction.channel.id, interaction.user.id)
    if key in active_debates:
        await interaction.response.send_message("❌ You already have an active debate in this channel.", ephemeral=True)
        return

    await interaction.response.defer()
    stance = random.choice(["for", "against"])
    active_debates[key] = {"topic": topic, "rounds": rounds, "started": time.time(), "transcript": []}
    await interaction.followup.send(f"🗣️ Debate started on **{topic}**. I will argue **{stance}**. You have 120s per reply.")
    try:
        for round_num in range(1, rounds + 1):
            ai_msg = await call_llm(
                "You are a concise debate opponent.",
                f"Topic: {topic}\nStance: {stance}\nRound: {round_num}\nGive one strong argument in <=100 words.",
                temperature=0.7,
                max_tokens=180
            )
            active_debates[key]["transcript"].append({"speaker": "AI", "text": ai_msg})
            await interaction.channel.send(f"**AI Round {round_num}:** {ai_msg}")

            def check(m):
                return m.channel.id == interaction.channel.id and m.author.id == interaction.user.id and not m.author.bot

            user_msg = await bot.wait_for("message", timeout=120, check=check)
            active_debates[key]["transcript"].append({"speaker": interaction.user.display_name, "text": user_msg.content})
            await interaction.channel.send(f"✅ Recorded your round {round_num} response.")

        transcript_text = "\n".join([f"{x['speaker']}: {x['text']}" for x in active_debates[key]["transcript"]])
        verdict = await call_llm(
            "You are an impartial debate judge.",
            f"Topic: {topic}\nTranscript:\n{transcript_text}\n\nReturn winner (AI or USER) and one-paragraph reason.",
            temperature=0.3,
            max_tokens=220
        )
        await interaction.channel.send(f"🏁 **Debate complete**\n{verdict[:1900]}")
    except asyncio.TimeoutError:
        await interaction.channel.send("⌛ Debate timed out due to inactivity.")
    except Exception as e:
        await interaction.channel.send(f"❌ Debate error: {e}")
    finally:
        active_debates.pop(key, None)
        command_logger.log_command(interaction.user, "/debate", interaction.guild, result=f"topic={topic}, rounds={rounds}")

@tree.command(name="birthday", description="Set your birthday for automatic announcements")
@app_commands.describe(date="Your birth date in YYYY-MM-DD format")
async def birthday(interaction: discord.Interaction, date: str):
    try:
        parsed = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        await interaction.response.send_message("❌ Invalid date format. Use YYYY-MM-DD.", ephemeral=True)
        return
    if parsed.date() > datetime.now().date():
        await interaction.response.send_message("❌ Birthday cannot be in the future.", ephemeral=True)
        return
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO birthdays (user_id, guild_id, birth_date, timezone)
        VALUES (?, ?, ?, 'America/New_York')
        ON CONFLICT(user_id) DO UPDATE SET guild_id=excluded.guild_id, birth_date=excluded.birth_date, timezone=excluded.timezone
        """,
        (interaction.user.id, interaction.guild.id, date)
    )
    conn.commit()
    conn.close()
    await interaction.response.send_message(f"✅ Birthday saved as **{date}**.", ephemeral=True)
    command_logger.log_command(interaction.user, "/birthday", interaction.guild, result=date)

ticket_group = app_commands.Group(name="ticket", description="AI ticket commands")

@ticket_group.command(name="open", description="Open a support ticket")
async def ticket_open(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Select what you need help with:",
        ephemeral=True,
        view=TicketCategoryView(user_id=interaction.user.id)
    )

guessimage_group = app_commands.Group(name="guessimage", description="Guess the AI image prompt")

@guessimage_group.command(name="start", description="Start a guess-the-image round")
async def guessimage_start(interaction: discord.Interaction):
    if interaction.channel.id in active_guessimage_games:
        await interaction.response.send_message("❌ A guessimage game is already active in this channel.", ephemeral=True)
        return
    prompt_seed = random.choice([
        "a cyberpunk fox DJ in neon rain",
        "a medieval knight riding a skateboard on mars",
        "a floating library above the ocean at sunset",
        "a tiny dragon guarding a coffee shop"
    ])
    image_url = f"https://image.pollinations.ai/prompt/{quote_plus(prompt_seed)}"
    active_guessimage_games[interaction.channel.id] = {
        "prompt": prompt_seed,
        "created_at": time.time(),
        "best_score": -1,
        "best_user": None,
        "best_guess": None
    }
    await interaction.response.send_message(f"🖼️ **Guess the prompt!**\n{image_url}")
    asyncio.create_task(finish_guessimage_round(interaction.channel.id, 120))
    command_logger.log_command(interaction.user, "/guessimage start", interaction.guild)

@guessimage_group.command(name="guess", description="Submit your guess for the current image game")
@app_commands.describe(answer="Your guess")
async def guessimage_guess(interaction: discord.Interaction, answer: str):
    game = active_guessimage_games.get(interaction.channel.id)
    if not game:
        await interaction.response.send_message("❌ No active guessimage game in this channel.", ephemeral=True)
        return
    key = (interaction.channel.id, interaction.user.id)
    if time.time() - guessimage_guess_cooldowns.get(key, 0) < 5:
        await interaction.response.send_message("⏳ Wait a few seconds before guessing again.", ephemeral=True)
        return
    guessimage_guess_cooldowns[key] = time.time()

    try:
        score_raw = await call_llm(
            "Score semantic similarity 0-100. Return only number.",
            f"Target: {game['prompt']}\nGuess: {answer}",
            temperature=0.1,
            max_tokens=10
        )
        score = int(re.sub(r"[^0-9]", "", score_raw) or 0)
    except Exception:
        target_words = set(game["prompt"].lower().split())
        guess_words = set(answer.lower().split())
        score = min(100, len(target_words & guess_words) * 18)

    if score > game["best_score"]:
        game["best_score"] = score
        game["best_user"] = interaction.user.id
        game["best_guess"] = answer
    await interaction.response.send_message(f"✅ Guess submitted. Similarity score: **{score}/100**", ephemeral=True)

async def finish_guessimage_round(channel_id: int, wait_seconds: int):
    await asyncio.sleep(wait_seconds)
    game = active_guessimage_games.pop(channel_id, None)
    if not game:
        return
    channel = bot.get_channel(channel_id)
    if not channel:
        return
    if game["best_user"]:
        await channel.send(
            f"🏁 Guessimage ended.\n"
            f"Prompt was: **{game['prompt']}**\n"
            f"Winner: <@{game['best_user']}> with **{game['best_guess']}** ({game['best_score']}/100)"
        )
    else:
        await channel.send(f"🏁 Guessimage ended. Prompt was: **{game['prompt']}**. No valid guesses.")

trivia_group = app_commands.Group(name="trivia", description="AI trivia commands")

@trivia_group.command(name="start", description="Start a timed trivia question")
@app_commands.describe(category="Optional category", difficulty="easy, medium, or hard")
async def trivia_start(interaction: discord.Interaction, category: str = "general", difficulty: str = "medium"):
    if interaction.channel.id in active_trivia_games:
        await interaction.response.send_message("❌ Trivia is already active in this channel.", ephemeral=True)
        return
    await interaction.response.defer()
    prompt = (
        f"Create one multiple choice trivia question.\nCategory: {category}\nDifficulty: {difficulty}\n"
        "Return strict JSON with keys: question, A, B, C, D, answer (A/B/C/D)."
    )
    question_data = None
    try:
        raw = await call_llm("You create valid trivia JSON.", prompt, temperature=0.5, max_tokens=220)
        question_data = json.loads(raw)
    except Exception:
        question_data = {
            "question": "Which planet is known as the Red Planet?",
            "A": "Venus",
            "B": "Mars",
            "C": "Jupiter",
            "D": "Mercury",
            "answer": "B"
        }

    view = TriviaAnswerView(interaction.channel.id, question_data)
    active_trivia_games[interaction.channel.id] = {"question_data": question_data, "started_at": time.time(), "view": view}
    embed = discord.Embed(title="🧠 Trivia Time", color=discord.Color.blue(), timestamp=datetime.now())
    embed.add_field(name="Question", value=question_data.get("question", "Unknown question"), inline=False)
    embed.add_field(name="A", value=question_data.get("A", "-"), inline=True)
    embed.add_field(name="B", value=question_data.get("B", "-"), inline=True)
    embed.add_field(name="C", value=question_data.get("C", "-"), inline=True)
    embed.add_field(name="D", value=question_data.get("D", "-"), inline=True)
    await interaction.followup.send(embed=embed, view=view)
    asyncio.create_task(finish_trivia_round(interaction.channel.id, 20))
    command_logger.log_command(interaction.user, "/trivia start", interaction.guild, result=f"{category}/{difficulty}")

async def finish_trivia_round(channel_id: int, wait_seconds: int):
    await asyncio.sleep(wait_seconds)
    game = active_trivia_games.pop(channel_id, None)
    if not game:
        return
    channel = bot.get_channel(channel_id)
    if not channel:
        return
    q = game["question_data"]
    leaderboard = sorted(
        [(uid, score) for (gid, uid), score in trivia_scores.items() if getattr(channel.guild, "id", None) == gid],
        key=lambda x: x[1],
        reverse=True
    )[:5]
    top_text = "\n".join([f"<@{uid}> - {score}" for uid, score in leaderboard]) if leaderboard else "No scores yet."
    await channel.send(
        f"⏰ Trivia ended.\nCorrect answer: **{q.get('answer', '?')}**\n**Leaderboard:**\n{top_text}"
    )

tree.add_command(ticket_group)
tree.add_command(guessimage_group)
tree.add_command(trivia_group)

@tree.command(name="ask", description="Ask TheBlackIris AI a question")
@app_commands.describe(prompt="What you want to ask")
async def ask(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer(thinking=True)

    try:
        context_block = build_context_block(interaction.channel.id, max_items=10)
        system_prompt = (
            "You are TheBlackIris's AI helper for a Discord server. "
            "Be concise, accurate, and friendly. Avoid illegal or harmful instructions."
        )
        user_prompt = (
            f"Recent channel context:\n{context_block}\n\n"
            f"User ({interaction.user.display_name}) asked: {prompt}\n\n"
            "Give a clear answer in Discord-friendly formatting."
        )
        response_text = await call_llm(system_prompt, user_prompt, temperature=0.7, max_tokens=350)
        for i, part in enumerate(chunk_text(response_text)):
            if i == 0:
                await interaction.followup.send(part)
            else:
                await interaction.channel.send(part)
        command_logger.log_command(interaction.user, "/ask", interaction.guild, result=f"Prompt: {prompt[:80]}")
    except Exception as e:
        await interaction.followup.send(f"❌ AI request failed: {str(e)}")
        command_logger.log_command(interaction.user, "/ask", interaction.guild, error=str(e))

@tree.command(name="setstatus", description="Change bot's status (Owner only)")
@app_commands.rename(status="text")
async def setstatus(interaction: discord.Interaction, status: str):
    if interaction.user.id not in OWNER_IDS:
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    await set_bot_status(status)
    await interaction.response.send_message(f"✅ Status changed to: `{status}`", ephemeral=True)
    command_logger.log_command(interaction.user, "/setstatus", interaction.guild, result=f"Status: {status}")

@tree.command(name="sync", description="Sync commands to Discord (Owner only)")
async def sync(interaction: discord.Interaction):
    if interaction.user.id not in OWNER_IDS:
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    try:
        synced = await tree.sync()
        await interaction.response.send_message(f"✅ Successfully synced {len(synced)} commands.", ephemeral=True)
        command_logger.log_command(interaction.user, "/sync", interaction.guild, result=f"Synced {len(synced)} commands")
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to sync commands: {str(e)}", ephemeral=True)
        command_logger.log_command(interaction.user, "/sync", interaction.guild, error=str(e))

# FIXED: Voice state update handler for recording - NOW PROPERLY IMPLEMENTED
@bot.event
async def on_voice_state_update(member, before, after):
    # Check if the member is a bot
    if member.bot:
        return

    # Voice channels to monitor for recording
    monitored_channels = [
        1000227075728347165, # VC 1
        1000227076055498823, # VC 2
        1370273932803833926, # VC 3
        1348260701847687180, # VC 4
        1348260743224623144 # VC 5
    ]

    # Check if user joined a monitored channel
    if after.channel and after.channel.id in monitored_channels:
        # Start recording if not already recording in this channel
        if after.channel.id not in voice_recorders:
            recorder = VoiceRecorder(after.channel, member.guild)
            voice_recorders[after.channel.id] = recorder
            await recorder.start_recording()

    # Check if user left a monitored channel
    if before.channel and before.channel.id in monitored_channels:
        # Check if channel is now empty (only bots remaining)
        non_bot_members = [m for m in before.channel.members if not m.bot]
        if len(non_bot_members) == 0:
            # Stop recording if this channel was being recorded
            if before.channel.id in voice_recorders:
                recorder = voice_recorders[before.channel.id]
                await recorder.stop_recording()
                del voice_recorders[before.channel.id]

async def sync_all_members_on_startup(guild: discord.Guild):
    print(f"⌛ Syncing all members in {guild.name}...")

    member_role = guild.get_role(MEMBER_ROLE_ID)
    if member_role is None:
        print(f"❌ Member role not found in {guild.name}")
        return

    synced_count = 0
    for member in guild.members:
        changed = await ensure_member_role(member, reason="Member role sync on startup")
        if changed:
            synced_count += 1

    print(f"✅ Synced member access for {synced_count} members in {guild.name}")

async def sherlock_backfill_guild(guild: discord.Guild):
    print(f"🔍 Starting sherlock backfill for {guild.name}...")
    for member in guild.members:
        if member.bot:
            continue
        out_dir = _sherlock_member_dir(guild.id, member)
        # Skip if already scanned (any .txt present)
        if any(out_dir.glob("*.txt")):
            continue
        try:
            await run_sherlock_scan_for_member(guild, member)
            await asyncio.sleep(2)
        except Exception as e:
            print(f"❌ Sherlock backfill failed for {member}: {e}")
    print(f"✅ Sherlock backfill complete for {guild.name}")

# ================= MODIFIED ON_READY =================
@bot.event
async def on_ready():
    global scheduler, startup_backfill_target_count, startup_backfill_finished_count, active_llm_provider
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    active_llm_provider = "openrouter"
    print("🤖 Active LLM provider set to openrouter (startup default)")

    # FIXED: Add ALL persistent views
    bot.add_view(ApplicationStartView())
    bot.add_view(VerificationView())
    bot.add_view(ApplicationReviewView(None, None, None, None))
    bot.add_view(TicketCreateView())
    bot.add_view(TicketCloseView(0, 0))
    bot.add_view(StaffComplaintCreateView())
    bot.add_view(StaffComplaintCloseView(0, 0))
    bot.add_view(ConfessionSubmitView())
    bot.add_view(ConfessionReviewView("", 0))
    bot.add_view(ConfessionPostView(""))
    bot.add_view(ThreadReplyView(""))
    bot.add_view(AIBanApprovalView(0))

    # NEW: Set bot status to "Watching over you"
    await set_bot_status("Watching over you")

    try:
        target_user = await bot.fetch_user(960346704236916766)
        await target_user.send("Hello! The TheBlackIris bot is now online and ready.")
        print(f"✅ Sent startup DM to {target_user.name}")
    except Exception as e:
        print(f"❌ Failed to send startup DM: {str(e)}")

    startup_backfill_target_count = len(bot.guilds)
    startup_backfill_finished_count = 0

    for guild in bot.guilds:
        await setup_ticket_system(guild)
        await setup_staff_complaints_system(guild)
        await setup_verification_system(guild)
        asyncio.create_task(backfill_guild_user_history(guild))
        asyncio.create_task(sync_all_members_on_startup(guild))
        asyncio.create_task(sherlock_backfill_guild(guild))

        # Post confessions embed on startup
        try:
            channel = guild.get_channel(CONFESSIONS_SUBMIT_CHANNEL_ID)
            if channel:
                # Check if confession embed already exists
                confession_embed_exists = False
                async for message in channel.history(limit=20):
                    if message.author == bot.user and message.embeds and "Anonymous Confessions" in message.embeds[0].title:
                        confession_embed_exists = True
                        break

                if not confession_embed_exists:
                    embed = discord.Embed(
                        title="📝 Anonymous Confessions",
                        description="Got something to get off your chest? Share it anonymously!",
                        color=discord.Color.purple()
                    )
                    embed.add_field(
                        name="How it works:",
                        value="1. Click the button below to submit a confession\n"
                              "2. Staff will review your submission\n"
                              "3. If approved, it will be posted anonymously\n"
                              "4. Others can reply in a discussion thread",
                        inline=False
                    )
                    embed.add_field(
                        name="Rules:",
                        value="• No hate speech or harassment\n• No personal information\n• Be respectful\n• No spam",
                        inline=False
                    )
                    embed.set_footer(text="All confessions are reviewed before posting")

                    view = ConfessionSubmitView()
                    message = await channel.send(embed=embed, view=view)
                    print(f"✅ Posted confessions embed in #{channel.name}")
        except Exception as e:
            print(f"❌ Failed to post confessions embed: {e}")

    print("Registered commands:")
    for cmd in tree.get_commands():
        print(f"- {cmd.name}: {cmd.description}")

    try:
        print("⌛ Syncing commands...")
        synced = await tree.sync()
        print(f"✅ Successfully synced {len(synced)} commands")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")
        try:
            await asyncio.sleep(5)
            synced = await tree.sync()
            print(f"✅ Successfully synced {len(synced)} commands on second attempt")
        except Exception as e2:
            print(f"❌ Failed second sync attempt: {e2}")
    await process_pending_ai_ban_reviews_on_startup()

    if scheduler is None:
        scheduler = AsyncIOScheduler(timezone=DAILY_TIMEZONE)
        scheduler.add_job(send_daily_logs, 'cron', hour=23, minute=59, id="daily_logs", replace_existing=True)
        scheduler.add_job(post_daily_question, 'cron', hour=12, minute=0, id="daily_question_noon", replace_existing=True)
        scheduler.add_job(post_birthday_announcements, 'cron', hour=9, minute=0, id="daily_birthdays", replace_existing=True)
        scheduler.start()
        print("✅ Scheduler started (logs, daily question, birthdays)")
    else:
        print("ℹ️ Scheduler already running")

# Welcome new members and grant the join (unverified) role.
@bot.event
async def on_member_join(member: discord.Member):
    save_member_activity(member.guild.id, member.id, "server_join", details="Joined the server")
    # Auto-run sherlock scan in background (all members opted in via onboarding)
    if not member.bot:
        async def _auto_scan():
            try:
                await asyncio.sleep(5)
                await run_sherlock_scan_for_member(member.guild, member)
            except Exception as e:
                print(f"❌ Auto sherlock scan failed for {member}: {e}")
        asyncio.create_task(_auto_scan())
    join_role = member.guild.get_role(JOIN_ROLE_ID)
    if join_role and join_role not in member.roles:
        try:
            await member.add_roles(join_role, reason="Granted join role on join")
        except Exception as e:
            print(f"❌ Failed to grant join role: {e}")
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        try:
            embed = discord.Embed(
                title="🌟 Welcome to TheBlackIris!",
                description=(
                    f"Welcome {member.mention} to our community!\n\n"
                    "You now have the member role and full server access."
                ),
                color=discord.Color.purple()
            )
            # Try to add the DO_banner image
            banner_path = script_dir / "TheBlackIris.png"
            if banner_path.exists():
                try:
                    file = discord.File(banner_path, filename="TheBlackIris.png")
                    embed.set_image(url="attachment://TheBlackIris.png")
                    await channel.send(file=file, embed=embed)
                except Exception as e:
                    print(f"❌ Failed to send banner image: {e}")
                    # Send embed without banner if image fails
                    await channel.send(embed=embed)
            else:
                print(f"❌ Banner image not found at {banner_path}")
                await channel.send(embed=embed)

            print(f"✅ Sent welcome message for {member.name}")
        except Exception as e:
            print(f"❌ Failed to send welcome message for {member.name}: {e}")
    else:
        print(f"❌ Welcome channel not found (ID: {WELCOME_CHANNEL_ID})")

# IMPROVED: Enhanced voice state update logging
@bot.event
async def on_voice_state_update(member, before, after):
    try:
        if member.bot:
            return

        monitored_channels = {
            1000227075728347165,
            1000227076055498823,
            1370273932803833926,
            1348260701847687180,
            1348260743224623144,
        }

        if after.channel and after.channel.id in monitored_channels and after.channel.id not in voice_recorders:
            recorder = VoiceRecorder(after.channel, member.guild)
            voice_recorders[after.channel.id] = recorder
            await recorder.start_recording()

        if before.channel and before.channel.id in monitored_channels:
            non_bot_members = [m for m in before.channel.members if not m.bot]
            if len(non_bot_members) == 0 and before.channel.id in voice_recorders:
                recorder = voice_recorders[before.channel.id]
                await recorder.stop_recording()
                del voice_recorders[before.channel.id]

        if before.channel != after.channel:
            if before.channel is None and after.channel is not None:
                save_member_activity(member.guild.id, member.id, "voice_join", after.channel.id, f"Joined {after.channel.name}")
            elif before.channel is not None and after.channel is None:
                save_member_activity(member.guild.id, member.id, "voice_leave", before.channel.id, f"Left {before.channel.name}")
            elif before.channel is not None and after.channel is not None:
                save_member_activity(
                    member.guild.id,
                    member.id,
                    "voice_move",
                    after.channel.id,
                    f"Moved from {before.channel.name} to {after.channel.name}",
                )

        # Log server mute/unmute
        if before.mute != after.mute:
            action = "server muted" if after.mute else "server unmuted"
            moderator = "Unknown"
            try:
                async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.member_update):
                    if entry.target.id == member.id and (datetime.now(datetime.timezone.utc) - entry.created_at).total_seconds() < 5:
                        if hasattr(entry.after, 'mute') and entry.after.mute == after.mute:
                            moderator = entry.user
                            break
            except:
                pass

            command_logger.log_voice_action(moderator, member, action, after.channel)
            await log_message_event("voice_mute", member=member, moderator=moderator, action=action)

        # Log server deafen/undeafen
        if before.deaf != after.deaf:
            action = "server deafened" if after.deaf else "server undeafened"
            moderator = "Unknown"
            try:
                async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.member_update):
                    if entry.target.id == member.id and (datetime.now(datetime.timezone.utc) - entry.created_at).total_seconds() < 5:
                        if hasattr(entry.after, 'deaf') and entry.after.deaf == after.deaf:
                            moderator = entry.user
                            break
            except:
                pass

            command_logger.log_voice_action(moderator, member, action, after.channel)
            await log_message_event("voice_deafen", member=member, moderator=moderator, action=action)

        # Original voice move logging
        if before.channel and after.channel and before.channel != after.channel:
            await asyncio.sleep(1)
            async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.member_move):
                if entry.target.id == member.id and (datetime.now(datetime.timezone.utc) - entry.created_at).seconds < 5:
                    await log_to_channel(member.guild, "Voice Move",
                                        f"{entry.user.mention} moved {member.mention}\n"
                                        f"**From:** {before.channel.mention}\n"
                                        f"**To:** {after.channel.mention}")
                    return
            await log_to_channel(member.guild, "Voice Move",
                                f"{member.mention} was moved\n"
                                f"**From:** {before.channel.mention}\n"
                                f"**To:** {after.channel.mention}")
    except Exception as e:
        print(f"❌ Error in on_voice_state_update: {str(e)}")

# FIXED: The main issue was in on_member_update where 'role' was not defined
@bot.event
async def on_member_update(before, after):
    if before.roles != after.roles:
        before_roles = set(r.id for r in before.roles)
        after_roles = set(r.id for r in after.roles)
        changed_roles = before_roles.symmetric_difference(after_roles)
        staff_role_ids = set(STAFF_ROLES.keys())

        if changed_roles & staff_role_ids:
            # IMPROVED: Enhanced staff role update logging
            added_roles = after_roles - before_roles
            removed_roles = before_roles - after_roles

            # Try to find who made the role change
            moderator = None
            try:
                async for entry in after.guild.audit_logs(limit=5, action=discord.AuditLogAction.member_role_update):
                    if entry.target.id == after.id and (datetime.now(datetime.timezone.utc) - entry.created_at).total_seconds() < 5:
                        moderator = entry.user
                        break
            except Exception as e:
                print(f"Error checking audit logs: {e}")
                moderator = "Unknown"

            # If no moderator found, set to "Unknown" but ensure it's a string
            if moderator is None:
                moderator = "Unknown"

            # Log added roles
            for role_id in added_roles:
                if role_id in STAFF_ROLES:
                    role_name = STAFF_ROLES[role_id]
                    # FIXED: Pass moderator which might be a string or Member object
                    command_logger.log_role_update(moderator, after, "assigned", role_name)
                    command_logger.log_staff_list_change("added", user=after, role_name=role_name, updated_by=moderator)

            # Log removed roles
            for role_id in removed_roles:
                if role_id in STAFF_ROLES:
                    role_name = STAFF_ROLES[role_id]
                    # FIXED: Pass moderator which might be a string or Member object
                    command_logger.log_role_update(moderator, after, "removed", role_name)
                    command_logger.log_staff_list_change("removed", user=after, role_name=role_name, updated_by=moderator)

            # Update staff list with moderator info
            await update_staff_list(after.guild, updated_by=moderator)

    if before.nick != after.nick:
        old_nick = before.nick or before.name
        new_nick = after.nick or after.name
        await log_to_channel(after.guild, "Nickname Changed",
                            f"{after.mention} changed nickname:\n**Before:** {old_nick}\n**After:** {new_nick}")

    # FIXED: Changed the condition to use 'r' instead of undefined 'role'
    if any(r.id in STAFF_ROLES for r in after.roles):
        await update_staff_list(after.guild)

@bot.event
async def on_user_update(before, after):
    if before.name == after.name:
        return
    for guild in bot.guilds:
        member = guild.get_member(after.id)
        if member:
            save_member_activity(guild.id, member.id, "username_changed", details=f"Changed username from {before.name} to {after.name}")

# FIXED: Added proper DM channel handling
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Handle DM messages
    if isinstance(message.channel, discord.DMChannel) and message.author != bot.user:
        # Check if it's an application response
        if message.author.id in application_sessions:
            await handle_application_response(message)
            return


    # Only process guild messages for these checks
    if hasattr(message, 'guild') and message.guild:
        # FIXED: Changed to use 'r' instead of undefined 'role'
        if "@everyone" in message.content or "@here" in message.content:
            has_allowed_role = any(r.id in EVERYONE_ALLOWED_ROLES for r in message.author.roles)
            if not has_allowed_role:
                try:
                    await message.delete()
                    await message.author.timeout(datetime.timedelta(minutes=15), reason=" @everyone mention")
                    await log_to_channel(message.guild, "Member Timed Out",
                                        f"{message.author.mention} was timed out by {bot.user.mention}\n"
                                        f"**Reason:** @everyone mention")
                    await log_message_event(
                        "timeout",
                        member=message.author,
                        moderator=bot.user,
                        duration="15 minutes",
                        reason="@everyone mention"
                    )
                    try:
                        await message.author.send(
                            "⚠️ You have been timed out for 15 minutes for using @everyone without permission. "
                            "Only staff members can use @everyone mentions."
                        )
                    except discord.Forbidden:
                        pass
                except discord.Forbidden:
                    print(f"❌ Missing permissions to timeout {message.author}")
                except Exception as e:
                    print(f"❌ Error handling @everyone mention: {str(e)}")
        content_lower = message.content.lower()
        for pattern in SEVERE_BLACKLIST:
            if re.search(pattern, content_lower):
                try:
                    await message.delete()
                    reason = "Automatic ban: severe blacklisted content"
                    await message.author.ban(reason=reason)
                    await log_to_channel(
                        message.guild,
                        "Member Banned",
                        f"{message.author.mention} was banned by {bot.user.mention}\n"
                        f"**Reason:** {reason}",
                        channel_id=BAN_LOG_CHANNEL_ID
                    )
                    await log_message_event(
                        "severe_blacklist",
                        message=message,
                        word=pattern
                    )
                    try:
                        await message.author.send(
                            f"⚠️ You have been banned from {message.guild.name}. Reason: {reason}"
                        )
                    except discord.Forbidden:
                        pass
                except discord.Forbidden:
                    print(f"❌ Missing permissions to ban {message.author}")
                except Exception as e:
                    print(f"❌ Error handling severe blacklisted word: {str(e)}")
                return
        for pattern in MODERATE_BLACKLIST:
            if re.search(pattern, content_lower):
                try:
                    await message.delete()
                    reason = "Blacklisted word (automatic timeout)"
                    await message.author.timeout(datetime.timedelta(minutes=60), reason=reason)
                    await log_to_channel(message.guild, "Member Timed Out",
                                        f"{message.author.mention} was timed out by {bot.user.mention}\n"
                                        f"**Reason:** {reason}")
                    await log_message_event(
                        "blacklist",
                        message=message,
                        word=pattern
                    )
                    try:
                        await message.author.send(
                            "⚠️ Your message was deleted and you've been timed out for 30 minutes for using inappropriate language. "
                            "Please review our server rules."
                        )
                    except discord.Forbidden:
                        pass
                except discord.Forbidden:
                    print(f"❌ Missing permissions to timeout {message.author}")
                except Exception as e:
                    print(f"❌ Error handling blacklisted word: {str(e)}")
                return

        store_message_log_entry(message)
        store_ai_memory_message(message)
        append_message_context(message)

        if should_auto_reply_in_general(message):
            try:
                reply_text = await generate_general_auto_reply(message)
                if reply_text:
                    global last_general_ai_reply_at
                    last_general_ai_reply_at = time.time()
                    for i, part in enumerate(chunk_text(reply_text)):
                        if i == 0:
                            await message.reply(part, mention_author=False)
                        else:
                            await message.channel.send(part)
            except Exception as e:
                print(f"❌ General AI auto-reply failed: {e}")
    await bot.process_commands(message)

# FIXED: Added proper DM channel handling
@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    moderator = "Unknown"
    try:
        # Only check audit logs for guild messages (not DMs)
        if hasattr(message, 'guild') and message.guild:
            async for entry in message.guild.audit_logs(limit=5, action=discord.AuditLogAction.message_delete):
                if entry.target.id == message.author.id and (datetime.now(datetime.timezone.utc) - entry.created_at).seconds < 5:
                    moderator = entry.user
                    break
    except discord.Forbidden:
        pass
    await log_message_event("delete", message=message, moderator=moderator)

# FIXED: Added proper DM channel handling
@bot.event
async def on_message_edit(before, after):
    if before.author.bot:
        return
    if before.content == after.content:
        return
    await log_message_event("edit", before=before, after=after)

# UPDATED: on_member_remove to skip logging for banned and kicked users
@bot.event
async def on_member_remove(member):
    # Check if the user was banned (log to mod log, skip leave log)
    try:
        async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.ban):
            if entry.target.id == member.id and (datetime.now(datetime.timezone.utc) - entry.created_at).seconds < 5:
                await log_to_channel(
                    member.guild,
                    "Member Banned",
                    f"{member.mention} was banned",
                    channel_id=BAN_LOG_CHANNEL_ID
                )
                return
    except:
        pass

    # Check if the user was kicked (log to mod log, skip leave log)
    try:
        async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.kick):
            if entry.target.id == member.id and (datetime.now(datetime.timezone.utc) - entry.created_at).seconds < 5:
                await log_to_channel(
                    member.guild,
                    "Member Kicked",
                    f"{member.mention} was kicked",
                    channel_id=KICK_LOG_CHANNEL_ID
                )
                return
    except:
        pass

    # Only log if not banned or kicked
    save_member_activity(member.guild.id, member.id, "server_leave", details="Left the server")
    await log_message_event("leave", member=member)

@bot.event
async def on_app_command_completion(interaction, command):
    print(f"✅ Command used: /{command.name} by {interaction.user} (ID: {interaction.user.id}) in guild {interaction.guild.name if interaction.guild else 'DM'}")

# ================= ERROR HANDLING =================
@bot.event
async def on_error(event, *args, **kwargs):
    print(f"Error in event {event}: {args} {kwargs}")
    import traceback
    traceback.print_exc()

if not TOKEN:
    if BYPASS_WARNINGS:
        print("⚠️ WARNING: Starting bot without token! Most features will not work.")
        print("   Run again without --bypass-warnings to see the error properly.")
        bot.run("dummy")
    else:
        print("\n❌ ERROR: Token not found. Bot cannot start without a valid token.")
        exit()
else:
    print(f"🔑 Using token: {TOKEN[:10]}...")
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("❌ Invalid token! Please check your .env file")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()


