import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Union

class AdvancedModeration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'moderation.db'
        
    async def init_database(self):
        """Initialize moderation database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    moderator_id INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS temp_bans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    moderator_id INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS mute_roles (
                    guild_id INTEGER PRIMARY KEY,
                    role_id INTEGER NOT NULL
                )
            ''')
            await db.commit()

    async def cog_load(self):
        await self.init_database()

    @app_commands.command(name="warn", description="Warn a user")
    @app_commands.describe(user="User to warn", reason="Reason for warning")
    @commands.has_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        """Warn a user"""
        await interaction.response.defer()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO warnings (guild_id, user_id, moderator_id, reason)
                VALUES (?, ?, ?, ?)
            ''', (interaction.guild_id, user.id, interaction.user.id, reason))
            await db.commit()
            
            # Get warning count
            cursor = await db.execute('''
                SELECT COUNT(*) FROM warnings WHERE guild_id = ? AND user_id = ?
            ''', (interaction.guild_id, user.id))
            warning_count = await cursor.fetchone()
        
        embed = discord.Embed(
            title="⚠️ User Warned",
            description=f"{user.mention} has been warned",
            color=0xffa500
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Total Warnings", value=str(warning_count[0]), inline=True)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="warnings", description="View user warnings")
    @app_commands.describe(user="User to check warnings for")
    @commands.has_permissions(moderate_members=True)
    async def warnings(self, interaction: discord.Interaction, user: discord.Member):
        """View warnings for a user"""
        await interaction.response.defer()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT reason, created_at FROM warnings 
                WHERE guild_id = ? AND user_id = ?
                ORDER BY created_at DESC LIMIT 10
            ''', (interaction.guild_id, user.id))
            warnings = await cursor.fetchall()
        
        if not warnings:
            await interaction.followup.send(f"{user.mention} has no warnings")
            return
        
        embed = discord.Embed(
            title=f"⚠️ Warnings for {user.display_name}",
            color=0xffa500
        )
        
        for i, (reason, created_at) in enumerate(warnings, 1):
            timestamp = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            embed.add_field(
                name=f"Warning {i}",
                value=f"**Reason:** {reason}\n**Date:** {timestamp.strftime('%Y-%m-%d %H:%M')}",
                inline=False
            )
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="clear-warnings", description="Clear all warnings for a user")
    @app_commands.describe(user="User to clear warnings for")
    @commands.has_permissions(moderate_members=True)
    async def clear_warnings(self, interaction: discord.Interaction, user: discord.Member):
        """Clear warnings for a user"""
        await interaction.response.defer()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                DELETE FROM warnings WHERE guild_id = ? AND user_id = ?
            ''', (interaction.guild_id, user.id))
            await db.commit()
            
            cleared_count = cursor.rowcount
        
        embed = discord.Embed(
            title="✅ Warnings Cleared",
            description=f"Cleared {cleared_count} warnings for {user.mention}",
            color=0x2ecc71
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="tempban", description="Temporarily ban a user")
    @app_commands.describe(
        user="User to ban",
        duration="Duration (e.g., 1h, 2d, 1w)",
        reason="Reason for ban"
    )
    @commands.has_permissions(ban_members=True)
    async def tempban(self, interaction: discord.Interaction, user: discord.Member, duration: str, reason: str = "No reason provided"):
        """Temporarily ban a user"""
        await interaction.response.defer()
        
        # Parse duration
        duration_map = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400, 'w': 604800}
        time_unit = duration[-1].lower()
        
        if time_unit not in duration_map:
            await interaction.followup.send("Invalid duration format. Use: 1h, 2d, 1w, etc.")
            return
        
        try:
            time_amount = int(duration[:-1])
            total_seconds = time_amount * duration_map[time_unit]
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=total_seconds)
        except ValueError:
            await interaction.followup.send("Invalid duration format")
            return
        
        try:
            await user.ban(reason=f"Temporary ban: {reason}")
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO temp_bans (guild_id, user_id, moderator_id, reason, expires_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (interaction.guild_id, user.id, interaction.user.id, reason, expires_at.isoformat()))
                await db.commit()
            
            embed = discord.Embed(
                title="🔨 User Temporarily Banned",
                description=f"{user.mention} has been banned for {duration}",
                color=0xe74c3c
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Expires", value=f"<t:{int(expires_at.timestamp())}:R>", inline=True)
            
            await interaction.followup.send(embed=embed)
            
            # Schedule unban
            await asyncio.sleep(total_seconds)
            await self.unban_user(interaction.guild, user.id)
            
        except discord.Forbidden:
            await interaction.followup.send("I don't have permission to ban this user")

    async def unban_user(self, guild: discord.Guild, user_id: int):
        """Unban a user"""
        try:
            user = await self.bot.fetch_user(user_id)
            await guild.unban(user, reason="Temporary ban expired")
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    DELETE FROM temp_bans WHERE guild_id = ? AND user_id = ?
                ''', (guild.id, user_id))
                await db.commit()
        except:
            pass

    @app_commands.command(name="slowmode", description="Set channel slowmode")
    @app_commands.describe(
        seconds="Slowmode duration in seconds (0 to disable)",
        channel="Channel to apply slowmode to"
    )
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, interaction: discord.Interaction, seconds: int, channel: Optional[discord.TextChannel] = None):
        """Set slowmode for a channel"""
        await interaction.response.defer()
        
        target_channel = channel or interaction.channel
        
        if seconds < 0 or seconds > 21600:  # Discord limit
            await interaction.followup.send("Slowmode must be between 0 and 21600 seconds (6 hours)")
            return
        
        await target_channel.edit(slowmode_delay=seconds)
        
        if seconds == 0:
            embed = discord.Embed(
                title="⏱️ Slowmode Disabled",
                description=f"Slowmode has been disabled in {target_channel.mention}",
                color=0x2ecc71
            )
        else:
            embed = discord.Embed(
                title="⏱️ Slowmode Enabled",
                description=f"Slowmode set to {seconds} seconds in {target_channel.mention}",
                color=0xf39c12
            )
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="purge", description="Delete multiple messages")
    @app_commands.describe(amount="Number of messages to delete (1-100)")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, amount: int):
        """Purge messages from channel"""
        await interaction.response.defer(ephemeral=True)
        
        if amount < 1 or amount > 100:
            await interaction.followup.send("Amount must be between 1 and 100")
            return
        
        deleted = await interaction.channel.purge(limit=amount)
        
        embed = discord.Embed(
            title="🗑️ Messages Deleted",
            description=f"Deleted {len(deleted)} messages",
            color=0xe74c3c
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="lock", description="Lock a channel")
    @app_commands.describe(channel="Channel to lock", reason="Reason for locking")
    @commands.has_permissions(manage_channels=True)
    async def lock(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None, reason: str = "No reason provided"):
        """Lock a channel"""
        await interaction.response.defer()
        
        target_channel = channel or interaction.channel
        
        overwrites = target_channel.overwrites_for(interaction.guild.default_role)
        overwrites.send_messages = False
        await target_channel.set_permissions(interaction.guild.default_role, overwrite=overwrites)
        
        embed = discord.Embed(
            title="🔒 Channel Locked",
            description=f"{target_channel.mention} has been locked",
            color=0xe74c3c
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="unlock", description="Unlock a channel")
    @app_commands.describe(channel="Channel to unlock")
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None):
        """Unlock a channel"""
        await interaction.response.defer()
        
        target_channel = channel or interaction.channel
        
        overwrites = target_channel.overwrites_for(interaction.guild.default_role)
        overwrites.send_messages = None
        await target_channel.set_permissions(interaction.guild.default_role, overwrite=overwrites)
        
        embed = discord.Embed(
            title="🔓 Channel Unlocked",
            description=f"{target_channel.mention} has been unlocked",
            color=0x2ecc71
        )
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AdvancedModeration(bot))