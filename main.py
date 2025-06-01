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

# Middleware for filtering message generation
def block_forbidden_messages(content: str) -> bool:
    forbidden_phrases = [
        "@everyone",
        "VIRAL CHALLENGE ALERT",
        "BREAKING",
        "CONTROVERSIAL gaming confession",
        "Collaboration corner",
        "COMMUNITY PULSE",
        "ENERGY CHECK",
        "HYPE TRAIN",
        "MOMENTUM ALERT",
        "POWER SURGE",
        "VIBE CHECK",
        "PEAK PERFORMANCE",
        "UNSTOPPABLE FORCE",
        "STAR POWER",
        "WAVE OF ENERGY",
        "DIAMOND MINDSET",
        "ENERGY AMPLIFICATION",
        "ENTHUSIASM OVERDRIVE",
        "PASSION AMPLIFIER",
        "HYPERDRIVE",
        "TURBOCHARGED",
        "MAXIMUM ENGAGEMENT",
        "NUCLEAR PARTICIPATION"
    ]
    for phrase in forbidden_phrases:
        if phrase.lower() in content.lower():
            logging.warning(f"Attempted to generate a blocked message containing: {phrase}")
            return False
    return True

# Enhanced message filtering - simplified approach
def enhanced_content_filter(content: str) -> bool:
    """Enhanced content filtering with improved detection"""
    if not content:
        return True
    
    # Check for forbidden phrases
    if not block_forbidden_messages(content):
        return False
    
    # Additional spam detection
    if len(content) > 2000:  # Discord's message limit
        return False
        
    # Check for excessive caps (more than 70% uppercase)
    if len(content) > 10:
        caps_ratio = sum(1 for c in content if c.isupper()) / len(content)
        if caps_ratio > 0.7:
            return False
    
    return True

# Function to filter undesired messages
def filter_message(content: str) -> str:
    forbidden_phrases = [
        "@everyone",
        "VIRAL CHALLENGE ALERT",
        "BREAKING",
        "CONTROVERSIAL gaming confession",
        "Collaboration corner",
        "COMMUNITY PULSE",
        "ENERGY CHECK",
        "HYPE TRAIN",
        "MOMENTUM ALERT",
        "POWER SURGE",
        "VIBE CHECK",
        "PEAK PERFORMANCE",
        "UNSTOPPABLE FORCE",
        "STAR POWER",
        "WAVE OF ENERGY",
        "DIAMOND MINDSET",
        "ENERGY AMPLIFICATION",
        "ENTHUSIASM OVERDRIVE",
        "PASSION AMPLIFIER",
        "HYPERDRIVE",
        "TURBOCHARGED",
        "MAXIMUM ENGAGEMENT",
        "NUCLEAR PARTICIPATION"
    ]
    for phrase in forbidden_phrases:
        if phrase.lower() in content.lower():
            logging.warning(f"Blocked message containing forbidden phrase: {phrase}")
            return "[Blocked Message]"
    return content

# Overriding send method for all outgoing messages
original_send = discord.TextChannel.send

async def new_send(self, content=None, **kwargs):
    if content:
        content = filter_message(content)
    return await original_send(self, content=content, **kwargs)

discord.TextChannel.send = new_send
from datetime import datetime, timezone
from dotenv import load_dotenv
import aiosqlite
import json

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)

