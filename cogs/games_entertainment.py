import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import asyncio
import random
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class GamesEntertainment(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}
        self.trivia_questions = [
            {"question": "What year was Discord launched?", "answer": "2015", "options": ["2013", "2014", "2015", "2016"]},
            {"question": "Which programming language is Discord primarily written in?", "answer": "JavaScript", "options": ["Python", "JavaScript", "Java", "C++"]},
            {"question": "What is the maximum file size for Discord uploads without Nitro?", "answer": "8MB", "options": ["5MB", "8MB", "10MB", "16MB"]},
        ]
        
    @app_commands.command(name="trivia", description="Start a trivia game with categories and difficulty")
    @app_commands.describe(
        category="Trivia category",
        difficulty="Question difficulty",
        questions="Number of questions"
    )
    @app_commands.choices(category=[
        app_commands.Choice(name="General Knowledge", value="general"),
        app_commands.Choice(name="Science", value="science"),
        app_commands.Choice(name="History", value="history"),
        app_commands.Choice(name="Gaming", value="gaming"),
        app_commands.Choice(name="Technology", value="tech")
    ])
    @app_commands.choices(difficulty=[
        app_commands.Choice(name="Easy", value="easy"),
        app_commands.Choice(name="Medium", value="medium"),
        app_commands.Choice(name="Hard", value="hard")
    ])
    async def trivia_game(self, interaction: discord.Interaction, 
                         category: str = "general", difficulty: str = "medium", questions: int = 5):
        await interaction.response.defer()
        
        try:
            # Generate trivia questions based on category
            game_questions = self.generate_trivia_questions(category, difficulty, questions)
            
            if not game_questions:
                await interaction.followup.send("❌ Failed to generate trivia questions. Please try again.")
                return
            
            game_id = f"{interaction.channel.id}_{int(datetime.now().timestamp())}"
            self.active_games[game_id] = {
                "type": "trivia",
                "questions": game_questions,
                "current_question": 0,
                "players": {},
                "channel": interaction.channel,
                "started_by": interaction.user.id
            }
            
            embed = discord.Embed(
                title="🧠 Trivia Game Started!",
                description=f"**Category:** {category.title()}\n**Difficulty:** {difficulty.title()}\n**Questions:** {questions}",
                color=discord.Color.blue()
            )
            embed.add_field(name="How to Play", value="React with 🇦 🇧 🇨 🇩 to answer questions!", inline=False)
            embed.set_footer(text="Game starting in 3 seconds...")
            
            await interaction.followup.send(embed=embed)
            await asyncio.sleep(3)
            
            # Start the trivia game
            await self.run_trivia_game(game_id)
            
        except Exception as e:
            logger.error(f"Trivia game error: {e}")
            await interaction.followup.send("❌ Failed to start trivia game.")

    @app_commands.command(name="word-chain", description="Start a word chain game")
    @app_commands.describe(
        min_length="Minimum word length",
        time_limit="Time limit per turn (seconds)",
        theme="Word theme (optional)"
    )
    async def word_chain(self, interaction: discord.Interaction, 
                        min_length: int = 3, time_limit: int = 30, theme: str = None):
        await interaction.response.defer()
        
        try:
            game_id = f"{interaction.channel.id}_wordchain"
            
            if game_id in self.active_games:
                await interaction.followup.send("❌ A word chain game is already running in this channel!")
                return
            
            # Starting words by theme
            starting_words = {
                "animals": ["elephant", "tiger", "rabbit", "dolphin"],
                "food": ["apple", "banana", "chocolate", "pasta"],
                "technology": ["computer", "robot", "internet", "smartphone"],
                None: ["adventure", "brilliant", "creative", "dynamic"]
            }
            
            start_word = random.choice(starting_words.get(theme, starting_words[None]))
            
            self.active_games[game_id] = {
                "type": "word_chain",
                "current_word": start_word,
                "used_words": {start_word.lower()},
                "players": {},
                "turn_order": [],
                "current_player": 0,
                "min_length": min_length,
                "time_limit": time_limit,
                "theme": theme,
                "channel": interaction.channel,
                "last_activity": datetime.now()
            }
            
            embed = discord.Embed(
                title="🔗 Word Chain Game Started!",
                description=f"**Starting word:** `{start_word}`\n**Next word must start with:** `{start_word[-1].upper()}`",
                color=discord.Color.green()
            )
            embed.add_field(name="Rules", 
                           value=f"• Words must be at least {min_length} letters\n• No repeated words\n• {time_limit}s per turn\n• React with 🎯 to join!", 
                           inline=False)
            if theme:
                embed.add_field(name="Theme", value=theme.title(), inline=True)
            
            message = await interaction.followup.send(embed=embed)
            await message.add_reaction("🎯")
            
            # Monitor for game timeout
            asyncio.create_task(self.monitor_word_chain(game_id))
            
        except Exception as e:
            logger.error(f"Word chain error: {e}")
            await interaction.followup.send("❌ Failed to start word chain game.")

    @app_commands.command(name="guess-number", description="Number guessing game with leaderboards")
    @app_commands.describe(
        min_number="Minimum number in range",
        max_number="Maximum number in range",
        max_guesses="Maximum number of guesses allowed"
    )
    async def guess_number(self, interaction: discord.Interaction, 
                          min_number: int = 1, max_number: int = 100, max_guesses: int = 10):
        await interaction.response.defer()
        
        try:
            if max_number <= min_number:
                await interaction.followup.send("❌ Maximum number must be greater than minimum number.")
                return
            
            secret_number = random.randint(min_number, max_number)
            game_id = f"{interaction.user.id}_guess"
            
            self.active_games[game_id] = {
                "type": "guess_number",
                "secret_number": secret_number,
                "min_number": min_number,
                "max_number": max_number,
                "max_guesses": max_guesses,
                "guesses_made": 0,
                "guesses": [],
                "player": interaction.user.id,
                "channel": interaction.channel,
                "started_at": datetime.now()
            }
            
            embed = discord.Embed(
                title="🎯 Number Guessing Game",
                description=f"I'm thinking of a number between **{min_number}** and **{max_number}**!\nYou have **{max_guesses}** guesses to find it.",
                color=discord.Color.purple()
            )
            embed.add_field(name="How to Play", value="Simply type your guess as a number in chat!", inline=False)
            embed.set_footer(text=f"Game started by {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Guess number error: {e}")
            await interaction.followup.send("❌ Failed to start guessing game.")

    @app_commands.command(name="rock-paper-scissors", description="Enhanced rock paper scissors with tournaments")
    @app_commands.describe(
        opponent="Challenge a specific user",
        best_of="Best of how many rounds",
        tournament="Start a tournament mode"
    )
    async def rock_paper_scissors(self, interaction: discord.Interaction, 
                                 opponent: discord.Member = None, best_of: int = 3, tournament: bool = False):
        await interaction.response.defer()
        
        try:
            if tournament:
                # Start tournament mode
                game_id = f"{interaction.channel.id}_rps_tournament"
                
                if game_id in self.active_games:
                    await interaction.followup.send("❌ A tournament is already running in this channel!")
                    return
                
                self.active_games[game_id] = {
                    "type": "rps_tournament",
                    "participants": [],
                    "rounds": [],
                    "current_round": 0,
                    "channel": interaction.channel,
                    "organizer": interaction.user.id
                }
                
                embed = discord.Embed(
                    title="🏆 Rock Paper Scissors Tournament!",
                    description="React with ✋ to join the tournament!\nTournament will start in 60 seconds.",
                    color=discord.Color.gold()
                )
                embed.add_field(name="Format", value="Single elimination\nBest of 3 rounds per match", inline=True)
                embed.set_footer(text="Minimum 4 players required")
                
                message = await interaction.followup.send(embed=embed)
                await message.add_reaction("✋")
                
                # Start tournament after delay
                asyncio.create_task(self.start_rps_tournament(game_id, 60))
                
            else:
                # Regular 1v1 game
                if opponent and opponent.bot:
                    await interaction.followup.send("❌ You can't challenge a bot!")
                    return
                
                game_id = f"{interaction.user.id}_{opponent.id if opponent else 'bot'}_rps"
                
                self.active_games[game_id] = {
                    "type": "rps_1v1",
                    "player1": interaction.user.id,
                    "player2": opponent.id if opponent else None,
                    "best_of": best_of,
                    "rounds": [],
                    "current_round": 0,
                    "channel": interaction.channel
                }
                
                if opponent:
                    embed = discord.Embed(
                        title="✂️ Rock Paper Scissors Challenge!",
                        description=f"{interaction.user.mention} challenges {opponent.mention}!\n**Best of {best_of}** rounds",
                        color=discord.Color.red()
                    )
                    embed.add_field(name="How to Play", value="Both players DM me your moves:\n🪨 Rock\n📄 Paper\n✂️ Scissors", inline=False)
                    
                    await interaction.followup.send(embed=embed)
                    
                    # Send DM instructions
                    try:
                        await interaction.user.send(f"🎮 RPS Game vs {opponent.display_name}\nSend your move: rock, paper, or scissors")
                        await opponent.send(f"🎮 RPS Game vs {interaction.user.display_name}\nSend your move: rock, paper, or scissors")
                    except discord.Forbidden:
                        await interaction.followup.send("⚠️ Couldn't send DMs. Please enable DMs from server members.")
                else:
                    # vs bot
                    embed = discord.Embed(
                        title="🤖 Rock Paper Scissors vs Bot",
                        description=f"Best of {best_of} rounds against me!",
                        color=discord.Color.blue()
                    )
                    embed.add_field(name="Make Your Move", value="React with:\n🪨 Rock\n📄 Paper\n✂️ Scissors", inline=False)
                    
                    message = await interaction.followup.send(embed=embed)
                    await message.add_reaction("🪨")
                    await message.add_reaction("📄")
                    await message.add_reaction("✂️")
                
        except Exception as e:
            logger.error(f"RPS error: {e}")
            await interaction.followup.send("❌ Failed to start rock paper scissors game.")

    @app_commands.command(name="riddle", description="Solve riddles with hints and difficulty levels")
    @app_commands.describe(
        difficulty="Riddle difficulty level"
    )
    @app_commands.choices(difficulty=[
        app_commands.Choice(name="Easy", value="easy"),
        app_commands.Choice(name="Medium", value="medium"),
        app_commands.Choice(name="Hard", value="hard"),
        app_commands.Choice(name="Extreme", value="extreme")
    ])
    async def riddle_game(self, interaction: discord.Interaction, difficulty: str = "medium"):
        await interaction.response.defer()
        
        try:
            riddles = self.get_riddles_by_difficulty(difficulty)
            riddle = random.choice(riddles)
            
            game_id = f"{interaction.channel.id}_riddle"
            
            self.active_games[game_id] = {
                "type": "riddle",
                "riddle": riddle,
                "difficulty": difficulty,
                "hints_used": 0,
                "max_hints": len(riddle.get("hints", [])),
                "solved": False,
                "solver": None,
                "channel": interaction.channel,
                "started_at": datetime.now()
            }
            
            embed = discord.Embed(
                title=f"🧩 Riddle Challenge ({difficulty.title()})",
                description=riddle["question"],
                color=discord.Color.purple()
            )
            embed.add_field(name="How to Solve", value="Simply type your answer in chat!", inline=False)
            if riddle.get("hints"):
                embed.add_field(name="Hints Available", value=f"{len(riddle['hints'])} hints available\nUse `/hint` command", inline=True)
            embed.set_footer(text="Good luck solving this riddle!")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Riddle error: {e}")
            await interaction.followup.send("❌ Failed to start riddle game.")

    @app_commands.command(name="hint", description="Get a hint for the current riddle")
    async def get_hint(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            game_id = f"{interaction.channel.id}_riddle"
            
            if game_id not in self.active_games:
                await interaction.followup.send("❌ No riddle game is currently running in this channel.")
                return
            
            game = self.active_games[game_id]
            riddle = game["riddle"]
            
            if game["hints_used"] >= game["max_hints"]:
                await interaction.followup.send("❌ No more hints available for this riddle!")
                return
            
            hint = riddle["hints"][game["hints_used"]]
            game["hints_used"] += 1
            
            embed = discord.Embed(
                title="💡 Riddle Hint",
                description=hint,
                color=discord.Color.yellow()
            )
            embed.add_field(
                name="Hints Used", 
                value=f"{game['hints_used']}/{game['max_hints']}", 
                inline=True
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Hint error: {e}")
            await interaction.followup.send("❌ Failed to get hint.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        # Handle game responses
        await self.handle_game_responses(message)

    async def handle_game_responses(self, message):
        """Handle responses for active games"""
        try:
            # Number guessing game
            game_id = f"{message.author.id}_guess"
            if game_id in self.active_games and message.content.isdigit():
                await self.handle_number_guess(message, game_id)
            
            # Riddle game
            riddle_game_id = f"{message.channel.id}_riddle"
            if riddle_game_id in self.active_games:
                await self.handle_riddle_guess(message, riddle_game_id)
            
            # Word chain game
            wordchain_game_id = f"{message.channel.id}_wordchain"
            if wordchain_game_id in self.active_games:
                await self.handle_word_chain(message, wordchain_game_id)
                
        except Exception as e:
            logger.error(f"Game response error: {e}")

    async def handle_number_guess(self, message, game_id):
        """Handle number guessing game logic"""
        game = self.active_games[game_id]
        guess = int(message.content)
        
        game["guesses_made"] += 1
        game["guesses"].append(guess)
        
        if guess == game["secret_number"]:
            # Correct guess!
            embed = discord.Embed(
                title="🎉 Congratulations!",
                description=f"You guessed it! The number was **{game['secret_number']}**",
                color=discord.Color.green()
            )
            embed.add_field(name="Guesses", value=f"{game['guesses_made']}/{game['max_guesses']}", inline=True)
            embed.add_field(name="Time", value=f"{(datetime.now() - game['started_at']).seconds}s", inline=True)
            
            await message.reply(embed=embed)
            
            # Save score to database
            await self.save_game_score(message.author.id, "number_guess", game["guesses_made"], game["max_guesses"])
            
            del self.active_games[game_id]
            
        elif game["guesses_made"] >= game["max_guesses"]:
            # Game over
            embed = discord.Embed(
                title="💥 Game Over!",
                description=f"You've used all {game['max_guesses']} guesses!\nThe number was **{game['secret_number']}**",
                color=discord.Color.red()
            )
            await message.reply(embed=embed)
            del self.active_games[game_id]
            
        else:
            # Give hint
            if guess < game["secret_number"]:
                hint = "📈 Too low!"
            else:
                hint = "📉 Too high!"
            
            remaining = game["max_guesses"] - game["guesses_made"]
            await message.reply(f"{hint} You have **{remaining}** guesses left.")

    async def handle_riddle_guess(self, message, game_id):
        """Handle riddle game logic"""
        game = self.active_games[game_id]
        riddle = game["riddle"]
        
        user_answer = message.content.lower().strip()
        correct_answers = [ans.lower().strip() for ans in riddle["answers"]]
        
        if any(answer in user_answer for answer in correct_answers):
            # Correct answer!
            game["solved"] = True
            game["solver"] = message.author.id
            
            time_taken = (datetime.now() - game["started_at"]).seconds
            difficulty_multiplier = {"easy": 1, "medium": 2, "hard": 3, "extreme": 5}
            score = difficulty_multiplier[game["difficulty"]] * (100 - game["hints_used"] * 10)
            
            embed = discord.Embed(
                title="🎉 Riddle Solved!",
                description=f"**Correct!** {riddle['answers'][0]}",
                color=discord.Color.green()
            )
            embed.add_field(name="Solver", value=message.author.mention, inline=True)
            embed.add_field(name="Time", value=f"{time_taken}s", inline=True)
            embed.add_field(name="Score", value=f"{score} points", inline=True)
            embed.add_field(name="Hints Used", value=f"{game['hints_used']}/{game['max_hints']}", inline=True)
            
            await message.reply(embed=embed)
            
            # Save score
            await self.save_game_score(message.author.id, "riddle", score, game["difficulty"])
            
            del self.active_games[game_id]

    def generate_trivia_questions(self, category, difficulty, count):
        """Generate trivia questions based on category and difficulty"""
        # This would ideally use an external trivia API
        # For now, return sample questions
        base_questions = [
            {"question": "What is the capital of France?", "answer": "Paris", "options": ["London", "Berlin", "Paris", "Madrid"]},
            {"question": "What year did World War II end?", "answer": "1945", "options": ["1943", "1944", "1945", "1946"]},
            {"question": "What is the largest planet in our solar system?", "answer": "Jupiter", "options": ["Saturn", "Jupiter", "Neptune", "Earth"]},
        ]
        
        return random.sample(base_questions, min(count, len(base_questions)))

    def get_riddles_by_difficulty(self, difficulty):
        """Get riddles based on difficulty level"""
        riddles = {
            "easy": [
                {
                    "question": "What has keys but no locks, space but no room, and you can enter but can't go inside?",
                    "answers": ["keyboard", "a keyboard"],
                    "hints": ["It's something you type on", "It has letters and numbers"]
                }
            ],
            "medium": [
                {
                    "question": "I speak without a mouth and hear without ears. I have no body, but I come alive with wind. What am I?",
                    "answers": ["echo", "an echo"],
                    "hints": ["You hear me in mountains", "I repeat what you say"]
                }
            ],
            "hard": [
                {
                    "question": "The more you take, the more you leave behind. What am I?",
                    "answers": ["footsteps", "steps", "footprints"],
                    "hints": ["Think about walking", "You make them when you move"]
                }
            ],
            "extreme": [
                {
                    "question": "I am not alive, but I grow; I don't have lungs, but I need air; I don't have a mouth, but water kills me. What am I?",
                    "answers": ["fire", "flame"],
                    "hints": ["I consume oxygen", "I'm afraid of water", "I provide heat and light"]
                }
            ]
        }
        
        return riddles.get(difficulty, riddles["medium"])

    async def save_game_score(self, user_id, game_type, score, extra_data=None):
        """Save game score to database"""
        try:
            async with aiosqlite.connect('ultrabot.db') as db:
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS game_scores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        game_type TEXT,
                        score INTEGER,
                        extra_data TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                await db.execute('''
                    INSERT INTO game_scores (user_id, game_type, score, extra_data)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, game_type, score, str(extra_data)))
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to save game score: {e}")

async def setup(bot):
    await bot.add_cog(GamesEntertainment(bot))