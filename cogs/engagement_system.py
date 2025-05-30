import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiosqlite
import asyncio
import random
from datetime import datetime, timezone, timedelta

class EngagementSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.level_up_messages.start()
        self.voice_activity_tracker.start()
        self.member_milestones.start()

    @tasks.loop(hours=24)
    async def level_up_messages(self):
        """Encourage members to level up and be active"""
        motivational_messages = [
            "Who's ready to climb the leaderboard today? 🚀",
            "Level up your activity! Chat more, gain more XP! ⭐",
            "The most active members get the best rewards! 💎",
            "Don't forget to use /daily for your free coins! 💰",
            "Voice chat gives bonus XP - hop in a channel! 🎤",
            "Screenshot sharing gets extra reactions! Share your wins! 📸"
        ]
        
        for guild in self.bot.guilds:
            general_channel = discord.utils.get(guild.text_channels, name="general-chat")
            if general_channel and random.random() < 0.05:
                try:
                    message = random.choice(motivational_messages)
                    embed = discord.Embed(
                        description=message,
                        color=0x00ff88
                    )
                    await general_channel.send(embed=embed)
                except:
                    pass

    @tasks.loop(minutes=15)
    async def voice_activity_tracker(self):
        """Track and reward voice activity"""
        for guild in self.bot.guilds:
            for voice_channel in guild.voice_channels:
                if len(voice_channel.members) >= 2:  # At least 2 people talking
                    for member in voice_channel.members:
                        if not member.bot:
                            async with aiosqlite.connect('ultrabot.db') as db:
                                await db.execute('''
                                    INSERT OR IGNORE INTO users (user_id, guild_id) VALUES (?, ?)
                                ''', (member.id, guild.id))
                                
                                await db.execute('''
                                    UPDATE users SET voice_time = voice_time + 15, xp = xp + 25
                                    WHERE user_id = ? AND guild_id = ?
                                ''', (member.id, guild.id))
                                
                                await db.commit()

    @tasks.loop(hours=8)
    async def member_milestones(self):
        """Celebrate member milestones"""
        for guild in self.bot.guilds:
            async with aiosqlite.connect('ultrabot.db') as db:
                # Find members hitting message milestones
                async with db.execute('''
                    SELECT user_id, messages_sent FROM users 
                    WHERE guild_id = ? AND messages_sent IN (100, 500, 1000, 2500, 5000)
                ''', (guild.id,)) as cursor:
                    milestone_members = await cursor.fetchall()
                
                general_channel = discord.utils.get(guild.text_channels, name="general-chat")
                
                for user_id, message_count in milestone_members:
                    member = guild.get_member(user_id)
                    if member and general_channel:
                        milestone_rewards = {
                            100: {"coins": 1000, "title": "Chatterbox"},
                            500: {"coins": 2500, "title": "Community Voice"},
                            1000: {"coins": 5000, "title": "Active Legend"},
                            2500: {"coins": 10000, "title": "Super Contributor"},
                            5000: {"coins": 25000, "title": "Community Champion"}
                        }
                        
                        reward = milestone_rewards.get(message_count)
                        if reward:
                            embed = discord.Embed(
                                title="🎉 Milestone Achievement!",
                                description=f"Congratulations {member.mention} on reaching **{message_count:,} messages**!",
                                color=0xffd700
                            )
                            embed.add_field(name="New Title", value=f"🏆 {reward['title']}", inline=True)
                            embed.add_field(name="Bonus Reward", value=f"💰 {reward['coins']:,} coins", inline=True)
                            
                            try:
                                message = await general_channel.send(embed=embed)
                                await message.add_reaction("🎉")
                                await message.add_reaction("👏")
                                
                                # Give the reward
                                await db.execute('''
                                    UPDATE users SET coins = coins + ? WHERE user_id = ? AND guild_id = ?
                                ''', (reward['coins'], member.id, guild.id))
                                await db.commit()
                            except:
                                pass

    @commands.Cog.listener()
    async def on_message(self, message):
        """Enhanced XP and engagement tracking"""
        if message.author.bot or not message.guild:
            return
        
        # Calculate XP based on message quality
        base_xp = 10
        bonus_xp = 0
        
        # Length bonus
        if len(message.content) > 50:
            bonus_xp += 5
        if len(message.content) > 100:
            bonus_xp += 10
        
        # Question bonus (encourages discussion)
        if '?' in message.content:
            bonus_xp += 15
        
        # Media sharing bonus
        if message.attachments:
            bonus_xp += 20
        
        # Gaming keyword bonus
        gaming_words = ['game', 'playing', 'stream', 'twitch', 'youtube', 'pc', 'console']
        if any(word in message.content.lower() for word in gaming_words):
            bonus_xp += 10
        
        total_xp = base_xp + bonus_xp
        
        async with aiosqlite.connect('ultrabot.db') as db:
            await db.execute('''
                INSERT OR IGNORE INTO users (user_id, guild_id) VALUES (?, ?)
            ''', (message.author.id, message.guild.id))
            
            # Get current stats
            async with db.execute('''
                SELECT xp, level FROM users WHERE user_id = ? AND guild_id = ?
            ''', (message.author.id, message.guild.id)) as cursor:
                result = await cursor.fetchone()
            
            current_xp = result[0] if result else 0
            current_level = result[1] if result else 1
            
            # Update XP and messages
            new_xp = current_xp + total_xp
            await db.execute('''
                UPDATE users SET xp = ?, messages_sent = messages_sent + 1
                WHERE user_id = ? AND guild_id = ?
            ''', (new_xp, message.author.id, message.guild.id))
            
            # Check for level up
            new_level = self.calculate_level(new_xp)
            if new_level > current_level:
                await db.execute('''
                    UPDATE users SET level = ? WHERE user_id = ? AND guild_id = ?
                ''', (new_level, message.author.id, message.guild.id))
                
                # Level up celebration
                level_rewards = {
                    5: 500,
                    10: 1000,
                    15: 1500,
                    20: 2500,
                    25: 5000,
                    30: 7500,
                    50: 15000,
                    75: 25000,
                    100: 50000
                }
                
                coin_reward = level_rewards.get(new_level, new_level * 100)
                
                await db.execute('''
                    UPDATE users SET coins = coins + ? WHERE user_id = ? AND guild_id = ?
                ''', (coin_reward, message.author.id, message.guild.id))
                
                embed = discord.Embed(
                    title="🎊 Level Up!",
                    description=f"Congratulations {message.author.mention}! You've reached **Level {new_level}**!",
                    color=0x00ff00
                )
                embed.add_field(name="Reward", value=f"💰 {coin_reward:,} coins", inline=True)
                embed.add_field(name="Total XP", value=f"⭐ {new_xp:,}", inline=True)
                
                if new_level in [10, 25, 50, 75, 100]:
                    embed.add_field(name="Special Milestone!", value="🎉 You've hit a major level!", inline=False)
                
                try:
                    level_message = await message.channel.send(embed=embed)
                    await level_message.add_reaction("🎉")
                    await level_message.add_reaction("🔥")
                except:
                    pass
            
            await db.commit()

    def calculate_level(self, xp):
        """Calculate level based on XP (exponential curve)"""
        level = 1
        required_xp = 100
        
        while xp >= required_xp:
            xp -= required_xp
            level += 1
            required_xp = int(required_xp * 1.2)  # 20% increase each level
        
        return level

    @level_up_messages.before_loop
    @voice_activity_tracker.before_loop
    @member_milestones.before_loop
    async def before_loops(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(EngagementSystem(bot))