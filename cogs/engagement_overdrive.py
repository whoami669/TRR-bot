import discord
from discord.ext import commands, tasks
import aiosqlite
import asyncio
import random
from datetime import datetime, timezone, timedelta

class EngagementOverdrive(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.hyperdrive_mode.start()
        self.turbocharged_events.start()
        self.maximum_engagement.start()
        self.nuclear_participation.start()

    @tasks.loop(minutes=7)
    async def hyperdrive_mode(self):
        """Activate hyperdrive engagement mode"""
        hyperdrive_events = [
            {
                "title": "🚀 HYPERDRIVE ACTIVATED",
                "mode": "MAXIMUM VELOCITY",
                "challenge": "Next 10 minutes: Share the FASTEST thing that comes to mind when I say 'EPIC GAMING MOMENT'!",
                "intensity": "LIGHTSPEED RESPONSES ONLY!"
            },
            {
                "title": "⚡ OVERDRIVE ENGAGED", 
                "mode": "EXTREME PARTICIPATION",
                "challenge": "EVERYONE MUST PARTICIPATE: Drop your gaming hot take in 3... 2... 1... GO!",
                "intensity": "NO HESITATION ALLOWED!"
            },
            {
                "title": "💥 WARP SPEED INITIATED",
                "mode": "INSTANTANEOUS MODE",
                "challenge": "RAPID FIRE: Name your top 3 games WITHOUT THINKING! First instinct only!",
                "intensity": "BRAIN-TO-KEYBOARD DIRECT CONNECTION!"
            },
            {
                "title": "🔥 AFTERBURNER IGNITED",
                "mode": "SUPERCHARGED ENERGY", 
                "challenge": "ENERGY CHECK: Rate your hype level 1-10 and JUSTIFY IT with pure enthusiasm!",
                "intensity": "MAXIMUM EMOTIONAL OUTPUT!"
            }
        ]
        
        for guild in self.bot.guilds:
            if random.random() < 0.8:
                gaming_channel = discord.utils.get(guild.text_channels, name="gaming-talk")
                general_channel = discord.utils.get(guild.text_channels, name="general-chat")
                target_channel = gaming_channel or general_channel
                
                if target_channel:
                    event = random.choice(hyperdrive_events)
                    
                    embed = discord.Embed(
                        title=event["title"],
                        description=f"**{event['mode']} ACTIVATED**\n\n🎯 **CHALLENGE:**\n{event['challenge']}\n\n⚡ **{event['intensity']}**",
                        color=0xff0000
                    )
                    embed.set_footer(text="HYPERDRIVE MODE: MAXIMUM ENGAGEMENT PROTOCOL!")
                    
                    try:
                        message = await target_channel.send("🚨 **HYPERDRIVE PROTOCOL INITIATED** 🚨", embed=embed)
                        hyperdrive_reactions = ["🚀", "⚡", "💥", "🔥", "💯"]
                        for reaction in hyperdrive_reactions:
                            await message.add_reaction(reaction)
                            await asyncio.sleep(0.1)
                    except:
                        pass

    @tasks.loop(minutes=21)
    async def turbocharged_events(self):
        """Create turbocharged mega-events"""
        turbo_events = [
            {
                "name": "TURBO CONFESSION HOUR",
                "description": "🏎️ TURBOCHARGED TRUTH TIME! Share your most OUTRAGEOUS gaming confession!",
                "rules": [
                    "Must be gaming-related and shocking",
                    "No shame allowed - own your choices",
                    "The more controversial, the better",
                    "Everyone judge with reactions only!"
                ]
            },
            {
                "name": "NITRO BOOST BRAGGING",
                "description": "💨 NITROUS POWERED FLEXING! Time to show off your most INSANE gaming achievements!",
                "rules": [
                    "Screenshots encouraged but not required",
                    "Humble bragging is FORBIDDEN",
                    "Go full ego mode - we want MAXIMUM pride",
                    "Others must react with appropriate awe!"
                ]
            },
            {
                "name": "SUPERCHARGED STORYTELLING",
                "description": "⚡ ELECTRIC NARRATIVE MODE! Tell your most LEGENDARY gaming story in exactly 4 sentences!",
                "rules": [
                    "Must be exactly 4 sentences - no more, no less",
                    "Each sentence must be MAXIMUM impact",
                    "Build to the most EPIC conclusion possible",
                    "Others vote with fire emojis for intensity!"
                ]
            }
        ]
        
        for guild in self.bot.guilds:
            if random.random() < 0.4:
                general_channel = discord.utils.get(guild.text_channels, name="general-chat")
                if general_channel:
                    event = random.choice(turbo_events)
                    
                    embed = discord.Embed(
                        title=f"🏎️ {event['name']} 🏎️",
                        description=event["description"],
                        color=0x00ff00
                    )
                    
                    rules_text = "\n".join([f"• {rule}" for rule in event["rules"]])
                    embed.add_field(name="🎯 TURBO RULES", value=rules_text, inline=False)
                    embed.set_footer(text="TURBOCHARGED EVENT: MAXIMUM PARTICIPATION REQUIRED!")
                    
                    try:
                        message = await general_channel.send("@everyone 🏎️ **TURBO EVENT STARTING** 🏎️", embed=embed)
                        await message.add_reaction("🏎️")
                        await message.add_reaction("💨")
                        await message.add_reaction("🔥")
                    except:
                        pass

    @tasks.loop(minutes=14)
    async def maximum_engagement(self):
        """Push engagement to absolute maximum levels"""
        max_engagement_tactics = [
            "🎯 MAXIMUM ENGAGEMENT PROTOCOL: Everyone must respond to this with their current gaming OBSESSION!",
            "💯 FULL PARTICIPATION MODE: If you're reading this, you MUST share what game you're thinking about right NOW!",
            "🔥 ENGAGEMENT OVERLOAD: This message demands a response - what's your most CONTROVERSIAL gaming opinion?",
            "⚡ MANDATORY INTERACTION: Server rule activated - everyone drop their gaming mood in ONE emoji!",
            "🚀 ULTIMATE ENGAGEMENT: No lurking allowed - share the last game that made you lose track of time!",
            "💥 MAXIMUM RESPONSE REQUIRED: What gaming achievement are you MOST proud of? Everyone must answer!",
            "🌟 TOTAL PARTICIPATION: Drop your gaming hot take that might get you canceled! No holding back!",
            "🔋 ENERGY DEMAND: Rate your current gaming enthusiasm 1-10 and EXPLAIN your number!"
        ]
        
        for guild in self.bot.guilds:
            if random.random() < 0.7:
                target_channels = []
                for channel_name in ["general-chat", "gaming-talk"]:
                    channel = discord.utils.get(guild.text_channels, name=channel_name)
                    if channel:
                        target_channels.append(channel)
                
                if target_channels:
                    channel = random.choice(target_channels)
                    engagement_message = random.choice(max_engagement_tactics)
                    
                    try:
                        message = await channel.send(engagement_message)
                        max_reactions = ["💯", "🎯", "🔥", "⚡", "💥"]
                        for reaction in max_reactions:
                            await message.add_reaction(reaction)
                            await asyncio.sleep(0.3)
                    except:
                        pass

    @tasks.loop(minutes=26)
    async def nuclear_participation(self):
        """Nuclear-level participation events"""
        nuclear_events = [
            {
                "alert": "☢️ NUCLEAR PARTICIPATION ALERT",
                "event": "ATOMIC LEVEL ENGAGEMENT REQUIRED",
                "description": "This is not a drill! EVERYONE must contribute to prevent engagement meltdown!",
                "mission": "Share something that would make the gaming community EXPLODE with excitement!",
                "countdown": "T-minus 5 minutes until engagement critical mass!"
            },
            {
                "alert": "🚨 CRITICAL ENGAGEMENT FAILURE",
                "event": "EMERGENCY PARTICIPATION PROTOCOL",
                "description": "Server engagement levels dangerously low! Immediate action required!",
                "mission": "All hands on deck - share your most NUCLEAR gaming take to save the server!",
                "countdown": "Engagement reactor going critical in 3 minutes!"
            },
            {
                "alert": "⚠️ MAXIMUM OVERDRIVE ACTIVATED",
                "event": "LEGENDARY PARTICIPATION MODE",
                "description": "We're going BEYOND maximum! This is legendary difficulty participation!",
                "mission": "Drop the gaming opinion that would start the BIGGEST argument possible!",
                "countdown": "Legendary mode expires in 10 minutes!"
            }
        ]
        
        for guild in self.bot.guilds:
            if random.random() < 0.3:
                general_channel = discord.utils.get(guild.text_channels, name="general-chat")
                if general_channel:
                    event = random.choice(nuclear_events)
                    
                    embed = discord.Embed(
                        title=event["alert"],
                        description=f"**{event['event']}**\n\n{event['description']}\n\n🎯 **MISSION:**\n{event['mission']}\n\n⏰ **{event['countdown']}**",
                        color=0xff4400
                    )
                    embed.set_footer(text="NUCLEAR PARTICIPATION: THIS IS NOT A DRILL!")
                    
                    try:
                        message = await general_channel.send("@everyone ☢️ **NUCLEAR ENGAGEMENT ALERT** ☢️", embed=embed)
                        nuclear_reactions = ["☢️", "🚨", "⚠️", "💥", "🔥"]
                        for reaction in nuclear_reactions:
                            await message.add_reaction(reaction)
                            await asyncio.sleep(0.2)
                    except:
                        pass

    @commands.Cog.listener()
    async def on_message(self, message):
        """Overdrive response to high-energy messages"""
        if message.author.bot or not message.guild:
            return
        
        # Overdrive keywords that trigger maximum amplification
        overdrive_triggers = [
            'overdrive', 'maximum', 'nuclear', 'extreme', 'ultimate', 'legendary',
            'insane', 'crazy', 'unbelievable', 'mindblowing', 'epic', 'godlike'
        ]
        
        message_lower = message.content.lower()
        
        if any(trigger in message_lower for trigger in overdrive_triggers):
            if random.random() < 0.9:
                try:
                    await message.add_reaction("🚀")
                    await message.add_reaction("💥")
                    await message.add_reaction("⚡")
                    
                    # Overdrive response with maximum energy
                    if random.random() < 0.4:
                        overdrive_responses = [
                            "OVERDRIVE DETECTED! MAXIMUM AMPLIFICATION ACTIVATED! 🚀💥⚡",
                            "NUCLEAR ENERGY LEVELS! THIS IS GOING SUPERNOVA! ☢️💥🔥",
                            "LEGENDARY STATUS ACHIEVED! GODLIKE ENERGY! 👑⚡💯",
                            "MAXIMUM OVERDRIVE! WE'RE BREAKING THE LIMITS! 🚀⚡💥"
                        ]
                        await asyncio.sleep(1)
                        await message.reply(random.choice(overdrive_responses), mention_author=False)
                except:
                    pass

    @hyperdrive_mode.before_loop
    @turbocharged_events.before_loop
    @maximum_engagement.before_loop
    @nuclear_participation.before_loop
    async def before_loops(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(EngagementOverdrive(bot))