import discord
from discord.ext import commands, tasks
import aiosqlite
import asyncio
import random
from datetime import datetime, timezone, timedelta

class InteractionEngine(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conversation_sparks.start()
        self.interaction_cascades.start()
        self.engagement_threads.start()
        self.social_catalyst.start()

    @tasks.loop(minutes=12)
    async def conversation_sparks(self):
        """Generate conversation sparks to ignite discussions"""
        conversation_starters = [
            {
                "text": "💭 Quick question: What's the most UNDERRATED game that everyone needs to play?",
                "follow_up": "Tell us why it deserves more recognition!"
            },
            {
                "text": "🎮 Controversial take time: Which popular game do you think is actually overrated?",
                "follow_up": "Respectful debate encouraged!"
            },
            {
                "text": "⚡ Lightning round: Name a game that changed your life in some way!",
                "follow_up": "Could be anything - perspective, friendships, skills!"
            },
            {
                "text": "🔥 Hot topic: What's the most money you've ever spent on gaming and was it worth it?",
                "follow_up": "No judgment zone - we've all been there!"
            },
            {
                "text": "👥 Community question: What gaming achievement are you most proud of?",
                "follow_up": "Flex on us! We want to celebrate with you!"
            },
            {
                "text": "🌟 Dream scenario: If you could master any game instantly, which would you choose?",
                "follow_up": "And what would you do first with those skills?"
            },
            {
                "text": "🎯 Real talk: What's your biggest gaming confession?",
                "follow_up": "Safe space - we've all got secrets!"
            },
            {
                "text": "💡 Imagine this: You can add ONE feature to any game. What game and what feature?",
                "follow_up": "Let your creativity run wild!"
            }
        ]
        
        for guild in self.bot.guilds:
            gaming_channel = discord.utils.get(guild.text_channels, name="gaming-talk")
            general_channel = discord.utils.get(guild.text_channels, name="general-chat")
            target_channel = gaming_channel or general_channel
            
            if target_channel and random.random() < 0.6:
                starter = random.choice(conversation_starters)
                
                embed = discord.Embed(
                    title="🚀 CONVERSATION SPARK",
                    description=f"**{starter['text']}**\n\n*{starter['follow_up']}*",
                    color=0x00ff88
                )
                embed.set_footer(text="Let's get this discussion rolling!")
                
                try:
                    message = await target_channel.send(embed=embed)
                    await message.add_reaction("💬")
                    await message.add_reaction("🔥")
                    await message.add_reaction("👀")
                except:
                    pass

    @tasks.loop(minutes=8)
    async def interaction_cascades(self):
        """Create cascading interactions across the server"""
        for guild in self.bot.guilds:
            # Find messages with potential for more interaction
            for channel in guild.text_channels:
                if channel.name in ["general-chat", "gaming-talk", "tech-talk"]:
                    try:
                        # Look for recent messages that could use more engagement
                        async for message in channel.history(limit=15, after=datetime.now(timezone.utc) - timedelta(minutes=30)):
                            if not message.author.bot and len(message.content) > 30:
                                reaction_count = sum(r.count for r in message.reactions)
                                
                                # If message has 1-2 reactions, add more to create cascade
                                if 1 <= reaction_count <= 2 and random.random() < 0.5:
                                    cascade_reactions = ["💯", "👀", "💬", "🎯", "⚡", "🔥"]
                                    existing = [str(r.emoji) for r in message.reactions]
                                    available = [r for r in cascade_reactions if r not in existing]
                                    
                                    if available:
                                        await message.add_reaction(random.choice(available))
                                        await asyncio.sleep(1)
                                
                                # Add encouraging comments to lonely messages
                                elif reaction_count == 0 and '?' in message.content and random.random() < 0.3:
                                    encouraging_responses = [
                                        "Great question! 🤔",
                                        "This is interesting! 👀",
                                        "I'm curious about this too! 💭",
                                        "Someone drop their thoughts! 💬"
                                    ]
                                    await asyncio.sleep(2)
                                    await message.reply(random.choice(encouraging_responses), mention_author=False)
                    except:
                        pass

    @tasks.loop(minutes=15)
    async def engagement_threads(self):
        """Create engaging conversation threads"""
        thread_topics = [
            {
                "title": "🎮 Gaming Setup Evolution",
                "starter": "Share how your gaming setup has evolved over the years! From potato PC to beast mode!",
                "questions": ["What was your first gaming device?", "What upgrade changed everything for you?", "What's your dream setup?"]
            },
            {
                "title": "⚡ Gaming Hot Takes",
                "starter": "Time for some spicy gaming opinions! Drop your most controversial gaming hot takes!",
                "questions": ["Which popular game do you dislike?", "What gaming trend needs to stop?", "What's an unpopular gaming opinion you have?"]
            },
            {
                "title": "🏆 Achievement Unlocked",
                "starter": "Brag time! What's your most impressive gaming achievement or accomplishment?",
                "questions": ["What took you the longest to achieve?", "What achievement are you most proud of?", "What's your rarest trophy/achievement?"]
            },
            {
                "title": "💭 Gaming Nostalgia",
                "starter": "Let's take a trip down memory lane! What gaming memories hit you right in the feels?",
                "questions": ["What was your first favorite game?", "What gaming moment made you emotional?", "What game brings back the best memories?"]
            }
        ]
        
        for guild in self.bot.guilds:
            gaming_channel = discord.utils.get(guild.text_channels, name="gaming-talk")
            if gaming_channel and random.random() < 0.4:
                topic = random.choice(thread_topics)
                
                embed = discord.Embed(
                    title=topic["title"],
                    description=topic["starter"],
                    color=0xff6b35
                )
                
                questions_text = "\n".join([f"• {q}" for q in topic["questions"]])
                embed.add_field(name="💡 Discussion Starters", value=questions_text, inline=False)
                embed.set_footer(text="Join the conversation! Everyone's story matters!")
                
                try:
                    message = await gaming_channel.send(embed=embed)
                    await message.add_reaction("🎮")
                    await message.add_reaction("💬")
                    await message.add_reaction("🔥")
                except:
                    pass

    @tasks.loop(minutes=25)
    async def social_catalyst(self):
        """Act as a social catalyst to bring people together"""
        catalyst_actions = [
            {
                "type": "member_spotlight",
                "message": "🌟 Shoutout time! Tag someone who's been awesome in the chat lately and tell them why!",
                "reactions": ["👏", "🌟", "💙"]
            },
            {
                "type": "collaboration_call",
                "message": "🤝 Collaboration corner! Looking to team up for games? Drop what you're playing and find your squad!",
                "reactions": ["🎮", "👥", "🤝"]
            },
            {
                "type": "knowledge_share",
                "message": "🧠 Knowledge share! Drop a gaming tip, trick, or piece of advice that others might find useful!",
                "reactions": ["💡", "🧠", "📚"]
            },
            {
                "type": "mood_check",
                "message": "💙 Vibe check! How's everyone feeling today? Drop an emoji that represents your current mood!",
                "reactions": ["😊", "😎", "🔥", "😤", "😴"]
            },
            {
                "type": "gratitude_moment",
                "message": "🙏 Gratitude moment! What's one thing about this community that you're grateful for?",
                "reactions": ["❤️", "🙏", "🥰"]
            }
        ]
        
        for guild in self.bot.guilds:
            general_channel = discord.utils.get(guild.text_channels, name="general-chat")
            if general_channel and random.random() < 0.5:
                action = random.choice(catalyst_actions)
                
                try:
                    message = await general_channel.send(action["message"])
                    for reaction in action["reactions"]:
                        await message.add_reaction(reaction)
                        await asyncio.sleep(0.3)
                except:
                    pass

    @commands.Cog.listener()
    async def on_message(self, message):
        """React to messages to encourage interaction"""
        if message.author.bot or not message.guild:
            return
        
        # Encourage questions
        if '?' in message.content and len(message.content) > 20:
            if random.random() < 0.4:
                try:
                    await message.add_reaction("🤔")
                    
                    # Sometimes add an encouraging response
                    if random.random() < 0.2:
                        encouraging_responses = [
                            "Great question! 👀",
                            "Someone's got to have thoughts on this! 💭",
                            "Curious to see the responses! 🤔"
                        ]
                        await asyncio.sleep(3)
                        await message.reply(random.choice(encouraging_responses), mention_author=False)
                except:
                    pass
        
        # Amplify sharing and storytelling
        sharing_words = ['i think', 'in my opinion', 'personally', 'i believe', 'my experience']
        story_words = ['happened to me', 'i remember', 'one time', 'yesterday', 'today i']
        
        message_lower = message.content.lower()
        
        if any(word in message_lower for word in sharing_words + story_words):
            if random.random() < 0.5:
                try:
                    if any(word in message_lower for word in sharing_words):
                        await message.add_reaction("💭")
                    else:
                        await message.add_reaction("👂")
                except:
                    pass
        
        # React to mentions of collaboration
        collab_words = ['looking for', 'want to play', 'anyone want', 'team up', 'play together']
        if any(word in message_lower for word in collab_words):
            if random.random() < 0.6:
                try:
                    await message.add_reaction("🤝")
                    await message.add_reaction("🎮")
                except:
                    pass

    @conversation_sparks.before_loop
    @interaction_cascades.before_loop
    @engagement_threads.before_loop
    @social_catalyst.before_loop
    async def before_loops(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(InteractionEngine(bot))