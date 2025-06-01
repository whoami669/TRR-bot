import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import os
import logging
import aiosqlite
import json
from datetime import datetime, timezone
import time
import traceback
from collections import defaultdict
import psutil
import sys

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Content filtering system
class ContentFilter:
    def __init__(self):
        self.forbidden_phrases = [
            "@everyone", "VIRAL CHALLENGE ALERT", "BREAKING",
            "CONTROVERSIAL gaming confession", "Collaboration corner",
            "COMMUNITY PULSE", "ENERGY CHECK", "HYPE TRAIN",
            "MOMENTUM ALERT", "POWER SURGE", "VIBE CHECK"
        ]
        self.spam_cache = defaultdict(list)
    
    def is_spam(self, user_id: int, content: str) -> bool:
        """Advanced spam detection"""
        current_time = time.time()
        user_messages = self.spam_cache[user_id]
        
        # Remove old messages (older than 10 seconds)
        user_messages[:] = [msg for msg in user_messages if current_time - msg['time'] < 10]
        
        # Check message frequency
        if len(user_messages) >= 5:
            return True
            
        # Check for repeated content
        similar_count = sum(1 for msg in user_messages if msg['content'] == content)
        if similar_count >= 2:
            return True
            
        # Add current message
        user_messages.append({'content': content, 'time': current_time})
        return False
    
    def filter_content(self, content: str) -> bool:
        """Enhanced content filtering"""
        if not content:
            return True
            
        content_lower = content.lower()
        
        # Check forbidden phrases
        for phrase in self.forbidden_phrases:
            if phrase.lower() in content_lower:
                logger.warning(f"Blocked forbidden phrase: {phrase}")
                return False
        
        # Check message length
        if len(content) > 2000:
            return False
            
        # Check excessive caps
        if len(content) > 10:
            caps_ratio = sum(1 for c in content if c.isupper()) / len(content)
            if caps_ratio > 0.7:
                return False
        
        return True

# Performance monitoring
class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            'commands_executed': 0,
            'errors_handled': 0,
            'database_queries': 0,
            'uptime_start': time.time()
        }
        
    def track_command(self):
        self.metrics['commands_executed'] += 1
        
    def track_error(self):
        self.metrics['errors_handled'] += 1
        
    def track_db_query(self):
        self.metrics['database_queries'] += 1
        
    def get_system_info(self):
        """Get system performance metrics"""
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'uptime': time.time() - self.metrics['uptime_start']
        }

