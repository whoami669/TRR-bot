import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import random
from datetime import datetime, timezone, timedelta
from typing import Optional

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'economy.db'
        
    async def init_database(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    guild_id INTEGER NOT NULL,
                    balance INTEGER DEFAULT 1000,
                    bank INTEGER DEFAULT 0,
                    last_daily TIMESTAMP,
                    last_work TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    amount INTEGER NOT NULL,
                    transaction_type TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.commit()

    async def cog_load(self):
        await self.init_database()

    async def get_user_data(self, user_id: int, guild_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT * FROM users WHERE user_id = ? AND guild_id = ?
            ''', (user_id, guild_id))
            result = await cursor.fetchone()
            
            if not result:
                await db.execute('''
                    INSERT INTO users (user_id, guild_id) VALUES (?, ?)
                ''', (user_id, guild_id))
                await db.commit()
                return (user_id, guild_id, 1000, 0, None, None, datetime.now())
            
            return result

    @app_commands.command(name="balance", description="Check your balance")
    @app_commands.describe(user="User to check balance for")
    async def balance(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        target_user = user or interaction.user
        user_data = await self.get_user_data(target_user.id, interaction.guild_id)
        
        embed = discord.Embed(
            title=f"💰 {target_user.display_name}'s Balance",
            color=0xf39c12
        )
        embed.add_field(name="Wallet", value=f"${user_data[2]:,}", inline=True)
        embed.add_field(name="Bank", value=f"${user_data[3]:,}", inline=True)
        embed.add_field(name="Total", value=f"${user_data[2] + user_data[3]:,}", inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="daily", description="Claim your daily reward")
    async def daily(self, interaction: discord.Interaction):
        user_data = await self.get_user_data(interaction.user.id, interaction.guild_id)
        
        if user_data[4]:  # last_daily
            last_daily = datetime.fromisoformat(user_data[4])
            next_daily = last_daily + timedelta(days=1)
            
            if datetime.now(timezone.utc) < next_daily:
                time_left = next_daily - datetime.now(timezone.utc)
                hours, remainder = divmod(int(time_left.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)
                
                embed = discord.Embed(
                    title="⏰ Daily Already Claimed",
                    description=f"You can claim your daily reward in {hours}h {minutes}m",
                    color=0xe74c3c
                )
                await interaction.response.send_message(embed=embed)
                return
        
        daily_amount = random.randint(500, 1500)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE users SET balance = balance + ?, last_daily = ?
                WHERE user_id = ? AND guild_id = ?
            ''', (daily_amount, datetime.now(timezone.utc).isoformat(), interaction.user.id, interaction.guild_id))
            
            await db.execute('''
                INSERT INTO transactions (user_id, guild_id, amount, transaction_type, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (interaction.user.id, interaction.guild_id, daily_amount, "daily", "Daily reward"))
            await db.commit()
        
        embed = discord.Embed(
            title="🎁 Daily Reward Claimed",
            description=f"You received **${daily_amount:,}**!",
            color=0x2ecc71
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="work", description="Work to earn money")
    async def work(self, interaction: discord.Interaction):
        user_data = await self.get_user_data(interaction.user.id, interaction.guild_id)
        
        if user_data[5]:  # last_work
            last_work = datetime.fromisoformat(user_data[5])
            next_work = last_work + timedelta(hours=1)
            
            if datetime.now(timezone.utc) < next_work:
                time_left = next_work - datetime.now(timezone.utc)
                minutes = int(time_left.total_seconds() / 60)
                
                embed = discord.Embed(
                    title="😴 Still Tired",
                    description=f"You can work again in {minutes} minutes",
                    color=0xe74c3c
                )
                await interaction.response.send_message(embed=embed)
                return
        
        jobs = [
            ("programming", 200, 500),
            ("delivery driver", 150, 400),
            ("cashier", 100, 300),
            ("janitor", 80, 250),
            ("freelancer", 300, 600)
        ]
        
        job, min_pay, max_pay = random.choice(jobs)
        earnings = random.randint(min_pay, max_pay)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE users SET balance = balance + ?, last_work = ?
                WHERE user_id = ? AND guild_id = ?
            ''', (earnings, datetime.now(timezone.utc).isoformat(), interaction.user.id, interaction.guild_id))
            
            await db.execute('''
                INSERT INTO transactions (user_id, guild_id, amount, transaction_type, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (interaction.user.id, interaction.guild_id, earnings, "work", f"Worked as {job}"))
            await db.commit()
        
        embed = discord.Embed(
            title="💼 Work Complete",
            description=f"You worked as a **{job}** and earned **${earnings:,}**!",
            color=0x2ecc71
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="deposit", description="Deposit money to your bank")
    @app_commands.describe(amount="Amount to deposit (or 'all')")
    async def deposit(self, interaction: discord.Interaction, amount: str):
        user_data = await self.get_user_data(interaction.user.id, interaction.guild_id)
        wallet_balance = user_data[2]
        
        if amount.lower() == "all":
            deposit_amount = wallet_balance
        else:
            try:
                deposit_amount = int(amount)
            except ValueError:
                await interaction.response.send_message("Invalid amount. Use a number or 'all'")
                return
        
        if deposit_amount <= 0:
            await interaction.response.send_message("Amount must be positive")
            return
        
        if deposit_amount > wallet_balance:
            await interaction.response.send_message("You don't have enough money in your wallet")
            return
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE users SET balance = balance - ?, bank = bank + ?
                WHERE user_id = ? AND guild_id = ?
            ''', (deposit_amount, deposit_amount, interaction.user.id, interaction.guild_id))
            await db.commit()
        
        embed = discord.Embed(
            title="🏦 Deposit Successful",
            description=f"Deposited **${deposit_amount:,}** to your bank",
            color=0x2ecc71
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="withdraw", description="Withdraw money from your bank")
    @app_commands.describe(amount="Amount to withdraw (or 'all')")
    async def withdraw(self, interaction: discord.Interaction, amount: str):
        user_data = await self.get_user_data(interaction.user.id, interaction.guild_id)
        bank_balance = user_data[3]
        
        if amount.lower() == "all":
            withdraw_amount = bank_balance
        else:
            try:
                withdraw_amount = int(amount)
            except ValueError:
                await interaction.response.send_message("Invalid amount. Use a number or 'all'")
                return
        
        if withdraw_amount <= 0:
            await interaction.response.send_message("Amount must be positive")
            return
        
        if withdraw_amount > bank_balance:
            await interaction.response.send_message("You don't have enough money in your bank")
            return
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE users SET balance = balance + ?, bank = bank - ?
                WHERE user_id = ? AND guild_id = ?
            ''', (withdraw_amount, withdraw_amount, interaction.user.id, interaction.guild_id))
            await db.commit()
        
        embed = discord.Embed(
            title="🏦 Withdrawal Successful",
            description=f"Withdrew **${withdraw_amount:,}** from your bank",
            color=0x2ecc71
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="pay", description="Send money to another user")
    @app_commands.describe(user="User to send money to", amount="Amount to send")
    async def pay(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if user.id == interaction.user.id:
            await interaction.response.send_message("You can't pay yourself!")
            return
        
        if amount <= 0:
            await interaction.response.send_message("Amount must be positive")
            return
        
        sender_data = await self.get_user_data(interaction.user.id, interaction.guild_id)
        if amount > sender_data[2]:
            await interaction.response.send_message("You don't have enough money")
            return
        
        await self.get_user_data(user.id, interaction.guild_id)  # Ensure recipient exists
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE users SET balance = balance - ?
                WHERE user_id = ? AND guild_id = ?
            ''', (amount, interaction.user.id, interaction.guild_id))
            
            await db.execute('''
                UPDATE users SET balance = balance + ?
                WHERE user_id = ? AND guild_id = ?
            ''', (amount, user.id, interaction.guild_id))
            
            await db.execute('''
                INSERT INTO transactions (user_id, guild_id, amount, transaction_type, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (interaction.user.id, interaction.guild_id, -amount, "transfer", f"Sent to {user.display_name}"))
            
            await db.execute('''
                INSERT INTO transactions (user_id, guild_id, amount, transaction_type, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (user.id, interaction.guild_id, amount, "transfer", f"Received from {interaction.user.display_name}"))
            await db.commit()
        
        embed = discord.Embed(
            title="💸 Payment Sent",
            description=f"Sent **${amount:,}** to {user.mention}",
            color=0x2ecc71
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="View the richest users")
    async def leaderboard(self, interaction: discord.Interaction):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT user_id, balance + bank as total
                FROM users WHERE guild_id = ?
                ORDER BY total DESC LIMIT 10
            ''', (interaction.guild_id,))
            results = await cursor.fetchall()
        
        if not results:
            await interaction.response.send_message("No users found")
            return
        
        embed = discord.Embed(
            title="💰 Richest Users",
            color=0xf39c12
        )
        
        for i, (user_id, total) in enumerate(results, 1):
            user = interaction.guild.get_member(user_id)
            if user:
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                embed.add_field(
                    name=f"{medal} {user.display_name}",
                    value=f"${total:,}",
                    inline=False
                )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))