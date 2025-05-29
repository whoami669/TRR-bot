import discord
import os
import asyncio
import random
import json
from discord.ext import commands, tasks
from discord.utils import get
from datetime import datetime, timedelta
from dotenv import load_dotenv
from database.database import Database
from utils.helpers import format_time, get_prefix
from utils.embeds import create_embed
from config.settings import CATEGORIES, DEFAULT_SETTINGS

load_dotenv()

class ComprehensiveBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(
            command_prefix=get_prefix,
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
        self.db = Database()
        self.start_time = datetime.utcnow()
        
    async def setup_hook(self):
        """Load all cogs and sync commands"""
        cogs = [
            'cogs.moderation',
            'cogs.music',
            'cogs.economy',
            'cogs.leveling',
            'cogs.utility',
            'cogs.fun',
            'cogs.tickets'
        ]
        
        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"✅ Loaded {cog}")
            except Exception as e:
                print(f"❌ Failed to load {cog}: {e}")
        
        # Initialize database
        await self.db.init_db()
        
    async def on_ready(self):
        print(f"🤖 {self.user.name} is now running!")
        print(f"📊 Connected to {len(self.guilds)} guilds")
        print(f"👥 Serving {sum(guild.member_count for guild in self.guilds)} members")
        
        # Start background tasks
        self.daily_tasks.start()
        self.auto_backup.start()
        self.status_rotation.start()
        
        # Setup servers
        for guild in self.guilds:
            await self.setup_comprehensive_server(guild)

    async def setup_comprehensive_server(self, guild):
        """Setup comprehensive server structure"""
        print(f"🏗️ Setting up server: {guild.name}")
        
        # Initialize server in database
        await self.db.init_server(guild.id)
        
        existing_channels = [channel.name for channel in guild.channels]
        existing_categories = [category.name for category in guild.categories]
        
        # Create comprehensive channel structure
        for category_name, channels in CATEGORIES.items():
            category = get(guild.categories, name=category_name)
            if category_name not in existing_categories:
                category = await guild.create_category(category_name)
                print(f"📁 Created category: {category_name}")
            
            for channel_data in channels:
                if isinstance(channel_data, dict):
                    channel_name = channel_data['name']
                    channel_type = channel_data.get('type', 'text')
                    overwrites = channel_data.get('overwrites', {})
                else:
                    channel_name = channel_data
                    channel_type = 'text'
                    overwrites = {}
                
                if channel_name not in existing_channels:
                    # Convert overwrites to Discord.py format
                    permission_overwrites = {}
                    for role_name, perms in overwrites.items():
                        if role_name == '@everyone':
                            role = guild.default_role
                        else:
                            role = get(guild.roles, name=role_name)
                            if not role:
                                role = await guild.create_role(name=role_name)
                        
                        overwrite = discord.PermissionOverwrite(**perms)
                        permission_overwrites[role] = overwrite
                    
                    if channel_type == 'voice':
                        await guild.create_voice_channel(
                            channel_name, 
                            category=category,
                            overwrites=permission_overwrites
                        )
                    else:
                        channel = await guild.create_text_channel(
                            channel_name, 
                            category=category,
                            overwrites=permission_overwrites
                        )
                        
                        # Setup special channels
                        if channel_name == 'rules':
                            await self.setup_rules_channel(channel)
                        elif channel_name == 'reaction-roles':
                            await self.setup_reaction_roles(channel)
                    
                    print(f"📺 Created {channel_type} channel: {channel_name}")
        
        # Create essential roles
        await self.create_essential_roles(guild)
        
        # Setup auto-moderation
        await self.setup_automod(guild)

    async def create_essential_roles(self, guild):
        """Create essential server roles"""
        essential_roles = [
            {'name': 'Owner', 'color': 0xFF0000, 'permissions': discord.Permissions.all()},
            {'name': 'Admin', 'color': 0xFF4500, 'permissions': discord.Permissions.all()},
            {'name': 'Moderator', 'color': 0x00FF00, 'permissions': discord.Permissions(
                kick_members=True, ban_members=True, manage_messages=True, 
                mute_members=True, deafen_members=True, move_members=True
            )},
            {'name': 'Helper', 'color': 0x0099FF, 'permissions': discord.Permissions(
                manage_messages=True, mute_members=True
            )},
            {'name': 'VIP', 'color': 0xFFD700, 'permissions': discord.Permissions(
                create_instant_invite=True, change_nickname=True, use_external_emojis=True
            )},
            {'name': 'Member', 'color': 0x808080, 'permissions': discord.Permissions(
                read_messages=True, send_messages=True, connect=True, speak=True
            )},
            {'name': 'Muted', 'color': 0x2F3136, 'permissions': discord.Permissions(
                read_messages=True, connect=True
            )}
        ]
        
        for role_data in essential_roles:
            role = get(guild.roles, name=role_data['name'])
            if not role:
                role = await guild.create_role(
                    name=role_data['name'],
                    color=role_data['color'],
                    permissions=role_data['permissions']
                )
                print(f"👑 Created role: {role_data['name']}")

    async def setup_rules_channel(self, channel):
        """Setup rules channel with comprehensive rules"""
        rules = [
            "🔹 **Be Respectful**: Treat all members with kindness and respect",
            "🔹 **No Spam**: Avoid excessive posting, caps lock, or repetitive messages",
            "🔹 **No NSFW Content**: Keep all content appropriate for all ages",
            "🔹 **No Harassment**: Bullying, hate speech, or discrimination is not tolerated",
            "🔹 **Use Appropriate Channels**: Post content in the relevant channels",
            "🔹 **No Self-Promotion**: Don't advertise without permission",
            "🔹 **Follow Discord TOS**: All Discord Terms of Service apply",
            "🔹 **Listen to Staff**: Respect moderator decisions and instructions",
            "🔹 **No Doxxing**: Don't share personal information of others",
            "🔹 **Have Fun**: Enjoy your time in our community!"
        ]
        
        embed = create_embed(
            title="📋 Server Rules",
            description="Please read and follow these rules to maintain a positive community",
            color=0x00FF00
        )
        
        for i, rule in enumerate(rules, 1):
            embed.add_field(name=f"Rule {i}", value=rule, inline=False)
        
        embed.set_footer(text="By staying in this server, you agree to follow these rules")
        
        await channel.send(embed=embed)

    async def setup_reaction_roles(self, channel):
        """Setup reaction roles system"""
        embed = create_embed(
            title="🎭 Reaction Roles",
            description="React to get roles! Click the reactions below to assign yourself roles.",
            color=0x7289DA
        )
        
        role_emojis = {
            "🎮": "Gamer",
            "🎵": "Music Lover",
            "📚": "Bookworm", 
            "🎨": "Artist",
            "💻": "Developer",
            "🏃": "Fitness",
            "🎬": "Movie Buff",
            "📰": "News Updates"
        }
        
        description = ""
        for emoji, role_name in role_emojis.items():
            description += f"{emoji} - {role_name}\n"
        
        embed.add_field(name="Available Roles", value=description, inline=False)
        
        message = await channel.send(embed=embed)
        
        # Add reactions
        for emoji in role_emojis.keys():
            await message.add_reaction(emoji)
        
        # Store in database
        await self.db.add_reaction_role_message(channel.guild.id, message.id, role_emojis)

    async def setup_automod(self, guild):
        """Setup automatic moderation"""
        # This would be expanded with actual automod rules
        await self.db.update_server_settings(guild.id, {'automod_enabled': True})

    async def on_member_join(self, member):
        """Enhanced member join handler"""
        guild = member.guild
        
        # Add default role
        default_role = get(guild.roles, name="Member")
        if default_role:
            await member.add_roles(default_role)
        
        # Send welcome message
        welcome_channel = get(guild.text_channels, name="welcome")
        if welcome_channel:
            embed = create_embed(
                title=f"Welcome to {guild.name}! 🎉",
                description=f"Hey {member.mention}, we're glad you're here!",
                color=0x00FF00
            )
            embed.add_field(
                name="Getting Started", 
                value="• Check out <#rules> for server rules\n• Introduce yourself in <#introductions>\n• Get roles in <#reaction-roles>", 
                inline=False
            )
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            embed.set_footer(text=f"You are member #{guild.member_count}")
            
            await welcome_channel.send(embed=embed)
        
        # Log join
        log_channel = get(guild.text_channels, name="member-logs")
        if log_channel:
            embed = create_embed(
                title="Member Joined",
                description=f"{member.mention} ({member}) joined the server",
                color=0x00FF00
            )
            embed.add_field(name="Account Created", value=format_time(member.created_at), inline=True)
            embed.add_field(name="Member Count", value=str(guild.member_count), inline=True)
            await log_channel.send(embed=embed)

    async def on_member_remove(self, member):
        """Handle member leaving"""
        guild = member.guild
        log_channel = get(guild.text_channels, name="member-logs")
        if log_channel:
            embed = create_embed(
                title="Member Left",
                description=f"{member} left the server",
                color=0xFF0000
            )
            embed.add_field(name="Joined", value=format_time(member.joined_at), inline=True)
            embed.add_field(name="Member Count", value=str(guild.member_count), inline=True)
            await log_channel.send(embed=embed)

    async def on_raw_reaction_add(self, payload):
        """Handle reaction role assignment"""
        if payload.user_id == self.user.id:
            return
        
        reaction_roles = await self.db.get_reaction_roles(payload.guild_id, payload.message_id)
        if not reaction_roles:
            return
        
        emoji = str(payload.emoji)
        if emoji not in reaction_roles:
            return
        
        guild = self.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        role = get(guild.roles, name=reaction_roles[emoji])
        
        if role and member:
            await member.add_roles(role)

    async def on_raw_reaction_remove(self, payload):
        """Handle reaction role removal"""
        if payload.user_id == self.user.id:
            return
        
        reaction_roles = await self.db.get_reaction_roles(payload.guild_id, payload.message_id)
        if not reaction_roles:
            return
        
        emoji = str(payload.emoji)
        if emoji not in reaction_roles:
            return
        
        guild = self.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        role = get(guild.roles, name=reaction_roles[emoji])
        
        if role and member:
            await member.remove_roles(role)

    async def on_message(self, message):
        """Enhanced message handler"""
        if message.author.bot:
            return
        
        # XP system
        if not message.content.startswith(await get_prefix(self, message)):
            await self.db.add_xp(message.guild.id, message.author.id, random.randint(15, 25))
        
        # Auto-responses
        content = message.content.lower()
        if any(word in content for word in ['hello', 'hi', 'hey']):
            if random.randint(1, 10) == 1:  # 10% chance
                await message.add_reaction('👋')
        
        await self.process_commands(message)

    @tasks.loop(hours=24)
    async def daily_tasks(self):
        """Daily automated tasks"""
        for guild in self.guilds:
            # Daily engagement prompts
            general_channel = get(guild.text_channels, name="general-chat")
            if general_channel:
                prompts = [
                    "🎮 What's everyone playing today?",
                    "📸 Share your best screenshot of the week!",
                    "🎯 What are your weekend gaming plans?",
                    "😂 Drop your favorite meme!",
                    "💭 What's your unpopular gaming opinion?",
                    "🏆 What achievement are you most proud of?",
                    "🎵 What music do you listen to while gaming?",
                    "🍕 What's your favorite gaming snack?"
                ]
                
                embed = create_embed(
                    title="Daily Discussion",
                    description=random.choice(prompts),
                    color=0x7289DA
                )
                await general_channel.send(embed=embed)

    @tasks.loop(hours=168)  # Weekly
    async def auto_backup(self):
        """Automatically backup server data"""
        for guild in self.guilds:
            await self.db.backup_server_data(guild.id)

    @tasks.loop(minutes=5)
    async def status_rotation(self):
        """Rotate bot status"""
        statuses = [
            discord.Activity(type=discord.ActivityType.watching, name=f"{len(self.guilds)} servers"),
            discord.Activity(type=discord.ActivityType.listening, name="your commands"),
            discord.Activity(type=discord.ActivityType.playing, name="with Discord.py"),
            discord.Activity(type=discord.ActivityType.competing, name="server management")
        ]
        
        await self.change_presence(activity=random.choice(statuses))

    @commands.command(name='help')
    async def help_command(self, ctx, *, command_name=None):
        """Custom help command"""
        if command_name:
            # Show help for specific command
            command = self.get_command(command_name)
            if command:
                embed = create_embed(
                    title=f"Help: {command.name}",
                    description=command.help or "No description available",
                    color=0x7289DA
                )
                if command.usage:
                    embed.add_field(name="Usage", value=f"`{ctx.prefix}{command.name} {command.usage}`", inline=False)
                if command.aliases:
                    embed.add_field(name="Aliases", value=", ".join(command.aliases), inline=False)
            else:
                embed = create_embed(
                    title="Command Not Found",
                    description=f"No command named '{command_name}' found.",
                    color=0xFF0000
                )
        else:
            # Show general help
            embed = create_embed(
                title="🤖 Bot Commands Help",
                description="Here are all available command categories:",
                color=0x7289DA
            )
            
            cog_commands = {}
            for command in self.commands:
                cog_name = command.cog_name or "General"
                if cog_name not in cog_commands:
                    cog_commands[cog_name] = []
                cog_commands[cog_name].append(command.name)
            
            for cog_name, commands in cog_commands.items():
                embed.add_field(
                    name=f"📂 {cog_name}",
                    value=f"`{', '.join(commands[:5])}{'...' if len(commands) > 5 else ''}`",
                    inline=True
                )
            
            embed.add_field(
                name="💡 Tip",
                value=f"Use `{ctx.prefix}help <command>` for detailed command info",
                inline=False
            )
        
        await ctx.send(embed=embed)

# Create and run bot
bot = ComprehensiveBot()

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        print("❌ DISCORD_TOKEN not found in environment variables!")
        exit(1)
    
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
