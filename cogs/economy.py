import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime, timedelta
from utils.embeds import create_embed

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='balance', aliases=['bal'])
    async def check_balance(self, ctx, member: discord.Member = None):
        """Check your or someone else's balance"""
        target = member or ctx.author
        
        balance = await self.bot.db.get_balance(ctx.guild.id, target.id)
        
        embed = create_embed(
            title=f"💰 {target.display_name}'s Balance",
            description=f"**{balance:,}** coins",
            color=0xFFD700
        )
        embed.set_thumbnail(url=target.avatar.url if target.avatar else target.default_avatar.url)
        
        await ctx.send(embed=embed)

    @commands.command(name='daily')
    async def daily_reward(self, ctx):
        """Claim your daily reward"""
        user_id = ctx.author.id
        guild_id = ctx.guild.id
        
        # Check if user already claimed today
        last_daily = await self.bot.db.get_last_daily(guild_id, user_id)
        now = datetime.utcnow()
        
        if last_daily and (now - last_daily).days < 1:
            next_daily = last_daily + timedelta(days=1)
            time_left = next_daily - now
            hours, remainder = divmod(int(time_left.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            
            embed = create_embed(
                title="⏰ Daily Already Claimed",
                description=f"You can claim your next daily reward in {hours}h {minutes}m",
                color=0xFF0000
            )
            return await ctx.send(embed=embed)
        
        # Calculate streak
        streak = await self.bot.db.get_daily_streak(guild_id, user_id)
        if last_daily and (now - last_daily).days == 1:
            streak += 1
        else:
            streak = 1
        
        # Calculate reward based on streak
        base_reward = 100
        streak_bonus = min(streak * 10, 500)  # Max 500 bonus
        total_reward = base_reward + streak_bonus
        
        # Add balance and update streak
        await self.bot.db.add_balance(guild_id, user_id, total_reward)
        await self.bot.db.update_daily_streak(guild_id, user_id, streak)
        
        embed = create_embed(
            title="🎁 Daily Reward Claimed!",
            description=f"You received **{total_reward:,}** coins!",
            color=0x00FF00
        )
        embed.add_field(name="Base Reward", value=f"{base_reward:,} coins", inline=True)
        embed.add_field(name="Streak Bonus", value=f"{streak_bonus:,} coins", inline=True)
        embed.add_field(name="Current Streak", value=f"{streak} days", inline=True)
        
        new_balance = await self.bot.db.get_balance(guild_id, user_id)
        embed.add_field(name="New Balance", value=f"{new_balance:,} coins", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name='work')
    async def work(self, ctx):
        """Work to earn coins"""
        user_id = ctx.author.id
        guild_id = ctx.guild.id
        
        # Check cooldown (1 hour)
        last_work = await self.bot.db.get_last_work(guild_id, user_id)
        if last_work and (datetime.utcnow() - last_work).total_seconds() < 3600:
            time_left = 3600 - (datetime.utcnow() - last_work).total_seconds()
            minutes = int(time_left // 60)
            
            embed = create_embed(
                title="⏰ Work Cooldown",
                description=f"You can work again in {minutes} minutes",
                color=0xFF0000
            )
            return await ctx.send(embed=embed)
        
        # Random work scenarios
        work_scenarios = [
            {"job": "delivered pizzas", "min": 50, "max": 150},
            {"job": "walked dogs", "min": 30, "max": 100},
            {"job": "cleaned cars", "min": 40, "max": 120},
            {"job": "tutored students", "min": 80, "max": 200},
            {"job": "coded a website", "min": 100, "max": 300},
            {"job": "designed graphics", "min": 60, "max": 180},
            {"job": "wrote articles", "min": 70, "max": 160},
            {"job": "fixed computers", "min": 90, "max": 250}
        ]
        
        scenario = random.choice(work_scenarios)
        earnings = random.randint(scenario["min"], scenario["max"])
        
        await self.bot.db.add_balance(guild_id, user_id, earnings)
        await self.bot.db.update_last_work(guild_id, user_id)
        
        embed = create_embed(
            title="💼 Work Complete!",
            description=f"You {scenario['job']} and earned **{earnings:,}** coins!",
            color=0x00FF00
        )
        
        new_balance = await self.bot.db.get_balance(guild_id, user_id)
        embed.add_field(name="New Balance", value=f"{new_balance:,} coins", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name='crime')
    async def commit_crime(self, ctx):
        """Commit a crime to potentially earn coins (risky!)"""
        user_id = ctx.author.id
        guild_id = ctx.guild.id
        
        # Check cooldown (2 hours)
        last_crime = await self.bot.db.get_last_crime(guild_id, user_id)
        if last_crime and (datetime.utcnow() - last_crime).total_seconds() < 7200:
            time_left = 7200 - (datetime.utcnow() - last_crime).total_seconds()
            hours = int(time_left // 3600)
            minutes = int((time_left % 3600) // 60)
            
            embed = create_embed(
                title="⏰ Crime Cooldown",
                description=f"You can commit a crime again in {hours}h {minutes}m",
                color=0xFF0000
            )
            return await ctx.send(embed=embed)
        
        current_balance = await self.bot.db.get_balance(guild_id, user_id)
        
        # 60% chance of success
        success = random.random() < 0.6
        
        crime_scenarios = [
            "robbed a bank",
            "pickpocketed someone",
            "sold illegal items",
            "hacked a system",
            "smuggled goods",
            "ran a scam"
        ]
        
        scenario = random.choice(crime_scenarios)
        
        if success:
            earnings = random.randint(200, 500)
            await self.bot.db.add_balance(guild_id, user_id, earnings)
            
            embed = create_embed(
                title="🕶️ Crime Successful!",
                description=f"You {scenario} and earned **{earnings:,}** coins!",
                color=0x00FF00
            )
            
            new_balance = await self.bot.db.get_balance(guild_id, user_id)
            embed.add_field(name="New Balance", value=f"{new_balance:,} coins", inline=True)
        else:
            fine = min(random.randint(100, 300), current_balance)
            await self.bot.db.remove_balance(guild_id, user_id, fine)
            
            embed = create_embed(
                title="🚔 Crime Failed!",
                description=f"You tried to {scenario[:-2]} but got caught! You paid a fine of **{fine:,}** coins.",
                color=0xFF0000
            )
            
            new_balance = await self.bot.db.get_balance(guild_id, user_id)
            embed.add_field(name="New Balance", value=f"{new_balance:,} coins", inline=True)
        
        await self.bot.db.update_last_crime(guild_id, user_id)
        await ctx.send(embed=embed)

    @commands.command(name='gamble', aliases=['bet'])
    async def gamble(self, ctx, amount):
        """Gamble coins with a chance to win or lose"""
        user_id = ctx.author.id
        guild_id = ctx.guild.id
        
        if amount.lower() == 'all':
            bet_amount = await self.bot.db.get_balance(guild_id, user_id)
        else:
            try:
                bet_amount = int(amount)
            except ValueError:
                return await ctx.send("❌ Please enter a valid amount!")
        
        if bet_amount <= 0:
            return await ctx.send("❌ You can't bet nothing!")
        
        current_balance = await self.bot.db.get_balance(guild_id, user_id)
        
        if bet_amount > current_balance:
            return await ctx.send("❌ You don't have enough coins!")
        
        # 45% chance to win
        win = random.random() < 0.45
        
        if win:
            winnings = bet_amount
            await self.bot.db.add_balance(guild_id, user_id, winnings)
            
            embed = create_embed(
                title="🎰 You Won!",
                description=f"You bet **{bet_amount:,}** coins and won **{winnings:,}** coins!",
                color=0x00FF00
            )
        else:
            await self.bot.db.remove_balance(guild_id, user_id, bet_amount)
            
            embed = create_embed(
                title="🎰 You Lost!",
                description=f"You bet **{bet_amount:,}** coins and lost them all!",
                color=0xFF0000
            )
        
        new_balance = await self.bot.db.get_balance(guild_id, user_id)
        embed.add_field(name="New Balance", value=f"{new_balance:,} coins", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name='give', aliases=['pay'])
    async def give_money(self, ctx, member: discord.Member, amount: int):
        """Give coins to another member"""
        if member == ctx.author:
            return await ctx.send("❌ You can't give money to yourself!")
        
        if member.bot:
            return await ctx.send("❌ You can't give money to bots!")
        
        if amount <= 0:
            return await ctx.send("❌ Amount must be positive!")
        
        sender_balance = await self.bot.db.get_balance(ctx.guild.id, ctx.author.id)
        
        if amount > sender_balance:
            return await ctx.send("❌ You don't have enough coins!")
        
        # Transfer money
        await self.bot.db.remove_balance(ctx.guild.id, ctx.author.id, amount)
        await self.bot.db.add_balance(ctx.guild.id, member.id, amount)
        
        embed = create_embed(
            title="💸 Money Transferred",
            description=f"{ctx.author.mention} gave **{amount:,}** coins to {member.mention}",
            color=0x00FF00
        )
        
        sender_new_balance = await self.bot.db.get_balance(ctx.guild.id, ctx.author.id)
        receiver_new_balance = await self.bot.db.get_balance(ctx.guild.id, member.id)
        
        embed.add_field(name=f"{ctx.author.display_name}'s Balance", value=f"{sender_new_balance:,} coins", inline=True)
        embed.add_field(name=f"{member.display_name}'s Balance", value=f"{receiver_new_balance:,} coins", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name='rob')
    async def rob_member(self, ctx, member: discord.Member):
        """Attempt to rob another member"""
        if member == ctx.author:
            return await ctx.send("❌ You can't rob yourself!")
        
        if member.bot:
            return await ctx.send("❌ You can't rob bots!")
        
        robber_id = ctx.author.id
        victim_id = member.id
        guild_id = ctx.guild.id
        
        # Check cooldown (4 hours)
        last_rob = await self.bot.db.get_last_rob(guild_id, robber_id)
        if last_rob and (datetime.utcnow() - last_rob).total_seconds() < 14400:
            time_left = 14400 - (datetime.utcnow() - last_rob).total_seconds()
            hours = int(time_left // 3600)
            minutes = int((time_left % 3600) // 60)
            
            embed = create_embed(
                title="⏰ Rob Cooldown",
                description=f"You can rob again in {hours}h {minutes}m",
                color=0xFF0000
            )
            return await ctx.send(embed=embed)
        
        victim_balance = await self.bot.db.get_balance(guild_id, victim_id)
        
        if victim_balance < 100:
            return await ctx.send(f"❌ {member.display_name} doesn't have enough coins to rob!")
        
        # 35% chance of success
        success = random.random() < 0.35
        
        if success:
            stolen_amount = random.randint(50, min(500, victim_balance // 2))
            
            await self.bot.db.remove_balance(guild_id, victim_id, stolen_amount)
            await self.bot.db.add_balance(guild_id, robber_id, stolen_amount)
            
            embed = create_embed(
                title="🔫 Robbery Successful!",
                description=f"{ctx.author.mention} successfully robbed **{stolen_amount:,}** coins from {member.mention}!",
                color=0x00FF00
            )
        else:
            fine = random.randint(100, 200)
            robber_balance = await self.bot.db.get_balance(guild_id, robber_id)
            actual_fine = min(fine, robber_balance)
            
            await self.bot.db.remove_balance(guild_id, robber_id, actual_fine)
            
            embed = create_embed(
                title="🚔 Robbery Failed!",
                description=f"{ctx.author.mention} tried to rob {member.mention} but got caught! They paid a fine of **{actual_fine:,}** coins.",
                color=0xFF0000
            )
        
        await self.bot.db.update_last_rob(guild_id, robber_id)
        await ctx.send(embed=embed)

    @commands.command(name='leaderboard', aliases=['lb', 'rich'])
    async def economy_leaderboard(self, ctx):
        """Show the server's richest members"""
        top_members = await self.bot.db.get_top_balances(ctx.guild.id, 10)
        
        if not top_members:
            return await ctx.send("❌ No economy data found!")
        
        embed = create_embed(
            title="💰 Economy Leaderboard",
            description="The richest members in the server",
            color=0xFFD700
        )
        
        for i, (user_id, balance) in enumerate(top_members, 1):
            member = ctx.guild.get_member(user_id)
            name = member.display_name if member else "Unknown User"
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            
            embed.add_field(
                name=f"{medal} {name}",
                value=f"{balance:,} coins",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command(name='shop')
    async def show_shop(self, ctx):
        """Show the server shop"""
        embed = create_embed(
            title="🛒 Server Shop",
            description="Buy items with your coins!",
            color=0x7289DA
        )
        
        items = [
            {"name": "VIP Role (7 days)", "price": 5000, "description": "Get VIP role for 7 days"},
            {"name": "Custom Color Role", "price": 10000, "description": "Get a custom colored role"},
            {"name": "Nickname Change", "price": 1000, "description": "Change someone's nickname"},
            {"name": "Channel Rename", "price": 15000, "description": "Temporarily rename a channel"},
            {"name": "Slowmode Immunity", "price": 3000, "description": "Ignore slowmode for 24 hours"}
        ]
        
        for item in items:
            embed.add_field(
                name=f"{item['name']} - {item['price']:,} coins",
                value=item['description'],
                inline=False
            )
        
        embed.add_field(
            name="How to Buy",
            value="Use `buy <item_name>` to purchase items",
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))
