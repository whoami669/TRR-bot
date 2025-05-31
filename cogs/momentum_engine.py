import discord
from discord.ext import commands, tasks
import aiosqlite
import asyncio
import random
from datetime import datetime, timezone, timedelta

class MomentumEngine(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # All automated messaging completely disabled
        pass

    @tasks.loop(minutes=10)
    async def peak_hour_detector(self):
        """Detect and amplify peak activity hours"""
        for guild in self.bot.guilds:
            current_hour = datetime.now().hour
            
            # Prime time hours (evening/night for most users)
            if current_hour in [18, 19, 20, 21, 22, 23]:
                for channel in guild.text_channels:
                    if channel.name in ["general-chat", "gaming-talk"]:
                        try:
                            # Count recent activity
                            activity_count = 0
                            async for message in channel.history(limit=50, after=datetime.now(timezone.utc) - timedelta(minutes=30)):
                                if not message.author.bot:
                                    activity_count += 1
                            
                            # If it's peak hours and there's activity, amplify it
                            if activity_count >= 5 and random.random() < 0.7:
                                peak_messages = [
                                    "🔥 PEAK HOURS ACTIVATED! The energy is UNREAL right now!",
                                    "⚡ PRIME TIME! This is when legends are made! Keep it going!",
                                    "💥 THE PERFECT STORM! Everyone's online and the vibes are IMMACULATE!",
                                    "🚀 PEAK PERFORMANCE HOURS! The server is absolutely ALIVE!",
                                    "💯 GOLDEN HOUR! This is exactly what peak Discord looks like!"
                                ]
                                
                                message = await channel.send(random.choice(peak_messages))
                                await message.add_reaction("🔥")
                                await message.add_reaction("⚡")
                                await message.add_reaction("💯")
                        except:
                            pass

    @tasks.loop(minutes=5)
    async def conversation_momentum(self):
        """Maintain and build conversation momentum"""
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                if channel.name in ["general-chat", "gaming-talk", "tech-talk"]:
                    try:
                        # Check for conversation gaps
                        last_message = None
                        async for message in channel.history(limit=1):
                            if not message.author.bot:
                                last_message = message
                                break
                        
                        if last_message:
                            time_since = datetime.now(timezone.utc) - last_message.created_at
                            
                            # If conversation died down (5-15 minutes), reignite it
                            if 5 <= time_since.total_seconds() / 60 <= 15 and random.random() < 0.4:
                                momentum_restarters = [
                                    "The chat got quiet... TOO QUIET! What's everyone up to? 👀",
                                    "Someone drop a conversation starter! The silence is LOUD! 💬",
                                    "Quick! Someone say something INTERESTING! Let's get this rolling again! 🔥",
                                    "The momentum machine needs fuel! What's on your mind? ⚡",
                                    "Break the silence! What's the most random thing you're thinking about right now? 🤔"
                                ]
                                
                                await channel.send(random.choice(momentum_restarters))
                                
                            # If there's recent activity, keep the momentum going
                            elif time_since.total_seconds() / 60 <= 3:
                                # Check if it's a question or discussion
                                if '?' in last_message.content and len(last_message.reactions) == 0:
                                    momentum_boosters = ["👀", "🤔", "💭", "💬"]
                                    await last_message.add_reaction(random.choice(momentum_boosters))
                    except:
                        pass

    @tasks.loop(minutes=20)
    async def energy_sustainer(self):
        """Sustain energy levels throughout the day"""
        energy_levels = {
            "morning": [6, 7, 8, 9, 10, 11],
            "afternoon": [12, 13, 14, 15, 16, 17], 
            "evening": [18, 19, 20, 21],
            "night": [22, 23, 0, 1, 2, 3, 4, 5]
        }
        
        current_hour = datetime.now().hour
        
        for guild in self.bot.guilds:
            general_channel = discord.utils.get(guild.text_channels, name="general-chat")
            if general_channel and random.random() < 0.3:
                
                if current_hour in energy_levels["morning"]:
                    messages = [
                        "☀️ MORNING ENERGY! Rise and grind, legends! What's the plan for today?",
                        "🌅 FRESH START! New day, new opportunities to be LEGENDARY!",
                        "☕ CAFFEINE AND CONFIDENCE! Let's make today INSANE!"
                    ]
                elif current_hour in energy_levels["afternoon"]:
                    messages = [
                        "⚡ AFTERNOON POWER! Keep that momentum rolling! How's everyone doing?",
                        "🔥 MIDDAY MOTIVATION! Don't let the energy drop! What's keeping you busy?",
                        "💪 AFTERNOON GRIND! The legends never rest! What's everyone working on?"
                    ]
                elif current_hour in energy_levels["evening"]:
                    messages = [
                        "🌟 PRIME TIME! The best hours are HERE! Let's make them COUNT!",
                        "🔥 EVENING EXCELLENCE! This is when the MAGIC happens!",
                        "⚡ PEAK HOURS! Everyone's online and the energy is ELECTRIC!"
                    ]
                else:  # night
                    messages = [
                        "🌙 NIGHT OWL ENERGY! The real ones are still up! What's good?",
                        "⭐ MIDNIGHT VIBES! Late night energy hits different! Who's still here?",
                        "🦉 NOCTURNAL LEGENDS! The night shift is the BEST shift!"
                    ]
                
                try:
                    await general_channel.send(random.choice(messages))
                except:
                    pass

    @tasks.loop(minutes=7)
    async def activity_cascades(self):
        """Create cascading activity across channels"""
        for guild in self.bot.guilds:
            # Find the most active channel in the last hour
            most_active_channel = None
            highest_activity = 0
            
            for channel in guild.text_channels:
                if channel.name in ["general-chat", "gaming-talk", "tech-talk", "memes-and-fun"]:
                    try:
                        activity_count = 0
                        async for message in channel.history(limit=30, after=datetime.now(timezone.utc) - timedelta(hours=1)):
                            if not message.author.bot:
                                activity_count += 1
                        
                        if activity_count > highest_activity:
                            highest_activity = activity_count
                            most_active_channel = channel
                    except:
                        pass
            
            # If we found an active channel with good activity, spread it
            if most_active_channel and highest_activity >= 5:
                other_channels = [ch for ch in guild.text_channels 
                               if ch.name in ["general-chat", "gaming-talk", "tech-talk"] 
                               and ch != most_active_channel]
                
                if other_channels and random.random() < 0.4:
                    target_channel = random.choice(other_channels)
                    cascade_messages = [
                        f"🔥 The energy in #{most_active_channel.name} is INSANE! Bring that same energy here!",
                        f"⚡ #{most_active_channel.name} is going OFF! Let's get this channel to the same level!",
                        f"💥 Someone's cooking in #{most_active_channel.name}! Time to match that energy!",
                        f"🚀 #{most_active_channel.name} is absolutely FLYING! Your turn to contribute!"
                    ]
                    
                    try:
                        await target_channel.send(random.choice(cascade_messages))
                    except:
                        pass

    @commands.Cog.listener()
    async def on_message(self, message):
        """React to momentum-building messages"""
        if message.author.bot or not message.guild:
            return
        
        # Detect momentum-building keywords
        momentum_words = [
            'everyone', 'anyone', 'thoughts', 'opinions', 'what do you think',
            'agree', 'disagree', 'discussion', 'debate', 'conversation',
            'chat', 'talk', 'lets go', 'hype', 'energy', 'vibe'
        ]
        
        message_lower = message.content.lower()
        
        # Boost messages that encourage engagement
        if any(word in message_lower for word in momentum_words):
            if random.random() < 0.6:
                try:
                    await message.add_reaction("💬")
                    await asyncio.sleep(0.5)
                    await message.add_reaction("👥")
                except:
                    pass
        
        # Detect and amplify storytelling
        story_starters = ['so yesterday', 'this morning', 'earlier today', 'last night', 
                         'funny story', 'true story', 'story time', 'storytime']
        
        if any(starter in message_lower for starter in story_starters):
            if random.random() < 0.7:
                try:
                    await message.add_reaction("👂")
                    await message.add_reaction("📖")
                    
                    if random.random() < 0.3:
                        story_responses = [
                            "Story time! I'm listening! 👂",
                            "Ooh, this sounds good! Continue! 📖",
                            "I'm invested! What happened next? 👀"
                        ]
                        await asyncio.sleep(2)
                        await message.reply(random.choice(story_responses), mention_author=False)
                except:
                    pass

    @peak_hour_detector.before_loop
    @conversation_momentum.before_loop
    @energy_sustainer.before_loop
    @activity_cascades.before_loop
    async def before_loops(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(MomentumEngine(bot))