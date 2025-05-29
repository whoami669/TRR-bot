import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import random
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional

class EconomyAdvanced(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="balance", description="Check your or someone's balance")
    @app_commands.describe(user="User to check balance for")
    async def check_balance(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        
        async with aiosqlite.connect('ultrabot.db') as db:
            await db.execute('''
                INSERT OR IGNORE INTO users (user_id, guild_id) VALUES (?, ?)
            ''', (target.id, interaction.guild.id))
            
            async with db.execute('''
                SELECT coins, xp, level FROM users 
                WHERE user_id = ? AND guild_id = ?
            ''', (target.id, interaction.guild.id)) as cursor:
                result = await cursor.fetchone()
                
            await db.commit()
        
        coins = result[0] if result else 100
        xp = result[1] if result else 0
        level = result[2] if result else 1
        
        embed = discord.Embed(
            title=f"💰 {target.display_name}'s Wallet",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Coins", value=f"{coins:,} 🪙", inline=True)
        embed.add_field(name="Level", value=f"{level}", inline=True)
        embed.add_field(name="XP", value=f"{xp:,}", inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="daily", description="Claim your daily reward")
    async def daily_reward(self, interaction: discord.Interaction):
        async with aiosqlite.connect('ultrabot.db') as db:
            await db.execute('''
                INSERT OR IGNORE INTO users (user_id, guild_id) VALUES (?, ?)
            ''', (interaction.user.id, interaction.guild.id))
            
            async with db.execute('''
                SELECT last_daily, coins FROM users 
                WHERE user_id = ? AND guild_id = ?
            ''', (interaction.user.id, interaction.guild.id)) as cursor:
                result = await cursor.fetchone()
            
            last_daily = result[0] if result and result[0] else None
            current_coins = result[1] if result else 100
            
            now = datetime.now(timezone.utc)
            
            # Check if already claimed today
            if last_daily:
                last_claim = datetime.fromisoformat(last_daily)
                if (now - last_claim.replace(tzinfo=timezone.utc)).total_seconds() < 86400:
                    time_left = 86400 - (now - last_claim.replace(tzinfo=timezone.utc)).total_seconds()
                    hours = int(time_left // 3600)
                    minutes = int((time_left % 3600) // 60)
                    
                    embed = discord.Embed(
                        title="⏰ Daily Already Claimed",
                        description=f"Come back in {hours}h {minutes}m for your next daily reward!",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
            
            # Give daily reward
            daily_amount = random.randint(100, 500)
            bonus = 0
            
            # Level bonus
            if result:
                level = await self.get_user_level(interaction.user.id, interaction.guild.id)
                bonus = level * 10
            
            total_reward = daily_amount + bonus
            
            await db.execute('''
                UPDATE users SET coins = coins + ?, last_daily = ? 
                WHERE user_id = ? AND guild_id = ?
            ''', (total_reward, now, interaction.user.id, interaction.guild.id))
            await db.commit()
        
        embed = discord.Embed(
            title="🎁 Daily Reward Claimed!",
            description=f"You earned **{total_reward:,}** coins!",
            color=discord.Color.green()
        )
        embed.add_field(name="Base Reward", value=f"{daily_amount:,} 🪙", inline=True)
        if bonus > 0:
            embed.add_field(name="Level Bonus", value=f"{bonus:,} 🪙", inline=True)
        embed.add_field(name="New Balance", value=f"{current_coins + total_reward:,} 🪙", inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="work", description="Work to earn coins")
    async def work(self, interaction: discord.Interaction):
        async with aiosqlite.connect('ultrabot.db') as db:
            await db.execute('''
                INSERT OR IGNORE INTO users (user_id, guild_id) VALUES (?, ?)
            ''', (interaction.user.id, interaction.guild.id))
            
            async with db.execute('''
                SELECT last_work, coins FROM users 
                WHERE user_id = ? AND guild_id = ?
            ''', (interaction.user.id, interaction.guild.id)) as cursor:
                result = await cursor.fetchone()
            
            last_work = result[0] if result and result[0] else None
            current_coins = result[1] if result else 100
            
            now = datetime.now(timezone.utc)
            
            # Check cooldown (1 hour)
            if last_work:
                last_work_time = datetime.fromisoformat(last_work)
                if (now - last_work_time.replace(tzinfo=timezone.utc)).total_seconds() < 3600:
                    time_left = 3600 - (now - last_work_time.replace(tzinfo=timezone.utc)).total_seconds()
                    minutes = int(time_left // 60)
                    
                    embed = discord.Embed(
                        title="😴 Take a Break",
                        description=f"You can work again in {minutes} minutes!",
                        color=discord.Color.orange()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
            
            # Work jobs and earnings
            jobs = [
                {"name": "Software Developer", "min": 150, "max": 300},
                {"name": "Coffee Barista", "min": 50, "max": 120},
                {"name": "Delivery Driver", "min": 80, "max": 180},
                {"name": "Content Creator", "min": 100, "max": 250},
                {"name": "Data Analyst", "min": 120, "max": 220},
                {"name": "Freelance Writer", "min": 90, "max": 190},
            ]
            
            job = random.choice(jobs)
            earnings = random.randint(job["min"], job["max"])
            
            await db.execute('''
                UPDATE users SET coins = coins + ?, last_work = ? 
                WHERE user_id = ? AND guild_id = ?
            ''', (earnings, now, interaction.user.id, interaction.guild.id))
            await db.commit()
        
        embed = discord.Embed(
            title="💼 Work Complete!",
            description=f"You worked as a **{job['name']}** and earned **{earnings:,}** coins!",
            color=discord.Color.blue()
        )
        embed.add_field(name="New Balance", value=f"{current_coins + earnings:,} 🪙", inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="gamble", description="Gamble your coins")
    @app_commands.describe(amount="Amount to gamble")
    async def gamble(self, interaction: discord.Interaction, amount: int):
        if amount <= 0:
            await interaction.response.send_message("❌ You must gamble a positive amount!", ephemeral=True)
            return
        
        async with aiosqlite.connect('ultrabot.db') as db:
            await db.execute('''
                INSERT OR IGNORE INTO users (user_id, guild_id) VALUES (?, ?)
            ''', (interaction.user.id, interaction.guild.id))
            
            async with db.execute('''
                SELECT coins FROM users 
                WHERE user_id = ? AND guild_id = ?
            ''', (interaction.user.id, interaction.guild.id)) as cursor:
                result = await cursor.fetchone()
            
            current_coins = result[0] if result else 100
            
            if current_coins < amount:
                await interaction.response.send_message(f"❌ You only have {current_coins:,} coins!", ephemeral=True)
                return
            
            # Gambling logic
            roll = random.randint(1, 100)
            
            if roll <= 45:  # 45% chance to lose
                winnings = -amount
                result_text = "You lost!"
                color = discord.Color.red()
                emoji = "📉"
            elif roll <= 85:  # 40% chance to win small
                winnings = amount // 2
                result_text = "Small win!"
                color = discord.Color.yellow()
                emoji = "📊"
            elif roll <= 95:  # 10% chance to win big
                winnings = amount
                result_text = "Big win!"
                color = discord.Color.green()
                emoji = "📈"
            else:  # 5% chance to win jackpot
                winnings = amount * 2
                result_text = "JACKPOT!"
                color = discord.Color.gold()
                emoji = "🎰"
            
            new_balance = current_coins + winnings
            
            await db.execute('''
                UPDATE users SET coins = ? 
                WHERE user_id = ? AND guild_id = ?
            ''', (new_balance, interaction.user.id, interaction.guild.id))
            await db.commit()
        
        embed = discord.Embed(
            title=f"{emoji} Gambling Results",
            description=f"**{result_text}**",
            color=color
        )
        embed.add_field(name="Bet Amount", value=f"{amount:,} 🪙", inline=True)
        embed.add_field(name="Roll", value=f"{roll}/100", inline=True)
        embed.add_field(name="Winnings", value=f"{winnings:+,} 🪙", inline=True)
        embed.add_field(name="New Balance", value=f"{new_balance:,} 🪙", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="give", description="Give coins to another user")
    @app_commands.describe(user="User to give coins to", amount="Amount to give")
    async def give_coins(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if user == interaction.user:
            await interaction.response.send_message("❌ You can't give coins to yourself!", ephemeral=True)
            return
        
        if user.bot:
            await interaction.response.send_message("❌ You can't give coins to bots!", ephemeral=True)
            return
        
        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
            return
        
        async with aiosqlite.connect('ultrabot.db') as db:
            # Check sender's balance
            await db.execute('''
                INSERT OR IGNORE INTO users (user_id, guild_id) VALUES (?, ?)
            ''', (interaction.user.id, interaction.guild.id))
            
            async with db.execute('''
                SELECT coins FROM users 
                WHERE user_id = ? AND guild_id = ?
            ''', (interaction.user.id, interaction.guild.id)) as cursor:
                sender_result = await cursor.fetchone()
            
            sender_coins = sender_result[0] if sender_result else 100
            
            if sender_coins < amount:
                await interaction.response.send_message(f"❌ You only have {sender_coins:,} coins!", ephemeral=True)
                return
            
            # Transfer coins
            await db.execute('''
                INSERT OR IGNORE INTO users (user_id, guild_id) VALUES (?, ?)
            ''', (user.id, interaction.guild.id))
            
            await db.execute('''
                UPDATE users SET coins = coins - ? 
                WHERE user_id = ? AND guild_id = ?
            ''', (amount, interaction.user.id, interaction.guild.id))
            
            await db.execute('''
                UPDATE users SET coins = coins + ? 
                WHERE user_id = ? AND guild_id = ?
            ''', (amount, user.id, interaction.guild.id))
            
            await db.commit()
        
        embed = discord.Embed(
            title="💸 Coins Transferred",
            description=f"**{interaction.user.display_name}** gave **{amount:,}** coins to **{user.display_name}**!",
            color=discord.Color.green()
        )
        embed.add_field(name="Your New Balance", value=f"{sender_coins - amount:,} 🪙", inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="View the server's richest members")
    async def economy_leaderboard(self, interaction: discord.Interaction):
        async with aiosqlite.connect('ultrabot.db') as db:
            async with db.execute('''
                SELECT user_id, coins FROM users 
                WHERE guild_id = ? AND coins > 0
                ORDER BY coins DESC LIMIT 10
            ''', (interaction.guild.id,)) as cursor:
                results = await cursor.fetchall()
        
        if not results:
            await interaction.response.send_message("No economy data available yet!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="💰 Economy Leaderboard",
            description="Richest members in the server",
            color=discord.Color.gold()
        )
        
        medals = ["🥇", "🥈", "🥉"]
        
        for i, (user_id, coins) in enumerate(results):
            member = interaction.guild.get_member(user_id)
            if member:
                medal = medals[i] if i < 3 else f"{i+1}."
                embed.add_field(
                    name=f"{medal} {member.display_name}",
                    value=f"{coins:,} 🪙",
                    inline=False
                )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="shop", description="View and buy items from the shop")
    async def shop(self, interaction: discord.Interaction):
        shop_items = [
            {"name": "VIP Role", "price": 10000, "description": "Get a special VIP role", "emoji": "👑"},
            {"name": "Custom Color", "price": 5000, "description": "Get a custom role color", "emoji": "🎨"},
            {"name": "Double XP", "price": 7500, "description": "2x XP for 24 hours", "emoji": "⚡"},
            {"name": "Profile Badge", "price": 2500, "description": "Special badge on your profile", "emoji": "🏆"},
            {"name": "Coin Multiplier", "price": 15000, "description": "1.5x coins for 7 days", "emoji": "💎"},
        ]
        
        embed = discord.Embed(
            title="🛒 Server Shop",
            description="Spend your coins on exclusive items!",
            color=discord.Color.blue()
        )
        
        for i, item in enumerate(shop_items, 1):
            embed.add_field(
                name=f"{item['emoji']} {item['name']}",
                value=f"{item['description']}\n**Price:** {item['price']:,} 🪙",
                inline=False
            )
        
        embed.set_footer(text="Use /buy <item_name> to purchase items")
        
        await interaction.response.send_message(embed=embed)

    async def get_user_level(self, user_id: int, guild_id: int) -> int:
        """Helper function to get user level"""
        async with aiosqlite.connect('ultrabot.db') as db:
            async with db.execute('''
                SELECT level FROM users WHERE user_id = ? AND guild_id = ?
            ''', (user_id, guild_id)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 1

async def setup(bot):
    await bot.add_cog(EconomyAdvanced(bot))