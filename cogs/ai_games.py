import discord
from discord.ext import commands
from discord import app_commands
import openai
import json
import random
import asyncio
import aiosqlite
from datetime import datetime, timezone
import os
from typing import Dict, List, Optional

class AIGames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.active_games = {}
        
    async def get_ai_response(self, prompt: str, system_prompt: str = None) -> str:
        """Get AI response for games"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=300,
                temperature=0.8
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"AI temporarily unavailable: {str(e)}"

    @app_commands.command(name="ai-20questions", description="Play 20 Questions with AI")
    async def twenty_questions(self, interaction: discord.Interaction):
        """Start a game of 20 Questions with AI"""
        await interaction.response.defer()
        
        # AI thinks of something
        prompt = "Think of a specific object, person, place, or concept for a game of 20 Questions. Don't reveal what it is, just confirm you've thought of something and give a brief hint category (like 'I'm thinking of an animal' or 'I'm thinking of a famous person')."
        
        ai_response = await self.get_ai_response(prompt)
        
        embed = discord.Embed(
            title="🎯 20 Questions with AI",
            description=f"{ai_response}\n\nAsk yes/no questions to guess what I'm thinking of!\nYou have 20 questions.",
            color=0x3498db,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Ask your first question!")
        
        # Store game state
        self.active_games[interaction.user.id] = {
            'type': '20questions',
            'questions_left': 20,
            'started_at': datetime.now(timezone.utc),
            'channel_id': interaction.channel.id
        }
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="ai-riddle", description="Get a challenging riddle from AI")
    @app_commands.describe(difficulty="Choose riddle difficulty")
    @app_commands.choices(difficulty=[
        app_commands.Choice(name="🌱 Easy", value="easy"),
        app_commands.Choice(name="🧠 Medium", value="medium"),
        app_commands.Choice(name="🔥 Hard", value="hard"),
        app_commands.Choice(name="💀 Expert", value="expert")
    ])
    async def ai_riddle(self, interaction: discord.Interaction, difficulty: str = "medium"):
        """Generate a riddle with AI"""
        await interaction.response.defer()
        
        difficulty_prompts = {
            "easy": "Create an easy riddle suitable for children. Make it fun and not too complex.",
            "medium": "Create a medium difficulty riddle that requires some thinking but isn't too hard.",
            "hard": "Create a challenging riddle that requires clever thinking and wordplay.",
            "expert": "Create a very difficult riddle with complex logic, wordplay, or lateral thinking required."
        }
        
        prompt = f"{difficulty_prompts[difficulty]} Format it as 'RIDDLE: [riddle text]' followed by 'ANSWER: [answer]' on a new line."
        
        riddle_response = await self.get_ai_response(prompt)
        
        # Parse riddle and answer
        lines = riddle_response.split('\n')
        riddle_text = "Generated riddle..."
        answer = "See answer below"
        
        for line in lines:
            if line.startswith('RIDDLE:'):
                riddle_text = line.replace('RIDDLE:', '').strip()
            elif line.startswith('ANSWER:'):
                answer = line.replace('ANSWER:', '').strip()
        
        embed = discord.Embed(
            title=f"🧩 AI Riddle - {difficulty.title()} Level",
            description=riddle_text,
            color=0x9b59b6,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Think you know the answer? Click the button below!")
        
        # Create a view with answer button
        view = RiddleView(answer)
        await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name="ai-wordgame", description="Play word association or word chain games")
    @app_commands.describe(game_type="Choose the type of word game")
    @app_commands.choices(game_type=[
        app_commands.Choice(name="🔗 Word Association", value="association"),
        app_commands.Choice(name="📝 Story Chain", value="story"),
        app_commands.Choice(name="🎭 Character Creation", value="character"),
        app_commands.Choice(name="🌍 World Building", value="world")
    ])
    async def ai_wordgame(self, interaction: discord.Interaction, game_type: str):
        """Play collaborative word games with AI"""
        await interaction.response.defer()
        
        game_prompts = {
            "association": "Start a word association game. I'll say a word, and you respond with the first related word that comes to mind. Then I'll respond to your word. Let's begin with: OCEAN",
            "story": "Let's write a story together! I'll start with one sentence, then you add the next sentence, and we'll keep building. Here's the opening: 'The mysterious package arrived at midnight.'",
            "character": "Let's create a character together! I'll give you a trait, and you add another trait that would be interesting or contradictory. Starting trait: 'A shy librarian who...'",
            "world": "Let's build a fantasy world together! I'll describe one element, you add another that complements or contrasts it. Starting element: 'A floating city powered by crystal magic.'"
        }
        
        ai_response = await self.get_ai_response(game_prompts[game_type])
        
        embed = discord.Embed(
            title=f"🎮 {game_type.replace('_', ' ').title()} Game",
            description=ai_response,
            color=0xe74c3c,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Continue the game by responding!")
        
        # Store game state
        self.active_games[interaction.user.id] = {
            'type': game_type,
            'started_at': datetime.now(timezone.utc),
            'channel_id': interaction.channel.id,
            'turns': 1
        }
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="ai-trivia", description="Play trivia with AI-generated questions")
    @app_commands.describe(category="Choose trivia category")
    @app_commands.choices(category=[
        app_commands.Choice(name="🌍 General Knowledge", value="general"),
        app_commands.Choice(name="🎬 Movies & TV", value="entertainment"),
        app_commands.Choice(name="🔬 Science", value="science"),
        app_commands.Choice(name="📚 Literature", value="literature"),
        app_commands.Choice(name="🎵 Music", value="music"),
        app_commands.Choice(name="🏆 Sports", value="sports"),
        app_commands.Choice(name="🎮 Gaming", value="gaming"),
        app_commands.Choice(name="🍕 Random Fun", value="random")
    ])
    async def ai_trivia(self, interaction: discord.Interaction, category: str = "general"):
        """Generate trivia questions with AI"""
        await interaction.response.defer()
        
        prompt = f"Create a trivia question about {category}. Format it as 'QUESTION: [question]' followed by 'A) [option]', 'B) [option]', 'C) [option]', 'D) [option]' and then 'CORRECT: [letter]' and 'EXPLANATION: [brief explanation]'."
        
        trivia_response = await self.get_ai_response(prompt)
        
        # Parse the response
        lines = trivia_response.split('\n')
        question = ""
        options = []
        correct = ""
        explanation = ""
        
        for line in lines:
            line = line.strip()
            if line.startswith('QUESTION:'):
                question = line.replace('QUESTION:', '').strip()
            elif line.startswith(('A)', 'B)', 'C)', 'D)')):
                options.append(line)
            elif line.startswith('CORRECT:'):
                correct = line.replace('CORRECT:', '').strip()
            elif line.startswith('EXPLANATION:'):
                explanation = line.replace('EXPLANATION:', '').strip()
        
        embed = discord.Embed(
            title=f"🧠 AI Trivia - {category.title()}",
            description=f"**{question}**\n\n" + "\n".join(options),
            color=0xf39c12,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Click the button with your answer!")
        
        # Create view with answer buttons
        view = TriviaView(correct, explanation)
        await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name="ai-mystery", description="Solve AI-generated mystery scenarios")
    @app_commands.describe(difficulty="Choose mystery complexity")
    @app_commands.choices(difficulty=[
        app_commands.Choice(name="🔍 Simple Mystery", value="simple"),
        app_commands.Choice(name="🕵️ Detective Case", value="detective"),
        app_commands.Choice(name="🏚️ Haunted Mystery", value="haunted"),
        app_commands.Choice(name="🚀 Sci-Fi Mystery", value="scifi")
    ])
    async def ai_mystery(self, interaction: discord.Interaction, difficulty: str = "simple"):
        """Generate interactive mystery scenarios"""
        await interaction.response.defer()
        
        mystery_prompts = {
            "simple": "Create a simple mystery scenario with 3-4 clues. Present the scenario and ask what the detective should investigate first.",
            "detective": "Create a detective case with multiple suspects, each with motives and alibis. Present the crime scene and initial information.",
            "haunted": "Create a spooky mystery involving unexplained phenomena. Set the scene and present the first strange occurrence.",
            "scifi": "Create a sci-fi mystery involving technology, space, or time. Present the anomaly and initial observations."
        }
        
        mystery = await self.get_ai_response(mystery_prompts[difficulty])
        
        embed = discord.Embed(
            title=f"🔍 AI Mystery - {difficulty.title()}",
            description=mystery,
            color=0x2c3e50,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="What's your first move, detective?")
        
        # Store mystery state
        self.active_games[interaction.user.id] = {
            'type': 'mystery',
            'difficulty': difficulty,
            'started_at': datetime.now(timezone.utc),
            'channel_id': interaction.channel.id,
            'clues_found': 0
        }
        
        await interaction.followup.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle responses to active games"""
        if message.author.bot:
            return
            
        user_id = message.author.id
        if user_id not in self.active_games:
            return
            
        game = self.active_games[user_id]
        if game['channel_id'] != message.channel.id:
            return
            
        # Handle different game types
        if game['type'] == '20questions':
            await self._handle_20questions(message, game)
        elif game['type'] in ['association', 'story', 'character', 'world']:
            await self._handle_wordgame(message, game)
        elif game['type'] == 'mystery':
            await self._handle_mystery(message, game)

    async def _handle_20questions(self, message, game):
        """Handle 20 questions responses"""
        if game['questions_left'] <= 0:
            return
            
        user_question = message.content
        prompt = f"Someone is playing 20 Questions and asked: '{user_question}'. Respond with yes/no and a brief helpful hint if appropriate. Keep track that this is question {21 - game['questions_left']} of 20."
        
        ai_response = await self.get_ai_response(prompt)
        
        game['questions_left'] -= 1
        
        embed = discord.Embed(
            title="🎯 20 Questions",
            description=f"**Your question:** {user_question}\n**AI Answer:** {ai_response}",
            color=0x3498db
        )
        embed.add_field(name="Questions Left", value=str(game['questions_left']), inline=True)
        
        if game['questions_left'] <= 0:
            embed.add_field(name="Game Over!", value="Make your final guess or ask for the answer!", inline=False)
            del self.active_games[message.author.id]
        
        await message.channel.send(embed=embed)

    async def _handle_wordgame(self, message, game):
        """Handle word game responses"""
        user_input = message.content
        game_type = game['type']
        
        prompts = {
            "association": f"Continue the word association game. They said '{user_input}'. Respond with a word associated with theirs.",
            "story": f"Continue the collaborative story. The last sentence was: '{user_input}'. Add the next sentence to continue the story.",
            "character": f"Continue character building. They added: '{user_input}'. Add another interesting trait or detail to the character.",
            "world": f"Continue world building. They added: '{user_input}'. Add another element to this fantasy world."
        }
        
        ai_response = await self.get_ai_response(prompts[game_type])
        
        game['turns'] += 1
        
        embed = discord.Embed(
            title=f"🎮 {game_type.title()} Game - Turn {game['turns']}",
            description=ai_response,
            color=0xe74c3c
        )
        
        if game['turns'] >= 10:
            embed.add_field(name="Great Game!", value="This has been a fun collaborative session!", inline=False)
            del self.active_games[message.author.id]
        
        await message.channel.send(embed=embed)

    async def _handle_mystery(self, message, game):
        """Handle mystery game responses"""
        user_action = message.content
        
        prompt = f"The detective decided to: '{user_action}'. Respond as the mystery game master. Reveal clues, describe what they find, or advance the mystery plot. Make it engaging and provide next steps."
        
        ai_response = await self.get_ai_response(prompt)
        
        game['clues_found'] += 1
        
        embed = discord.Embed(
            title=f"🔍 Mystery Investigation",
            description=ai_response,
            color=0x2c3e50
        )
        embed.add_field(name="Clues Found", value=str(game['clues_found']), inline=True)
        
        if game['clues_found'] >= 5:
            embed.add_field(name="Ready to Solve?", value="You've gathered enough clues! What's your theory?", inline=False)
        
        await message.channel.send(embed=embed)

