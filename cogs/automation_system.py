import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiosqlite
import asyncio
import re
import json
import random
from datetime import datetime, timezone, timedelta
from typing import Optional

class AutomationSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Keep only essential functions, disable automated messaging
        self.auto_role_check.start()
        # self.scheduled_messages.start()  # Disabled due to database errors

    def cog_unload(self):
        self.auto_role_check.cancel()
        self.scheduled_messages.cancel()

    @app_commands.command(name="auto-role", description="Configure automatic role assignment")
    @app_commands.describe(
        trigger="What triggers the role assignment",
        role="Role to assign",
        condition="Condition for assignment"
    )
    @app_commands.choices(trigger=[
        app_commands.Choice(name="On Join", value="join"),
        app_commands.Choice(name="Level Milestone", value="level"),
        app_commands.Choice(name="Message Count", value="messages"),
        app_commands.Choice(name="Time in Server", value="time")
    ])
    @app_commands.default_permissions(manage_roles=True)
    async def setup_auto_role(self, interaction: discord.Interaction, 
                            trigger: str, role: discord.Role, condition: str = "1"):
        
        async with aiosqlite.connect('ultrabot.db') as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS auto_roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    trigger_type TEXT,
                    role_id INTEGER,
                    condition_value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.execute('''
                INSERT INTO auto_roles (guild_id, trigger_type, role_id, condition_value)
                VALUES (?, ?, ?, ?)
            ''', (interaction.guild.id, trigger, role.id, condition))
            await db.commit()

        embed = discord.Embed(
            title="🤖 Auto-Role Configured",
            description=f"**Role:** {role.mention}\n**Trigger:** {trigger}\n**Condition:** {condition}",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="welcome-setup", description="Configure welcome messages and actions")
    @app_commands.describe(
        channel="Channel for welcome messages",
        message="Welcome message (use {user} for mention, {server} for server name)",
        auto_role="Role to give new members"
    )
    @app_commands.default_permissions(manage_guild=True)
    async def setup_welcome(self, interaction: discord.Interaction, 
                          channel: discord.TextChannel, message: str,
                          auto_role: discord.Role = None):
        
        async with aiosqlite.connect('ultrabot.db') as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS welcome_config (
                    guild_id INTEGER PRIMARY KEY,
                    channel_id INTEGER,
                    message TEXT,
                    auto_role_id INTEGER
                )
            ''')
            
            await db.execute('''
                INSERT OR REPLACE INTO welcome_config (guild_id, channel_id, message, auto_role_id)
                VALUES (?, ?, ?, ?)
            ''', (interaction.guild.id, channel.id, message, auto_role.id if auto_role else None))
            await db.commit()

        embed = discord.Embed(
            title="👋 Welcome System Configured",
            color=discord.Color.blue()
        )
        embed.add_field(name="Channel", value=channel.mention, inline=True)
        embed.add_field(name="Auto Role", value=auto_role.mention if auto_role else "None", inline=True)
        embed.add_field(name="Message Preview", value=message.replace("{user}", interaction.user.mention).replace("{server}", interaction.guild.name), inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="auto-mod-config", description="Configure automatic moderation responses")
    @app_commands.describe(
        violation_type="Type of violation to auto-moderate",
        action="Action to take",
        threshold="Number of violations before action"
    )
    @app_commands.choices(
        violation_type=[
            app_commands.Choice(name="Spam Messages", value="spam"),
            app_commands.Choice(name="Caps Lock Abuse", value="caps"),
            app_commands.Choice(name="Link Posting", value="links"),
            app_commands.Choice(name="Duplicate Messages", value="duplicate")
        ],
        action=[
            app_commands.Choice(name="Delete Message", value="delete"),
            app_commands.Choice(name="Timeout 5 minutes", value="timeout_5m"),
            app_commands.Choice(name="Timeout 1 hour", value="timeout_1h"),
            app_commands.Choice(name="Warn User", value="warn")
        ]
    )
    @app_commands.default_permissions(manage_guild=True)
    async def configure_auto_mod(self, interaction: discord.Interaction,
                               violation_type: str, action: str, threshold: int = 3):
        
        async with aiosqlite.connect('ultrabot.db') as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS auto_mod_config (
                    guild_id INTEGER,
                    violation_type TEXT,
                    action TEXT,
                    threshold INTEGER,
                    PRIMARY KEY (guild_id, violation_type)
                )
            ''')
            
            await db.execute('''
                INSERT OR REPLACE INTO auto_mod_config (guild_id, violation_type, action, threshold)
                VALUES (?, ?, ?, ?)
            ''', (interaction.guild.id, violation_type, action, threshold))
            await db.commit()

        embed = discord.Embed(
            title="⚙️ Auto-Moderation Configured",
            description=f"**Violation:** {violation_type.title()}\n**Action:** {action.replace('_', ' ').title()}\n**Threshold:** {threshold}",
            color=discord.Color.orange()
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="schedule-message", description="Schedule a message to be sent later")
    @app_commands.describe(
        channel="Channel to send the message",
        message="Message content",
        time="When to send (e.g., '2h', '1d', '2024-12-25 15:30')"
    )
    @app_commands.default_permissions(manage_messages=True)
    async def schedule_message(self, interaction: discord.Interaction,
                             channel: discord.TextChannel, message: str, time: str):
        
        try:
            # Parse time
            if re.match(r'\d+[mhd]', time):
                time_units = {'m': 60, 'h': 3600, 'd': 86400}
                match = re.match(r'(\d+)([mhd])', time)
                amount, unit = match.groups()
                seconds = int(amount) * time_units[unit]
                send_at = datetime.now(timezone.utc) + timedelta(seconds=seconds)
            else:
                send_at = datetime.strptime(time, "%Y-%m-%d %H:%M")
                send_at = send_at.replace(tzinfo=timezone.utc)
        except:
            await interaction.response.send_message("❌ Invalid time format! Use '2h', '1d' or 'YYYY-MM-DD HH:MM'", ephemeral=True)
            return

        async with aiosqlite.connect('ultrabot.db') as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS scheduled_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    channel_id INTEGER,
                    message_content TEXT,
                    send_at TIMESTAMP,
                    created_by INTEGER,
                    sent BOOLEAN DEFAULT 0
                )
            ''')
            
            await db.execute('''
                INSERT INTO scheduled_messages (guild_id, channel_id, message_content, send_at, created_by)
                VALUES (?, ?, ?, ?, ?)
            ''', (interaction.guild.id, channel.id, message, send_at, interaction.user.id))
            await db.commit()

        embed = discord.Embed(
            title="⏰ Message Scheduled",
            description=f"**Channel:** {channel.mention}\n**Send at:** <t:{int(send_at.timestamp())}:F>\n**That's:** <t:{int(send_at.timestamp())}:R>",
            color=discord.Color.blue()
        )
        embed.add_field(name="Message Preview", value=message[:100] + ("..." if len(message) > 100 else ""), inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="auto-reactions", description="Set up automatic reactions to messages")
    @app_commands.describe(
        trigger="What triggers the auto-reaction",
        emojis="Emojis to react with (separated by spaces)"
    )
    @app_commands.choices(trigger=[
        app_commands.Choice(name="Contains specific word", value="word"),
        app_commands.Choice(name="From specific user", value="user"),
        app_commands.Choice(name="In specific channel", value="channel"),
        app_commands.Choice(name="All messages", value="all")
    ])
    @app_commands.default_permissions(manage_messages=True)
    async def setup_auto_reactions(self, interaction: discord.Interaction,
                                 trigger: str, emojis: str):
        
        # Validate emojis
        emoji_list = emojis.split()
        if len(emoji_list) > 5:
            await interaction.response.send_message("❌ Maximum 5 emojis allowed!", ephemeral=True)
            return

        async with aiosqlite.connect('ultrabot.db') as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS auto_reactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    trigger_type TEXT,
                    trigger_value TEXT,
                    emojis TEXT
                )
            ''')
            
            await db.execute('''
                INSERT INTO auto_reactions (guild_id, trigger_type, trigger_value, emojis)
                VALUES (?, ?, ?, ?)
            ''', (interaction.guild.id, trigger, "", emojis))
            await db.commit()

        embed = discord.Embed(
            title="😀 Auto-Reactions Configured",
            description=f"**Trigger:** {trigger}\n**Emojis:** {emojis}",
            color=discord.Color.yellow()
        )
        
        await interaction.response.send_message(embed=embed)

    @tasks.loop(minutes=5)
    async def auto_role_check(self):
        """Check and assign automatic roles based on conditions"""
        try:
            async with aiosqlite.connect('ultrabot.db') as db:
                async with db.execute('SELECT * FROM auto_roles') as cursor:
                    auto_roles = await cursor.fetchall()

            for auto_role in auto_roles:
                guild_id, trigger_type, role_id, condition_value = auto_role[1:5]
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    continue

                role = guild.get_role(role_id)
                if not role:
                    continue

                if trigger_type == "level":
                    target_level = int(condition_value)
                    async with aiosqlite.connect('ultrabot.db') as db:
                        async with db.execute('''
                            SELECT user_id FROM users 
                            WHERE guild_id = ? AND level >= ?
                        ''', (guild_id, target_level)) as cursor:
                            eligible_users = await cursor.fetchall()

                    for user_tuple in eligible_users:
                        member = guild.get_member(user_tuple[0])
                        if member and role not in member.roles:
                            try:
                                await member.add_roles(role, reason=f"Auto-role: Level {target_level}")
                            except:
                                pass

        except Exception as e:
            print(f"Auto-role check error: {e}")

    @tasks.loop(minutes=1)
    async def scheduled_messages(self):
        """Send scheduled messages when their time comes"""
        try:
            async with aiosqlite.connect('ultrabot.db') as db:
                async with db.execute('''
                    SELECT * FROM scheduled_messages 
                    WHERE send_at <= datetime('now') AND sent = 0
                ''') as cursor:
                    messages = await cursor.fetchall()

                for msg in messages:
                    msg_id, guild_id, channel_id, content, send_at, created_by, sent = msg
                    
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        try:
                            await channel.send(content)
                            await db.execute('UPDATE scheduled_messages SET sent = 1 WHERE id = ?', (msg_id,))
                        except:
                            pass

                await db.commit()

        except Exception as e:
            print(f"Scheduled messages error: {e}")

    @auto_role_check.before_loop
    @scheduled_messages.before_loop
    async def before_automation_loops(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Handle new member welcome and auto-roles"""
        try:
            async with aiosqlite.connect('ultrabot.db') as db:
                # Check welcome config
                async with db.execute('''
                    SELECT channel_id, message, auto_role_id FROM welcome_config 
                    WHERE guild_id = ?
                ''', (member.guild.id,)) as cursor:
                    welcome_config = await cursor.fetchone()

                if welcome_config:
                    channel_id, message, auto_role_id = welcome_config
                    
                    # Send welcome message
                    channel = member.guild.get_channel(channel_id)
                    if channel and message:
                        formatted_message = message.replace("{user}", member.mention).replace("{server}", member.guild.name).replace("{count}", str(member.guild.member_count))
                        
                        # Mimu-style welcome embed
                        embed = discord.Embed(
                            description=f"**{member.display_name}** just joined the server!",
                            color=0x2B2D31  # Discord dark theme color
                        )
                        
                        # Large profile picture
                        embed.set_author(
                            name=f"Welcome to {member.guild.name}!",
                            icon_url=member.guild.icon.url if member.guild.icon else None
                        )
                        embed.set_image(url=member.display_avatar.url)
                        
                        # Member info
                        embed.add_field(
                            name="Member Info",
                            value=f"**Account Created:** <t:{int(member.created_at.timestamp())}:R>\n**Member #{member.guild.member_count}**",
                            inline=True
                        )
                        
                        # Custom message
                        if formatted_message != message:  # If variables were replaced
                            embed.add_field(
                                name="Message",
                                value=formatted_message,
                                inline=False
                            )
                        
                        embed.set_footer(
                            text=f"User ID: {member.id}",
                            icon_url=member.display_avatar.url
                        )
                        
                        await channel.send(embed=embed)
                    
                    # Assign auto role
                    if auto_role_id:
                        role = member.guild.get_role(auto_role_id)
                        if role:
                            try:
                                await member.add_roles(role, reason="Auto-role on join")
                            except:
                                pass

                # Check for join-trigger auto roles
                async with db.execute('''
                    SELECT role_id FROM auto_roles 
                    WHERE guild_id = ? AND trigger_type = 'join'
                ''', (member.guild.id,)) as cursor:
                    join_roles = await cursor.fetchall()

                for role_tuple in join_roles:
                    role = member.guild.get_role(role_tuple[0])
                    if role:
                        try:
                            await member.add_roles(role, reason="Auto-role on join")
                        except:
                            pass

        except Exception as e:
            print(f"Member join automation error: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle auto-moderation and auto-reactions"""
        if message.author.bot or not message.guild:
            return

        try:
            async with aiosqlite.connect('ultrabot.db') as db:
                # Check auto-reactions
                async with db.execute('''
                    SELECT trigger_type, trigger_value, emojis FROM auto_reactions 
                    WHERE guild_id = ?
                ''', (message.guild.id,)) as cursor:
                    auto_reactions = await cursor.fetchall()

                for trigger_type, trigger_value, emojis in auto_reactions:
                    should_react = False
                    
                    if trigger_type == "all":
                        should_react = True
                    elif trigger_type == "word" and trigger_value.lower() in message.content.lower():
                        should_react = True
                    elif trigger_type == "channel" and str(message.channel.id) == trigger_value:
                        should_react = True
                    elif trigger_type == "user" and str(message.author.id) == trigger_value:
                        should_react = True
                    
                    if should_react:
                        for emoji in emojis.split():
                            try:
                                await message.add_reaction(emoji)
                            except:
                                pass

        except Exception as e:
            print(f"Message automation error: {e}")

async def setup(bot):
    await bot.add_cog(AutomationSystem(bot))