import discord
from discord.ext import commands, tasks
import aiosqlite
import asyncio
import random
from datetime import datetime, timezone, timedelta

class EnergyMultiplier(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.energy_amplification.start()
        self.power_surges.start()
        self.enthusiasm_injection.start()
        self.collective_energy.start()

    @tasks.loop(minutes=9)
    async def energy_amplification(self):
        """Amplify energy levels across all channels simultaneously"""
        amplification_events = [
            {
                "trigger": "ENERGY AMPLIFICATION ACTIVATED",
                "multiplier": "x3 POWER MODE",
                "message": "🔋 ENERGY LEVELS TRIPLING! Everyone drop what you're doing and share your current OBSESSION!",
                "timeout": "Next 3 minutes = MAXIMUM POWER!"
            },
            {
                "trigger": "ENTHUSIASM OVERDRIVE ENGAGED",
                "multiplier": "x5 HYPE LEVEL",
                "message": "⚡ OVERDRIVE MODE! Tell everyone the ONE thing that makes you absolutely LOSE YOUR MIND with excitement!",
                "timeout": "Pure enthusiasm for 5 minutes straight!"
            },
            {
                "trigger": "PASSION AMPLIFIER ONLINE",
                "multiplier": "x10 INTENSITY",
                "message": "🚀 PASSION LEVELS MAXIMUM! What's something you could talk about for HOURS without stopping?",
                "timeout": "Unlimited energy for the next 10 minutes!"
            }
        ]
        
        for guild in self.bot.guilds:
            if random.random() < 0.6:
                event = random.choice(amplification_events)
                
                # Hit multiple channels simultaneously
                target_channels = []
                for channel_name in ["general-chat", "gaming-talk", "tech-talk"]:
                    channel = discord.utils.get(guild.text_channels, name=channel_name)
                    if channel:
                        target_channels.append(channel)
                
                if target_channels:
                    # Send to main channel
                    main_channel = target_channels[0]
                    
                    embed = discord.Embed(
                        title=f"⚡ {event['trigger']} ⚡",
                        description=f"**{event['multiplier']}**\n\n{event['message']}\n\n⏰ {event['timeout']}",
                        color=0xffff00
                    )
                    embed.set_footer(text="ENERGY SURGE IN PROGRESS!")
                    
                    try:
                        message = await main_channel.send("🚨 **ENERGY AMPLIFICATION DETECTED** 🚨", embed=embed)
                        surge_reactions = ["⚡", "🔋", "🚀", "💥", "🔥"]
                        for reaction in surge_reactions:
                            await message.add_reaction(reaction)
                            await asyncio.sleep(0.2)
                    except:
                        pass

    @tasks.loop(minutes=16)
    async def power_surges(self):
        """Create sudden power surges of activity"""
        surge_types = [
            {
                "name": "LIGHTNING SURGE",
                "description": "⚡ LIGHTNING FAST RESPONSES ONLY! Quick fire round!",
                "challenge": "Answer in 5 words or less: What's your gaming superpower?",
                "duration": "30 seconds per person!"
            },
            {
                "name": "THUNDER SURGE", 
                "description": "⛈️ LOUD AND PROUD MODE! Maximum volume responses!",
                "challenge": "CAPS LOCK ONLY: WHAT GAME MAKES YOU SCREAM WITH JOY?",
                "duration": "BE AS LOUD AS POSSIBLE!"
            },
            {
                "name": "PLASMA SURGE",
                "description": "🌟 PURE ENERGY DISCHARGE! Channel your inner electricity!",
                "challenge": "Share something that gives you UNLIMITED ENERGY when you think about it!",
                "duration": "Let the energy flow through you!"
            },
            {
                "name": "NUCLEAR SURGE",
                "description": "☢️ ATOMIC LEVEL EXCITEMENT! Explosive enthusiasm required!",
                "challenge": "What achievement would make you literally EXPLODE with happiness?",
                "duration": "Nuclear levels of hype only!"
            }
        ]
        
        for guild in self.bot.guilds:
            if random.random() < 0.5:
                gaming_channel = discord.utils.get(guild.text_channels, name="gaming-talk")
                general_channel = discord.utils.get(guild.text_channels, name="general-chat")
                target_channel = gaming_channel or general_channel
                
                if target_channel:
                    surge = random.choice(surge_types)
                    
                    embed = discord.Embed(
                        title=f"⚡ {surge['name']} DETECTED ⚡",
                        description=f"{surge['description']}\n\n🎯 **CHALLENGE:**\n{surge['challenge']}\n\n⏰ **{surge['duration']}**",
                        color=0xff6600
                    )
                    embed.set_footer(text="POWER LEVELS CRITICAL!")
                    
                    try:
                        message = await target_channel.send(embed=embed)
                        await message.add_reaction("⚡")
                        await message.add_reaction("💥")
                        await message.add_reaction("🔥")
                    except:
                        pass

    @tasks.loop(minutes=13)
    async def enthusiasm_injection(self):
        """Inject pure enthusiasm into conversations"""
        injection_doses = [
            "💉 ENTHUSIASM INJECTION! Someone tell me about their LATEST OBSESSION right now!",
            "💊 ENERGY PILL ADMINISTERED! What's got you absolutely BUZZING today?",
            "🔋 BATTERY RECHARGE! Share what's charging your excitement levels!",
            "⚡ VOLTAGE BOOST! What makes you feel like you're running on pure electricity?",
            "🚀 ROCKET FUEL INFUSION! What's launching your enthusiasm to the stratosphere?",
            "💥 EXCITEMENT EXPLOSION! What's about to make you BURST with energy?",
            "🌟 STELLAR ENERGY TRANSFER! What's making you shine brighter than a star?",
            "🔥 PASSION IGNITION! What's setting your soul on FIRE right now?"
        ]
        
        for guild in self.bot.guilds:
            if random.random() < 0.7:
                general_channel = discord.utils.get(guild.text_channels, name="general-chat")
                if general_channel:
                    injection = random.choice(injection_doses)
                    
                    try:
                        message = await general_channel.send(injection)
                        await message.add_reaction("💉")
                        await message.add_reaction("⚡")
                        await message.add_reaction("🔥")
                    except:
                        pass

    @tasks.loop(minutes=19)
    async def collective_energy(self):
        """Harness collective energy from the entire server"""
        collective_events = [
            {
                "title": "🌊 COLLECTIVE ENERGY WAVE",
                "description": "Everyone contribute to the MEGA ENERGY POOL!",
                "instructions": [
                    "Drop ONE emoji that represents your current energy",
                    "Share ONE word that pumps you up",
                    "Tag ONE person who needs an energy boost",
                    "Let's create a TSUNAMI of collective power!"
                ]
            },
            {
                "title": "⚡ ENERGY CONVERGENCE EVENT",
                "description": "All individual energies combining into SUPER POWER!",
                "instructions": [
                    "Everyone share what's fueling your fire today",
                    "Amplify someone else's energy with reactions",
                    "Create a chain reaction of enthusiasm", 
                    "We're building a REACTOR of pure hype!"
                ]
            },
            {
                "title": "🔋 COMMUNITY BATTERY CHARGE",
                "description": "Charging the server's energy reserves to MAXIMUM!",
                "instructions": [
                    "Share your most energizing achievement",
                    "Celebrate someone else's success",
                    "Spread positive energy like it's contagious",
                    "Fill the battery to 100% POWER!"
                ]
            }
        ]
        
        for guild in self.bot.guilds:
            if random.random() < 0.4:
                general_channel = discord.utils.get(guild.text_channels, name="general-chat")
                if general_channel:
                    event = random.choice(collective_events)
                    
                    embed = discord.Embed(
                        title=event["title"],
                        description=event["description"],
                        color=0x00ffff
                    )
                    
                    instructions_text = "\n".join([f"• {instruction}" for instruction in event["instructions"]])
                    embed.add_field(name="🎯 How to Contribute", value=instructions_text, inline=False)
                    embed.set_footer(text="COLLECTIVE POWER ACTIVATED!")
                    
                    try:
                        message = await general_channel.send("@everyone 🔋 **ENERGY CONVERGENCE INITIATING** 🔋", embed=embed)
                        await message.add_reaction("🌊")
                        await message.add_reaction("⚡")
                        await message.add_reaction("🔋")
                    except:
                        pass

    @commands.Cog.listener()
    async def on_message(self, message):
        """Multiply energy in real-time"""
        if message.author.bot or not message.guild:
            return
        
        # High energy keywords get multiplied
        energy_multipliers = [
            'excited', 'pumped', 'hyped', 'energized', 'motivated', 'fired up',
            'amazing', 'incredible', 'fantastic', 'outstanding', 'phenomenal',
            'lets go', 'im ready', 'bring it on', 'full energy', 'maximum power'
        ]
        
        message_lower = message.content.lower()
        
        # Detect high energy and multiply it
        if any(keyword in message_lower for keyword in energy_multipliers):
            if random.random() < 0.8:
                try:
                    await message.add_reaction("⚡")
                    await message.add_reaction("🔋")
                    
                    # Sometimes add energy amplification response
                    if random.random() < 0.3:
                        energy_responses = [
                            "ENERGY LEVELS DETECTED! Amplifying now! ⚡⚡⚡",
                            "POWER SURGE INCOMING! Keep that energy flowing! 🔋🔋🔋",
                            "MAXIMUM ENERGY ACHIEVED! You're ELECTRIC! ⚡🔥⚡",
                            "ENERGY MULTIPLIER ACTIVATED! This is PURE POWER! 🚀⚡🚀"
                        ]
                        await asyncio.sleep(1)
                        await message.reply(random.choice(energy_responses), mention_author=False)
                except:
                    pass
        
        # Detect energy drains and counter them
        energy_drains = ['tired', 'exhausted', 'drained', 'low energy', 'burnt out', 'sleepy']
        
        if any(drain in message_lower for drain in energy_drains):
            if random.random() < 0.6:
                try:
                    await message.add_reaction("🔋")
                    
                    if random.random() < 0.4:
                        energy_boosters = [
                            "ENERGY RECHARGE PROTOCOL ACTIVATED! 🔋⚡",
                            "DETECTING LOW POWER! Sending energy boost! ⚡🔋⚡",
                            "EMERGENCY ENERGY TRANSFER! You've got this! 💪⚡💪"
                        ]
                        await asyncio.sleep(2)
                        await message.reply(random.choice(energy_boosters), mention_author=False)
                except:
                    pass

    @energy_amplification.before_loop
    @power_surges.before_loop
    @enthusiasm_injection.before_loop
    @collective_energy.before_loop
    async def before_loops(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(EnergyMultiplier(bot))