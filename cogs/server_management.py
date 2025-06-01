import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import asyncio
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ServerManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="server-stats", description="Comprehensive server statistics and analytics")
    async def server_stats(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            guild = interaction.guild
            
            # Basic server info
            total_members = guild.member_count
            online_members = sum(1 for member in guild.members if member.status != discord.Status.offline)
            bot_count = sum(1 for member in guild.members if member.bot)
            human_count = total_members - bot_count
            
            # Channel counts
            text_channels = len(guild.text_channels)
            voice_channels = len(guild.voice_channels)
            categories = len(guild.categories)
            
            # Role info
            role_count = len(guild.roles)
            
            # Get database analytics
            async with aiosqlite.connect('ultrabot.db') as db:
                # Messages in last 24h
                async with db.execute('''
                    SELECT COUNT(*) FROM chat_analytics 
                    WHERE guild_id = ? AND timestamp > datetime('now', '-24 hours')
                ''', (guild.id,)) as cursor:
                    daily_messages = (await cursor.fetchone())[0]
                
                # Most active users
                async with db.execute('''
                    SELECT user_id, COUNT(*) as msg_count
                    FROM chat_analytics 
                    WHERE guild_id = ? AND timestamp > datetime('now', '-7 days')
                    GROUP BY user_id 
                    ORDER BY msg_count DESC 
                    LIMIT 5
                ''', (guild.id,)) as cursor:
                    top_users = await cursor.fetchall()
            
            embed = discord.Embed(
                title=f"📊 {guild.name} Server Statistics",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
            
            # Member stats
            embed.add_field(
                name="👥 Members",
                value=f"Total: {total_members:,}\nOnline: {online_members:,}\nHumans: {human_count:,}\nBots: {bot_count:,}",
                inline=True
            )
            
            # Channel stats
            embed.add_field(
                name="💬 Channels",
                value=f"Text: {text_channels}\nVoice: {voice_channels}\nCategories: {categories}\nTotal: {text_channels + voice_channels}",
                inline=True
            )
            
            # Server info
            embed.add_field(
                name="🏠 Server Info",
                value=f"Created: <t:{int(guild.created_at.timestamp())}:R>\nOwner: {guild.owner.mention if guild.owner else 'Unknown'}\nRoles: {role_count}\nBoosts: {guild.premium_subscription_count}",
                inline=True
            )
            
            # Activity stats
            embed.add_field(
                name="📈 Activity (24h)",
                value=f"Messages: {daily_messages:,}\nAvg/hour: {daily_messages/24:.1f}",
                inline=True
            )
            
            # Top users
            if top_users:
                top_users_text = ""
                for i, (user_id, count) in enumerate(top_users, 1):
                    user = guild.get_member(user_id)
                    if user:
                        top_users_text += f"{i}. {user.display_name}: {count}\n"
                
                embed.add_field(
                    name="🏆 Most Active (7 days)",
                    value=top_users_text or "No data",
                    inline=True
                )
            
            embed.set_footer(text=f"Server ID: {guild.id}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Server stats error: {e}")
            await interaction.followup.send("Failed to retrieve server statistics.")

    @app_commands.command(name="cleanup-channels", description="Clean up inactive or empty channels")
    @app_commands.describe(
        days_inactive="Days of inactivity before considering cleanup",
        dry_run="Preview what would be deleted without actually deleting"
    )
    @app_commands.default_permissions(manage_channels=True)
    async def cleanup_channels(self, interaction: discord.Interaction, days_inactive: int = 30, dry_run: bool = True):
        await interaction.response.defer()
        
        try:
            guild = interaction.guild
            cutoff_date = datetime.now() - timedelta(days=days_inactive)
            
            channels_to_cleanup = []
            
            for channel in guild.text_channels:
                try:
                    # Get last message
                    async for message in channel.history(limit=1):
                        if message.created_at < cutoff_date:
                            channels_to_cleanup.append((channel, message.created_at))
                        break
                    else:
                        # No messages found
                        channels_to_cleanup.append((channel, channel.created_at))
                except discord.Forbidden:
                    continue
            
            if not channels_to_cleanup:
                await interaction.followup.send("✅ No inactive channels found.")
                return
            
            embed = discord.Embed(
                title="🧹 Channel Cleanup Analysis",
                description=f"Found {len(channels_to_cleanup)} inactive channels (>{days_inactive} days)",
                color=discord.Color.orange() if dry_run else discord.Color.red()
            )
            
            cleanup_text = ""
            for channel, last_activity in channels_to_cleanup[:10]:  # Show max 10
                days_ago = (datetime.now() - last_activity).days
                cleanup_text += f"#{channel.name} - {days_ago} days ago\n"
            
            if len(channels_to_cleanup) > 10:
                cleanup_text += f"... and {len(channels_to_cleanup) - 10} more"
            
            embed.add_field(name="Channels to Clean", value=cleanup_text, inline=False)
            embed.add_field(name="Mode", value="DRY RUN - No channels deleted" if dry_run else "LIVE - Channels will be deleted", inline=True)
            
            if not dry_run:
                # Actually delete channels
                deleted_count = 0
                for channel, _ in channels_to_cleanup:
                    try:
                        await channel.delete(reason=f"Cleanup: Inactive for {days_inactive}+ days")
                        deleted_count += 1
                        await asyncio.sleep(1)  # Rate limiting
                    except discord.Forbidden:
                        continue
                
                embed.add_field(name="Deleted", value=f"{deleted_count} channels", inline=True)
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Channel cleanup error: {e}")
            await interaction.followup.send("Failed to perform channel cleanup.")

    @app_commands.command(name="role-manager", description="Advanced role management and assignment")
    @app_commands.describe(
        action="Action to perform",
        role="Role to manage",
        user="User to assign/remove role",
        reason="Reason for role change"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Assign Role", value="assign"),
        app_commands.Choice(name="Remove Role", value="remove"),
        app_commands.Choice(name="Create Role", value="create"),
        app_commands.Choice(name="Delete Role", value="delete"),
        app_commands.Choice(name="Role Info", value="info")
    ])
    @app_commands.default_permissions(manage_roles=True)
    async def role_manager(self, interaction: discord.Interaction, action: str, 
                          role: discord.Role = None, user: discord.Member = None, reason: str = "No reason provided"):
        await interaction.response.defer()
        
        try:
            if action == "assign" and role and user:
                await user.add_roles(role, reason=reason)
                embed = discord.Embed(
                    title="✅ Role Assigned",
                    description=f"Assigned {role.mention} to {user.mention}",
                    color=discord.Color.green()
                )
                embed.add_field(name="Reason", value=reason, inline=False)
                
            elif action == "remove" and role and user:
                await user.remove_roles(role, reason=reason)
                embed = discord.Embed(
                    title="✅ Role Removed",
                    description=f"Removed {role.mention} from {user.mention}",
                    color=discord.Color.orange()
                )
                embed.add_field(name="Reason", value=reason, inline=False)
                
            elif action == "info" and role:
                members_with_role = len(role.members)
                permissions = [perm for perm, value in role.permissions if value]
                
                embed = discord.Embed(
                    title=f"📋 Role Information: {role.name}",
                    color=role.color
                )
                embed.add_field(name="Members", value=str(members_with_role), inline=True)
                embed.add_field(name="Position", value=str(role.position), inline=True)
                embed.add_field(name="Mentionable", value="Yes" if role.mentionable else "No", inline=True)
                embed.add_field(name="Hoisted", value="Yes" if role.hoist else "No", inline=True)
                embed.add_field(name="Created", value=f"<t:{int(role.created_at.timestamp())}:R>", inline=True)
                
                if permissions:
                    perm_text = ", ".join(permissions[:10])
                    if len(permissions) > 10:
                        perm_text += f" ... and {len(permissions) - 10} more"
                    embed.add_field(name="Key Permissions", value=perm_text, inline=False)
                
            else:
                embed = discord.Embed(
                    title="❌ Invalid Action",
                    description="Please provide the required parameters for the selected action.",
                    color=discord.Color.red()
                )
            
            await interaction.followup.send(embed=embed)
            
        except discord.Forbidden:
            await interaction.followup.send("❌ I don't have permission to manage this role.")
        except Exception as e:
            logger.error(f"Role manager error: {e}")
            await interaction.followup.send("❌ Failed to perform role action.")

    @app_commands.command(name="backup-server", description="Create a backup configuration of server settings")
    @app_commands.default_permissions(administrator=True)
    async def backup_server(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            guild = interaction.guild
            
            # Collect server data
            backup_data = {
                "server_info": {
                    "name": guild.name,
                    "description": guild.description,
                    "verification_level": str(guild.verification_level),
                    "default_notifications": str(guild.default_notifications),
                    "explicit_content_filter": str(guild.explicit_content_filter)
                },
                "channels": [],
                "roles": [],
                "categories": [],
                "created_at": datetime.now().isoformat()
            }
            
            # Backup categories
            for category in guild.categories:
                backup_data["categories"].append({
                    "name": category.name,
                    "position": category.position,
                    "overwrites": {str(target.id): {perm: value for perm, value in overwrite} 
                                 for target, overwrite in category.overwrites.items()}
                })
            
            # Backup channels
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    channel_data = {
                        "name": channel.name,
                        "type": "text",
                        "category": channel.category.name if channel.category else None,
                        "position": channel.position,
                        "topic": channel.topic,
                        "slowmode": channel.slowmode_delay,
                        "nsfw": channel.nsfw
                    }
                elif isinstance(channel, discord.VoiceChannel):
                    channel_data = {
                        "name": channel.name,
                        "type": "voice",
                        "category": channel.category.name if channel.category else None,
                        "position": channel.position,
                        "bitrate": channel.bitrate,
                        "user_limit": channel.user_limit
                    }
                else:
                    continue
                
                backup_data["channels"].append(channel_data)
            
            # Backup roles (excluding @everyone and bot roles)
            for role in guild.roles:
                if role.name != "@everyone" and not role.managed:
                    backup_data["roles"].append({
                        "name": role.name,
                        "color": role.color.value,
                        "hoist": role.hoist,
                        "mentionable": role.mentionable,
                        "position": role.position,
                        "permissions": role.permissions.value
                    })
            
            # Save backup to database
            backup_json = json.dumps(backup_data, indent=2)
            backup_id = f"{guild.id}_{int(datetime.now().timestamp())}"
            
            async with aiosqlite.connect('ultrabot.db') as db:
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS server_backups (
                        id TEXT PRIMARY KEY,
                        guild_id INTEGER,
                        backup_data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                await db.execute('''
                    INSERT INTO server_backups (id, guild_id, backup_data)
                    VALUES (?, ?, ?)
                ''', (backup_id, guild.id, backup_json))
                await db.commit()
            
            # Create downloadable file
            file_content = backup_json.encode('utf-8')
            file = discord.File(
                fp=io.BytesIO(file_content),
                filename=f"backup_{guild.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            embed = discord.Embed(
                title="💾 Server Backup Created",
                description=f"Successfully backed up server configuration",
                color=discord.Color.green()
            )
            embed.add_field(name="Backup ID", value=backup_id, inline=True)
            embed.add_field(name="Channels", value=str(len(backup_data["channels"])), inline=True)
            embed.add_field(name="Roles", value=str(len(backup_data["roles"])), inline=True)
            embed.add_field(name="Categories", value=str(len(backup_data["categories"])), inline=True)
            embed.set_footer(text="Backup file attached for download")
            
            await interaction.followup.send(embed=embed, file=file)
            
        except Exception as e:
            logger.error(f"Server backup error: {e}")
            await interaction.followup.send("❌ Failed to create server backup.")

    @app_commands.command(name="member-activity", description="Analyze member activity patterns")
    @app_commands.describe(
        user="Specific user to analyze (optional)",
        days="Number of days to analyze",
        show_graph="Generate activity graph"
    )
    async def member_activity(self, interaction: discord.Interaction, 
                            user: discord.Member = None, days: int = 7, show_graph: bool = False):
        await interaction.response.defer()
        
        try:
            guild = interaction.guild
            
            async with aiosqlite.connect('ultrabot.db') as db:
                if user:
                    # Individual user analysis
                    async with db.execute('''
                        SELECT DATE(timestamp) as date, COUNT(*) as messages,
                               AVG(message_length) as avg_length,
                               SUM(CASE WHEN has_attachments THEN 1 ELSE 0 END) as attachments
                        FROM chat_analytics 
                        WHERE guild_id = ? AND user_id = ? 
                        AND timestamp > datetime('now', '-{} days')
                        GROUP BY DATE(timestamp)
                        ORDER BY date DESC
                    '''.format(days), (guild.id, user.id)) as cursor:
                        daily_stats = await cursor.fetchall()
                    
                    total_messages = sum(stat[1] for stat in daily_stats)
                    avg_daily = total_messages / days if days > 0 else 0
                    
                    embed = discord.Embed(
                        title=f"📊 Activity Analysis: {user.display_name}",
                        color=discord.Color.blue()
                    )
                    embed.set_thumbnail(url=user.display_avatar.url)
                    
                    embed.add_field(name="Total Messages", value=f"{total_messages:,}", inline=True)
                    embed.add_field(name="Daily Average", value=f"{avg_daily:.1f}", inline=True)
                    embed.add_field(name="Period", value=f"{days} days", inline=True)
                    
                    if daily_stats:
                        recent_activity = "\n".join([
                            f"{stat[0]}: {stat[1]} messages" 
                            for stat in daily_stats[:7]
                        ])
                        embed.add_field(name="Recent Activity", value=recent_activity, inline=False)
                
                else:
                    # Server-wide analysis
                    async with db.execute('''
                        SELECT user_id, COUNT(*) as messages,
                               AVG(message_length) as avg_length
                        FROM chat_analytics 
                        WHERE guild_id = ? 
                        AND timestamp > datetime('now', '-{} days')
                        GROUP BY user_id
                        ORDER BY messages DESC
                        LIMIT 10
                    '''.format(days), (guild.id,)) as cursor:
                        top_users = await cursor.fetchall()
                    
                    embed = discord.Embed(
                        title=f"📊 Server Activity Analysis ({days} days)",
                        color=discord.Color.blue()
                    )
                    
                    if top_users:
                        leaderboard = ""
                        for i, (user_id, messages, avg_len) in enumerate(top_users, 1):
                            member = guild.get_member(user_id)
                            if member:
                                leaderboard += f"{i}. {member.display_name}: {messages} msgs\n"
                        
                        embed.add_field(name="🏆 Most Active Members", value=leaderboard, inline=False)
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Member activity error: {e}")
            await interaction.followup.send("❌ Failed to analyze member activity.")

async def setup(bot):
    await bot.add_cog(ServerManagement(bot))