# Enhanced database manager
class DatabaseManager:
    def __init__(self, db_path='ultrabot_enhanced.db'):
        self.db_path = db_path
        
    async def init_database(self):
        """Initialize enhanced database schema"""
        async with aiosqlite.connect(self.db_path) as db:
            # Enhanced guilds table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS guilds (
                    guild_id INTEGER PRIMARY KEY,
                    prefix TEXT DEFAULT '/',
                    settings TEXT DEFAULT '{}',
                    premium_until TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Enhanced users table with more tracking
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER,
                    guild_id INTEGER,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    coins INTEGER DEFAULT 100,
                    warnings INTEGER DEFAULT 0,
                    messages_sent INTEGER DEFAULT 0,
                    voice_time INTEGER DEFAULT 0,
                    commands_used INTEGER DEFAULT 0,
                    last_daily TIMESTAMP,
                    last_work TIMESTAMP,
                    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_reactions_given INTEGER DEFAULT 0,
                    total_reactions_received INTEGER DEFAULT 0,
                    streak_days INTEGER DEFAULT 0,
                    reputation INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, guild_id)
                )
            ''')
            
            # Command usage statistics
            await db.execute('''
                CREATE TABLE IF NOT EXISTS command_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    command_name TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    success BOOLEAN DEFAULT TRUE,
                    execution_time REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Error logs
            await db.execute('''
                CREATE TABLE IF NOT EXISTS error_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    traceback_info TEXT,
                    guild_id INTEGER,
                    user_id INTEGER,
                    command_name TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Performance metrics
            await db.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.commit()
            logger.info("Enhanced database initialized successfully")
    
    async def log_command_usage(self, command_name: str, user_id: int, guild_id: int, 
                              success: bool = True, execution_time: float = 0.0):
        """Log command usage for analytics"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO command_stats 
                (command_name, user_id, guild_id, success, execution_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (command_name, user_id, guild_id, success, execution_time))
            await db.commit()
    
    async def log_error(self, error_type: str, error_message: str, traceback_info: str = None,
                       guild_id: int = None, user_id: int = None, command_name: str = None):
        """Log errors for debugging"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO error_logs 
                (error_type, error_message, traceback_info, guild_id, user_id, command_name)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (error_type, error_message, traceback_info, guild_id, user_id, command_name))
            await db.commit()

class UltraBotEnhanced(commands.Bot):
    def __init__(self):
        # Enhanced intents configuration
        intents = discord.Intents.all()
        
        super().__init__(
            command_prefix='/',  # Fixed prefix for better performance
            intents=intents,
            help_command=None,
            case_insensitive=True,
            max_messages=15000,  # Increased message cache
            chunk_guilds_at_startup=False,  # Optimize startup
            member_cache_flags=discord.MemberCacheFlags.from_intents(intents)
        )
        
        # Initialize components
        self.start_time = datetime.now(timezone.utc)
        self.content_filter = ContentFilter()
        self.performance_monitor = PerformanceMonitor()
        self.db_manager = DatabaseManager()
        
        # Enhanced tracking
        self.command_cooldowns = defaultdict(lambda: defaultdict(float))
        self.error_count = 0
        self.last_restart = time.time()
        self.ready_time = None
        
        # Rate limiting
        self.rate_limits = defaultdict(list)
        
    async def setup_hook(self):
        """Enhanced setup with better error handling"""
        try:
            logger.info("Starting bot setup...")
            
            # Initialize enhanced database
            await self.db_manager.init_database()
            
            # Load cogs with priority system
            priority_cogs = [
                'cogs.ai_features',  # High priority - main feature
                'cogs.moderation_advanced',
                'cogs.spam_control',
                'cogs.advanced_analytics'
            ]
            
            standard_cogs = [
                'cogs.entertainment_suite',
                'cogs.social_features',
                'cogs.automation_system',
                'cogs.economy_advanced',
                'cogs.music_premium',
                'cogs.customization_hub',
                'cogs.security_suite',
                'cogs.productivity_tools',
                'cogs.gamer_suite'
            ]
            
            # Load priority cogs first
            for cog in priority_cogs:
                await self._load_cog_safely(cog, priority=True)
            
            # Load standard cogs
            for cog in standard_cogs:
                await self._load_cog_safely(cog)
                
            # Start background tasks
            self.performance_tracking.start()
            self.database_cleanup.start()
            
            logger.info("Bot setup completed successfully")
            
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            logger.error(traceback.format_exc())
    
    async def _load_cog_safely(self, cog_name: str, priority: bool = False):
        """Safely load cogs with enhanced error handling"""
        try:
            await self.load_extension(cog_name)
            logger.info(f"✅ Loaded {cog_name}")
        except ImportError as e:
            logger.warning(f"⚠️ Missing dependency for {cog_name}: {e}")
        except Exception as e:
            logger.error(f"❌ Failed to load {cog_name}: {e}")
            if priority:
                logger.critical(f"Priority cog {cog_name} failed to load!")
    
    async def on_ready(self):
        """Enhanced ready event with comprehensive startup info"""
        self.ready_time = datetime.now(timezone.utc)
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f"✅ Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
        
        # Display startup information
        startup_info = [
            f"🤖 {self.user.name} - Enhanced Ultra Bot",
            f"📊 Connected to {len(self.guilds)} guilds",
            f"👥 Serving {sum(guild.member_count for guild in self.guilds)} members",
            f"⚡ Startup time: {(self.ready_time - self.start_time).total_seconds():.2f}s",
            f"🔧 Discord.py version: {discord.__version__}",
            f"🐍 Python version: {sys.version.split()[0]}",
            f"💾 Memory usage: {psutil.Process().memory_info().rss / 1024 / 1024:.1f} MB"
        ]
        
        for info in startup_info:
            logger.info(info)
        
        # Set enhanced presence
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{len(self.guilds)} servers | /help for commands"
            )
        )
    
    async def on_command_error(self, ctx, error):
        """Enhanced error handling with logging"""
        self.performance_monitor.track_error()
        
        # Log error to database
        await self.db_manager.log_error(
            error_type=type(error).__name__,
            error_message=str(error),
            traceback_info=traceback.format_exc(),
            guild_id=ctx.guild.id if ctx.guild else None,
            user_id=ctx.author.id,
            command_name=ctx.command.name if ctx.command else None
        )
        
        # Handle specific errors
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏰ Command on cooldown. Try again in {error.retry_after:.1f}s")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ I don't have the required permissions")
        else:
            logger.error(f"Unhandled error in {ctx.command}: {error}")
    
    async def on_message(self, message):
        """Enhanced message processing with filtering"""
        if message.author.bot:
            return
            
        # Content filtering
        if not self.content_filter.filter_content(message.content):
            return
            
        # Spam detection
        if self.content_filter.is_spam(message.author.id, message.content):
            try:
                await message.delete()
                await message.channel.send(
                    f"{message.author.mention}, please slow down!",
                    delete_after=5
                )
            except discord.HTTPException:
                pass
            return
        
        await self.process_commands(message)
    
    @tasks.loop(minutes=5)
    async def performance_tracking(self):
        """Track performance metrics"""
        try:
            system_info = self.performance_monitor.get_system_info()
            
            # Log key metrics to database
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                for metric, value in system_info.items():
                    await db.execute(
                        'INSERT INTO performance_metrics (metric_type, value) VALUES (?, ?)',
                        (metric, value)
                    )
                await db.commit()
                
        except Exception as e:
            logger.error(f"Performance tracking error: {e}")
    
    @tasks.loop(hours=24)
    async def database_cleanup(self):
        """Clean up old database entries"""
        try:
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                # Clean old performance metrics (keep 30 days)
                await db.execute('''
                    DELETE FROM performance_metrics 
                    WHERE timestamp < datetime('now', '-30 days')
                ''')
                
                # Clean old error logs (keep 7 days)
                await db.execute('''
                    DELETE FROM error_logs 
                    WHERE timestamp < datetime('now', '-7 days')
                ''')
                
                await db.commit()
                logger.info("Database cleanup completed")
                
        except Exception as e:
            logger.error(f"Database cleanup error: {e}")
    
    @performance_tracking.before_loop
    @database_cleanup.before_loop
    async def before_loops(self):
        await self.wait_until_ready()

async def main():
    """Enhanced main function with better error handling"""
    bot = UltraBotEnhanced()
    
    # Get token with validation
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN environment variable not found!")
        return
    
    try:
        logger.info("Starting Enhanced Ultra Bot...")
        await bot.start(token)
    except discord.LoginFailure:
        logger.error("Invalid Discord token provided")
    except Exception as e:
        logger.error(f"Bot startup failed: {e}")
        logger.error(traceback.format_exc())
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())