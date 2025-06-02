import discord
from discord.ext import commands, tasks
import aiosqlite
import asyncio
import random
from datetime import datetime, timezone, timedelta

class ViralContent(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # All automated messaging disabled

    @tasks.loop(hours=6)
    async def viral_challenges(self):
        """Disabled - no automated challenges"""
        return
        challenges = [
            {
                "title": "🔥 Gaming Setup Tour Challenge",
                "description": "Post a photo of your gaming setup and rate others! Best setup gets crowned! Use reactions to vote!",
                "hashtag": "#SetupTour",
                "channel": "tech-talk"
            },
            {
                "title": "⚡ One-Minute Gaming Story",
                "description": "Tell your most epic gaming moment in exactly one minute of reading time! Ready, set, GO!",
                "hashtag": "#EpicMinute",
                "channel": "gaming-talk"
            },
            {
                "title": "🎮 Game Title Emoji Challenge",
                "description": "Describe your favorite game using ONLY emojis! Others have to guess! First correct guess wins!",
                "hashtag": "#EmojiGame",
                "channel": "gaming-talk"
            },
            {
                "title": "🏆 Achievement Flex Friday",
                "description": "Screenshot your rarest achievement/trophy! Let's see who has the most insane collection!",
                "hashtag": "#AchievementFlex",
                "channel": "achievements"
            },
            {
                "title": "💭 Controversial Gaming Opinion",
                "description": "Share your most controversial gaming hot take! Respectful debate encouraged! 🍿",
                "hashtag": "#HotTake",
                "channel": "gaming-talk"
            }
        ]
        
        for guild in self.bot.guilds:
            if random.random() < 0.8:
                challenge = random.choice(challenges)
                target_channel = discord.utils.get(guild.text_channels, name=challenge["channel"]) or \
                               discord.utils.get(guild.text_channels, name="general-chat")
                
                if target_channel:
                    embed = discord.Embed(
                        title=challenge["title"],
                        description=f"{challenge['description']}\n\n**{challenge['hashtag']}**",
                        color=0xff1744
                    )
                    embed.add_field(name="⏰ Duration", value="Next 24 hours!", inline=True)
                    embed.add_field(name="🎁 Reward", value="Community recognition + 2000 coins", inline=True)
                    embed.set_footer(text="Join the trend and go viral!")
                    
                    try:
                        message = await target_channel.send("@everyone 🚨 **VIRAL CHALLENGE ALERT** 🚨", embed=embed)
                        await message.add_reaction("🔥")
                        await message.add_reaction("💯")
                        await message.add_reaction("⚡")
                    except:
                        pass

    @tasks.loop(hours=2)
    async def trend_monitor(self):
        """Monitor and amplify trending topics"""
        trending_topics = [
            "What's the most underrated game that deserves a sequel?",
            "If you could live in any game universe, where would you choose?",
            "What's your biggest gaming confession?",
            "Which game soundtrack hits different at 3AM?",
            "What's the most money you've spent on a single game?",
            "Which gaming character would be your best friend IRL?",
            "What's your weirdest gaming habit?",
            "Which game made you rage quit the hardest?",
            "What's the longest you've played a game in one session?",
            "Which game do you pretend not to like but secretly love?"
        ]
        
        for guild in self.bot.guilds:
            gaming_channel = discord.utils.get(guild.text_channels, name="gaming-talk")
            if gaming_channel and random.random() < 0.6:
                topic = random.choice(trending_topics)
                
                embed = discord.Embed(
                    title="🌊 TRENDING NOW",
                    description=f"**{topic}**\n\nDrop your answer below and react to others! Let's see this blow up! 📈",
                    color=0x00d4aa
                )
                embed.set_footer(text="The most viral answers get featured!")
                
                try:
                    message = await gaming_channel.send(embed=embed)
                    await message.add_reaction("👀")
                    await message.add_reaction("🔥")
                    await message.add_reaction("💬")
                except:
                    pass

    @tasks.loop(minutes=30)
    async def content_boost(self):
        """Boost engaging content automatically"""
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                if channel.name in ["gaming-talk", "general-chat", "memes-and-fun"]:
                    try:
                        # Get recent messages
                        messages = []
                        async for message in channel.history(limit=20, after=datetime.now(timezone.utc) - timedelta(hours=1)):
                            if not message.author.bot and len(message.content) > 50:
                                messages.append(message)
                        
                        # Boost messages with potential
                        for message in messages[:3]:  # Only boost top 3
                            if len(message.reactions) < 3 and random.random() < 0.4:
                                boost_reactions = ["🔥", "💯", "⚡", "👀", "💬"]
                                await message.add_reaction(random.choice(boost_reactions))
                                await asyncio.sleep(0.5)
                    except:
                        pass

    @commands.Cog.listener()
    async def on_message(self, message):
        """Detect and amplify viral potential"""
        if message.author.bot or not message.guild:
            return
        
        # Viral keywords detection
        viral_indicators = [
            'unpopular opinion', 'hot take', 'controversial', 'change my mind',
            'fight me', 'anyone else', 'am i the only one', 'confession',
            'controversial take', 'hear me out', 'red flag', 'green flag'
        ]
        
        message_lower = message.content.lower()
        
        # Check for viral potential
        if any(indicator in message_lower for indicator in viral_indicators):
            if random.random() < 0.7:
                try:
                    await message.add_reaction("👀")
                    await message.add_reaction("🍿")
                    
                    viral_responses = [
                        "This is about to get spicy! 🌶️",
                        "Someone said controversial take? I'm here for it! 👀",
                        "The tea is HOT today! ☕",
                        "This is the content we came for! 🔥"
                    ]
                    
                    if random.random() < 0.3:
                        await asyncio.sleep(1)
                        await message.reply(random.choice(viral_responses), mention_author=False)
                except:
                    pass
        
        # Amplify questions
        if '?' in message.content and len(message.content) > 30:
            if random.random() < 0.4:
                try:
                    await message.add_reaction("💭")
                except:
                    pass
        
        # Detect storytelling
        story_words = ['so i was', 'this one time', 'funny story', 'true story', 'no joke']
        if any(word in message_lower for word in story_words):
            if random.random() < 0.5:
                try:
                    await message.add_reaction("📖")
                    await message.add_reaction("👂")
                except:
                    pass

    @viral_challenges.before_loop
    @trend_monitor.before_loop
    @content_boost.before_loop
    async def before_loops(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(ViralContent(bot))