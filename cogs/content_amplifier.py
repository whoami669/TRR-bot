import discord
from discord.ext import commands, tasks
import aiosqlite
import asyncio
import random
from datetime import datetime, timezone, timedelta

class ContentAmplifier(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.content_scanner.start()
        self.reaction_cascades.start()
        self.engagement_multiplier.start()

    @tasks.loop(minutes=15)
    async def content_scanner(self):
        """Scan for high-quality content and amplify it"""
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                if channel.name in ["general-chat", "gaming-talk", "memes-and-fun", "screenshots"]:
                    try:
                        # Get recent messages
                        recent_messages = []
                        async for message in channel.history(limit=30, after=datetime.now(timezone.utc) - timedelta(hours=2)):
                            if not message.author.bot and len(message.content) > 20:
                                recent_messages.append(message)
                        
                        # Score messages based on engagement potential
                        for message in recent_messages:
                            score = self.calculate_engagement_score(message)
                            
                            if score > 7 and len(message.reactions) < 3:
                                # High potential content - amplify it
                                amplify_reactions = ["🔥", "💯", "⚡", "👀", "💬", "🎮", "🚀"]
                                selected_reactions = random.sample(amplify_reactions, min(3, len(amplify_reactions)))
                                
                                for reaction in selected_reactions:
                                    await message.add_reaction(reaction)
                                    await asyncio.sleep(0.5)
                                
                                # Chance for amplification comment
                                if score > 9 and random.random() < 0.3:
                                    amplify_comments = [
                                        "This content is FIRE! 🔥",
                                        "Quality content right here! 💯",
                                        "Everyone needs to see this! 👀",
                                        "This is why I love this community! ⚡"
                                    ]
                                    await asyncio.sleep(2)
                                    await message.reply(random.choice(amplify_comments), mention_author=False)
                    except:
                        pass

    def calculate_engagement_score(self, message):
        """Calculate engagement potential score (0-10)"""
        score = 0
        content = message.content.lower()
        
        # Length bonus
        if 50 <= len(message.content) <= 200:
            score += 2
        elif len(message.content) > 200:
            score += 1
        
        # Question bonus (encourages discussion)
        if '?' in content:
            score += 2
        
        # Gaming keywords
        gaming_words = ['game', 'play', 'gaming', 'stream', 'win', 'lose', 'achievement', 'level']
        score += min(2, sum(1 for word in gaming_words if word in content))
        
        # Enthusiasm indicators
        excitement_words = ['amazing', 'awesome', 'incredible', 'epic', 'legendary', 'insane', 'crazy']
        score += min(2, sum(1 for word in excitement_words if word in content))
        
        # Exclamation marks (but not too many)
        exclamations = content.count('!')
        if 1 <= exclamations <= 3:
            score += 1
        
        # Attachment bonus
        if message.attachments:
            score += 1
        
        # Existing engagement
        reaction_count = sum(reaction.count for reaction in message.reactions)
        if reaction_count > 0:
            score += min(2, reaction_count)
        
        return min(10, score)

    @tasks.loop(minutes=10)
    async def reaction_cascades(self):
        """Create reaction cascades on popular content"""
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                try:
                    # Find messages with momentum
                    async for message in channel.history(limit=20, after=datetime.now(timezone.utc) - timedelta(hours=1)):
                        if not message.author.bot:
                            reaction_count = sum(reaction.count for reaction in message.reactions)
                            
                            # If message has 2+ reactions, add more to create cascade
                            if 2 <= reaction_count <= 5 and random.random() < 0.4:
                                cascade_reactions = ["🔥", "💯", "⚡", "👏", "🎉", "💪", "🚀"]
                                new_reaction = random.choice(cascade_reactions)
                                
                                # Don't add if already exists
                                existing_reactions = [str(r.emoji) for r in message.reactions]
                                if new_reaction not in existing_reactions:
                                    await message.add_reaction(new_reaction)
                                    await asyncio.sleep(0.5)
                except:
                    pass

    @tasks.loop(minutes=30)
    async def engagement_multiplier(self):
        """Multiply engagement during active periods"""
        for guild in self.bot.guilds:
            active_channels = []
            
            # Identify currently active channels
            for channel in guild.text_channels:
                if channel.name in ["general-chat", "gaming-talk"]:
                    try:
                        recent_count = 0
                        async for message in channel.history(limit=10, after=datetime.now(timezone.utc) - timedelta(minutes=30)):
                            if not message.author.bot:
                                recent_count += 1
                        
                        if recent_count >= 3:
                            active_channels.append(channel)
                    except:
                        pass
            
            # Boost active channels
            for channel in active_channels:
                if random.random() < 0.6:
                    engagement_boosters = [
                        "🔥 This chat is absolutely ON FIRE right now! Keep the energy going!",
                        "⚡ The momentum in here is INSANE! Don't stop now!",
                        "💥 PEAK ACTIVITY HOURS! This is what I love to see!",
                        "🚀 The vibe is PERFECT! Everyone's bringing their A-game!",
                        "💯 This is exactly the energy this server needs! More of this!"
                    ]
                    
                    try:
                        boost_message = await channel.send(random.choice(engagement_boosters))
                        await boost_message.add_reaction("🔥")
                        await boost_message.add_reaction("⚡")
                    except:
                        pass

    @commands.Cog.listener()
    async def on_message(self, message):
        """Real-time content amplification"""
        if message.author.bot or not message.guild:
            return
        
        # Instant amplification for high-value content
        score = self.calculate_engagement_score(message)
        
        if score >= 8:
            # High-value content gets instant boost
            try:
                await asyncio.sleep(random.uniform(1, 3))
                await message.add_reaction("🔥")
                
                if score >= 9:
                    await asyncio.sleep(1)
                    await message.add_reaction("💯")
            except:
                pass
        
        # Amplify based on channel context
        channel_amplifiers = {
            "gaming-talk": ["🎮", "🔥", "⚡"],
            "memes-and-fun": ["😂", "💀", "🔥"],
            "screenshots": ["📸", "🔥", "👀"],
            "achievements": ["🏆", "👏", "💪"]
        }
        
        if message.channel.name in channel_amplifiers:
            if random.random() < 0.3:
                try:
                    reaction = random.choice(channel_amplifiers[message.channel.name])
                    await message.add_reaction(reaction)
                except:
                    pass

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Amplify reactions that gain traction"""
        if user.bot:
            return
        
        message = reaction.message
        if message.author.bot:
            return
        
        # If a message gets 3+ reactions, consider it trending
        total_reactions = sum(r.count for r in message.reactions)
        
        if total_reactions >= 3 and random.random() < 0.4:
            # Add complementary reactions
            trending_reactions = ["🔥", "💯", "⚡", "👀", "💬"]
            existing = [str(r.emoji) for r in message.reactions]
            
            available_reactions = [r for r in trending_reactions if r not in existing]
            if available_reactions:
                try:
                    await message.add_reaction(random.choice(available_reactions))
                except:
                    pass

    @content_scanner.before_loop
    @reaction_cascades.before_loop
    @engagement_multiplier.before_loop
    async def before_loops(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(ContentAmplifier(bot))