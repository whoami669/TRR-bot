import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
from datetime import datetime, timezone

class SlashCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # UTILITY COMMANDS
    @app_commands.command(name="serverinfo", description="Show server information")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(
            title=f"📊 {guild.name}",
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(name="👑 Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="🆔 Server ID", value=guild.id, inline=True)
        embed.add_field(name="📅 Created", value=f"<t:{int(guild.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="👥 Members", value=f"{guild.member_count:,}", inline=True)
        embed.add_field(name="💬 Channels", value=f"{len(guild.channels):,}", inline=True)
        embed.add_field(name="🎭 Roles", value=f"{len(guild.roles):,}", inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="Show user information")
    @app_commands.describe(member="The user to get information about (optional)")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        
        embed = discord.Embed(
            title=f"👤 {target.display_name}",
            color=target.color,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="📛 Username", value=str(target), inline=True)
        embed.add_field(name="🆔 User ID", value=target.id, inline=True)
        embed.add_field(name="📅 Account Created", value=f"<t:{int(target.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="📥 Joined Server", value=f"<t:{int(target.joined_at.timestamp())}:R>", inline=True)
        
        roles = [role.mention for role in target.roles[1:]]
        if roles:
            embed.add_field(name=f"🎭 Roles ({len(roles)})", value=" ".join(roles[:10]), inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ping", description="Check bot latency")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Bot latency: **{latency}ms**",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    # FUN COMMANDS
    @app_commands.command(name="flip", description="Flip a coin")
    async def flip(self, interaction: discord.Interaction):
        result = random.choice(["Heads", "Tails"])
        emoji = "🪙" if result == "Heads" else "🔄"
        embed = discord.Embed(
            title=f"{emoji} Coin Flip",
            description=f"**{result}!**",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="roll", description="Roll a dice")
    @app_commands.describe(sides="Number of sides on the dice (default: 6)")
    async def roll(self, interaction: discord.Interaction, sides: int = 6):
        if sides < 2:
            await interaction.response.send_message("Dice must have at least 2 sides!", ephemeral=True)
            return
        
        result = random.randint(1, sides)
        embed = discord.Embed(
            title="🎲 Dice Roll",
            description=f"You rolled a **{result}** on a {sides}-sided dice!",
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question")
    @app_commands.describe(question="The question you want to ask")
    async def magic_8ball(self, interaction: discord.Interaction, question: str):
        responses = [
            "It is certain", "Reply hazy, try again", "Don't count on it",
            "It is decidedly so", "Ask again later", "My reply is no",
            "Without a doubt", "Better not tell you now", "My sources say no",
            "Yes definitely", "Cannot predict now", "Outlook not so good",
            "You may rely on it", "Concentrate and ask again", "Very doubtful",
            "As I see it, yes", "Most likely", "Outlook good",
            "Yes", "Signs point to yes"
        ]
        
        response = random.choice(responses)
        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            description=f"**Question:** {question}\n**Answer:** {response}",
            color=discord.Color.dark_blue()
        )
        await interaction.response.send_message(embed=embed)

    # MODERATION COMMANDS
    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.describe(member="The member to kick", reason="Reason for the kick")
    @app_commands.default_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("You cannot kick someone with equal or higher roles!", ephemeral=True)
            return
        
        try:
            await member.kick(reason=reason)
            embed = discord.Embed(
                title="👢 Member Kicked",
                description=f"**{member}** has been kicked.\n**Reason:** {reason}",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"Failed to kick member: {e}", ephemeral=True)

    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.describe(member="The member to ban", reason="Reason for the ban")
    @app_commands.default_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("You cannot ban someone with equal or higher roles!", ephemeral=True)
            return
        
        try:
            await member.ban(reason=reason)
            embed = discord.Embed(
                title="🔨 Member Banned",
                description=f"**{member}** has been banned.\n**Reason:** {reason}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"Failed to ban member: {e}", ephemeral=True)

    @app_commands.command(name="clear", description="Clear messages from the channel")
    @app_commands.describe(amount="Number of messages to delete (1-100)")
    @app_commands.default_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        if amount < 1 or amount > 100:
            await interaction.response.send_message("Amount must be between 1 and 100!", ephemeral=True)
            return
        
        try:
            deleted = await interaction.channel.purge(limit=amount)
            embed = discord.Embed(
                title="🧹 Messages Cleared",
                description=f"Deleted **{len(deleted)}** messages.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to clear messages: {e}", ephemeral=True)

    # ECONOMY COMMANDS
    @app_commands.command(name="balance", description="Check your or someone's balance")
    @app_commands.describe(member="The member to check balance for (optional)")
    async def balance(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        balance = await self.bot.db.get_balance(interaction.guild.id, target.id)
        
        embed = discord.Embed(
            title="💰 Balance",
            description=f"**{target.display_name}** has **{balance:,}** coins!",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="daily", description="Claim your daily reward")
    async def daily(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        
        last_daily = await self.bot.db.get_last_daily(guild_id, user_id)
        now = datetime.now(timezone.utc)
        
        if last_daily and (now - last_daily).total_seconds() < 86400:
            time_left = 86400 - (now - last_daily).total_seconds()
            hours = int(time_left // 3600)
            minutes = int((time_left % 3600) // 60)
            await interaction.response.send_message(f"You already claimed your daily reward! Come back in {hours}h {minutes}m", ephemeral=True)
            return
        
        streak = await self.bot.db.get_daily_streak(guild_id, user_id)
        if last_daily and (now - last_daily).days == 1:
            streak += 1
        else:
            streak = 1
        
        base_reward = 100
        streak_bonus = min(streak * 10, 500)
        total_reward = base_reward + streak_bonus
        
        await self.bot.db.add_balance(guild_id, user_id, total_reward)
        await self.bot.db.update_daily_streak(guild_id, user_id, streak)
        
        embed = discord.Embed(
            title="🎁 Daily Reward",
            description=f"You received **{total_reward:,}** coins!\n**Streak:** {streak} days",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    # MUSIC COMMANDS
    @app_commands.command(name="join", description="Join your voice channel")
    async def join(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            await interaction.response.send_message("You need to be in a voice channel!", ephemeral=True)
            return
        
        channel = interaction.user.voice.channel
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.move_to(channel)
        else:
            await channel.connect()
        
        embed = discord.Embed(
            title="🎵 Joined Voice Channel",
            description=f"Connected to **{channel.name}**",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leave", description="Leave the voice channel")
    async def leave(self, interaction: discord.Interaction):
        if not interaction.guild.voice_client:
            await interaction.response.send_message("I'm not connected to a voice channel!", ephemeral=True)
            return
        
        await interaction.guild.voice_client.disconnect()
        embed = discord.Embed(
            title="👋 Left Voice Channel",
            description="Disconnected from voice channel",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(SlashCommands(bot))