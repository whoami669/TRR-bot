import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiosqlite
import asyncio
import random
from datetime import datetime, timezone, timedelta

class AutoGaming(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Disabled automated messaging per user request
        # self.gaming_questions_loop.start()

    def cog_unload(self):
        self.gaming_questions_loop.cancel()

    @tasks.loop(hours=12)
    async def gaming_questions_loop(self):
        """Automatically post gaming questions to boost engagement"""
        for guild in self.bot.guilds:
            gaming_channel = discord.utils.get(guild.text_channels, name="gaming-talk")
            general_channel = discord.utils.get(guild.text_channels, name="general-chat")
            
            target_channel = gaming_channel or general_channel
            
            if target_channel and random.random() < 0.1:  # 10% chance every 12 hours
                await self.post_gaming_question(target_channel)

    @gaming_questions_loop.before_loop
    async def before_gaming_loop(self):
        await self.bot.wait_until_ready()

    async def post_gaming_question(self, channel):
        """Post a random gaming question"""
        gaming_questions = [
            "What's the most challenging game you've ever completed? Share your victory story! 🏆",
            "If you could live in any video game world, which would you choose and why? 🌍",
            "What's your favorite gaming memory from childhood? Let's get nostalgic! 🎮",
            "Which game soundtrack gives you the most goosebumps? Drop a link! 🎵",
            "What's the longest gaming session you've ever had? How many hours? ⏰",
            "Which game mechanic do you think is absolutely genius? 🧠",
            "What's your go-to game when you want to relax and unwind? 😌",
            "If you could bring back one discontinued game series, what would it be? 📺",
            "What's the most beautiful game environment you've ever seen? 🌅",
            "Which gaming character would make the best friend in real life? 👥",
            "What's your biggest gaming achievement that you're proud of? 🥇",
            "Which game completely changed your perspective on gaming? 🔄",
            "What's the scariest moment you've experienced in a horror game? 👻",
            "If you could have any superpower from a video game, what would it be? ⚡",
            "What's the most addictive mobile game you've ever played? 📱",
            "Which retro game holds up perfectly even today? 🕹️",
            "What's your favorite co-op gaming experience with friends? 🤝",
            "Which game has the best character customization system? ✨",
            "What's the most emotional moment you've experienced in gaming? 😭",
            "If you could be a game developer for one day, what would you create? 💡"
        ]
        
        question = random.choice(gaming_questions)
        
        embed = discord.Embed(
            title="🎮 Gaming Discussion",
            description=question,
            color=random.choice([0x00ff00, 0xff6b6b, 0x4ecdc4, 0x45b7d1, 0xf39c12])
        )
        embed.set_footer(text="Join the conversation and share your thoughts!")
        
        try:
            message = await channel.send(embed=embed)
            await message.add_reaction("🎮")
            await message.add_reaction("💬")
            await message.add_reaction("🔥")
        except Exception as e:
            print(f"Error posting gaming question: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        """React to gaming-related messages automatically"""
        if message.author.bot or not message.guild:
            return
        
        # Gaming keywords for auto-engagement
        gaming_triggers = {
            'achievement': ['🏆', '👏', '🎉'],
            'victory': ['🏆', '🎊', '💯'],
            'completed': ['✅', '🎯', '👍'],
            'finished': ['✅', '🎯', '👍'],
            'won': ['🏆', '🎉', '💪'],
            'beat': ['💪', '🔥', '👑'],
            'platinum': ['💎', '🏆', '⭐'],
            'legendary': ['👑', '⭐', '🔥'],
            'epic': ['🔥', '💯', '⚡'],
            'clutch': ['🔥', '💯', '🎯'],
            'headshot': ['🎯', '💥', '🔥'],
            'speedrun': ['⚡', '🏃', '⏱️'],
            'world record': ['🌍', '🏆', '⭐'],
            'first try': ['🍀', '🎯', '👍'],
            'no death': ['💪', '🛡️', '👑'],
            'perfect': ['💯', '⭐', '✨'],
            'flawless': ['💎', '✨', '👑']
        }
        
        message_lower = message.content.lower()
        
        # Check for gaming achievements
        for trigger, reactions in gaming_triggers.items():
            if trigger in message_lower:
                if random.random() < 0.8:  # 80% chance
                    try:
                        await message.add_reaction(random.choice(reactions))
                        
                        # Chance for congratulatory response
                        if random.random() < 0.3:  # 30% chance
                            congrats_messages = [
                                "That's incredible! Well done! 🎉",
                                "Amazing achievement! You're on fire! 🔥",
                                "Absolutely legendary! Keep it up! 👑",
                                "That's what I'm talking about! 💪",
                                "Epic gaming moment right there! ⚡"
                            ]
                            await asyncio.sleep(1)
                            await message.reply(random.choice(congrats_messages), mention_author=False)
                    except:
                        pass
                break
        
        # General gaming enthusiasm
        gaming_words = ['gaming', 'playing', 'stream', 'twitch', 'youtube gaming', 'esports']
        if any(word in message_lower for word in gaming_words):
            if random.random() < 0.2:  # 20% chance
                try:
                    await message.add_reaction('🎮')
                except:
                    pass

async def setup(bot):
    await bot.add_cog(AutoGaming(bot))