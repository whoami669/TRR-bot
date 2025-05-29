import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiosqlite
import asyncio
import random
from datetime import datetime, timezone, timedelta

class CommunityRevival(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conversation_starters.start()
        self.activity_rewards.start()
        self.community_challenges.start()

    @tasks.loop(hours=4)
    async def conversation_starters(self):
        """Post engaging conversation starters"""
        starters = [
            "What's the most underrated game you've ever played?",
            "If you could redesign any game mechanic, what would you change?",
            "What's your current gaming setup like?",
            "Share a gaming memory that always makes you smile",
            "What game are you most hyped for this year?",
            "Desert island scenario: you can only bring 3 games. Which ones?",
            "What's the hardest boss you've ever defeated?",
            "Tell us about your first gaming experience",
            "What's your favorite gaming soundtrack?",
            "Which game character would you want as a friend?"
        ]
        
        for guild in self.bot.guilds:
            gaming_channel = discord.utils.get(guild.text_channels, name="gaming-talk")
            if gaming_channel and random.random() < 0.6:
                starter = random.choice(starters)
                embed = discord.Embed(
                    title="💭 Discussion Starter",
                    description=starter,
                    color=0x00ff88
                )
                embed.set_footer(text="Join the conversation!")
                try:
                    message = await gaming_channel.send(embed=embed)
                    await message.add_reaction("🎮")
                    await message.add_reaction("💬")
                except:
                    pass

    @tasks.loop(hours=6)
    async def activity_rewards(self):
        """Reward active community members"""
        for guild in self.bot.guilds:
            async with aiosqlite.connect('ultrabot.db') as db:
                async with db.execute('''
                    SELECT user_id, messages_sent FROM users 
                    WHERE guild_id = ? AND messages_sent >= 5
                    ORDER BY RANDOM() LIMIT 1
                ''', (guild.id,)) as cursor:
                    result = await cursor.fetchone()
                
                if result:
                    member = guild.get_member(result[0])
                    general_channel = discord.utils.get(guild.text_channels, name="general-chat")
                    
                    if member and general_channel:
                        rewards = [
                            f"🌟 {member.mention} just earned 500 bonus coins for being awesome!",
                            f"🎉 Special recognition for {member.mention} - you're making this community great!",
                            f"💎 {member.mention} gets VIP status for the next 24 hours for their amazing activity!",
                            f"🏆 Community MVP alert: {member.mention} is crushing it today!"
                        ]
                        
                        try:
                            await general_channel.send(random.choice(rewards))
                            # Actually give coins
                            await db.execute('''
                                UPDATE users SET coins = coins + 500 
                                WHERE user_id = ? AND guild_id = ?
                            ''', (member.id, guild.id))
                            await db.commit()
                        except:
                            pass

    @tasks.loop(hours=12)
    async def community_challenges(self):
        """Post weekly community challenges"""
        challenges = [
            {
                "title": "Screenshot Challenge",
                "desc": "Share your most epic gaming screenshot! Best one gets featured.",
                "emoji": "📸",
                "channel": "screenshots"
            },
            {
                "title": "Meme Monday",
                "desc": "Create the funniest gaming meme! Most reactions wins.",
                "emoji": "😂",
                "channel": "memes-and-fun"
            },
            {
                "title": "Game Recommendation",
                "desc": "Recommend a hidden gem game and tell us why it's amazing!",
                "emoji": "💎",
                "channel": "game-suggestions"
            },
            {
                "title": "Setup Showcase",
                "desc": "Show off your gaming setup! Rate each other's setups.",
                "emoji": "🖥️",
                "channel": "tech-talk"
            }
        ]
        
        for guild in self.bot.guilds:
            if random.random() < 0.7:
                challenge = random.choice(challenges)
                target_channel = discord.utils.get(guild.text_channels, name=challenge["channel"])
                
                if target_channel:
                    embed = discord.Embed(
                        title=f"{challenge['emoji']} {challenge['title']}",
                        description=challenge['desc'],
                        color=0xff6b6b
                    )
                    embed.add_field(name="Duration", value="24 hours", inline=True)
                    embed.add_field(name="Reward", value="1000 coins + special role", inline=True)
                    embed.set_footer(text="Get creative and have fun!")
                    
                    try:
                        message = await target_channel.send(embed=embed)
                        await message.add_reaction(challenge["emoji"])
                        await message.add_reaction("🔥")
                    except:
                        pass

    @commands.Cog.listener()
    async def on_message(self, message):
        """Boost engagement with smart reactions and responses"""
        if message.author.bot or not message.guild:
            return
        
        # Gaming keywords for auto-engagement
        gaming_keywords = [
            'playing', 'game', 'gaming', 'stream', 'twitch', 'youtube',
            'pc', 'console', 'xbox', 'playstation', 'nintendo', 'switch',
            'fps', 'rpg', 'mmorpg', 'mobile', 'android', 'ios'
        ]
        
        # Check if message contains gaming content
        if any(keyword in message.content.lower() for keyword in gaming_keywords):
            if random.random() < 0.3:  # 30% chance
                reactions = ["🎮", "🔥", "👍", "💯"]
                try:
                    await message.add_reaction(random.choice(reactions))
                except:
                    pass
        
        # Question detection for engagement boost
        if message.content.endswith('?') and len(message.content) > 20:
            if random.random() < 0.2:  # 20% chance
                engagement_responses = [
                    "Great question! 🤔",
                    "Interesting! Anyone have thoughts on this? 💭",
                    "This deserves more discussion! 🗣️"
                ]
                try:
                    await message.reply(random.choice(engagement_responses), mention_author=False)
                except:
                    pass

    @conversation_starters.before_loop
    @activity_rewards.before_loop
    @community_challenges.before_loop
    async def before_loops(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(CommunityRevival(bot))