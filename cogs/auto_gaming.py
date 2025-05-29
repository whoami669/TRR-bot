import discord
from discord.ext import commands, tasks
import random
import asyncio
from datetime import datetime, timezone

class AutoGaming(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gaming_questions_loop.start()

    def cog_unload(self):
        self.gaming_questions_loop.cancel()

    @tasks.loop(hours=2)  # Post gaming questions every 2 hours
    async def gaming_questions_loop(self):
        for guild in self.bot.guilds:
            # Find gaming channels
            gaming_channels = []
            for channel in guild.text_channels:
                if any(keyword in channel.name.lower() for keyword in ['gaming', 'game', 'esports', 'valorant', 'minecraft', 'league', 'fortnite']):
                    gaming_channels.append(channel)
            
            # Post in random gaming channel
            if gaming_channels:
                channel = random.choice(gaming_channels)
                await self.post_gaming_question(channel)

    @gaming_questions_loop.before_loop
    async def before_gaming_loop(self):
        await self.bot.wait_until_ready()

    async def post_gaming_question(self, channel):
        gaming_questions = [
            {
                "type": "trivia",
                "question": "What was the first commercially successful video game?",
                "answer": "Pong (1972)",
                "options": ["Pong", "Pac-Man", "Space Invaders", "Tetris"]
            },
            {
                "type": "would_you_rather",
                "question": "Would you rather have unlimited gaming time but only play one game forever, or play any game but only 1 hour per day?"
            },
            {
                "type": "discussion",
                "question": "What's your most memorable gaming moment?"
            },
            {
                "type": "trivia",
                "question": "Which game holds the record for fastest speedrun completion?",
                "answer": "Various games have different categories",
                "options": ["Mario Bros", "Sonic", "Doom", "It varies by game"]
            },
            {
                "type": "poll",
                "question": "Best gaming platform?",
                "options": ["PC", "PlayStation", "Xbox", "Nintendo", "Mobile"]
            },
            {
                "type": "discussion",
                "question": "What game are you currently obsessed with and why?"
            },
            {
                "type": "would_you_rather",
                "question": "Would you rather be the best player at a game nobody plays, or average at the most popular game?"
            },
            {
                "type": "trivia",
                "question": "What does 'RNG' stand for in gaming?",
                "answer": "Random Number Generator",
                "options": ["Random Number Generator", "Rapid Network Gaming", "Real Number Graphics", "Random Name Generator"]
            },
            {
                "type": "discussion",
                "question": "What's a game you think is underrated and deserves more attention?"
            },
            {
                "type": "challenge",
                "question": "Gaming Challenge: Share a screenshot of your current game setup or favorite gaming achievement!"
            }
        ]

        question_data = random.choice(gaming_questions)
        
        if question_data["type"] == "trivia":
            embed = discord.Embed(
                title="🎮 Gaming Trivia Time!",
                description=f"**{question_data['question']}**\n\n" + 
                           "\n".join([f"**{chr(65+i)}.** {option}" for i, option in enumerate(question_data['options'])]),
                color=discord.Color.purple()
            )
            embed.add_field(name="💡 Answer", value=f"||{question_data['answer']}||", inline=False)
            embed.set_footer(text="React with 🎯 if you got it right!")
            
        elif question_data["type"] == "would_you_rather":
            embed = discord.Embed(
                title="🤔 Gaming Would You Rather",
                description=question_data["question"],
                color=discord.Color.orange()
            )
            embed.set_footer(text="Let us know your choice in the comments!")
            
        elif question_data["type"] == "discussion":
            embed = discord.Embed(
                title="💬 Gaming Discussion",
                description=question_data["question"],
                color=discord.Color.blue()
            )
            embed.set_footer(text="Share your thoughts below!")
            
        elif question_data["type"] == "poll":
            embed = discord.Embed(
                title="📊 Gaming Poll",
                description=question_data["question"],
                color=discord.Color.green()
            )
            # Will add reactions after sending
            
        elif question_data["type"] == "challenge":
            embed = discord.Embed(
                title="🏆 Gaming Challenge",
                description=question_data["question"],
                color=discord.Color.gold()
            )
            embed.set_footer(text="Show off your gaming setup!")

        try:
            message = await channel.send(embed=embed)
            
            # Add appropriate reactions
            if question_data["type"] == "trivia":
                await message.add_reaction("🎯")
            elif question_data["type"] == "would_you_rather":
                await message.add_reaction("1️⃣")
                await message.add_reaction("2️⃣")
            elif question_data["type"] == "poll":
                reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
                for i, option in enumerate(question_data.get("options", [])):
                    if i < len(reactions):
                        await message.add_reaction(reactions[i])
            elif question_data["type"] in ["discussion", "challenge"]:
                await message.add_reaction("💬")
                await message.add_reaction("👍")
                
        except Exception as e:
            print(f"Failed to post gaming question in {channel.name}: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
            
        # Respond to gaming-related keywords in gaming channels
        if any(keyword in message.channel.name.lower() for keyword in ['gaming', 'game']):
            content = message.content.lower()
            
            # Gaming tips for common questions
            tips = {
                'lag': "Try checking your internet connection, closing background apps, or lowering graphics settings!",
                'fps': "For better FPS: Lower graphics settings, update drivers, close unnecessary programs, or consider hardware upgrades.",
                'build': "For PC builds, balance your CPU and GPU, don't forget enough RAM, and ensure good cooling!",
                'setup': "Good gaming setup tips: Comfortable chair, proper lighting, organized desk, and quality peripherals.",
                'headset': "Popular gaming headsets: SteelSeries, HyperX, Logitech G, Razer, or Audio-Technica for quality audio."
            }
            
            for keyword, tip in tips.items():
                if keyword in content and '?' in content:
                    embed = discord.Embed(
                        title="🎮 Gaming Tip",
                        description=tip,
                        color=discord.Color.blue()
                    )
                    embed.set_footer(text="Hope this helps!")
                    await message.channel.send(embed=embed)
                    break

async def setup(bot):
    await bot.add_cog(AutoGaming(bot))