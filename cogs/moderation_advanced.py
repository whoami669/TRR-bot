import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import asyncio
import re
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Union

class ModerationAdvanced(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spam_tracker = {}
        self.raid_protection = {}

    @app_commands.command(name="automod", description="Configure automatic moderation")
    @app_commands.describe(
        feature="Moderation feature to configure",
        enabled="Enable or disable the feature",
        threshold="Threshold for triggering action"
    )
    @app_commands.choices(feature=[
        app_commands.Choice(name="Spam Protection", value="spam"),
        app_commands.Choice(name="Link Filter", value="links"),
        app_commands.Choice(name="Word Filter", value="words"),
        app_commands.Choice(name="Caps Filter", value="caps"),
        app_commands.Choice(name="Emoji Spam", value="emojis"),
        app_commands.Choice(name="Raid Protection", value="raid")
    ])
    @app_commands.default_permissions(administrator=True)
    async def configure_automod(self, interaction: discord.Interaction, 
                              feature: str, enabled: bool, threshold: int = 5):
        async with aiosqlite.connect('ultrabot.db') as db:
            await db.execute('''
                INSERT OR REPLACE INTO automod_settings 
                (guild_id, spam_protection, link_filter, word_filter, caps_filter, emoji_spam_filter)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (interaction.guild.id, 1, 1, 1, 1, 1))
            
            column_map = {
                "spam": "spam_protection",
                "links": "link_filter", 
                "words": "word_filter",
                "caps": "caps_filter",
                "emojis": "emoji_spam_filter"
            }
            
            if feature in column_map:
                await db.execute(f'''
                    UPDATE automod_settings SET {column_map[feature]} = ? 
                    WHERE guild_id = ?
                ''', (1 if enabled else 0, interaction.guild.id))
            
            await db.commit()

        embed = discord.Embed(
            title="⚙️ AutoMod Configuration",
            description=f"{feature.title()} has been {'enabled' if enabled else 'disabled'}",
            color=discord.Color.green() if enabled else discord.Color.red()
        )
        embed.add_field(name="Threshold", value=str(threshold), inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ban", description="Ban a user with advanced options")
    @app_commands.describe(
        user="User to ban",
        reason="Reason for the ban",
        delete_days="Days of messages to delete (0-7)",
        duration="Duration for temporary ban (e.g., 1h, 2d, 1w)"
    )
    @app_commands.default_permissions(ban_members=True)
    async def advanced_ban(self, interaction: discord.Interaction, 
                          user: Union[discord.Member, discord.User], 
                          reason: str = "No reason provided",
                          delete_days: int = 1,
                          duration: str = None):
        
        if isinstance(user, discord.Member):
            if user.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
                await interaction.response.send_message("❌ Cannot ban someone with equal or higher roles!", ephemeral=True)
                return

        # Parse duration
        unban_at = None
        if duration:
            try:
                time_units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400, 'w': 604800}
                match = re.match(r'(\d+)([smhdw])', duration.lower())
                if match:
                    amount, unit = match.groups()
                    seconds = int(amount) * time_units[unit]
                    unban_at = datetime.now(timezone.utc) + timedelta(seconds=seconds)
            except:
                await interaction.response.send_message("❌ Invalid duration format! Use format like: 1h, 2d, 1w", ephemeral=True)
                return

        try:
            await interaction.guild.ban(user, reason=reason, delete_message_days=min(delete_days, 7))
            
            # Log the ban
            async with aiosqlite.connect('ultrabot.db') as db:
                await db.execute('''
                    INSERT INTO moderation_logs (guild_id, user_id, moderator_id, action, reason)
                    VALUES (?, ?, ?, ?, ?)
                ''', (interaction.guild.id, user.id, interaction.user.id, 
                      f"ban{'_temp' if duration else ''}", f"{reason} | Duration: {duration or 'Permanent'}"))
                await db.commit()

            embed = discord.Embed(
                title="🔨 User Banned",
                description=f"**{user}** has been banned",
                color=discord.Color.red()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Messages Deleted", value=f"{delete_days} days", inline=True)
            embed.add_field(name="Duration", value=duration or "Permanent", inline=True)
            embed.set_footer(text=f"Banned by {interaction.user}")
            
            if unban_at:
                embed.add_field(name="Unbanned At", value=f"<t:{int(unban_at.timestamp())}:R>", inline=False)
                
            await interaction.response.send_message(embed=embed)
            
            # Schedule unban if temporary
            if unban_at:
                await asyncio.sleep((unban_at - datetime.now(timezone.utc)).total_seconds())
                try:
                    await interaction.guild.unban(user, reason="Temporary ban expired")
                except:
                    pass

        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to ban user: {str(e)}", ephemeral=True)

    @app_commands.command(name="kick", description="Kick a user with logging")
    @app_commands.describe(user="User to kick", reason="Reason for the kick")
    @app_commands.default_permissions(kick_members=True)
    async def advanced_kick(self, interaction: discord.Interaction, 
                           user: discord.Member, reason: str = "No reason provided"):
        
        if user.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("❌ Cannot kick someone with equal or higher roles!", ephemeral=True)
            return

        try:
            await user.kick(reason=reason)
            
            # Log the kick
            async with aiosqlite.connect('ultrabot.db') as db:
                await db.execute('''
                    INSERT INTO moderation_logs (guild_id, user_id, moderator_id, action, reason)
                    VALUES (?, ?, ?, ?, ?)
                ''', (interaction.guild.id, user.id, interaction.user.id, "kick", reason))
                await db.commit()

            embed = discord.Embed(
                title="👢 User Kicked",
                description=f"**{user}** has been kicked",
                color=discord.Color.orange()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.set_footer(text=f"Kicked by {interaction.user}")
            
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to kick user: {str(e)}", ephemeral=True)

    @app_commands.command(name="timeout", description="Timeout a user with advanced options")
    @app_commands.describe(
        user="User to timeout",
        duration="Duration (e.g., 10m, 1h, 2d)",
        reason="Reason for timeout"
    )
    @app_commands.default_permissions(moderate_members=True)
    async def advanced_timeout(self, interaction: discord.Interaction, 
                              user: discord.Member, duration: str, 
                              reason: str = "No reason provided"):
        
        # Parse duration
        try:
            time_units = {'m': 60, 'h': 3600, 'd': 86400}
            match = re.match(r'(\d+)([mhd])', duration.lower())
            if not match:
                await interaction.response.send_message("❌ Invalid duration format! Use: 10m, 1h, 2d", ephemeral=True)
                return
            
            amount, unit = match.groups()
            seconds = int(amount) * time_units[unit]
            
            if seconds > 2419200:  # 28 days max
                await interaction.response.send_message("❌ Maximum timeout duration is 28 days!", ephemeral=True)
                return
            
            timeout_until = datetime.now(timezone.utc) + timedelta(seconds=seconds)
            
        except Exception:
            await interaction.response.send_message("❌ Invalid duration format!", ephemeral=True)
            return

        try:
            await user.timeout(timeout_until, reason=reason)
            
            # Log the timeout
            async with aiosqlite.connect('ultrabot.db') as db:
                await db.execute('''
                    INSERT INTO moderation_logs (guild_id, user_id, moderator_id, action, reason)
                    VALUES (?, ?, ?, ?, ?)
                ''', (interaction.guild.id, user.id, interaction.user.id, "timeout", f"{reason} | Duration: {duration}"))
                await db.commit()

            embed = discord.Embed(
                title="⏱️ User Timed Out",
                description=f"**{user}** has been timed out",
                color=discord.Color.yellow()
            )
            embed.add_field(name="Duration", value=duration, inline=True)
            embed.add_field(name="Until", value=f"<t:{int(timeout_until.timestamp())}:R>", inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.set_footer(text=f"Timed out by {interaction.user}")
            
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to timeout user: {str(e)}", ephemeral=True)

    @app_commands.command(name="warn", description="Warn a user with tracking")
    @app_commands.describe(user="User to warn", reason="Reason for warning")
    @app_commands.default_permissions(moderate_members=True)
    async def warn_user(self, interaction: discord.Interaction, 
                       user: discord.Member, reason: str = "No reason provided"):
        
        async with aiosqlite.connect('ultrabot.db') as db:
            # Add warning
            await db.execute('''
                INSERT INTO moderation_logs (guild_id, user_id, moderator_id, action, reason)
                VALUES (?, ?, ?, ?, ?)
            ''', (interaction.guild.id, user.id, interaction.user.id, "warn", reason))
            
            # Update user warnings count
            await db.execute('''
                INSERT OR IGNORE INTO users (user_id, guild_id) VALUES (?, ?)
            ''', (user.id, interaction.guild.id))
            
            await db.execute('''
                UPDATE users SET warnings = warnings + 1 
                WHERE user_id = ? AND guild_id = ?
            ''', (user.id, interaction.guild.id))
            
            # Get total warnings
            async with db.execute('''
                SELECT warnings FROM users WHERE user_id = ? AND guild_id = ?
            ''', (user.id, interaction.guild.id)) as cursor:
                result = await cursor.fetchone()
                total_warnings = result[0] if result else 1
            
            await db.commit()

        embed = discord.Embed(
            title="⚠️ User Warned",
            description=f"**{user}** has been warned",
            color=discord.Color.yellow()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Total Warnings", value=str(total_warnings), inline=True)
        embed.set_footer(text=f"Warned by {interaction.user}")
        
        await interaction.response.send_message(embed=embed)
        
        # Auto-action based on warning count
        if total_warnings >= 5:
            try:
                await user.timeout(datetime.now(timezone.utc) + timedelta(hours=1), 
                                 reason="Automatic: 5+ warnings")
                embed.add_field(name="Auto-Action", value="1 hour timeout for 5+ warnings", inline=False)
            except:
                pass

    @app_commands.command(name="modlogs", description="View moderation logs")
    @app_commands.describe(
        user="User to view logs for (optional)",
        action="Type of action to filter by (optional)",
        limit="Number of logs to show (default: 10)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="All Actions", value="all"),
        app_commands.Choice(name="Bans", value="ban"),
        app_commands.Choice(name="Kicks", value="kick"),
        app_commands.Choice(name="Timeouts", value="timeout"),
        app_commands.Choice(name="Warnings", value="warn")
    ])
    @app_commands.default_permissions(view_audit_log=True)
    async def view_modlogs(self, interaction: discord.Interaction, 
                          user: discord.Member = None, action: str = "all", limit: int = 10):
        
        async with aiosqlite.connect('ultrabot.db') as db:
            query = '''
                SELECT user_id, moderator_id, action, reason, timestamp 
                FROM moderation_logs WHERE guild_id = ?
            '''
            params = [interaction.guild.id]
            
            if user:
                query += ' AND user_id = ?'
                params.append(user.id)
                
            if action != "all":
                query += ' AND action LIKE ?'
                params.append(f'{action}%')
            
            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)
            
            async with db.execute(query, params) as cursor:
                logs = await cursor.fetchall()

        if not logs:
            await interaction.response.send_message("No moderation logs found.", ephemeral=True)
            return

        embed = discord.Embed(
            title="📋 Moderation Logs",
            color=discord.Color.blue()
        )
        
        for log in logs:
            user_obj = self.bot.get_user(log[0])
            mod_obj = self.bot.get_user(log[1])
            timestamp = datetime.fromisoformat(log[4])
            
            embed.add_field(
                name=f"{log[2].title()} - {user_obj or 'Unknown User'}",
                value=f"**Moderator:** {mod_obj or 'Unknown'}\n**Reason:** {log[3]}\n**Time:** <t:{int(timestamp.timestamp())}:R>",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="purge", description="Advanced message cleanup")
    @app_commands.describe(
        amount="Number of messages to check (max 100)",
        user="Only delete messages from this user",
        contains="Only delete messages containing this text",
        before_message="Delete messages before this message ID"
    )
    @app_commands.default_permissions(manage_messages=True)
    async def purge_messages(self, interaction: discord.Interaction, 
                           amount: int, user: discord.Member = None, 
                           contains: str = None, before_message: str = None):
        
        if amount > 100:
            await interaction.response.send_message("❌ Cannot check more than 100 messages at once!", ephemeral=True)
            return

        def check(message):
            if user and message.author != user:
                return False
            if contains and contains.lower() not in message.content.lower():
                return False
            return True

        try:
            # Check if channel supports purging
            if not isinstance(interaction.channel, discord.TextChannel):
                await interaction.response.send_message("❌ Cannot purge messages in this channel type!", ephemeral=True)
                return
                
            before = None
            if before_message:
                try:
                    before = await interaction.channel.fetch_message(int(before_message))
                except:
                    await interaction.response.send_message("❌ Invalid message ID!", ephemeral=True)
                    return

            deleted = await interaction.channel.purge(limit=amount, check=check, before=before)
            
            embed = discord.Embed(
                title="🧹 Messages Purged",
                description=f"Successfully deleted {len(deleted)} messages",
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Purged by {interaction.user}")
            
            try:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except discord.errors.NotFound:
                # Interaction already expired, send follow-up
                await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            try:
                await interaction.response.send_message(f"❌ Failed to purge messages: {str(e)}", ephemeral=True)
            except discord.errors.NotFound:
                # Interaction already expired, send follow-up  
                await interaction.followup.send(f"❌ Failed to purge messages: {str(e)}", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        # Check automod settings
        async with aiosqlite.connect('ultrabot.db') as db:
            async with db.execute('''
                SELECT * FROM automod_settings WHERE guild_id = ?
            ''', (message.guild.id,)) as cursor:
                settings = await cursor.fetchone()

        if not settings:
            return

        # Spam detection
        if settings[1]:  # spam_protection
            user_id = message.author.id
            now = datetime.now()
            
            if user_id not in self.spam_tracker:
                self.spam_tracker[user_id] = []
            
            self.spam_tracker[user_id].append(now)
            self.spam_tracker[user_id] = [
                time for time in self.spam_tracker[user_id] 
                if (now - time).seconds < 10
            ]
            
            if len(self.spam_tracker[user_id]) > 5:
                try:
                    await message.author.timeout(
                        datetime.now(timezone.utc) + timedelta(minutes=5),
                        reason="Automatic: Spam detection"
                    )
                    await message.channel.send(f"⚠️ {message.author.mention} has been timed out for spamming.")
                except:
                    pass

        # Link filter
        if settings[2]:  # link_filter
            links = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message.content)
            if links and not message.author.guild_permissions.manage_messages:
                await message.delete()
                await message.channel.send(f"⚠️ {message.author.mention}, links are not allowed!", delete_after=5)

        # Caps filter
        if settings[4]:  # caps_filter
            if len(message.content) > 10 and sum(1 for c in message.content if c.isupper()) / len(message.content) > 0.7:
                await message.delete()
                await message.channel.send(f"⚠️ {message.author.mention}, please don't use excessive caps!", delete_after=5)

async def setup(bot):
    await bot.add_cog(ModerationAdvanced(bot))