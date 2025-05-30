import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiosqlite
import asyncio
from datetime import datetime, timezone, timedelta
import json
from collections import defaultdict

class AdvancedAnalytics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_sessions = {}  # Track active voice sessions
        self.daily_aggregator.start()

    def cog_unload(self):
        self.daily_aggregator.cancel()

    @tasks.loop(hours=1)
    async def daily_aggregator(self):
        """Aggregate analytics data hourly"""
        await self.aggregate_daily_metrics()

    @daily_aggregator.before_loop
    async def before_daily_aggregator(self):
        await self.bot.wait_until_ready()

    async def aggregate_daily_metrics(self):
        """Aggregate daily metrics for all guilds"""
        async with aiosqlite.connect('ultrabot.db') as db:
            for guild in self.bot.guilds:
                today = datetime.now().date()
                
                # Get daily message stats
                async with db.execute('''
                    SELECT COUNT(*) as total_messages, 
                           COUNT(DISTINCT user_id) as active_users,
                           AVG(message_length) as avg_length
                    FROM chat_analytics 
                    WHERE guild_id = ? AND date(timestamp) = ?
                ''', (guild.id, today)) as cursor:
                    message_stats = await cursor.fetchone()
                
                # Get voice activity stats
                async with db.execute('''
                    SELECT SUM(duration_seconds)/60 as voice_minutes
                    FROM voice_analytics 
                    WHERE guild_id = ? AND date(join_time) = ?
                ''', (guild.id, today)) as cursor:
                    voice_stats = await cursor.fetchone()
                
                # Update or insert daily metrics
                await db.execute('''
                    INSERT OR REPLACE INTO server_metrics 
                    (guild_id, date, total_messages, active_users, avg_message_length, voice_minutes)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    guild.id, today,
                    message_stats[0] or 0,
                    message_stats[1] or 0, 
                    message_stats[2] or 0,
                    voice_stats[0] or 0
                ))
                
                await db.commit()

    @commands.Cog.listener()
    async def on_message(self, message):
        """Track message analytics"""
        if message.author.bot or not message.guild:
            return
        
        async with aiosqlite.connect('ultrabot.db') as db:
            # Record message analytics
            await db.execute('''
                INSERT INTO chat_analytics 
                (guild_id, channel_id, user_id, message_length, has_mentions, has_attachments, is_thread)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                message.guild.id,
                message.channel.id,
                message.author.id,
                len(message.content),
                len(message.mentions) > 0,
                len(message.attachments) > 0,
                hasattr(message.channel, 'parent') and message.channel.parent is not None
            ))
            
            # Update user activity summary
            today = datetime.now().date()
            await db.execute('''
                INSERT OR IGNORE INTO user_activity_summary 
                (guild_id, user_id, date, messages_sent, first_activity, last_activity)
                VALUES (?, ?, ?, 0, ?, ?)
            ''', (message.guild.id, message.author.id, today, datetime.now(), datetime.now()))
            
            await db.execute('''
                UPDATE user_activity_summary 
                SET messages_sent = messages_sent + 1, last_activity = ?
                WHERE guild_id = ? AND user_id = ? AND date = ?
            ''', (datetime.now(), message.guild.id, message.author.id, today))
            
            await db.commit()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Track voice analytics"""
        if member.bot:
            return
        
        guild_id = member.guild.id
        user_id = member.id
        now = datetime.now()
        
        # User joined a voice channel
        if before.channel is None and after.channel is not None:
            self.voice_sessions[f"{guild_id}_{user_id}"] = {
                'join_time': now,
                'channel_id': after.channel.id,
                'was_muted': after.mute,
                'was_deafened': after.deaf
            }
        
        # User left a voice channel
        elif before.channel is not None and after.channel is None:
            session_key = f"{guild_id}_{user_id}"
            if session_key in self.voice_sessions:
                session = self.voice_sessions.pop(session_key)
                duration = (now - session['join_time']).total_seconds()
                
                async with aiosqlite.connect('ultrabot.db') as db:
                    await db.execute('''
                        INSERT INTO voice_analytics 
                        (guild_id, channel_id, user_id, join_time, leave_time, duration_seconds, was_muted, was_deafened)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        guild_id,
                        session['channel_id'],
                        user_id,
                        session['join_time'],
                        now,
                        int(duration),
                        session['was_muted'],
                        session['was_deafened']
                    ))
                    
                    # Update user activity summary
                    today = now.date()
                    await db.execute('''
                        INSERT OR IGNORE INTO user_activity_summary 
                        (guild_id, user_id, date, voice_minutes, first_activity, last_activity)
                        VALUES (?, ?, ?, 0, ?, ?)
                    ''', (guild_id, user_id, today, now, now))
                    
                    await db.execute('''
                        UPDATE user_activity_summary 
                        SET voice_minutes = voice_minutes + ?, last_activity = ?
                        WHERE guild_id = ? AND user_id = ? AND date = ?
                    ''', (duration / 60, now, guild_id, user_id, today))
                    
                    await db.commit()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Track reaction analytics"""
        if user.bot or not reaction.message.guild:
            return
        
        async with aiosqlite.connect('ultrabot.db') as db:
            # Update user activity - reactions given
            today = datetime.now().date()
            await db.execute('''
                INSERT OR IGNORE INTO user_activity_summary 
                (guild_id, user_id, date, reactions_given, first_activity, last_activity)
                VALUES (?, ?, ?, 0, ?, ?)
            ''', (reaction.message.guild.id, user.id, today, datetime.now(), datetime.now()))
            
            await db.execute('''
                UPDATE user_activity_summary 
                SET reactions_given = reactions_given + 1, last_activity = ?
                WHERE guild_id = ? AND user_id = ? AND date = ?
            ''', (datetime.now(), reaction.message.guild.id, user.id, today))
            
            # Update message author - reactions received
            await db.execute('''
                INSERT OR IGNORE INTO user_activity_summary 
                (guild_id, user_id, date, reactions_received, first_activity, last_activity)
                VALUES (?, ?, ?, 0, ?, ?)
            ''', (reaction.message.guild.id, reaction.message.author.id, today, datetime.now(), datetime.now()))
            
            await db.execute('''
                UPDATE user_activity_summary 
                SET reactions_received = reactions_received + 1
                WHERE guild_id = ? AND user_id = ? AND date = ?
            ''', (reaction.message.guild.id, reaction.message.author.id, today))
            
            await db.commit()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Track member joins"""
        async with aiosqlite.connect('ultrabot.db') as db:
            today = datetime.now().date()
            await db.execute('''
                INSERT OR IGNORE INTO server_metrics 
                (guild_id, date, new_members) VALUES (?, ?, 0)
            ''', (member.guild.id, today))
            
            await db.execute('''
                UPDATE server_metrics 
                SET new_members = new_members + 1
                WHERE guild_id = ? AND date = ?
            ''', (member.guild.id, today))
            
            await db.commit()

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Track member leaves"""
        async with aiosqlite.connect('ultrabot.db') as db:
            today = datetime.now().date()
            await db.execute('''
                INSERT OR IGNORE INTO server_metrics 
                (guild_id, date, left_members) VALUES (?, ?, 0)
            ''', (member.guild.id, today))
            
            await db.execute('''
                UPDATE server_metrics 
                SET left_members = left_members + 1
                WHERE guild_id = ? AND date = ?
            ''', (member.guild.id, today))
            
            await db.commit()

    @app_commands.command(name="server_analytics", description="View comprehensive server analytics")
    @app_commands.describe(period="Time period for analytics")
    @app_commands.choices(period=[
        app_commands.Choice(name="24 Hours", value="24h"),
        app_commands.Choice(name="7 Days", value="7d"),
        app_commands.Choice(name="30 Days", value="30d")
    ])
    async def server_analytics(self, interaction: discord.Interaction, period: str = "7d"):
        await interaction.response.defer()
        
        # Calculate date range
        now = datetime.now()
        if period == "24h":
            start_date = now - timedelta(days=1)
            title_period = "24 Hours"
        elif period == "7d":
            start_date = now - timedelta(days=7)
            title_period = "7 Days"
        else:  # 30d
            start_date = now - timedelta(days=30)
            title_period = "30 Days"
        
        async with aiosqlite.connect('ultrabot.db') as db:
            # Get message statistics
            async with db.execute('''
                SELECT COUNT(*) as total_messages,
                       COUNT(DISTINCT user_id) as active_users,
                       AVG(message_length) as avg_length,
                       SUM(CASE WHEN has_attachments = 1 THEN 1 ELSE 0 END) as messages_with_files
                FROM chat_analytics 
                WHERE guild_id = ? AND timestamp >= ?
            ''', (interaction.guild.id, start_date)) as cursor:
                message_stats = await cursor.fetchone()
            
            # Get voice statistics
            async with db.execute('''
                SELECT SUM(duration_seconds)/60 as total_voice_minutes,
                       COUNT(DISTINCT user_id) as voice_users,
                       COUNT(*) as voice_sessions
                FROM voice_analytics 
                WHERE guild_id = ? AND join_time >= ?
            ''', (interaction.guild.id, start_date)) as cursor:
                voice_stats = await cursor.fetchone()
            
            # Get top channels by activity
            async with db.execute('''
                SELECT channel_id, COUNT(*) as message_count
                FROM chat_analytics 
                WHERE guild_id = ? AND timestamp >= ?
                GROUP BY channel_id
                ORDER BY message_count DESC
                LIMIT 3
            ''', (interaction.guild.id, start_date)) as cursor:
                top_channels = await cursor.fetchall()
            
            # Get top users by activity
            async with db.execute('''
                SELECT user_id, COUNT(*) as message_count
                FROM chat_analytics 
                WHERE guild_id = ? AND timestamp >= ?
                GROUP BY user_id
                ORDER BY message_count DESC
                LIMIT 3
            ''', (interaction.guild.id, start_date)) as cursor:
                top_users = await cursor.fetchall()
            
            # Get member statistics
            async with db.execute('''
                SELECT SUM(new_members) as new_members,
                       SUM(left_members) as left_members
                FROM server_metrics 
                WHERE guild_id = ? AND date >= ?
            ''', (interaction.guild.id, start_date.date())) as cursor:
                member_stats = await cursor.fetchone()

        embed = discord.Embed(
            title=f"📊 Server Analytics - {title_period}",
            description=f"Comprehensive analysis for {interaction.guild.name}",
            color=discord.Color.blue()
        )
        
        # Message activity
        total_messages = message_stats[0] or 0
        active_users = message_stats[1] or 0
        avg_length = round(message_stats[2] or 0, 1)
        files_shared = message_stats[3] or 0
        
        embed.add_field(
            name="💬 Message Activity",
            value=f"**{total_messages:,}** total messages\n**{active_users}** active users\n**{avg_length}** avg length\n**{files_shared}** files shared",
            inline=True
        )
        
        # Voice activity
        voice_minutes = round(voice_stats[0] or 0, 1)
        voice_users = voice_stats[1] or 0
        voice_sessions = voice_stats[2] or 0
        voice_hours = round(voice_minutes / 60, 1)
        
        embed.add_field(
            name="🎤 Voice Activity", 
            value=f"**{voice_hours}** total hours\n**{voice_users}** unique users\n**{voice_sessions}** sessions\n**{voice_minutes:.0f}** minutes",
            inline=True
        )
        
        # Member changes
        new_members = member_stats[0] or 0
        left_members = member_stats[1] or 0
        net_growth = new_members - left_members
        growth_symbol = "+" if net_growth >= 0 else ""
        
        embed.add_field(
            name="👥 Member Changes",
            value=f"**{new_members}** joined\n**{left_members}** left\n**{growth_symbol}{net_growth}** net growth\n**{interaction.guild.member_count:,}** total members",
            inline=True
        )
        
        # Engagement metrics
        if total_messages > 0 and interaction.guild.member_count > 0:
            messages_per_user = round(total_messages / max(active_users, 1), 1)
            participation_rate = round((active_users / interaction.guild.member_count) * 100, 1)
            activity_score = min(100, round((total_messages + voice_minutes) / 10, 1))
        else:
            messages_per_user = 0
            participation_rate = 0
            activity_score = 0
        
        embed.add_field(
            name="📈 Engagement Metrics",
            value=f"**{participation_rate}%** participation rate\n**{messages_per_user}** msgs per user\n**{activity_score}%** activity score",
            inline=True
        )
        
        # Top channels
        if top_channels:
            channel_text = ""
            for channel_id, count in top_channels:
                channel = interaction.guild.get_channel(channel_id)
                if channel:
                    channel_text += f"**#{channel.name}**: {count:,}\n"
            
            if channel_text:
                embed.add_field(
                    name="🔥 Most Active Channels",
                    value=channel_text.strip(),
                    inline=True
                )
        
        # Top users
        if top_users:
            user_text = ""
            for user_id, count in top_users:
                user = interaction.guild.get_member(user_id)
                if user:
                    user_text += f"**{user.display_name}**: {count:,}\n"
            
            if user_text:
                embed.add_field(
                    name="⭐ Most Active Users",
                    value=user_text.strip(),
                    inline=True
                )
        
        embed.set_footer(text=f"Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M UTC')}")
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="user_stats", description="View detailed statistics for a specific user")
    @app_commands.describe(user="User to analyze", period="Time period")
    @app_commands.choices(period=[
        app_commands.Choice(name="7 Days", value="7d"),
        app_commands.Choice(name="30 Days", value="30d"),
        app_commands.Choice(name="All Time", value="all")
    ])
    async def user_stats(self, interaction: discord.Interaction, user: discord.Member, period: str = "30d"):
        await interaction.response.defer()
        
        # Calculate date range
        if period == "7d":
            start_date = datetime.now() - timedelta(days=7)
            title_period = "7 Days"
        elif period == "30d":
            start_date = datetime.now() - timedelta(days=30)
            title_period = "30 Days"
        else:
            start_date = datetime(2020, 1, 1)
            title_period = "All Time"
        
        async with aiosqlite.connect('ultrabot.db') as db:
            # Get comprehensive user statistics
            async with db.execute('''
                SELECT COUNT(*) as message_count,
                       AVG(message_length) as avg_length,
                       SUM(CASE WHEN has_attachments = 1 THEN 1 ELSE 0 END) as files_shared,
                       MIN(timestamp) as first_message,
                       MAX(timestamp) as last_message
                FROM chat_analytics 
                WHERE guild_id = ? AND user_id = ? AND timestamp >= ?
            ''', (interaction.guild.id, user.id, start_date)) as cursor:
                message_stats = await cursor.fetchone()
            
            # Get voice statistics
            async with db.execute('''
                SELECT SUM(duration_seconds)/60 as voice_minutes,
                       COUNT(*) as voice_sessions,
                       AVG(duration_seconds)/60 as avg_session_length
                FROM voice_analytics 
                WHERE guild_id = ? AND user_id = ? AND join_time >= ?
            ''', (interaction.guild.id, user.id, start_date)) as cursor:
                voice_stats = await cursor.fetchone()
            
            # Get social statistics
            async with db.execute('''
                SELECT SUM(reactions_given) as reactions_given,
                       SUM(reactions_received) as reactions_received,
                       COUNT(*) as active_days
                FROM user_activity_summary 
                WHERE guild_id = ? AND user_id = ? AND date >= ?
            ''', (interaction.guild.id, user.id, start_date.date())) as cursor:
                social_stats = await cursor.fetchone()
            
            # Get rank by messages
            async with db.execute('''
                SELECT COUNT(*) + 1 as rank
                FROM (
                    SELECT user_id, COUNT(*) as message_count
                    FROM chat_analytics 
                    WHERE guild_id = ? AND timestamp >= ?
                    GROUP BY user_id
                    HAVING message_count > (
                        SELECT COUNT(*) FROM chat_analytics 
                        WHERE guild_id = ? AND user_id = ? AND timestamp >= ?
                    )
                )
            ''', (interaction.guild.id, start_date, interaction.guild.id, user.id, start_date)) as cursor:
                rank_result = await cursor.fetchone()

        embed = discord.Embed(
            title=f"👤 User Statistics - {user.display_name}",
            description=f"Detailed activity analysis for {title_period}",
            color=user.color or discord.Color.purple()
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        
        # Message activity
        message_count = message_stats[0] or 0
        avg_length = round(message_stats[1] or 0, 1)
        files_shared = message_stats[2] or 0
        
        embed.add_field(
            name="💬 Messages",
            value=f"**{message_count:,}** messages sent\n**{avg_length}** avg length\n**{files_shared}** files shared",
            inline=True
        )
        
        # Voice activity
        voice_minutes = round(voice_stats[0] or 0, 1)
        voice_sessions = voice_stats[1] or 0
        avg_session = round(voice_stats[2] or 0, 1)
        voice_hours = round(voice_minutes / 60, 1)
        
        embed.add_field(
            name="🎤 Voice",
            value=f"**{voice_hours}** hours total\n**{voice_sessions}** sessions\n**{avg_session}** min avg session",
            inline=True
        )
        
        # Social engagement
        reactions_given = social_stats[0] or 0
        reactions_received = social_stats[1] or 0
        active_days = social_stats[2] or 0
        
        embed.add_field(
            name="🤝 Social",
            value=f"**{reactions_given:,}** reactions given\n**{reactions_received:,}** reactions received\n**{active_days}** active days",
            inline=True
        )
        
        # Server ranking and status
        rank = rank_result[0] if rank_result else "N/A"
        join_date = user.joined_at.strftime('%m/%d/%Y') if user.joined_at else 'Unknown'
        
        embed.add_field(
            name="📊 Server Status",
            value=f"**#{rank}** message rank\n**{len(user.roles)-1}** roles\n**Joined:** {join_date}",
            inline=True
        )
        
        # Activity timeline
        if message_stats[3] and message_stats[4]:
            first_msg = datetime.fromisoformat(message_stats[3]).strftime('%m/%d/%Y')
            last_msg = datetime.fromisoformat(message_stats[4]).strftime('%m/%d/%Y %H:%M')
            
            embed.add_field(
                name="📅 Activity Timeline",
                value=f"**First message:** {first_msg}\n**Latest activity:** {last_msg}",
                inline=True
            )
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="channel_stats", description="View analytics for server channels")
    async def channel_stats(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        async with aiosqlite.connect('ultrabot.db') as db:
            # Get channel activity for last 7 days
            async with db.execute('''
                SELECT channel_id, 
                       COUNT(*) as message_count,
                       COUNT(DISTINCT user_id) as unique_users,
                       AVG(message_length) as avg_length
                FROM chat_analytics 
                WHERE guild_id = ? AND timestamp >= datetime('now', '-7 days')
                GROUP BY channel_id
                ORDER BY message_count DESC
                LIMIT 10
            ''', (interaction.guild.id,)) as cursor:
                channel_data = await cursor.fetchall()

        embed = discord.Embed(
            title="📺 Channel Analytics",
            description="7-day channel activity breakdown",
            color=discord.Color.orange()
        )
        
        if channel_data:
            for channel_id, msg_count, users, avg_len in channel_data[:6]:
                channel = interaction.guild.get_channel(channel_id)
                if channel:
                    embed.add_field(
                        name=f"#{channel.name}",
                        value=f"**{msg_count:,}** messages\n**{users}** users\n**{avg_len:.0f}** avg length",
                        inline=True
                    )
        else:
            embed.add_field(
                name="📋 Status",
                value="No channel activity data available yet. Start chatting to generate analytics!",
                inline=False
            )
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="activity_trends", description="View server activity trends and growth")
    async def activity_trends(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        async with aiosqlite.connect('ultrabot.db') as db:
            # Get trend data for the last 30 days
            async with db.execute('''
                SELECT date, total_messages, active_users, voice_minutes, new_members, left_members
                FROM server_metrics 
                WHERE guild_id = ? AND date >= date('now', '-30 days')
                ORDER BY date DESC
                LIMIT 30
            ''', (interaction.guild.id,)) as cursor:
                trend_data = await cursor.fetchall()

        embed = discord.Embed(
            title="📈 Activity Trends",
            description="30-day server growth and engagement analysis",
            color=discord.Color.green()
        )
        
        if len(trend_data) >= 7:
            # Calculate weekly comparisons
            recent_week = trend_data[:7]
            previous_week = trend_data[7:14] if len(trend_data) >= 14 else []
            
            recent_messages = sum(row[1] for row in recent_week)
            recent_users = sum(row[2] for row in recent_week) / len(recent_week)
            recent_voice = sum(row[3] for row in recent_week)
            
            if previous_week:
                prev_messages = sum(row[1] for row in previous_week)
                prev_users = sum(row[2] for row in previous_week) / len(previous_week)
                prev_voice = sum(row[3] for row in previous_week)
                
                msg_change = ((recent_messages - prev_messages) / max(prev_messages, 1)) * 100
                user_change = ((recent_users - prev_users) / max(prev_users, 1)) * 100
                voice_change = ((recent_voice - prev_voice) / max(prev_voice, 1)) * 100
                
                embed.add_field(
                    name="📊 Weekly Trends",
                    value=f"**Messages:** {msg_change:+.1f}%\n**Active Users:** {user_change:+.1f}%\n**Voice Time:** {voice_change:+.1f}%",
                    inline=True
                )
            
            # Find peak activity day
            if trend_data:
                peak_day = max(trend_data, key=lambda x: x[1])
                peak_date = datetime.strptime(peak_day[0], '%Y-%m-%d').strftime('%m/%d')
                
                embed.add_field(
                    name="🔥 Peak Activity Day",
                    value=f"**Date:** {peak_date}\n**Messages:** {peak_day[1]:,}\n**Active Users:** {peak_day[2]}",
                    inline=True
                )
            
            # Calculate member growth
            total_new = sum(row[4] or 0 for row in trend_data)
            total_left = sum(row[5] or 0 for row in trend_data)
            net_growth = total_new - total_left
            
            embed.add_field(
                name="👥 Member Growth (30d)",
                value=f"**Joined:** {total_new}\n**Left:** {total_left}\n**Net:** {net_growth:+}",
                inline=True
            )
            
        else:
            embed.add_field(
                name="📋 Status",
                value="Not enough historical data yet. Analytics improve as the bot collects more activity data over time.",
                inline=False
            )
        
        # Current server overview
        embed.add_field(
            name="📋 Current Server",
            value=f"**Total Members:** {interaction.guild.member_count:,}\n**Text Channels:** {len(interaction.guild.text_channels)}\n**Voice Channels:** {len(interaction.guild.voice_channels)}",
            inline=True
        )
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AdvancedAnalytics(bot))