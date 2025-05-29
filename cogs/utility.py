import discord
from discord.ext import commands
import asyncio
import json
import random
from datetime import datetime, timezone
from utils.embeds import create_embed
from utils.helpers import format_time

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='serverinfo', aliases=['si'])
    async def server_info(self, ctx):
        """Show server information"""
        guild = ctx.guild
        
        # Count members by status
        online = sum(1 for m in guild.members if m.status != discord.Status.offline)
        total_members = guild.member_count
        bots = sum(1 for m in guild.members if m.bot)
        humans = total_members - bots
        
        # Count channels
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        # Server features
        features = [feature.replace('_', ' ').title() for feature in guild.features]
        
        embed = create_embed(
            title=f"📊 {guild.name} Server Info",
            color=0x7289DA
        )
        
        embed.add_field(name="👑 Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="📅 Created", value=format_time(guild.created_at), inline=True)
        embed.add_field(name="🆔 Server ID", value=str(guild.id), inline=True)
        
        embed.add_field(name="👥 Members", value=f"**Total:** {total_members:,}\n**Humans:** {humans:,}\n**Bots:** {bots:,}\n**Online:** {online:,}", inline=True)
        embed.add_field(name="📺 Channels", value=f"**Text:** {text_channels}\n**Voice:** {voice_channels}\n**Categories:** {categories}", inline=True)
        embed.add_field(name="🎭 Roles", value=str(len(guild.roles)), inline=True)
        
        embed.add_field(name="😀 Emojis", value=f"{len(guild.emojis)}/{guild.emoji_limit}", inline=True)
        embed.add_field(name="🚀 Boosts", value=f"**Level:** {guild.premium_tier}\n**Boosts:** {guild.premium_subscription_count}", inline=True)
        embed.add_field(name="🔒 Verification", value=str(guild.verification_level).title(), inline=True)
        
        if features:
            embed.add_field(name="✨ Features", value="\n".join(features[:5]), inline=False)
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        if guild.banner:
            embed.set_image(url=guild.banner.url)
        
        await ctx.send(embed=embed)

    @commands.command(name='userinfo', aliases=['ui'])
    async def user_info(self, ctx, member: discord.Member = None):
        """Show user information"""
        target = member or ctx.author
        
        # User status and activity
        status_emoji = {
            discord.Status.online: "🟢",
            discord.Status.idle: "🟡", 
            discord.Status.dnd: "🔴",
            discord.Status.offline: "⚫"
        }
        
        embed = create_embed(
            title=f"👤 {target.display_name}",
            description=f"{status_emoji.get(target.status, '⚫')} {str(target.status).title()}",
            color=target.color if target.color != discord.Color.default() else 0x7289DA
        )
        
        embed.add_field(name="🏷️ Username", value=str(target), inline=True)
        embed.add_field(name="🆔 User ID", value=str(target.id), inline=True)
        embed.add_field(name="🤖 Bot", value="Yes" if target.bot else "No", inline=True)
        
        embed.add_field(name="📅 Account Created", value=format_time(target.created_at), inline=True)
        embed.add_field(name="📥 Joined Server", value=format_time(target.joined_at) if target.joined_at else "Unknown", inline=True)
        
        # Calculate join position
        if target.joined_at:
            sorted_members = sorted(ctx.guild.members, key=lambda m: m.joined_at or datetime.min.replace(tzinfo=timezone.utc))
            join_position = sorted_members.index(target) + 1
            embed.add_field(name="📍 Join Position", value=f"#{join_position:,}", inline=True)
        
        # Roles (excluding @everyone)
        roles = [role.mention for role in target.roles[1:]]
        if roles:
            embed.add_field(name=f"🎭 Roles ({len(roles)})", value=" ".join(roles[:10]) + (f" +{len(roles)-10} more" if len(roles) > 10 else ""), inline=False)
        
        # User activity
        if target.activity:
            activity_type = {
                discord.ActivityType.playing: "🎮 Playing",
                discord.ActivityType.streaming: "📺 Streaming", 
                discord.ActivityType.listening: "🎵 Listening to",
                discord.ActivityType.watching: "👀 Watching",
                discord.ActivityType.competing: "🏆 Competing in"
            }
            embed.add_field(name="🎯 Activity", value=f"{activity_type.get(target.activity.type, '❓')} {target.activity.name}", inline=False)
        
        # User permissions
        key_perms = []
        if target.guild_permissions.administrator:
            key_perms.append("Administrator")
        elif target.guild_permissions.manage_guild:
            key_perms.append("Manage Server")
        elif target.guild_permissions.manage_messages:
            key_perms.append("Manage Messages")
        elif target.guild_permissions.kick_members:
            key_perms.append("Kick Members")
        elif target.guild_permissions.ban_members:
            key_perms.append("Ban Members")
        
        if key_perms:
            embed.add_field(name="🔑 Key Permissions", value=", ".join(key_perms), inline=False)
        
        embed.set_thumbnail(url=target.avatar.url if target.avatar else target.default_avatar.url)
        
        await ctx.send(embed=embed)

    @commands.command(name='avatar', aliases=['av'])
    async def show_avatar(self, ctx, member: discord.Member = None):
        """Show user's avatar"""
        target = member or ctx.author
        
        embed = create_embed(
            title=f"🖼️ {target.display_name}'s Avatar",
            color=target.color if target.color != discord.Color.default() else 0x7289DA
        )
        
        avatar_url = target.avatar.url if target.avatar else target.default_avatar.url
        embed.set_image(url=avatar_url)
        embed.add_field(name="🔗 Direct Link", value=f"[Click Here]({avatar_url})", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name='roleinfo', aliases=['ri'])
    async def role_info(self, ctx, *, role: discord.Role):
        """Show role information"""
        embed = create_embed(
            title=f"🎭 Role: {role.name}",
            color=role.color if role.color != discord.Color.default() else 0x7289DA
        )
        
        embed.add_field(name="🆔 Role ID", value=str(role.id), inline=True)
        embed.add_field(name="🎨 Color", value=str(role.color), inline=True)
        embed.add_field(name="📍 Position", value=str(role.position), inline=True)
        
        embed.add_field(name="👥 Members", value=str(len(role.members)), inline=True)
        embed.add_field(name="📅 Created", value=format_time(role.created_at), inline=True)
        embed.add_field(name="🔗 Mentionable", value="Yes" if role.mentionable else "No", inline=True)
        
        embed.add_field(name="🎯 Hoisted", value="Yes" if role.hoist else "No", inline=True)
        embed.add_field(name="🤖 Managed", value="Yes" if role.managed else "No", inline=True)
        embed.add_field(name="🔒 Permissions", value=str(len([perm for perm, value in role.permissions if value])), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name='channelinfo', aliases=['ci'])
    async def channel_info(self, ctx, channel: discord.TextChannel = None):
        """Show channel information"""
        target = channel or ctx.channel
        
        embed = create_embed(
            title=f"📺 Channel: {target.name}",
            color=0x7289DA
        )
        
        embed.add_field(name="🆔 Channel ID", value=str(target.id), inline=True)
        embed.add_field(name="📂 Category", value=target.category.name if target.category else "None", inline=True)
        embed.add_field(name="📍 Position", value=str(target.position), inline=True)
        
        embed.add_field(name="📅 Created", value=format_time(target.created_at), inline=True)
        embed.add_field(name="🔒 NSFW", value="Yes" if target.nsfw else "No", inline=True)
        embed.add_field(name="📰 News", value="Yes" if target.is_news() else "No", inline=True)
        
        if target.slowmode_delay:
            embed.add_field(name="🐌 Slowmode", value=f"{target.slowmode_delay}s", inline=True)
        
        if target.topic:
            embed.add_field(name="📝 Topic", value=target.topic[:100] + ("..." if len(target.topic) > 100 else ""), inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name='ping')
    async def ping(self, ctx):
        """Show bot latency"""
        embed = create_embed(
            title="🏓 Pong!",
            description=f"Bot latency: **{round(self.bot.latency * 1000)}ms**",
            color=0x00FF00
        )
        await ctx.send(embed=embed)

    @commands.command(name='uptime')
    async def uptime(self, ctx):
        """Show bot uptime"""
        uptime = datetime.utcnow() - self.bot.start_time
        
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        embed = create_embed(
            title="⏰ Bot Uptime",
            description=f"**{days}d {hours}h {minutes}m {seconds}s**",
            color=0x7289DA
        )
        await ctx.send(embed=embed)

    @commands.command(name='invite')
    async def invite_bot(self, ctx):
        """Get bot invite link"""
        permissions = discord.Permissions(
            read_messages=True,
            send_messages=True,
            manage_messages=True,
            manage_roles=True,
            kick_members=True,
            ban_members=True,
            manage_channels=True,
            connect=True,
            speak=True,
            use_voice_activation=True
        )
        
        invite_url = discord.utils.oauth_url(self.bot.user.id, permissions=permissions)
        
        embed = create_embed(
            title="🤖 Invite Me!",
            description=f"[Click here to invite me to your server!]({invite_url})",
            color=0x7289DA
        )
        embed.add_field(name="🔗 Direct Link", value=invite_url, inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name='suggest')
    async def suggestion(self, ctx, *, suggestion):
        """Make a suggestion"""
        suggestions_channel = discord.utils.get(ctx.guild.text_channels, name="suggestions")
        
        if not suggestions_channel:
            return await ctx.send("❌ No suggestions channel found!")
        
        embed = create_embed(
            title="💡 New Suggestion",
            description=suggestion,
            color=0xFFD700
        )
        embed.add_field(name="Suggested by", value=ctx.author.mention, inline=True)
        embed.add_field(name="Channel", value=ctx.channel.mention, inline=True)
        embed.set_footer(text=f"Suggestion ID: {ctx.message.id}")
        embed.timestamp = datetime.utcnow()
        
        suggestion_msg = await suggestions_channel.send(embed=embed)
        await suggestion_msg.add_reaction("👍")
        await suggestion_msg.add_reaction("👎")
        
        await ctx.send("✅ Your suggestion has been submitted!")

    @commands.command(name='poll')
    async def create_poll(self, ctx, *, question):
        """Create a simple yes/no poll"""
        embed = create_embed(
            title="📊 Poll",
            description=question,
            color=0x7289DA
        )
        embed.add_field(name="Options", value="👍 Yes\n👎 No", inline=False)
        embed.set_footer(text=f"Poll by {ctx.author.display_name}")
        
        poll_msg = await ctx.send(embed=embed)
        await poll_msg.add_reaction("👍")
        await poll_msg.add_reaction("👎")

    @commands.command(name='multipoll')
    async def create_multipoll(self, ctx, question, *options):
        """Create a poll with multiple options (max 10)"""
        if len(options) < 2:
            return await ctx.send("❌ You need at least 2 options!")
        
        if len(options) > 10:
            return await ctx.send("❌ Maximum 10 options allowed!")
        
        emoji_numbers = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        embed = create_embed(
            title="📊 Poll",
            description=question,
            color=0x7289DA
        )
        
        options_text = ""
        for i, option in enumerate(options):
            options_text += f"{emoji_numbers[i]} {option}\n"
        
        embed.add_field(name="Options", value=options_text, inline=False)
        embed.set_footer(text=f"Poll by {ctx.author.display_name}")
        
        poll_msg = await ctx.send(embed=embed)
        
        for i in range(len(options)):
            await poll_msg.add_reaction(emoji_numbers[i])

    @commands.command(name='reminder', aliases=['remindme'])
    async def set_reminder(self, ctx, time, *, reminder):
        """Set a reminder (e.g., 10m, 1h, 2d)"""
        time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        
        if time[-1].lower() not in time_units:
            return await ctx.send("❌ Invalid time format! Use s/m/h/d (e.g., 10m, 1h, 2d)")
        
        try:
            amount = int(time[:-1])
            unit = time[-1].lower()
            seconds = amount * time_units[unit]
        except ValueError:
            return await ctx.send("❌ Invalid time format!")
        
        if seconds > 604800:  # 7 days
            return await ctx.send("❌ Maximum reminder time is 7 days!")
        
        embed = create_embed(
            title="⏰ Reminder Set",
            description=f"I'll remind you in {amount}{unit}: {reminder}",
            color=0x00FF00
        )
        await ctx.send(embed=embed)
        
        await asyncio.sleep(seconds)
        
        remind_embed = create_embed(
            title="⏰ Reminder",
            description=reminder,
            color=0xFFD700
        )
        remind_embed.add_field(name="Set", value=f"{amount}{unit} ago", inline=True)
        
        try:
            await ctx.author.send(embed=remind_embed)
        except discord.Forbidden:
            await ctx.send(f"{ctx.author.mention}", embed=remind_embed)

    @commands.command(name='choose')
    async def choose_option(self, ctx, *choices):
        """Choose randomly from given options"""
        if len(choices) < 2:
            return await ctx.send("❌ I need at least 2 choices!")
        
        choice = random.choice(choices)
        
        embed = create_embed(
            title="🎲 Random Choice",
            description=f"I choose: **{choice}**",
            color=0x7289DA
        )
        embed.add_field(name="Options", value=", ".join(choices), inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name='8ball')
    async def magic_8ball(self, ctx, *, question):
        """Ask the magic 8-ball a question"""
        responses = [
            "It is certain", "Reply hazy, try again", "Don't count on it",
            "It is decidedly so", "Ask again later", "My reply is no",
            "Without a doubt", "Better not tell you now", "My sources say no",
            "Yes definitely", "Cannot predict now", "Outlook not so good",
            "You may rely on it", "Concentrate and ask again", "Very doubtful",
            "As I see it, yes", "Most likely", "Outlook good", "Yes",
            "Signs point to yes"
        ]
        
        answer = random.choice(responses)
        
        embed = create_embed(
            title="🎱 Magic 8-Ball",
            color=0x7289DA
        )
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=answer, inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot))
