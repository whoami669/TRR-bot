import discord
from discord.ext import commands, tasks
import aiosqlite
import asyncio
import random
from datetime import datetime, timezone, timedelta

class HypeMachine(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # All automated messaging completely disabled
        pass

    @tasks.loop(hours=6)
    async def hype_bursts(self):
        """Create sudden bursts of hype and energy"""
        hype_messages = [
            "🔥 **ENERGY CHECK!** Who's still crushing it today? React with ⚡ if you're ALIVE!",
            "💥 **HYPE TRAIN INCOMING!** All aboard! What's got you pumped right now?",
            "🚀 **MOMENTUM ALERT!** This server is about to EXPLODE with activity! Who's ready?",
            "⚡ **POWER SURGE!** Drop your most FIRE gaming moment in the next 5 minutes!",
            "🎊 **VIBE CHECK!** Rate your current energy: 1-10! Let's see those numbers!",
            "💯 **PEAK PERFORMANCE MODE!** What achievement are you most proud of today?",
            "🔥 **UNSTOPPABLE FORCE!** Name one thing that makes you feel LEGENDARY!",
            "⭐ **STAR POWER ACTIVATED!** Time to shine! What's your superpower?",
            "🌊 **WAVE OF ENERGY!** Ride this wave! What's your next big goal?",
            "💎 **DIAMOND MINDSET!** Pressure makes diamonds! What challenge are you crushing?"
        ]
        
        for guild in self.bot.guilds:
            general_channel = discord.utils.get(guild.text_channels, name="general-chat")
            if general_channel and random.random() < 0.2:
                hype_msg = random.choice(hype_messages)
                try:
                    message = await general_channel.send(hype_msg)
                    reactions = ["🔥", "⚡", "💥", "🚀", "💯", "⭐"]
                    for reaction in random.sample(reactions, 3):
                        await message.add_reaction(reaction)
                        await asyncio.sleep(0.3)
                except:
                    pass

    @tasks.loop(hours=2)
    async def energy_waves(self):
        """Send waves of motivational energy"""
        energy_topics = [
            {
                "title": "💪 UNSTOPPABLE ENERGY WAVE",
                "content": "Nothing can stop you when you're in the zone! What puts you in your FLOW STATE?",
                "reactions": ["💪", "🔥", "⚡"]
            },
            {
                "title": "🎯 LASER FOCUS MODE",
                "content": "Time to LOCK IN! What's the one thing you're absolutely dominating right now?",
                "reactions": ["🎯", "👁️", "🔒"]
            },
            {
                "title": "🚀 BREAKTHROUGH MOMENT",
                "content": "Every legend has that ONE moment! Share your biggest breakthrough or 'AHA!' moment!",
                "reactions": ["🚀", "💡", "🎊"]
            },
            {
                "title": "⚡ ELECTRIC ATMOSPHERE",
                "content": "The energy in here is INSANE! What's charging you up today?",
                "reactions": ["⚡", "🔋", "⭐"]
            }
        ]
        
        for guild in self.bot.guilds:
            gaming_channel = discord.utils.get(guild.text_channels, name="gaming-talk")
            target_channel = gaming_channel or discord.utils.get(guild.text_channels, name="general-chat")
            
            if target_channel and random.random() < 0.8:
                topic = random.choice(energy_topics)
                embed = discord.Embed(
                    title=topic["title"],
                    description=topic["content"],
                    color=0xff0040
                )
                embed.set_footer(text="RIDE THE WAVE OF ENERGY!")
                
                try:
                    message = await target_channel.send(embed=embed)
                    for reaction in topic["reactions"]:
                        await message.add_reaction(reaction)
                        await asyncio.sleep(0.2)
                except:
                    pass

    @tasks.loop(minutes=20)
    async def momentum_builder(self):
        """Build momentum through smart engagement"""
        for guild in self.bot.guilds:
            # Check for recent activity and amplify it
            for channel in guild.text_channels:
                if channel.name in ["general-chat", "gaming-talk"]:
                    try:
                        recent_messages = []
                        async for msg in channel.history(limit=10, after=datetime.now(timezone.utc) - timedelta(minutes=20)):
                            if not msg.author.bot and len(msg.content) > 20:
                                recent_messages.append(msg)
                        
                        # If there's activity, amplify it
                        if len(recent_messages) >= 2:
                            momentum_boosters = [
                                "🔥 This chat is ON FIRE! Keep it going!",
                                "⚡ The energy here is ELECTRIC! More of this!",
                                "💥 MOMENTUM BUILDING! Who else wants to join in?",
                                "🚀 This conversation is taking OFF! Love to see it!",
                                "💯 The vibe is PERFECT right now! Don't stop!"
                            ]
                            
                            if random.random() < 0.4:
                                booster = random.choice(momentum_boosters)
                                await channel.send(booster)
                                
                        # Add reactions to build momentum
                        for msg in recent_messages[:2]:
                            if len(msg.reactions) < 2 and random.random() < 0.6:
                                momentum_reactions = ["🔥", "💯", "⚡", "👀", "💪"]
                                await msg.add_reaction(random.choice(momentum_reactions))
                                await asyncio.sleep(0.5)
                    except:
                        pass

    @commands.Cog.listener()
    async def on_message(self, message):
        """Detect and amplify hype moments"""
        if message.author.bot or not message.guild:
            return
        
        # Hype words that get instant amplification
        hype_words = [
            'lets go', 'lets goo', 'lets gooo', 'poggers', 'pog', 'sheesh',
            'no way', 'insane', 'crazy', 'unreal', 'incredible', 'amazing',
            'legendary', 'epic win', 'clutch', 'goated', 'built different',
            'that was sick', 'absolutely insane', 'mind blown', 'fire',
            'thats fire', 'straight fire', 'pure fire', 'on fire'
        ]
        
        message_lower = message.content.lower()
        
        # Instant hype amplification
        if any(word in message_lower for word in hype_words):
            if random.random() < 0.8:
                try:
                    await message.add_reaction("🔥")
                    await asyncio.sleep(0.2)
                    await message.add_reaction("💯")
                    
                    # Chance for hype response
                    if random.random() < 0.4:
                        hype_responses = [
                            "YOOOOO! 🔥🔥🔥",
                            "That's what I'm talking about! ⚡",
                            "SHEESH! The energy! 💥",
                            "FIRE ALERT! 🚨🔥",
                            "ABSOLUTELY LEGENDARY! 👑",
                            "NO WAY! That's insane! 🤯",
                            "BUILT DIFFERENT! 💪⚡"
                        ]
                        await asyncio.sleep(1)
                        await message.reply(random.choice(hype_responses), mention_author=False)
                except:
                    pass
        
        # Detect excitement levels
        exclamation_count = message.content.count('!')
        caps_ratio = sum(1 for c in message.content if c.isupper()) / max(len(message.content), 1)
        
        if exclamation_count >= 2 or caps_ratio > 0.6:
            if random.random() < 0.6:
                try:
                    energy_reactions = ["⚡", "🔥", "💥", "🚀"]
                    await message.add_reaction(random.choice(energy_reactions))
                except:
                    pass

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Hype up new members"""
        if member.bot:
            return
        
        general_channel = discord.utils.get(member.guild.text_channels, name="general-chat")
        if general_channel:
            hype_welcomes = [
                f"🔥 YOOOOO! {member.mention} just ENTERED THE BUILDING! Welcome to the squad! 🎉",
                f"⚡ ENERGY BOOST! {member.mention} just joined the party! Let's show them what we're about! 💥",
                f"🚀 NEW LEGEND ALERT! {member.mention} welcome to the most FIRE community on Discord! 🔥",
                f"💯 THE SQUAD JUST GOT STRONGER! Welcome {member.mention}! Ready to have some fun? ⚡",
                f"🎊 ANOTHER LEGEND JOINS! {member.mention} you picked the RIGHT server! Let's gooo! 🔥"
            ]
            
            if random.random() < 0.8:
                try:
                    await asyncio.sleep(3)
                    welcome_msg = await general_channel.send(random.choice(hype_welcomes))
                    await welcome_msg.add_reaction("🔥")
                    await welcome_msg.add_reaction("🎉")
                    await welcome_msg.add_reaction("⚡")
                except:
                    pass

    @hype_bursts.before_loop
    @energy_waves.before_loop
    @momentum_builder.before_loop
    async def before_loops(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(HypeMachine(bot))