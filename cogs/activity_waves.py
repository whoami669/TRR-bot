import discord
from discord.ext import commands, tasks
import aiosqlite
import asyncio
import random
from datetime import datetime, timezone, timedelta

class ActivityWaves(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.wave_generator.start()
        self.activity_storms.start()
        self.engagement_tsunamis.start()
        self.community_pulses.start()

    @tasks.loop(minutes=6)
    async def wave_generator(self):
        """Generate waves of activity across different channels"""
        wave_types = [
            {
                "name": "Discussion Wave",
                "channels": ["general-chat", "gaming-talk"],
                "messages": [
                    "🌊 DISCUSSION WAVE INCOMING! What's the most mind-blowing thing that happened to you this week?",
                    "💭 THOUGHT WAVE ACTIVATED! Share your most random shower thought about gaming!",
                    "🧠 BRAIN WAVE SURGE! What's something you learned recently that blew your mind?",
                    "💡 IDEA WAVE FLOWING! If you could invent any game feature, what would it be?"
                ]
            },
            {
                "name": "Energy Wave", 
                "channels": ["general-chat", "gaming-talk"],
                "messages": [
                    "⚡ ENERGY WAVE DETECTED! Drop your current energy level (1-10) and what's fueling it!",
                    "🔥 MOTIVATION WAVE! What's keeping you pumped up today?",
                    "💪 POWER WAVE SURGE! Share something you're crushing at right now!",
                    "🚀 MOMENTUM WAVE! What goal are you actively working towards?"
                ]
            },
            {
                "name": "Gaming Wave",
                "channels": ["gaming-talk"],
                "messages": [
                    "🎮 GAMING WAVE ACTIVATED! What's your current gaming obsession?",
                    "🏆 ACHIEVEMENT WAVE! Brag about your latest gaming accomplishment!",
                    "💀 RAGE WAVE! What game made you question your life choices recently?",
                    "🎯 SKILL WAVE! What gaming skill are you trying to master right now?"
                ]
            },
            {
                "name": "Social Wave",
                "channels": ["general-chat"],
                "messages": [
                    "👥 SOCIAL WAVE RISING! Tag someone who's been awesome lately and tell them why!",
                    "🤝 CONNECTION WAVE! Share how you met your best gaming buddy!",
                    "💙 APPRECIATION WAVE! What do you love most about this community?",
                    "🌟 RECOGNITION WAVE! Shoutout someone who deserves more credit!"
                ]
            }
        ]
        
        for guild in self.bot.guilds:
            if random.random() < 0.8:
                wave = random.choice(wave_types)
                target_channels = []
                
                for channel_name in wave["channels"]:
                    channel = discord.utils.get(guild.text_channels, name=channel_name)
                    if channel:
                        target_channels.append(channel)
                
                if target_channels:
                    channel = random.choice(target_channels)
                    message_text = random.choice(wave["messages"])
                    
                    try:
                        message = await channel.send(message_text)
                        wave_reactions = ["🌊", "⚡", "🔥", "💯", "👀"]
                        for reaction in random.sample(wave_reactions, 3):
                            await message.add_reaction(reaction)
                            await asyncio.sleep(0.4)
                    except:
                        pass

    @tasks.loop(minutes=18)
    async def activity_storms(self):
        """Create intense bursts of coordinated activity"""
        storm_scenarios = [
            {
                "title": "⛈️ GAMING STORM ALERT",
                "description": "Multiple gaming topics dropping at once! Choose your battlefield!",
                "topics": [
                    "🎯 Most underrated indie game you've played?",
                    "💀 Hardest boss fight you've ever conquered?", 
                    "🏆 Achievement you're most proud of?",
                    "🎮 Game that completely changed your perspective?"
                ]
            },
            {
                "title": "🌪️ OPINION TORNADO",
                "description": "Controversial takes spinning everywhere! Enter at your own risk!",
                "topics": [
                    "🔥 Most overrated popular game?",
                    "💭 Gaming opinion that might get you canceled?",
                    "⚡ Feature that ruins modern games?",
                    "🎯 Game series that peaked and went downhill?"
                ]
            },
            {
                "title": "💥 NOSTALGIA EXPLOSION", 
                "description": "Memories flooding in from all directions! Share your stories!",
                "topics": [
                    "🕹️ First game that made you cry?",
                    "👾 Best gaming memory with friends?",
                    "🎮 Game that defined your childhood?",
                    "⭐ Moment you fell in love with gaming?"
                ]
            }
        ]
        
        for guild in self.bot.guilds:
            gaming_channel = discord.utils.get(guild.text_channels, name="gaming-talk")
            if gaming_channel and random.random() < 0.6:
                storm = random.choice(storm_scenarios)
                
                embed = discord.Embed(
                    title=storm["title"],
                    description=storm["description"],
                    color=0xff4444
                )
                
                topics_text = "\n".join([f"• {topic}" for topic in storm["topics"]])
                embed.add_field(name="🎯 Choose Your Topic", value=topics_text, inline=False)
                embed.set_footer(text="Multiple conversations incoming! Jump into any or all!")
                
                try:
                    message = await gaming_channel.send(embed=embed)
                    storm_reactions = ["⛈️", "💥", "🌪️", "🔥", "⚡"]
                    for reaction in storm_reactions:
                        await message.add_reaction(reaction)
                        await asyncio.sleep(0.3)
                except:
                    pass

    @tasks.loop(minutes=35)
    async def engagement_tsunamis(self):
        """Create massive engagement events that sweep across the server"""
        tsunami_events = [
            {
                "title": "🌊 MEGA ENGAGEMENT TSUNAMI",
                "description": "EVERYONE PARTICIPATE! This is server-wide madness!",
                "challenge": "Next 10 minutes: Everyone share ONE thing that makes them unique! Let's flood this chat with personality!",
                "reward": "Most creative answer gets legendary status!"
            },
            {
                "title": "🌊 RAPID FIRE TSUNAMI", 
                "description": "SPEED ROUND ACTIVATED! Lightning fast responses only!",
                "challenge": "60 seconds: Drop your gaming hot take in 10 words or less! GO GO GO!",
                "reward": "Fastest and spiciest takes get crowned!"
            },
            {
                "title": "🌊 STORY TSUNAMI",
                "description": "NARRATIVE FLOOD WARNING! Everyone becomes a storyteller!",
                "challenge": "Tell your most EPIC gaming moment in exactly 3 sentences! Make it LEGENDARY!",
                "reward": "Best stories get featured in hall of fame!"
            },
            {
                "title": "🌊 REACTION TSUNAMI",
                "description": "EMOJI EXPLOSION INCOMING! React to everything!",
                "challenge": "Next 5 minutes: React to every message with the PERFECT emoji! Create emoji chaos!",
                "reward": "Most creative emoji usage wins!"
            }
        ]
        
        for guild in self.bot.guilds:
            general_channel = discord.utils.get(guild.text_channels, name="general-chat")
            if general_channel and random.random() < 0.5:
                tsunami = random.choice(tsunami_events)
                
                embed = discord.Embed(
                    title=tsunami["title"],
                    description=f"**{tsunami['description']}**\n\n🎯 **CHALLENGE:**\n{tsunami['challenge']}\n\n🏆 **REWARD:**\n{tsunami['reward']}",
                    color=0x00aaff
                )
                embed.set_footer(text="TSUNAMI ALERT: MAXIMUM PARTICIPATION REQUIRED!")
                
                try:
                    message = await general_channel.send("@everyone 🚨 **ENGAGEMENT TSUNAMI DETECTED** 🚨", embed=embed)
                    tsunami_reactions = ["🌊", "💥", "⚡", "🔥", "💯", "🚀"]
                    for reaction in tsunami_reactions:
                        await message.add_reaction(reaction)
                        await asyncio.sleep(0.2)
                except:
                    pass

    @tasks.loop(minutes=14)
    async def community_pulses(self):
        """Send regular pulses of community energy"""
        pulse_messages = [
            {
                "type": "appreciation",
                "content": "💙 COMMUNITY PULSE: This server has the most INCREDIBLE energy! What's your favorite thing about being here?",
                "reactions": ["💙", "🥰", "🌟"]
            },
            {
                "type": "energy_check", 
                "content": "⚡ ENERGY PULSE: How's everyone's vibe right now? Drop an emoji that represents your current mood!",
                "reactions": ["😊", "🔥", "💪", "😎", "🤔"]
            },
            {
                "type": "connection",
                "content": "🤝 CONNECTION PULSE: Tag someone random and tell them one thing you appreciate about them!",
                "reactions": ["🤝", "❤️", "👏"]
            },
            {
                "type": "motivation",
                "content": "🚀 MOTIVATION PULSE: What's keeping you motivated today? Share your driving force!",
                "reactions": ["🚀", "💪", "⚡"]
            },
            {
                "type": "curiosity",
                "content": "🤔 CURIOSITY PULSE: What's something you've been wondering about lately? Let's explore together!",
                "reactions": ["🤔", "💭", "🧠"]
            }
        ]
        
        for guild in self.bot.guilds:
            general_channel = discord.utils.get(guild.text_channels, name="general-chat")
            if general_channel and random.random() < 0.7:
                pulse = random.choice(pulse_messages)
                
                try:
                    message = await general_channel.send(pulse["content"])
                    for reaction in pulse["reactions"]:
                        await message.add_reaction(reaction)
                        await asyncio.sleep(0.4)
                except:
                    pass

    @commands.Cog.listener()
    async def on_message(self, message):
        """Detect and amplify wave-worthy content"""
        if message.author.bot or not message.guild:
            return
        
        # Detect wave indicators
        wave_triggers = [
            'everyone', 'anyone else', 'all of you', 'community', 'squad',
            'lets all', 'group activity', 'server wide', 'mass participation'
        ]
        
        message_lower = message.content.lower()
        
        if any(trigger in message_lower for trigger in wave_triggers):
            if random.random() < 0.8:
                try:
                    await message.add_reaction("🌊")
                    await message.add_reaction("💥")
                    
                    # Sometimes amplify with encouraging response
                    if random.random() < 0.3:
                        wave_responses = [
                            "WAVE DETECTED! Everyone jump in! 🌊",
                            "TSUNAMI INCOMING! All hands on deck! 💥",
                            "COMMUNITY ACTIVATION! Let's go! ⚡"
                        ]
                        await asyncio.sleep(1)
                        await message.reply(random.choice(wave_responses), mention_author=False)
                except:
                    pass

    @wave_generator.before_loop
    @activity_storms.before_loop  
    @engagement_tsunamis.before_loop
    @community_pulses.before_loop
    async def before_loops(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(ActivityWaves(bot))