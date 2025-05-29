import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import random
import asyncio
from datetime import datetime, timezone
from typing import Optional

class SocialFeatures(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ship", description="Ship two users together")
    @app_commands.describe(user1="First person", user2="Second person")
    async def ship_users(self, interaction: discord.Interaction, 
                        user1: discord.Member, user2: discord.Member):
        
        # Calculate compatibility based on user IDs for consistency
        combined_id = user1.id + user2.id
        compatibility = (combined_id % 100) + 1
        
        ship_name = user1.display_name[:len(user1.display_name)//2] + user2.display_name[len(user2.display_name)//2:]
        
        if compatibility >= 90:
            result = "💕 Perfect Match!"
            color = discord.Color.magenta()
        elif compatibility >= 70:
            result = "💖 Great Match!"
            color = discord.Color.red()
        elif compatibility >= 50:
            result = "💗 Good Match!"
            color = discord.Color.pink()
        elif compatibility >= 30:
            result = "💙 Okay Match"
            color = discord.Color.blue()
        else:
            result = "💔 Not Meant To Be"
            color = discord.Color.dark_gray()
        
        embed = discord.Embed(
            title="💘 Love Calculator",
            description=f"**{user1.display_name}** + **{user2.display_name}** = **{ship_name}**",
            color=color
        )
        embed.add_field(name="Compatibility", value=f"{compatibility}%", inline=True)
        embed.add_field(name="Result", value=result, inline=True)
        
        # Add fun compatibility bar
        filled = "💖" * (compatibility // 10)
        empty = "🤍" * (10 - (compatibility // 10))
        embed.add_field(name="Compatibility Bar", value=filled + empty, inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="compliment", description="Give someone a compliment")
    @app_commands.describe(user="Person to compliment")
    async def give_compliment(self, interaction: discord.Interaction, 
                             user: discord.Member = None):
        target = user or interaction.user
        
        compliments = [
            "You're absolutely amazing!", "You have great taste!", "You're incredibly thoughtful!",
            "You light up the room!", "You're one of a kind!", "You're absolutely wonderful!",
            "You have the best laugh!", "You're so creative!", "You're super smart!",
            "You're really awesome!", "You make everyone around you happier!", "You're fantastic!",
            "You're an inspiration!", "You're incredibly talented!", "You have such a kind heart!",
            "You're so funny!", "You're genuinely amazing!", "You're a ray of sunshine!",
            "You're so positive!", "You're incredibly wise!", "You make the world better!"
        ]
        
        compliment = random.choice(compliments)
        
        embed = discord.Embed(
            title="💝 Compliment",
            description=f"{target.mention}, {compliment}",
            color=discord.Color.pink()
        )
        embed.set_footer(text=f"From {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="hug", description="Give someone a virtual hug")
    @app_commands.describe(user="Person to hug")
    async def virtual_hug(self, interaction: discord.Interaction, user: discord.Member):
        
        hug_gifs = [
            "https://tenor.com/view/hug-bear-gif-7576777",
            "https://tenor.com/view/anime-hug-gif-9200932",
            "https://tenor.com/view/group-hug-gif-12408194"
        ]
        
        embed = discord.Embed(
            title="🤗 Virtual Hug",
            description=f"**{interaction.user.display_name}** gave **{user.display_name}** a big warm hug!",
            color=discord.Color.gold()
        )
        
        # Store hug in database
        async with aiosqlite.connect('ultrabot.db') as db:
            await db.execute('''
                INSERT OR IGNORE INTO users (user_id, guild_id) VALUES (?, ?)
            ''', (user.id, interaction.guild.id))
            await db.execute('''
                INSERT OR IGNORE INTO users (user_id, guild_id) VALUES (?, ?)
            ''', (interaction.user.id, interaction.guild.id))
            await db.commit()
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="marry", description="Propose marriage to someone")
    @app_commands.describe(user="Person to propose to")
    async def propose_marriage(self, interaction: discord.Interaction, user: discord.Member):
        
        if user == interaction.user:
            await interaction.response.send_message("❌ You can't marry yourself!", ephemeral=True)
            return
        
        if user.bot:
            await interaction.response.send_message("❌ You can't marry a bot!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="💍 Marriage Proposal",
            description=f"**{interaction.user.display_name}** is proposing to **{user.display_name}**!",
            color=discord.Color.gold()
        )
        embed.add_field(name="💐", value=f"{user.mention}, will you marry {interaction.user.mention}?", inline=False)
        embed.set_footer(text="React with 💍 to accept or 💔 to decline")
        
        message = await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        
        await message.add_reaction("💍")
        await message.add_reaction("💔")
        
        def check(reaction, reactor):
            return (reactor == user and 
                   str(reaction.emoji) in ["💍", "💔"] and 
                   reaction.message.id == message.id)
        
        try:
            reaction, reactor = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            
            if str(reaction.emoji) == "💍":
                result_embed = discord.Embed(
                    title="💒 Congratulations!",
                    description=f"**{user.display_name}** accepted **{interaction.user.display_name}**'s proposal! 🎉",
                    color=discord.Color.green()
                )
                result_embed.add_field(name="💕", value="You are now married in this server!", inline=False)
            else:
                result_embed = discord.Embed(
                    title="💔 Proposal Declined",
                    description=f"**{user.display_name}** declined the proposal.",
                    color=discord.Color.red()
                )
            
            await message.edit(embed=result_embed)
            
        except asyncio.TimeoutError:
            timeout_embed = discord.Embed(
                title="⏰ Proposal Timeout",
                description="The proposal expired without an answer.",
                color=discord.Color.orange()
            )
            await message.edit(embed=timeout_embed)

    @app_commands.command(name="profile", description="View or create your social profile")
    @app_commands.describe(user="User to view profile for")
    async def user_profile(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        
        async with aiosqlite.connect('ultrabot.db') as db:
            async with db.execute('''
                SELECT messages_sent, xp, level, coins FROM users 
                WHERE user_id = ? AND guild_id = ?
            ''', (target.id, interaction.guild.id)) as cursor:
                stats = await cursor.fetchone()
        
        if not stats:
            stats = (0, 0, 1, 100)
        
        embed = discord.Embed(
            title=f"👤 {target.display_name}'s Profile",
            color=target.color or discord.Color.blue()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        
        # Basic info
        embed.add_field(name="💬 Messages", value=f"{stats[0]:,}", inline=True)
        embed.add_field(name="⭐ Level", value=stats[2], inline=True)
        embed.add_field(name="💰 Coins", value=f"{stats[3]:,}", inline=True)
        
        # Join info
        embed.add_field(name="📅 Joined", value=f"<t:{int(target.joined_at.timestamp())}:R>", inline=True)
        embed.add_field(name="🎭 Roles", value=len(target.roles) - 1, inline=True)  # Exclude @everyone
        embed.add_field(name="🏆 XP", value=f"{stats[1]:,}", inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="Show server leaderboards")
    @app_commands.describe(category="Leaderboard category")
    @app_commands.choices(category=[
        app_commands.Choice(name="Messages", value="messages"),
        app_commands.Choice(name="Levels", value="levels"),
        app_commands.Choice(name="Coins", value="coins")
    ])
    async def show_leaderboard(self, interaction: discord.Interaction, category: str = "levels"):
        
        column_map = {
            "messages": "messages_sent",
            "levels": "level",
            "coins": "coins"
        }
        
        async with aiosqlite.connect('ultrabot.db') as db:
            async with db.execute(f'''
                SELECT user_id, {column_map[category]} FROM users 
                WHERE guild_id = ? AND {column_map[category]} > 0
                ORDER BY {column_map[category]} DESC LIMIT 10
            ''', (interaction.guild.id,)) as cursor:
                results = await cursor.fetchall()
        
        if not results:
            await interaction.response.send_message(f"No {category} data available yet!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"🏆 {category.title()} Leaderboard",
            color=discord.Color.gold()
        )
        
        medals = ["🥇", "🥈", "🥉"]
        
        for i, (user_id, value) in enumerate(results):
            user = interaction.guild.get_member(user_id)
            if user:
                medal = medals[i] if i < 3 else f"{i+1}."
                embed.add_field(
                    name=f"{medal} {user.display_name}",
                    value=f"{value:,}" + (" messages" if category == "messages" else " coins" if category == "coins" else ""),
                    inline=False
                )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rep", description="Give reputation to a user")
    @app_commands.describe(user="User to give reputation to")
    async def give_reputation(self, interaction: discord.Interaction, user: discord.Member):
        
        if user == interaction.user:
            await interaction.response.send_message("❌ You can't give reputation to yourself!", ephemeral=True)
            return
        
        if user.bot:
            await interaction.response.send_message("❌ You can't give reputation to bots!", ephemeral=True)
            return
        
        # Check cooldown (24 hours)
        async with aiosqlite.connect('ultrabot.db') as db:
            # Create reputation table if not exists
            await db.execute('''
                CREATE TABLE IF NOT EXISTS reputation (
                    giver_id INTEGER,
                    receiver_id INTEGER,
                    guild_id INTEGER,
                    last_given TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (giver_id, guild_id)
                )
            ''')
            
            # Check last rep given
            async with db.execute('''
                SELECT last_given FROM reputation 
                WHERE giver_id = ? AND guild_id = ?
            ''', (interaction.user.id, interaction.guild.id)) as cursor:
                result = await cursor.fetchone()
            
            if result:
                last_given = datetime.fromisoformat(result[0])
                time_diff = datetime.now(timezone.utc) - last_given.replace(tzinfo=timezone.utc)
                if time_diff.total_seconds() < 86400:  # 24 hours
                    hours_left = 24 - (time_diff.total_seconds() / 3600)
                    await interaction.response.send_message(
                        f"❌ You can give reputation again in {hours_left:.1f} hours!",
                        ephemeral=True
                    )
                    return
            
            # Give reputation
            await db.execute('''
                INSERT OR REPLACE INTO reputation (giver_id, receiver_id, guild_id)
                VALUES (?, ?, ?)
            ''', (interaction.user.id, user.id, interaction.guild.id))
            
            await db.commit()
        
        embed = discord.Embed(
            title="⭐ Reputation Given",
            description=f"**{interaction.user.display_name}** gave reputation to **{user.display_name}**!",
            color=discord.Color.yellow()
        )
        embed.set_footer(text="You can give reputation again in 24 hours")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="quote", description="Save or retrieve memorable quotes")
    @app_commands.describe(
        action="What to do with quotes",
        message="Message to quote (for add action)",
        author="Quote author (for add action)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Random Quote", value="random"),
        app_commands.Choice(name="Add Quote", value="add"),
        app_commands.Choice(name="List Quotes", value="list")
    ])
    async def manage_quotes(self, interaction: discord.Interaction, 
                           action: str, message: str = None, author: str = None):
        
        async with aiosqlite.connect('ultrabot.db') as db:
            # Create quotes table if not exists
            await db.execute('''
                CREATE TABLE IF NOT EXISTS quotes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    quote_text TEXT,
                    author TEXT,
                    added_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            if action == "add":
                if not message or not author:
                    await interaction.response.send_message("❌ Please provide both message and author for adding a quote!", ephemeral=True)
                    return
                
                await db.execute('''
                    INSERT INTO quotes (guild_id, quote_text, author, added_by)
                    VALUES (?, ?, ?, ?)
                ''', (interaction.guild.id, message, author, interaction.user.id))
                await db.commit()
                
                embed = discord.Embed(
                    title="📝 Quote Added",
                    description=f'"{message}"\n\n— {author}',
                    color=discord.Color.green()
                )
                await interaction.response.send_message(embed=embed)
                
            elif action == "random":
                async with db.execute('''
                    SELECT quote_text, author FROM quotes 
                    WHERE guild_id = ? ORDER BY RANDOM() LIMIT 1
                ''', (interaction.guild.id,)) as cursor:
                    quote = await cursor.fetchone()
                
                if not quote:
                    await interaction.response.send_message("❌ No quotes available! Add some with `/quote add`", ephemeral=True)
                    return
                
                embed = discord.Embed(
                    title="💭 Random Quote",
                    description=f'"{quote[0]}"\n\n— {quote[1]}',
                    color=discord.Color.blue()
                )
                await interaction.response.send_message(embed=embed)
                
            elif action == "list":
                async with db.execute('''
                    SELECT quote_text, author FROM quotes 
                    WHERE guild_id = ? ORDER BY created_at DESC LIMIT 10
                ''', (interaction.guild.id,)) as cursor:
                    quotes = await cursor.fetchall()
                
                if not quotes:
                    await interaction.response.send_message("❌ No quotes available!", ephemeral=True)
                    return
                
                embed = discord.Embed(
                    title="📚 Server Quotes",
                    color=discord.Color.purple()
                )
                
                for i, (text, author) in enumerate(quotes[:5], 1):
                    embed.add_field(
                        name=f"Quote {i}",
                        value=f'"{text[:100]}{"..." if len(text) > 100 else ""}" — {author}',
                        inline=False
                    )
                
                await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(SocialFeatures(bot))