class RiddleView(discord.ui.View):
    def __init__(self, answer):
        super().__init__(timeout=300)
        self.answer = answer

    @discord.ui.button(label="Show Answer", style=discord.ButtonStyle.primary, emoji="💡")
    async def show_answer(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="💡 Riddle Answer",
            description=f"**Answer:** {self.answer}",
            color=0x27ae60
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class TriviaView(discord.ui.View):
    def __init__(self, correct_answer, explanation):
        super().__init__(timeout=60)
        self.correct = correct_answer.upper()
        self.explanation = explanation

    @discord.ui.button(label="A", style=discord.ButtonStyle.secondary)
    async def answer_a(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._check_answer(interaction, "A")

    @discord.ui.button(label="B", style=discord.ButtonStyle.secondary)
    async def answer_b(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._check_answer(interaction, "B")

    @discord.ui.button(label="C", style=discord.ButtonStyle.secondary)
    async def answer_c(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._check_answer(interaction, "C")

    @discord.ui.button(label="D", style=discord.ButtonStyle.secondary)
    async def answer_d(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._check_answer(interaction, "D")

    async def _check_answer(self, interaction, choice):
        if choice == self.correct:
            embed = discord.Embed(
                title="✅ Correct!",
                description=f"Great job! The answer was {choice}.\n\n**Explanation:** {self.explanation}",
                color=0x27ae60
            )
        else:
            embed = discord.Embed(
                title="❌ Incorrect",
                description=f"Sorry! The correct answer was {self.correct}.\n\n**Explanation:** {self.explanation}",
                color=0xe74c3c
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(AIGames(bot))