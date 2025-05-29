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

    # MORE FUN COMMANDS
    @app_commands.command(name="joke", description="Get a random joke")
    async def joke(self, interaction: discord.Interaction):
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the scarecrow win an award? He was outstanding in his field!",
            "Why don't eggs tell jokes? They'd crack each other up!",
            "What do you call a fake noodle? An impasta!",
            "Why did the math book look so sad? Because it had too many problems!",
            "What do you call a bear with no teeth? A gummy bear!",
            "Why can't a bicycle stand up by itself? It's two tired!",
            "What do you call a sleeping bull? A bulldozer!",
            "Why did the coffee file a police report? It got mugged!",
            "What's orange and sounds like a parrot? A carrot!"
        ]
        
        joke = random.choice(jokes)
        embed = discord.Embed(
            title="😂 Random Joke",
            description=joke,
            color=discord.Color.yellow()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="fact", description="Get a random fun fact")
    async def fact(self, interaction: discord.Interaction):
        facts = [
            "Honey never spoils. Archaeologists have found edible honey in ancient Egyptian tombs!",
            "A group of flamingos is called a 'flamboyance'.",
            "Bananas are berries, but strawberries aren't!",
            "The shortest war in history lasted only 38-45 minutes.",
            "Octopuses have three hearts and blue blood.",
            "A shrimp's heart is in its head.",
            "It's impossible to hum while holding your nose closed.",
            "The human brain uses about 20% of the body's total energy.",
            "There are more possible chess games than atoms in the observable universe.",
            "A day on Venus is longer than its year!"
        ]
        
        fact = random.choice(facts)
        embed = discord.Embed(
            title="🤓 Fun Fact",
            description=fact,
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="compliment", description="Give someone a compliment")
    @app_commands.describe(member="The person to compliment (optional)")
    async def compliment(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        compliments = [
            "You're absolutely amazing!", "You have great taste!", "You're incredibly thoughtful!",
            "You light up the room!", "You're one of a kind!", "You're absolutely wonderful!",
            "You have the best laugh!", "You're so creative!", "You're super smart!",
            "You're really awesome!", "You make everyone around you happier!", "You're fantastic!"
        ]
        
        compliment = random.choice(compliments)
        embed = discord.Embed(
            title="💝 Compliment",
            description=f"{target.mention}, {compliment}",
            color=discord.Color.pink()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="meme", description="Get a random meme (requires internet)")
    async def meme(self, interaction: discord.Interaction):
        # Simple fallback memes
        memes = [
            "```\n    Wow\n        Such Discord\n             Very Bot\n                  Much Commands\n```",
            "```\nMe: I'll just check Discord for 5 minutes\n*3 hours later*\nMe: What year is it?\n```",
            "```\nDiscord notifications at 3 AM:\n'Someone is typing...'\nMe: 👁👄👁\n```"
        ]
        
        meme = random.choice(memes)
        embed = discord.Embed(
            title="😂 Random Meme",
            description=meme,
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ship", description="Ship two users together")
    @app_commands.describe(user1="First person", user2="Second person")
    async def ship(self, interaction: discord.Interaction, user1: discord.Member, user2: discord.Member):
        compatibility = random.randint(0, 100)
        
        if compatibility >= 90:
            result = "💕 Perfect Match!"
        elif compatibility >= 70:
            result = "💖 Great Match!"
        elif compatibility >= 50:
            result = "💗 Good Match!"
        elif compatibility >= 30:
            result = "💙 Okay Match"
        else:
            result = "💔 Not Meant To Be"
        
        ship_name = user1.display_name[:3] + user2.display_name[-3:]
        
        embed = discord.Embed(
            title="💘 Love Calculator",
            description=f"**{user1.display_name}** + **{user2.display_name}** = **{ship_name}**\n\n**Compatibility:** {compatibility}%\n**Result:** {result}",
            color=discord.Color.magenta()
        )
        await interaction.response.send_message(embed=embed)

    # MORE UTILITY COMMANDS
    @app_commands.command(name="avatar", description="Show someone's avatar")
    @app_commands.describe(member="The user to show avatar for (optional)")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        
        embed = discord.Embed(
            title=f"🖼️ {target.display_name}'s Avatar",
            color=target.color
        )
        embed.set_image(url=target.display_avatar.url)
        embed.add_field(name="Direct Link", value=f"[Click here]({target.display_avatar.url})", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="poll", description="Create a simple yes/no poll")
    @app_commands.describe(question="The poll question")
    async def poll(self, interaction: discord.Interaction, question: str):
        embed = discord.Embed(
            title="📊 Poll",
            description=question,
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Poll created by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction("✅")
        await message.add_reaction("❌")

    @app_commands.command(name="choose", description="Choose randomly from options")
    @app_commands.describe(options="Choices separated by commas (e.g., pizza, burgers, tacos)")
    async def choose(self, interaction: discord.Interaction, options: str):
        choices = [choice.strip() for choice in options.split(",")]
        if len(choices) < 2:
            await interaction.response.send_message("Please provide at least 2 options separated by commas!", ephemeral=True)
            return
        
        choice = random.choice(choices)
        embed = discord.Embed(
            title="🎯 Random Choice",
            description=f"I choose: **{choice}**",
            color=discord.Color.orange()
        )
        embed.add_field(name="Options", value=", ".join(choices), inline=False)
        await interaction.response.send_message(embed=embed)

    # MORE ECONOMY COMMANDS
    @app_commands.command(name="work", description="Work to earn coins")
    async def work(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        
        last_work = await self.bot.db.get_last_work(guild_id, user_id)
        now = datetime.now(timezone.utc)
        
        if last_work and (now - last_work).total_seconds() < 3600:  # 1 hour cooldown
            time_left = 3600 - (now - last_work).total_seconds()
            minutes = int(time_left // 60)
            await interaction.response.send_message(f"You need to wait {minutes} more minutes before working again!", ephemeral=True)
            return
        
        jobs = [
            ("delivery driver", 50, 150),
            ("cashier", 40, 120),
            ("programmer", 80, 200),
            ("janitor", 30, 100),
            ("teacher", 60, 180),
            ("chef", 70, 190)
        ]
        
        job, min_pay, max_pay = random.choice(jobs)
        earnings = random.randint(min_pay, max_pay)
        
        await self.bot.db.add_balance(guild_id, user_id, earnings)
        await self.bot.db.update_last_work(guild_id, user_id)
        
        embed = discord.Embed(
            title="💼 Work Complete",
            description=f"You worked as a **{job}** and earned **{earnings:,}** coins!",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="gamble", description="Gamble your coins")
    @app_commands.describe(amount="Amount to gamble")
    async def gamble(self, interaction: discord.Interaction, amount: int):
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        
        if amount < 10:
            await interaction.response.send_message("Minimum bet is 10 coins!", ephemeral=True)
            return
        
        balance = await self.bot.db.get_balance(guild_id, user_id)
        if balance < amount:
            await interaction.response.send_message("You don't have enough coins!", ephemeral=True)
            return
        
        win_chance = 45  # 45% chance to win
        if random.randint(1, 100) <= win_chance:
            winnings = int(amount * 1.8)
            await self.bot.db.add_balance(guild_id, user_id, winnings - amount)
            
            embed = discord.Embed(
                title="🎰 Gambling Result",
                description=f"🎉 **You won!**\nYou bet {amount:,} coins and won {winnings:,} coins!\nProfit: {winnings - amount:,} coins",
                color=discord.Color.green()
            )
        else:
            await self.bot.db.remove_balance(guild_id, user_id, amount)
            
            embed = discord.Embed(
                title="🎰 Gambling Result",
                description=f"💸 **You lost!**\nYou lost {amount:,} coins. Better luck next time!",
                color=discord.Color.red()
            )
        
        new_balance = await self.bot.db.get_balance(guild_id, user_id)
        embed.add_field(name="New Balance", value=f"{new_balance:,} coins", inline=False)
        await interaction.response.send_message(embed=embed)

    # LEVELING COMMANDS
    @app_commands.command(name="rank", description="Check your or someone's rank")
    @app_commands.describe(member="The member to check rank for (optional)")
    async def rank(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        stats = await self.bot.db.get_user_stats(interaction.guild.id, target.id)
        
        if not stats:
            await interaction.response.send_message("No rank data found for this user!", ephemeral=True)
            return
        
        xp, level = stats
        rank = await self.bot.db.get_user_rank(interaction.guild.id, target.id)
        
        embed = discord.Embed(
            title=f"📊 {target.display_name}'s Rank",
            color=target.color
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Level", value=f"**{level}**", inline=True)
        embed.add_field(name="XP", value=f"**{xp:,}**", inline=True)
        embed.add_field(name="Rank", value=f"**#{rank}**", inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="Show the server leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        top_users = await self.bot.db.get_top_users(interaction.guild.id, 10)
        
        if not top_users:
            await interaction.response.send_message("No leaderboard data available!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🏆 Server Leaderboard",
            color=discord.Color.gold()
        )
        
        for i, (user_id, xp, level) in enumerate(top_users):
            user = interaction.guild.get_member(user_id)
            if user:
                rank_emoji = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}."
                embed.add_field(
                    name=f"{rank_emoji} {user.display_name}",
                    value=f"Level {level} • {xp:,} XP",
                    inline=False
                )
        
        await interaction.response.send_message(embed=embed)

    # MORE MODERATION COMMANDS
    @app_commands.command(name="timeout", description="Timeout a member")
    @app_commands.describe(member="The member to timeout", duration="Duration in minutes", reason="Reason for timeout")
    @app_commands.default_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = "No reason provided"):
        if duration < 1 or duration > 10080:  # Max 7 days
            await interaction.response.send_message("Duration must be between 1 minute and 7 days (10080 minutes)!", ephemeral=True)
            return
        
        try:
            await member.timeout(discord.utils.utcnow() + discord.timedelta(minutes=duration), reason=reason)
            embed = discord.Embed(
                title="⏱️ Member Timed Out",
                description=f"**{member}** has been timed out for {duration} minutes.\n**Reason:** {reason}",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"Failed to timeout member: {e}", ephemeral=True)

    @app_commands.command(name="warn", description="Warn a member")
    @app_commands.describe(member="The member to warn", reason="Reason for the warning")
    @app_commands.default_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        await self.bot.db.add_warning(interaction.guild.id, member.id, interaction.user.id, reason)
        
        embed = discord.Embed(
            title="⚠️ Warning Issued",
            description=f"**{member}** has been warned.\n**Reason:** {reason}",
            color=discord.Color.yellow()
        )
        await interaction.response.send_message(embed=embed)
        
        try:
            await member.send(f"You have been warned in **{interaction.guild.name}** for: {reason}")
        except:
            pass

    # GAMING COMMANDS
    @app_commands.command(name="trivia", description="Get a gaming trivia question")
    async def gaming_trivia(self, interaction: discord.Interaction):
        trivia_questions = [
            {
                "question": "What year was the original Super Mario Bros. released?",
                "answer": "1985",
                "options": ["1983", "1985", "1987", "1989"]
            },
            {
                "question": "Which game popularized the battle royale genre?",
                "answer": "PlayerUnknown's Battlegrounds (PUBG)",
                "options": ["Fortnite", "Apex Legends", "PUBG", "H1Z1"]
            },
            {
                "question": "What is the best-selling video game of all time?",
                "answer": "Minecraft",
                "options": ["Tetris", "Minecraft", "GTA V", "Fortnite"]
            },
            {
                "question": "Which company developed the Witcher series?",
                "answer": "CD Projekt Red",
                "options": ["Bethesda", "CD Projekt Red", "BioWare", "Ubisoft"]
            },
            {
                "question": "In League of Legends, what does 'ADC' stand for?",
                "answer": "Attack Damage Carry",
                "options": ["Attack Damage Carry", "Auto Defense Core", "Advanced Damage Control", "Area Damage Command"]
            },
            {
                "question": "What is the maximum level in Minecraft without commands?",
                "answer": "There is no maximum level",
                "options": ["50", "100", "999", "No maximum"]
            },
            {
                "question": "Which game features the character Master Chief?",
                "answer": "Halo",
                "options": ["Call of Duty", "Halo", "Destiny", "Titanfall"]
            },
            {
                "question": "What does 'FPS' stand for in gaming?",
                "answer": "First Person Shooter (or Frames Per Second)",
                "options": ["Fast Player Sync", "First Person Shooter", "Full Power System", "Final Player Score"]
            }
        ]
        
        question_data = random.choice(trivia_questions)
        embed = discord.Embed(
            title="🎮 Gaming Trivia",
            description=f"**Question:** {question_data['question']}\n\n**Options:**\n" + 
                       "\n".join([f"• {option}" for option in question_data['options']]),
            color=discord.Color.purple()
        )
        embed.add_field(name="💡 Answer", value=f"||{question_data['answer']}||", inline=False)
        embed.set_footer(text="Click the spoiler to reveal the answer!")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="gamesuggestion", description="Get a random game suggestion")
    async def game_suggestion(self, interaction: discord.Interaction):
        games = [
            {"name": "The Witcher 3: Wild Hunt", "genre": "RPG", "platform": "PC, Console"},
            {"name": "Among Us", "genre": "Social Deduction", "platform": "PC, Mobile"},
            {"name": "Minecraft", "genre": "Sandbox", "platform": "All Platforms"},
            {"name": "Valorant", "genre": "FPS", "platform": "PC"},
            {"name": "Fall Guys", "genre": "Party", "platform": "PC, Console"},
            {"name": "Rocket League", "genre": "Sports", "platform": "PC, Console"},
            {"name": "Apex Legends", "genre": "Battle Royale", "platform": "PC, Console"},
            {"name": "Genshin Impact", "genre": "Action RPG", "platform": "PC, Mobile, Console"},
            {"name": "Stardew Valley", "genre": "Simulation", "platform": "All Platforms"},
            {"name": "Hollow Knight", "genre": "Metroidvania", "platform": "PC, Console"}
        ]
        
        game = random.choice(games)
        embed = discord.Embed(
            title="🎲 Game Suggestion",
            description=f"**{game['name']}**",
            color=discord.Color.blue()
        )
        embed.add_field(name="Genre", value=game['genre'], inline=True)
        embed.add_field(name="Platform", value=game['platform'], inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setuproles", description="Setup new custom roles for the server")
    @app_commands.default_permissions(administrator=True)
    async def setup_roles(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        # Define new role structure
        new_roles = [
            {"name": "🔥 A-Team", "color": 0xff0000, "permissions": discord.Permissions.all()},  # Admin
            {"name": "⭐ Founder", "color": 0xffd700, "permissions": discord.Permissions(administrator=True)},  # Co-owner
            {"name": "🎯 President", "color": 0x00ff00, "permissions": discord.Permissions(kick_members=True, ban_members=True, manage_messages=True, manage_channels=True)},  # Mod
            {"name": "🛡️ Guardian", "color": 0x0099ff, "permissions": discord.Permissions(kick_members=True, manage_messages=True)},  # Helper
            {"name": "💎 Elite", "color": 0x9932cc, "permissions": discord.Permissions.none()},  # VIP
            {"name": "🎮 Gamer", "color": 0xff6600, "permissions": discord.Permissions.none()},  # Regular
            {"name": "🌟 Member", "color": 0x808080, "permissions": discord.Permissions.none()},  # Basic
            {"name": "🤖 Bot", "color": 0x36393f, "permissions": discord.Permissions.none()},  # Bot role
        ]
        
        guild = interaction.guild
        created_roles = []
        
        try:
            # Remove old default roles (except @everyone and existing bots)
            roles_to_remove = []
            for role in guild.roles:
                if role.name.lower() in ['member', 'vip', 'moderator', 'admin'] and not role.managed:
                    roles_to_remove.append(role)
            
            for role in roles_to_remove:
                try:
                    await role.delete()
                except:
                    pass
            
            # Create new roles
            for role_data in new_roles:
                try:
                    new_role = await guild.create_role(
                        name=role_data["name"],
                        color=discord.Color(role_data["color"]),
                        permissions=role_data["permissions"],
                        mentionable=True
                    )
                    created_roles.append(new_role.name)
                except Exception as e:
                    print(f"Failed to create role {role_data['name']}: {e}")
            
            embed = discord.Embed(
                title="🎭 Roles Setup Complete",
                description="Successfully created new custom roles!",
                color=discord.Color.green()
            )
            
            if created_roles:
                embed.add_field(
                    name="Created Roles",
                    value="\n".join(created_roles),
                    inline=False
                )
            
            embed.add_field(
                name="Role Hierarchy",
                value="🔥 A-Team (Admin)\n⭐ Founder (Co-owner)\n🎯 President (Mod)\n🛡️ Guardian (Helper)\n💎 Elite (VIP)\n🎮 Gamer (Regular)\n🌟 Member (Basic)",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Setup Failed",
                description=f"Failed to setup roles: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(SlashCommands(bot))