import discord
from discord.ext import commands, tasks
import aiosqlite
import asyncio
import random
from datetime import datetime, timezone, timedelta

class ActivityBoosters(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.hourly_boosters.start()
        self.voice_channel_monitor.start()
        self.trending_topics.start()

    @tasks.loop(hours=1)
    async def hourly_boosters(self):
        """Send activity boosters every hour"""
        boosters = [
            "💬 Who's online and ready to chat? Drop a 👋 in the chat!",
            "🎮 What's everyone playing right now? Share your current game!",
            "🔥 Let's get this chat active! What's on your mind today?",
            "⚡ Energy check! React with ⚡ if you're feeling pumped!",
            "💭 Question of the hour: What's your favorite thing about gaming?",
            "🎯 Challenge time! Share your best gaming tip in one sentence!",
            "🌟 Spread some positivity! Compliment someone in the server!",
            "🎪 Fun fact Friday! Share something interesting you learned recently!",
            "🎨 Creative minds unite! What's the coolest thing you've made?",
            "🚀 Motivation Monday! What goals are you working towards?"
        ]
        
        for guild in self.bot.guilds:
            general_channel = discord.utils.get(guild.text_channels, name="general-chat")
            if general_channel and random.random() < 0.6:
                try:
                    await general_channel.send(random.choice(boosters))
                except:
                    pass

    @tasks.loop(minutes=10)
    async def voice_channel_monitor(self):
        """Monitor and encourage voice activity"""
        for guild in self.bot.guilds:
            for vc in guild.voice_channels:
                if len(vc.members) == 1 and not vc.members[0].bot:
                    # Someone is alone in voice, encourage others to join
                    general_channel = discord.utils.get(guild.text_channels, name="general-chat")
                    if general_channel and random.random() < 0.3:
                        lonely_member = vc.members[0]
                        messages = [
                            f"🎤 {lonely_member.mention} is chilling in {vc.mention}! Anyone want to join the conversation?",
                            f"🗣️ {vc.mention} could use some company! {lonely_member.mention} is waiting for friends!",
                            f"💬 Hop into {vc.mention} and chat with {lonely_member.mention}! Voice chat is always more fun with friends!"
                        ]
                        try:
                            await general_channel.send(random.choice(messages))
                        except:
                            pass

    @tasks.loop(hours=3)
    async def trending_topics(self):
        """Post trending discussion topics"""
        topics = [
            "🎮 **Gaming Hot Take**: What's a popular game that you just couldn't get into?",
            "🔥 **Debate Time**: Single player or multiplayer games? Which do you prefer?",
            "💭 **Deep Question**: What game world would you want to live in for a week?",
            "⚡ **Quick Poll**: Console, PC, or mobile gaming? React with your choice!",
            "🎯 **Challenge**: Describe your favorite game using only emojis!",
            "🌟 **Nostalgia Trip**: What's the first game that made you fall in love with gaming?",
            "🎪 **Fun Theory**: If video games were real, which character would be the best roommate?",
            "🚀 **Future Talk**: What gaming technology are you most excited about?",
            "🎨 **Creative Corner**: If you could redesign any game, what would you change?",
            "🏆 **Achievement Unlocked**: What's your proudest gaming moment?"
        ]
        
        for guild in self.bot.guilds:
            gaming_channel = discord.utils.get(guild.text_channels, name="gaming-talk")
            if gaming_channel and random.random() < 0.8:
                topic = random.choice(topics)
                embed = discord.Embed(
                    description=topic,
                    color=random.choice([0xff6b6b, 0x4ecdc4, 0x45b7d1, 0xf39c12, 0xe74c3c, 0x9b59b6])
                )
                try:
                    message = await gaming_channel.send(embed=embed)
                    await message.add_reaction("💭")
                    await message.add_reaction("🎮")
                    await message.add_reaction("🔥")
                except:
                    pass

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Welcome new members with energy"""
        if member.bot:
            return
        
        # Post in general to encourage others to welcome
        general_channel = discord.utils.get(member.guild.text_channels, name="general-chat")
        if general_channel:
            welcome_encouragements = [
                f"🎉 Everyone welcome {member.mention} to the party! Let's show them how awesome this community is!",
                f"🌟 Fresh face alert! {member.mention} just joined us! Drop some love in the chat!",
                f"🎮 New gamer in the house! {member.mention}, introduce yourself! What games do you play?",
                f"🔥 The squad just got bigger! Welcome {member.mention}! Who's going to be their first friend here?"
            ]
            
            if random.random() < 0.7:
                try:
                    await asyncio.sleep(2)
                    await general_channel.send(random.choice(welcome_encouragements))
                except:
                    pass

    @commands.Cog.listener()
    async def on_message(self, message):
        """Boost engagement through smart responses"""
        if message.author.bot or not message.guild:
            return
        
        # Detect and boost inactive periods
        channel = message.channel
        if hasattr(channel, 'last_message') and channel.last_message:
            time_since_last = datetime.now(timezone.utc) - channel.last_message.created_at
            if time_since_last.total_seconds() > 3600:  # 1 hour of inactivity
                if random.random() < 0.4:
                    try:
                        await message.add_reaction("🔥")
                        comeback_messages = [
                            "Chat's coming back to life! 🔥",
                            "The silence is broken! Keep it going! 💪",
                            "Activity detected! Let's keep this energy up! ⚡"
                        ]
                        await asyncio.sleep(1)
                        await message.reply(random.choice(comeback_messages), mention_author=False)
                    except:
                        pass

        # Encourage questions
        if '?' in message.content and len(message.content) > 15:
            if random.random() < 0.3:
                try:
                    await message.add_reaction("🤔")
                except:
                    pass

        # Celebrate enthusiasm
        enthusiasm_words = ['amazing', 'awesome', 'incredible', 'epic', 'legendary', 'fantastic', 'brilliant']
        if any(word in message.content.lower() for word in enthusiasm_words):
            if random.random() < 0.4:
                try:
                    await message.add_reaction(random.choice(["🔥", "💯", "⭐", "🎉"]))
                except:
                    pass

    @hourly_boosters.before_loop
    @voice_channel_monitor.before_loop
    @trending_topics.before_loop
    async def before_loops(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(ActivityBoosters(bot))