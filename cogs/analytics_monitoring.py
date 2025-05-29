import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Optional
import matplotlib.pyplot as plt
import io
import base64

class AnalyticsMonitoring(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="analytics", description="View detailed server analytics")
    @app_commands.describe(period="Time period for analytics")
    @app_commands.choices(period=[
        app_commands.Choice(name="Last 24 Hours", value="24h"),
        app_commands.Choice(name="Last 7 Days", value="7d"),
        app_commands.Choice(name="Last 30 Days", value="30d"),
        app_commands.Choice(name="All Time", value="all")
    ])
    @app_commands.default_permissions(administrator=True)
    async def view_analytics(self, interaction: discord.Interaction, period: str = "7d"):
        await interaction.response.defer()
        
        # Calculate time range
        now = datetime.now(timezone.utc)
        if period == "24h":
            start_time = now - timedelta(hours=24)
        elif period == "7d":
            start_time = now - timedelta(days=7)
        elif period == "30d":
            start_time = now - timedelta(days=30)
        else:
            start_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        
        async with aiosqlite.connect('ultrabot.db') as db:
            # Message activity
            async with db.execute('''
                SELECT COUNT(*) FROM chat_analytics 
                WHERE guild_id = ? AND timestamp >= ?
            ''', (interaction.guild.id, start_time)) as cursor:
                total_messages = (await cursor.fetchone())[0]
            
            # Active users
            async with db.execute('''
                SELECT COUNT(DISTINCT user_id) FROM chat_analytics 
                WHERE guild_id = ? AND timestamp >= ?
            ''', (interaction.guild.id, start_time)) as cursor:
                active_users = (await cursor.fetchone())[0]
            
            # Top channels by activity
            async with db.execute('''
                SELECT channel_id, COUNT(*) as message_count 
                FROM chat_analytics 
                WHERE guild_id = ? AND timestamp >= ?
                GROUP BY channel_id 
                ORDER BY message_count DESC LIMIT 5
            ''', (interaction.guild.id, start_time)) as cursor:
                top_channels = await cursor.fetchall()
            
            # Top users by activity
            async with db.execute('''
                SELECT user_id, COUNT(*) as message_count 
                FROM chat_analytics 
                WHERE guild_id = ? AND timestamp >= ?
                GROUP BY user_id 
                ORDER BY message_count DESC LIMIT 5
            ''', (interaction.guild.id, start_time)) as cursor:
                top_users = await cursor.fetchall()
            
            # Hourly activity (last 24 hours for chart)
            async with db.execute('''
                SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
                FROM chat_analytics 
                WHERE guild_id = ? AND timestamp >= ?
                GROUP BY hour
                ORDER BY hour
            ''', (interaction.guild.id, now - timedelta(hours=24))) as cursor:
                hourly_activity = await cursor.fetchall()

        embed = discord.Embed(
            title=f"📊 Server Analytics - {period.upper()}",
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )
        
        # Overview stats
        embed.add_field(name="💬 Total Messages", value=f"{total_messages:,}", inline=True)
        embed.add_field(name="👥 Active Users", value=f"{active_users:,}", inline=True)
        embed.add_field(name="📈 Avg/Day", value=f"{total_messages/max(1, (now-start_time).days):.1f}", inline=True)
        
        # Top channels
        if top_channels:
            channel_text = "\n".join([
                f"<#{channel_id}>: {count:,} messages" 
                for channel_id, count in top_channels[:3]
            ])
            embed.add_field(name="🔥 Most Active Channels", value=channel_text, inline=False)
        
        # Top users
        if top_users:
            user_text = "\n".join([
                f"<@{user_id}>: {count:,} messages" 
                for user_id, count in top_users[:3]
            ])
            embed.add_field(name="⭐ Most Active Users", value=user_text, inline=False)
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="activity-report", description="Generate detailed activity report")
    @app_commands.default_permissions(administrator=True)
    async def activity_report(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        async with aiosqlite.connect('ultrabot.db') as db:
            # Get comprehensive stats
            stats = {}
            
            # Total users and activity
            async with db.execute('''
                SELECT COUNT(*), SUM(messages_sent), AVG(messages_sent)
                FROM users WHERE guild_id = ?
            ''', (interaction.guild.id,)) as cursor:
                result = await cursor.fetchone()
                stats['total_users'] = result[0] or 0
                stats['total_messages'] = result[1] or 0
                stats['avg_messages'] = result[2] or 0
            
            # Moderation stats
            async with db.execute('''
                SELECT action, COUNT(*) FROM moderation_logs 
                WHERE guild_id = ? AND timestamp >= datetime('now', '-30 days')
                GROUP BY action
            ''', (interaction.guild.id,)) as cursor:
                mod_stats = dict(await cursor.fetchall())
            
            # Daily activity trend (last 7 days)
            async with db.execute('''
                SELECT DATE(timestamp) as date, COUNT(*) as count
                FROM chat_analytics 
                WHERE guild_id = ? AND timestamp >= datetime('now', '-7 days')
                GROUP BY date
                ORDER BY date
            ''', (interaction.guild.id,)) as cursor:
                daily_trend = await cursor.fetchall()

        embed = discord.Embed(
            title="📋 Comprehensive Activity Report",
            description="Detailed server activity analysis for the past 30 days",
            color=discord.Color.green()
        )
        
        # User engagement
        embed.add_field(
            name="👥 User Engagement",
            value=f"**Total Users:** {stats['total_users']:,}\n"
                  f"**Total Messages:** {stats['total_messages']:,}\n"
                  f"**Avg Messages/User:** {stats['avg_messages']:.1f}",
            inline=False
        )
        
        # Moderation overview
        if mod_stats:
            mod_text = "\n".join([f"**{action.title()}:** {count}" for action, count in mod_stats.items()])
            embed.add_field(name="⚖️ Moderation (30 days)", value=mod_text, inline=False)
        
        # Growth trend
        if daily_trend:
            trend_text = "\n".join([f"**{date}:** {count} messages" for date, count in daily_trend[-3:]])
            embed.add_field(name="📈 Recent Daily Activity", value=trend_text, inline=False)
        
        embed.set_footer(text="Report generated at")
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="user-stats", description="Detailed statistics for a specific user")
    @app_commands.describe(user="User to analyze", period="Time period")
    @app_commands.choices(period=[
        app_commands.Choice(name="Last 7 Days", value="7d"),
        app_commands.Choice(name="Last 30 Days", value="30d"),
        app_commands.Choice(name="All Time", value="all")
    ])
    async def user_statistics(self, interaction: discord.Interaction, 
                            user: discord.Member, period: str = "30d"):
        await interaction.response.defer()
        
        # Calculate time range
        now = datetime.now(timezone.utc)
        if period == "7d":
            start_time = now - timedelta(days=7)
        elif period == "30d":
            start_time = now - timedelta(days=30)
        else:
            start_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        
        async with aiosqlite.connect('ultrabot.db') as db:
            # User basic stats
            async with db.execute('''
                SELECT messages_sent, xp, level, coins, warnings
                FROM users WHERE user_id = ? AND guild_id = ?
            ''', (user.id, interaction.guild.id)) as cursor:
                user_stats = await cursor.fetchone()
            
            if not user_stats:
                await interaction.followup.send("No data available for this user.", ephemeral=True)
                return
            
            # Activity in period
            async with db.execute('''
                SELECT COUNT(*), AVG(message_length)
                FROM chat_analytics 
                WHERE user_id = ? AND guild_id = ? AND timestamp >= ?
            ''', (user.id, interaction.guild.id, start_time)) as cursor:
                period_stats = await cursor.fetchone()
            
            # Channel activity
            async with db.execute('''
                SELECT channel_id, COUNT(*) as count
                FROM chat_analytics 
                WHERE user_id = ? AND guild_id = ? AND timestamp >= ?
                GROUP BY channel_id
                ORDER BY count DESC LIMIT 3
            ''', (user.id, interaction.guild.id, start_time)) as cursor:
                channel_activity = await cursor.fetchall()
            
            # Rank calculation
            async with db.execute('''
                SELECT COUNT(*) + 1 as rank FROM users 
                WHERE guild_id = ? AND level > ?
            ''', (interaction.guild.id, user_stats[2])) as cursor:
                rank = (await cursor.fetchone())[0]

        embed = discord.Embed(
            title=f"📊 {user.display_name}'s Statistics",
            color=user.color or discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        
        # Overall stats
        embed.add_field(name="📈 Overall Stats", 
                       value=f"**Level:** {user_stats[2]} (Rank #{rank})\n"
                             f"**Total XP:** {user_stats[1]:,}\n"
                             f"**Total Messages:** {user_stats[0]:,}\n"
                             f"**Coins:** {user_stats[3]:,}\n"
                             f"**Warnings:** {user_stats[4]}", inline=False)
        
        # Period activity
        period_messages = period_stats[0] if period_stats else 0
        avg_length = period_stats[1] if period_stats and period_stats[1] else 0
        
        embed.add_field(name=f"📅 {period.upper()} Activity",
                       value=f"**Messages:** {period_messages:,}\n"
                             f"**Avg Length:** {avg_length:.1f} chars\n"
                             f"**Daily Avg:** {period_messages/max(1, (now-start_time).days):.1f}", inline=False)
        
        # Top channels
        if channel_activity:
            channel_text = "\n".join([
                f"<#{channel_id}>: {count:,} messages" 
                for channel_id, count in channel_activity
            ])
            embed.add_field(name="🔥 Most Active Channels", value=channel_text, inline=False)
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="server-health", description="Monitor server health and issues")
    @app_commands.default_permissions(administrator=True)
    async def server_health(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        guild = interaction.guild
        
        # Calculate health metrics
        health_score = 100
        issues = []
        
        # Check member activity
        active_members = len([m for m in guild.members if not m.bot and m.status != discord.Status.offline])
        activity_ratio = active_members / max(1, len([m for m in guild.members if not m.bot]))
        
        if activity_ratio < 0.3:
            health_score -= 20
            issues.append("⚠️ Low member activity (< 30% online)")
        
        # Check moderation workload
        async with aiosqlite.connect('ultrabot.db') as db:
            async with db.execute('''
                SELECT COUNT(*) FROM moderation_logs 
                WHERE guild_id = ? AND timestamp >= datetime('now', '-7 days')
            ''', (guild.id,)) as cursor:
                recent_mod_actions = (await cursor.fetchone())[0]
        
        if recent_mod_actions > 50:
            health_score -= 15
            issues.append("🚨 High moderation activity (>50 actions/week)")
        
        # Check role distribution
        members_with_roles = len([m for m in guild.members if len(m.roles) > 1 and not m.bot])
        role_ratio = members_with_roles / max(1, len([m for m in guild.members if not m.bot]))
        
        if role_ratio < 0.5:
            health_score -= 10
            issues.append("📝 Many members lack assigned roles")
        
        # Determine health status
        if health_score >= 90:
            status = "🟢 Excellent"
            color = discord.Color.green()
        elif health_score >= 70:
            status = "🟡 Good"
            color = discord.Color.yellow()
        elif health_score >= 50:
            status = "🟠 Fair"
            color = discord.Color.orange()
        else:
            status = "🔴 Needs Attention"
            color = discord.Color.red()
        
        embed = discord.Embed(
            title="🏥 Server Health Report",
            description=f"**Overall Health:** {status} ({health_score}/100)",
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Key metrics
        embed.add_field(name="👥 Member Activity", 
                       value=f"{active_members}/{len([m for m in guild.members if not m.bot])} online ({activity_ratio:.1%})", 
                       inline=True)
        embed.add_field(name="⚖️ Mod Actions (7d)", value=str(recent_mod_actions), inline=True)
        embed.add_field(name="🎭 Role Coverage", value=f"{role_ratio:.1%}", inline=True)
        
        # Issues and recommendations
        if issues:
            embed.add_field(name="⚠️ Identified Issues", value="\n".join(issues), inline=False)
        else:
            embed.add_field(name="✅ Status", value="No major issues detected!", inline=False)
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="export-data", description="Export server data for analysis")
    @app_commands.describe(data_type="Type of data to export")
    @app_commands.choices(data_type=[
        app_commands.Choice(name="User Statistics", value="users"),
        app_commands.Choice(name="Message Analytics", value="messages"),
        app_commands.Choice(name="Moderation Logs", value="moderation")
    ])
    @app_commands.default_permissions(administrator=True)
    async def export_data(self, interaction: discord.Interaction, data_type: str):
        await interaction.response.defer()
        
        async with aiosqlite.connect('ultrabot.db') as db:
            if data_type == "users":
                async with db.execute('''
                    SELECT user_id, messages_sent, xp, level, coins, warnings
                    FROM users WHERE guild_id = ?
                    ORDER BY level DESC, xp DESC
                ''', (interaction.guild.id,)) as cursor:
                    data = await cursor.fetchall()
                
                headers = ["User ID", "Messages", "XP", "Level", "Coins", "Warnings"]
                
            elif data_type == "messages":
                async with db.execute('''
                    SELECT channel_id, user_id, message_length, timestamp
                    FROM chat_analytics WHERE guild_id = ?
                    ORDER BY timestamp DESC LIMIT 1000
                ''', (interaction.guild.id,)) as cursor:
                    data = await cursor.fetchall()
                
                headers = ["Channel ID", "User ID", "Message Length", "Timestamp"]
                
            elif data_type == "moderation":
                async with db.execute('''
                    SELECT user_id, moderator_id, action, reason, timestamp
                    FROM moderation_logs WHERE guild_id = ?
                    ORDER BY timestamp DESC
                ''', (interaction.guild.id,)) as cursor:
                    data = await cursor.fetchall()
                
                headers = ["User ID", "Moderator ID", "Action", "Reason", "Timestamp"]
        
        if not data:
            await interaction.followup.send(f"No {data_type} data available for export.", ephemeral=True)
            return
        
        # Create CSV content
        csv_content = ",".join(headers) + "\n"
        for row in data:
            csv_content += ",".join(str(item) for item in row) + "\n"
        
        # Create file
        file_content = csv_content.encode('utf-8')
        file = discord.File(io.BytesIO(file_content), filename=f"{data_type}_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv")
        
        embed = discord.Embed(
            title="📤 Data Export",
            description=f"Successfully exported {len(data)} {data_type} records",
            color=discord.Color.blue()
        )
        embed.add_field(name="Format", value="CSV", inline=True)
        embed.add_field(name="Records", value=str(len(data)), inline=True)
        
        await interaction.followup.send(embed=embed, file=file)

async def setup(bot):
    await bot.add_cog(AnalyticsMonitoring(bot))