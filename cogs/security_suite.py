import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import re
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional

class SecuritySuite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.raid_detection = {}
        self.suspicious_activity = {}

    @app_commands.command(name="lockdown", description="Lock down the server")
    @app_commands.describe(
        duration="Lockdown duration (e.g., 10m, 1h)",
        reason="Reason for lockdown"
    )
    @app_commands.default_permissions(administrator=True)
    async def lockdown_server(self, interaction: discord.Interaction, 
                            duration: str = "30m", reason: str = "Security lockdown"):
        
        # Parse duration
        try:
            time_units = {'m': 60, 'h': 3600, 'd': 86400}
            match = re.match(r'(\d+)([mhd])', duration.lower())
            if not match:
                await interaction.response.send_message("❌ Invalid duration format! Use: 10m, 1h, 2d", ephemeral=True)
                return
            
            amount, unit = match.groups()
            seconds = int(amount) * time_units[unit]
            end_time = datetime.now(timezone.utc) + timedelta(seconds=seconds)
        except:
            await interaction.response.send_message("❌ Invalid duration format!", ephemeral=True)
            return

        # Lock all channels
        locked_channels = []
        for channel in interaction.guild.text_channels:
            try:
                overwrites = channel.overwrites
                overwrites[interaction.guild.default_role] = discord.PermissionOverwrite(send_messages=False)
                await channel.edit(overwrites=overwrites, reason=f"Lockdown: {reason}")
                locked_channels.append(channel.id)
            except:
                pass

        # Store lockdown info
        async with aiosqlite.connect('ultrabot.db') as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS lockdowns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    end_time TIMESTAMP,
                    reason TEXT,
                    locked_channels TEXT,
                    active BOOLEAN DEFAULT 1
                )
            ''')
            
            await db.execute('''
                INSERT INTO lockdowns (guild_id, end_time, reason, locked_channels)
                VALUES (?, ?, ?, ?)
            ''', (interaction.guild.id, end_time, reason, str(locked_channels)))
            await db.commit()

        embed = discord.Embed(
            title="🔒 Server Lockdown Active",
            description=f"**Reason:** {reason}\n**Duration:** {duration}\n**Ends:** <t:{int(end_time.timestamp())}:R>",
            color=discord.Color.red()
        )
        embed.add_field(name="Locked Channels", value=str(len(locked_channels)), inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="unlock", description="Remove server lockdown")
    @app_commands.default_permissions(administrator=True)
    async def unlock_server(self, interaction: discord.Interaction):
        
        async with aiosqlite.connect('ultrabot.db') as db:
            async with db.execute('''
                SELECT locked_channels FROM lockdowns 
                WHERE guild_id = ? AND active = 1
                ORDER BY id DESC LIMIT 1
            ''', (interaction.guild.id,)) as cursor:
                result = await cursor.fetchone()
            
            if not result:
                await interaction.response.send_message("❌ No active lockdown found!", ephemeral=True)
                return
            
            locked_channels = eval(result[0])
            
            # Unlock channels
            unlocked_count = 0
            for channel_id in locked_channels:
                channel = interaction.guild.get_channel(channel_id)
                if channel:
                    try:
                        overwrites = channel.overwrites
                        if interaction.guild.default_role in overwrites:
                            del overwrites[interaction.guild.default_role]
                            await channel.edit(overwrites=overwrites, reason="Lockdown removed")
                            unlocked_count += 1
                    except:
                        pass
            
            # Mark lockdown as inactive
            await db.execute('''
                UPDATE lockdowns SET active = 0 WHERE guild_id = ? AND active = 1
            ''', (interaction.guild.id,))
            await db.commit()

        embed = discord.Embed(
            title="🔓 Server Unlocked",
            description=f"Lockdown has been removed. Unlocked {unlocked_count} channels.",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="raid-protection", description="Configure raid protection")
    @app_commands.describe(
        enabled="Enable or disable raid protection",
        join_threshold="Number of joins to trigger protection",
        time_window="Time window in seconds"
    )
    @app_commands.default_permissions(administrator=True)
    async def raid_protection(self, interaction: discord.Interaction, 
                             enabled: bool, join_threshold: int = 10, time_window: int = 60):
        
        async with aiosqlite.connect('ultrabot.db') as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS raid_protection (
                    guild_id INTEGER PRIMARY KEY,
                    enabled BOOLEAN,
                    join_threshold INTEGER,
                    time_window INTEGER
                )
            ''')
            
            await db.execute('''
                INSERT OR REPLACE INTO raid_protection 
                (guild_id, enabled, join_threshold, time_window)
                VALUES (?, ?, ?, ?)
            ''', (interaction.guild.id, enabled, join_threshold, time_window))
            await db.commit()

        embed = discord.Embed(
            title="🛡️ Raid Protection",
            description=f"Raid protection has been {'enabled' if enabled else 'disabled'}",
            color=discord.Color.green() if enabled else discord.Color.red()
        )
        
        if enabled:
            embed.add_field(name="Join Threshold", value=str(join_threshold), inline=True)
            embed.add_field(name="Time Window", value=f"{time_window}s", inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="verify-setup", description="Set up verification system")
    @app_commands.describe(
        verification_role="Role to give verified members",
        verification_channel="Channel for verification"
    )
    @app_commands.default_permissions(administrator=True)
    async def verification_setup(self, interaction: discord.Interaction,
                                verification_role: discord.Role,
                                verification_channel: discord.TextChannel):
        
        async with aiosqlite.connect('ultrabot.db') as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS verification_config (
                    guild_id INTEGER PRIMARY KEY,
                    role_id INTEGER,
                    channel_id INTEGER
                )
            ''')
            
            await db.execute('''
                INSERT OR REPLACE INTO verification_config 
                (guild_id, role_id, channel_id)
                VALUES (?, ?, ?)
            ''', (interaction.guild.id, verification_role.id, verification_channel.id))
            await db.commit()

        # Create verification embed
        embed = discord.Embed(
            title="✅ Verification Required",
            description="Click the button below to verify and gain access to the server.",
            color=discord.Color.blue()
        )
        
        view = VerificationView()
        message = await verification_channel.send(embed=embed, view=view)
        
        confirmation_embed = discord.Embed(
            title="✅ Verification System Setup",
            description=f"Verification system configured successfully!",
            color=discord.Color.green()
        )
        confirmation_embed.add_field(name="Verification Role", value=verification_role.mention, inline=True)
        confirmation_embed.add_field(name="Verification Channel", value=verification_channel.mention, inline=True)
        
        await interaction.response.send_message(embed=confirmation_embed)

    @app_commands.command(name="security-scan", description="Scan server for security issues")
    @app_commands.default_permissions(administrator=True)
    async def security_scan(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        guild = interaction.guild
        issues = []
        recommendations = []
        
        # Check for dangerous permissions
        dangerous_perms = ['administrator', 'manage_guild', 'manage_roles', 'manage_channels']
        for role in guild.roles:
            if role.name != '@everyone' and not role.managed:
                for perm_name in dangerous_perms:
                    if getattr(role.permissions, perm_name, False):
                        if len(role.members) > 5:  # Many members with dangerous perms
                            issues.append(f"Role '{role.name}' has {perm_name} permission with {len(role.members)} members")
        
        # Check verification level
        if guild.verification_level < discord.VerificationLevel.medium:
            issues.append("Server verification level is too low")
            recommendations.append("Set verification level to Medium or High")
        
        # Check for public channels with dangerous permissions
        for channel in guild.text_channels:
            overwrites = channel.overwrites_for(guild.default_role)
            if overwrites.manage_messages or overwrites.manage_channels:
                issues.append(f"Channel '{channel.name}' gives dangerous permissions to @everyone")
        
        # Check for too many admins
        admin_count = len([m for m in guild.members if m.guild_permissions.administrator and not m.bot])
        if admin_count > guild.member_count * 0.1:  # More than 10% admins
            issues.append(f"Too many administrators ({admin_count}) for server size")
            recommendations.append("Limit administrator permissions to essential staff only")
        
        # Security score
        max_issues = 10
        score = max(0, 100 - (len(issues) * (100 // max_issues)))
        
        if score >= 90:
            status = "🟢 Excellent"
            color = discord.Color.green()
        elif score >= 70:
            status = "🟡 Good"
            color = discord.Color.yellow()
        elif score >= 50:
            status = "🟠 Fair"
            color = discord.Color.orange()
        else:
            status = "🔴 Poor"
            color = discord.Color.red()
        
        embed = discord.Embed(
            title="🔍 Security Scan Results",
            description=f"**Security Score:** {score}/100 ({status})",
            color=color
        )
        
        if issues:
            issues_text = "\n".join(f"• {issue}" for issue in issues[:5])
            if len(issues) > 5:
                issues_text += f"\n... and {len(issues) - 5} more issues"
            embed.add_field(name="⚠️ Issues Found", value=issues_text, inline=False)
        
        if recommendations:
            rec_text = "\n".join(f"• {rec}" for rec in recommendations[:3])
            embed.add_field(name="💡 Recommendations", value=rec_text, inline=False)
        
        if not issues:
            embed.add_field(name="✅ Status", value="No major security issues detected!", inline=False)
        
        await interaction.followup.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Monitor for potential raids"""
        guild_id = member.guild.id
        now = datetime.now(timezone.utc)
        
        # Check raid protection settings
        async with aiosqlite.connect('ultrabot.db') as db:
            async with db.execute('''
                SELECT enabled, join_threshold, time_window FROM raid_protection 
                WHERE guild_id = ?
            ''', (guild_id,)) as cursor:
                settings = await cursor.fetchone()
        
        if not settings or not settings[0]:  # Not enabled
            return
        
        threshold, window = settings[1], settings[2]
        
        # Track joins
        if guild_id not in self.raid_detection:
            self.raid_detection[guild_id] = []
        
        self.raid_detection[guild_id].append(now)
        
        # Clean old entries
        cutoff = now - timedelta(seconds=window)
        self.raid_detection[guild_id] = [
            join_time for join_time in self.raid_detection[guild_id] 
            if join_time > cutoff
        ]
        
        # Check if threshold exceeded
        if len(self.raid_detection[guild_id]) >= threshold:
            # Potential raid detected - implement automatic lockdown
            try:
                # Find a channel to send alert
                alert_channel = None
                for channel in member.guild.text_channels:
                    if channel.permissions_for(member.guild.me).send_messages:
                        alert_channel = channel
                        break
                
                if alert_channel:
                    embed = discord.Embed(
                        title="🚨 Potential Raid Detected",
                        description=f"**{len(self.raid_detection[guild_id])}** members joined in the last {window} seconds",
                        color=discord.Color.red()
                    )
                    embed.add_field(name="Action Required", value="Consider enabling lockdown", inline=False)
                    
                    await alert_channel.send(embed=embed)
            except:
                pass

class VerificationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.green, emoji="✅")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        
        async with aiosqlite.connect('ultrabot.db') as db:
            async with db.execute('''
                SELECT role_id FROM verification_config WHERE guild_id = ?
            ''', (interaction.guild.id,)) as cursor:
                result = await cursor.fetchone()
        
        if not result:
            await interaction.response.send_message("❌ Verification not configured!", ephemeral=True)
            return
        
        role = interaction.guild.get_role(result[0])
        if not role:
            await interaction.response.send_message("❌ Verification role not found!", ephemeral=True)
            return
        
        if role in interaction.user.roles:
            await interaction.response.send_message("✅ You are already verified!", ephemeral=True)
            return
        
        try:
            await interaction.user.add_roles(role, reason="Verification completed")
            
            embed = discord.Embed(
                title="✅ Verification Complete",
                description="You have been verified and now have access to the server!",
                color=discord.Color.green()
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            await interaction.response.send_message("❌ Failed to verify. Please contact an administrator.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SecuritySuite(bot))