# Database setup
async def init_database():
    async with aiosqlite.connect('ultrabot.db') as db:
        # Core tables
        await db.execute('''
            CREATE TABLE IF NOT EXISTS guilds (
                guild_id INTEGER PRIMARY KEY,
                prefix TEXT DEFAULT '/',
                settings TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
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
                last_daily TIMESTAMP,
                last_work TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, guild_id)
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS moderation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                moderator_id INTEGER,
                action TEXT,
                reason TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS automod_settings (
                guild_id INTEGER PRIMARY KEY,
                spam_protection BOOLEAN DEFAULT 1,
                link_filter BOOLEAN DEFAULT 1,
                word_filter BOOLEAN DEFAULT 1,
                caps_filter BOOLEAN DEFAULT 1,
                emoji_spam_filter BOOLEAN DEFAULT 1,
                banned_words TEXT DEFAULT '[]',
                immune_roles TEXT DEFAULT '[]'
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS chat_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                channel_id INTEGER,
                user_id INTEGER,
                message_length INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sentiment_score REAL,
                toxicity_score REAL,
                has_mentions BOOLEAN DEFAULT FALSE,
                has_attachments BOOLEAN DEFAULT FALSE,
                reaction_count INTEGER DEFAULT 0,
                is_thread BOOLEAN DEFAULT FALSE
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS voice_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                channel_id INTEGER,
                user_id INTEGER,
                join_time TIMESTAMP,
                leave_time TIMESTAMP,
                duration_seconds INTEGER,
                was_muted BOOLEAN DEFAULT FALSE,
                was_deafened BOOLEAN DEFAULT FALSE
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS server_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                date DATE,
                total_messages INTEGER DEFAULT 0,
                active_users INTEGER DEFAULT 0,
                new_members INTEGER DEFAULT 0,
                left_members INTEGER DEFAULT 0,
                voice_minutes INTEGER DEFAULT 0,
                channels_created INTEGER DEFAULT 0,
                channels_deleted INTEGER DEFAULT 0,
                avg_message_length REAL DEFAULT 0
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_activity_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                date DATE,
                messages_sent INTEGER DEFAULT 0,
                voice_minutes INTEGER DEFAULT 0,
                reactions_given INTEGER DEFAULT 0,
                reactions_received INTEGER DEFAULT 0,
                commands_used INTEGER DEFAULT 0,
                first_activity TIMESTAMP,
                last_activity TIMESTAMP,
                UNIQUE(guild_id, user_id, date)
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS channel_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                channel_id INTEGER,
                date DATE,
                message_count INTEGER DEFAULT 0,
                unique_users INTEGER DEFAULT 0,
                avg_message_length REAL DEFAULT 0,
                peak_hour INTEGER DEFAULT 0,
                UNIQUE(guild_id, channel_id, date)
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                guild_id INTEGER,
                channel_id INTEGER,
                reminder_text TEXT,
                remind_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS custom_commands (
                guild_id INTEGER,
                command_name TEXT,
                response TEXT,
                created_by INTEGER,
                usage_count INTEGER DEFAULT 0,
                PRIMARY KEY (guild_id, command_name)
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS starboard (
                message_id INTEGER PRIMARY KEY,
                guild_id INTEGER,
                channel_id INTEGER,
                author_id INTEGER,
                star_count INTEGER DEFAULT 0,
                starboard_message_id INTEGER
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                send_at TIMESTAMP NOT NULL,
                created_by INTEGER NOT NULL,
                sent BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Create role menus table for customization hub
        await db.execute('''
            CREATE TABLE IF NOT EXISTS role_menus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                title TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create role menu options table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS role_menu_options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                menu_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                emoji TEXT,
                description TEXT,
                FOREIGN KEY (menu_id) REFERENCES role_menus (id)
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS auto_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                trigger_type TEXT NOT NULL,
                trigger_value TEXT NOT NULL,
                role_id INTEGER NOT NULL,
                condition_value INTEGER DEFAULT 1
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS auto_reactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                trigger_type TEXT NOT NULL,
                trigger_value TEXT NOT NULL,
                emojis TEXT NOT NULL
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS welcome_config (
                guild_id INTEGER PRIMARY KEY,
                channel_id INTEGER,
                message TEXT,
                auto_role_id INTEGER
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS ai_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                command_name TEXT NOT NULL,
                tokens_used INTEGER DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await db.commit()

class UltraBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix=self.get_prefix,
            intents=intents,
            help_command=None,
            case_insensitive=True,
            max_messages=10000  # Increased message cache for better performance
        )
        self.start_time = datetime.now(timezone.utc)
        self.command_stats = defaultdict(int)
        self.error_count = 0
        self.last_restart = time.time()
        self.rate_limits = defaultdict(list)
        self.performance_metrics = {
            'commands_executed': 0,
            'errors_handled': 0,
            'database_queries': 0,
            'memory_usage': 0
        }
        
    async def get_system_stats(self):
        """Get enhanced system performance statistics"""
        try:
            process = psutil.Process()
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'memory_usage_mb': process.memory_info().rss / 1024 / 1024,
                'uptime_hours': (time.time() - self.last_restart) / 3600,
                'guilds': len(self.guilds),
                'users': sum(guild.member_count or 0 for guild in self.guilds),
                'commands_run': self.performance_metrics['commands_executed']
            }
        except Exception:
            return {}
        
    async def get_prefix(self, message):
        if not message.guild:
            return '/'
        
        async with aiosqlite.connect('ultrabot.db') as db:
            async with db.execute('SELECT prefix FROM guilds WHERE guild_id = ?', (message.guild.id,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else '/'

    async def setup_hook(self):
        # Initialize database
        await init_database()
        
        # Load essential cogs (staying within Discord's 100 command limit)
        cogs = [
            'cogs.spam_control',
            'cogs.advanced_analytics',
            'cogs.moderation_advanced',
            'cogs.entertainment_suite',
            'cogs.utility_toolkit',
            'cogs.social_features',
            'cogs.automation_system',
            'cogs.economy_advanced',
            'cogs.music_premium',
            'cogs.customization_hub',
            'cogs.security_suite',
            'cogs.productivity_tools',
            'cogs.server_takeover',
            'cogs.community_revival',
            'cogs.engagement_system',
            'cogs.auto_gaming',
            'cogs.activity_boosters',
            'cogs.viral_content',
            'cogs.hype_machine',
            'cogs.content_amplifier',
            'cogs.momentum_engine',
            'cogs.interaction_engine',
            'cogs.activity_waves',
            'cogs.chaos_engine',
            'cogs.energy_multiplier',
            'cogs.engagement_overdrive',
            'cogs.gamer_suite',
            'cogs.ai_features',
            'cogs.advanced_utilities',
            'cogs.server_management',
            'cogs.games_entertainment',
            'cogs.web_tools',
            'cogs.help_system',
        ]
        
        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"✅ Loaded {cog}")
            except Exception as e:
                print(f"❌ Failed to load {cog}: {e}")
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            print(f"✅ Synced {len(synced)} slash commands")
        except Exception as e:
            print(f"❌ Failed to sync commands: {e}")
        
        # Start background tasks
        self.cleanup_tasks.start()
        self.analytics_processor.start()
        self.reminder_checker.start()

    async def on_ready(self):
        print(f"🤖 {self.user.name} - Ultra Multi-Functional Bot")
        print(f"📊 Connected to {len(self.guilds)} guilds")
        print(f"👥 Serving {sum(guild.member_count or 0 for guild in self.guilds)} members")
        print(f"🚀 Ready for maximum productivity and fun!")
        
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="Where am i? who am i? | /help"
            )
        )

    async def on_guild_join(self, guild):
        # Initialize guild in database
        async with aiosqlite.connect('ultrabot.db') as db:
            await db.execute(
                'INSERT OR IGNORE INTO guilds (guild_id) VALUES (?)',
                (guild.id,)
            )
            await db.commit()

    @tasks.loop(hours=1)
    async def cleanup_tasks(self):
        """Clean up expired data"""
        async with aiosqlite.connect('ultrabot.db') as db:
            # Clean old reminder entries
            await db.execute(
                'DELETE FROM reminders WHERE remind_at < datetime("now", "-7 days")'
            )
            # Clean old analytics data (keep 30 days)
            await db.execute(
                'DELETE FROM chat_analytics WHERE timestamp < datetime("now", "-30 days")'
            )
            await db.commit()

    @tasks.loop(minutes=5)
    async def analytics_processor(self):
        """Process chat analytics and generate insights"""
        # This would contain analytics processing logic
        pass

    @tasks.loop(minutes=1)
    async def reminder_checker(self):
        """Check and send reminders"""
        async with aiosqlite.connect('ultrabot.db') as db:
            async with db.execute(
                'SELECT * FROM reminders WHERE remind_at <= datetime("now")'
            ) as cursor:
                reminders = await cursor.fetchall()
                
                for reminder in reminders:
                    try:
                        channel = self.get_channel(reminder[3])
                        user = self.get_user(reminder[1])
                        if channel and user:
                            embed = discord.Embed(
                                title="⏰ Reminder",
                                description=reminder[4],
                                color=discord.Color.blue(),
                                timestamp=datetime.now(timezone.utc)
                            )
                            embed.set_footer(text=f"Reminder for {user.display_name}")
                            await channel.send(f"{user.mention}", embed=embed)
                            
                        # Remove completed reminder
                        await db.execute('DELETE FROM reminders WHERE id = ?', (reminder[0],))
                    except Exception as e:
                        print(f"Error sending reminder: {e}")
                        
                await db.commit()

    @cleanup_tasks.before_loop
    @analytics_processor.before_loop
    @reminder_checker.before_loop
    async def before_loops(self):
        await self.wait_until_ready()

    async def on_message(self, message):
        if message.author.bot:
            return
            
        # Check if bot is mentioned or replied to
        is_mentioned = self.user in message.mentions
        is_reply = message.reference and message.reference.resolved and message.reference.resolved.author == self.user
        
        if is_mentioned or is_reply:
            # Respond with ChatGPT when mentioned or replied to
            try:
                # Get user's message content, removing bot mention
                user_message = message.content
                if self.user.mention in user_message:
                    user_message = user_message.replace(self.user.mention, "").strip()
                
                # If message is empty after removing mention, use a default
                if not user_message:
                    user_message = "Hello"
                
                # Use OpenAI to generate response
                import openai
                import os
                
                openai.api_key = os.getenv('OPENAI_API_KEY')
                
                if openai.api_key:
                    # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
                    # do not change this unless explicitly requested by the user
                    response = openai.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "system", 
                                "content": "You are a helpful Discord bot assistant. Be friendly, concise, and helpful. Keep responses under 200 characters when possible. You can mention that you have many slash commands available with /help if relevant."
                            },
                            {
                                "role": "user", 
                                "content": user_message
                            }
                        ],
                        max_tokens=150,
                        temperature=0.7
                    )
                    
                    ai_response = response.choices[0].message.content
                    await message.reply(ai_response)
                else:
                    # Fallback if no OpenAI key
                    await message.reply("Hey! I'd love to chat but I need an OpenAI API key. Use `/help` to see my commands!")
                    
            except Exception as e:
                # Fallback response if there's an error
                try:
                    await message.reply("Hey! Use `/help` to see what I can do!")
                except:
                    pass  # If we can't reply, just continue
            
        # Process analytics
        if message.guild:
            async with aiosqlite.connect('ultrabot.db') as db:
                await db.execute('''
                    INSERT OR IGNORE INTO users (user_id, guild_id) VALUES (?, ?)
                ''', (message.author.id, message.guild.id))
                
                await db.execute('''
                    UPDATE users SET messages_sent = messages_sent + 1 
                    WHERE user_id = ? AND guild_id = ?
                ''', (message.author.id, message.guild.id))
                
                await db.execute('''
                    INSERT INTO chat_analytics (guild_id, channel_id, user_id, message_length)
                    VALUES (?, ?, ?, ?)
                ''', (message.guild.id, message.channel.id, message.author.id, len(message.content)))
                
                await db.commit()
        
        await self.process_commands(message)

async def main():
    bot = UltraBot()
    await bot.start(os.getenv('DISCORD_TOKEN'))

if __name__ == "__main__":
    asyncio.run(main())