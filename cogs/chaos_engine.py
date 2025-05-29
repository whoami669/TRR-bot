import discord
from discord.ext import commands, tasks
import aiosqlite
import asyncio
import random
from datetime import datetime, timezone, timedelta

class ChaosEngine(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.random_chaos.start()
        self.organized_madness.start()
        self.controlled_mayhem.start()
        self.spontaneous_events.start()

    @tasks.loop(minutes=11)
    async def random_chaos(self):
        """Inject random chaos into the server at unpredictable intervals"""
        chaos_events = [
            {
                "type": "sudden_question",
                "content": "🎲 RANDOM CHAOS QUESTION: If you could delete one game from existence, which would it be and why?",
                "reactions": ["🎲", "💥", "🤔"]
            },
            {
                "type": "instant_challenge",
                "content": "⚡ CHAOS CHALLENGE: Next person to type gets to choose a topic for everyone to discuss! GO!",
                "reactions": ["⚡", "🏃", "💨"]
            },
            {
                "type": "random_confession",
                "content": "🌪️ CHAOS CONFESSION TIME: Drop your most embarrassing gaming moment RIGHT NOW!",
                "reactions": ["🌪️", "😅", "💀"]
            },
            {
                "type": "speed_round",
                "content": "💨 SPEED CHAOS: Everyone type your favorite game in 3 words or less! 30 seconds GO!",
                "reactions": ["💨", "⏰", "🎮"]
            },
            {
                "type": "reverse_psychology",
                "content": "🔄 REVERSE CHAOS: Everyone try NOT to respond to this message! (I bet you can't resist)",
                "reactions": ["🔄", "😏", "🎭"]
            }
        ]
        
        for guild in self.bot.guilds:
            # Only trigger chaos sometimes to keep it unpredictable
            if random.random() < 0.4:
                target_channel = None
                possible_channels = ["general-chat", "gaming-talk", "chaos", "random"]
                
                for channel_name in possible_channels:
                    channel = discord.utils.get(guild.text_channels, name=channel_name)
                    if channel:
                        target_channel = channel
                        break
                
                if target_channel:
                    chaos_event = random.choice(chaos_events)
                    
                    try:
                        message = await target_channel.send(chaos_event["content"])
                        for reaction in chaos_event["reactions"]:
                            await message.add_reaction(reaction)
                            await asyncio.sleep(0.3)
                    except:
                        pass

    @tasks.loop(minutes=22)
    async def organized_madness(self):
        """Create structured chaos events"""
        madness_scenarios = [
            {
                "title": "🎭 ROLE REVERSAL MADNESS",
                "description": "For the next 10 minutes, everyone pretend to be the OPPOSITE of their personality!",
                "rules": [
                    "Introverts become super outgoing",
                    "Optimists become pessimistic", 
                    "Serious people become comedians",
                    "Chaos lovers become organized"
                ]
            },
            {
                "title": "🎪 CIRCUS OF OPINIONS",
                "description": "Time for the most ridiculous debate ever!",
                "rules": [
                    "Argue passionately about which is better: spoons or forks",
                    "Defend your position like your life depends on it",
                    "Use gaming analogies to support your argument",
                    "No backing down allowed!"
                ]
            },
            {
                "title": "🃏 WILD CARD CHAOS",
                "description": "Everyone gets a random personality for 15 minutes!",
                "rules": [
                    "React to everything with maximum drama",
                    "Speak only in gaming terms",
                    "End every sentence with a question mark?",
                    "Pretend everything is the most exciting thing ever"
                ]
            }
        ]
        
        for guild in self.bot.guilds:
            if random.random() < 0.3:
                general_channel = discord.utils.get(guild.text_channels, name="general-chat")
                if general_channel:
                    madness = random.choice(madness_scenarios)
                    
                    embed = discord.Embed(
                        title=madness["title"],
                        description=madness["description"],
                        color=0xff00ff
                    )
                    
                    rules_text = "\n".join([f"• {rule}" for rule in madness["rules"]])
                    embed.add_field(name="🎯 The Rules", value=rules_text, inline=False)
                    embed.set_footer(text="EMBRACE THE MADNESS! No rules, just chaos!")
                    
                    try:
                        message = await general_channel.send(embed=embed)
                        madness_reactions = ["🎭", "🎪", "🃏", "🌪️", "💥"]
                        for reaction in madness_reactions:
                            await message.add_reaction(reaction)
                            await asyncio.sleep(0.2)
                    except:
                        pass

    @tasks.loop(minutes=17)
    async def controlled_mayhem(self):
        """Strategic chaos to boost engagement"""
        mayhem_tactics = [
            {
                "tactic": "opinion_bomb",
                "message": "💣 OPINION BOMB DROPPED: Pineapple on pizza is actually amazing and here's why...",
                "followup": "Actually, I changed my mind. Convince me I'm wrong!"
            },
            {
                "tactic": "fake_drama",
                "message": "🚨 BREAKING: I have a CONTROVERSIAL gaming confession that might shock you all...",
                "followup": "I actually... enjoy tutorial levels. There, I said it!"
            },
            {
                "tactic": "impossible_choice",
                "message": "⚖️ IMPOSSIBLE CHOICE: You can only play ONE game for the rest of your life. What is it?",
                "followup": "Plot twist: Multiplayer games don't count!"
            },
            {
                "tactic": "reverse_bait",
                "message": "🎣 Don't everyone respond at once, but what's your most unpopular gaming opinion?",
                "followup": "Actually, DO everyone respond at once! Let's break the chat!"
            }
        ]
        
        for guild in self.bot.guilds:
            if random.random() < 0.5:
                gaming_channel = discord.utils.get(guild.text_channels, name="gaming-talk")
                general_channel = discord.utils.get(guild.text_channels, name="general-chat")
                target_channel = gaming_channel or general_channel
                
                if target_channel:
                    mayhem = random.choice(mayhem_tactics)
                    
                    try:
                        # Send initial message
                        initial_msg = await target_channel.send(mayhem["message"])
                        await initial_msg.add_reaction("👀")
                        await initial_msg.add_reaction("🍿")
                        
                        # Wait a bit then send the followup
                        await asyncio.sleep(random.randint(30, 90))
                        await target_channel.send(mayhem["followup"])
                    except:
                        pass

    @tasks.loop(minutes=28)
    async def spontaneous_events(self):
        """Create completely random spontaneous events"""
        events = [
            {
                "announcement": "🎊 SPONTANEOUS CELEBRATION TIME!",
                "event": "Everyone celebrate the most random thing that happened to you today!",
                "duration": "Next 5 minutes only!"
            },
            {
                "announcement": "🚀 SUDDEN TALENT SHOW!",
                "event": "Show off your weirdest skill or talent! Anything counts!",
                "duration": "Right now! Don't think, just do!"
            },
            {
                "announcement": "💡 INSTANT INVENTION CONVENTION!",
                "event": "Invent a ridiculous game mechanic that would break any game!",
                "duration": "Most creative idea wins eternal glory!"
            },
            {
                "announcement": "🎭 IMPROMPTU STORYTELLING!",
                "event": "Tell a 2-sentence story about your gaming alter ego!",
                "duration": "Wildest stories get featured!"
            },
            {
                "announcement": "⚡ FLASH MOB... VIRTUALLY!",
                "event": "Everyone spam the same emoji for exactly 30 seconds!",
                "duration": "Starting... NOW!"
            }
        ]
        
        for guild in self.bot.guilds:
            if random.random() < 0.4:
                general_channel = discord.utils.get(guild.text_channels, name="general-chat")
                if general_channel:
                    event = random.choice(events)
                    
                    embed = discord.Embed(
                        title=event["announcement"],
                        description=f"**{event['event']}**\n\n⏰ **{event['duration']}**",
                        color=0x00ff00
                    )
                    embed.set_footer(text="SPONTANEOUS EVENT! No planning allowed!")
                    
                    try:
                        message = await general_channel.send("🚨 **SPONTANEOUS EVENT ALERT** 🚨", embed=embed)
                        event_reactions = ["🎊", "🚀", "💡", "🎭", "⚡"]
                        for reaction in event_reactions:
                            await message.add_reaction(reaction)
                            await asyncio.sleep(0.2)
                    except:
                        pass

    @commands.Cog.listener()
    async def on_message(self, message):
        """React chaotically to certain messages"""
        if message.author.bot or not message.guild:
            return
        
        # Chaos triggers
        chaos_words = [
            'boring', 'quiet', 'dead chat', 'nothing happening', 'silence',
            'peaceful', 'calm', 'uneventful', 'sleepy', 'tired'
        ]
        
        message_lower = message.content.lower()
        
        # If someone mentions things are quiet/boring, inject chaos
        if any(word in message_lower for word in chaos_words):
            if random.random() < 0.7:
                chaos_responses = [
                    "Did someone say BORING? Time for chaos! 🌪️",
                    "Quiet? Not on my watch! CHAOS INCOMING! 💥",
                    "Dead chat? Allow me to resurrect it! ⚡",
                    "Peaceful? We don't do peaceful here! 🎭",
                    "CHAOS SENSORS ACTIVATED! Deploying mayhem! 🚀"
                ]
                
                try:
                    await asyncio.sleep(1)
                    await message.reply(random.choice(chaos_responses), mention_author=False)
                    await message.add_reaction("🌪️")
                except:
                    pass
        
        # Random chaos reactions
        if random.random() < 0.02:  # 2% chance for any message
            chaos_reactions = ["🎲", "🌪️", "💥", "🎭", "🃏"]
            try:
                await message.add_reaction(random.choice(chaos_reactions))
            except:
                pass

    @random_chaos.before_loop
    @organized_madness.before_loop
    @controlled_mayhem.before_loop
    @spontaneous_events.before_loop
    async def before_loops(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(ChaosEngine(bot))