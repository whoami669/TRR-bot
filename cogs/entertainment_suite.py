import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import random
import asyncio
import aiohttp
import json
from datetime import datetime, timezone
from typing import Optional

class EntertainmentSuite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.trivia_sessions = {}
        self.game_sessions = {}

    @app_commands.command(name="trivia", description="Start an interactive trivia game")
    @app_commands.describe(
        category="Trivia category",
        difficulty="Question difficulty",
        amount="Number of questions"
    )
    @app_commands.choices(
        category=[
            app_commands.Choice(name="General Knowledge", value="9"),
            app_commands.Choice(name="Entertainment: Books", value="10"),
            app_commands.Choice(name="Entertainment: Film", value="11"),
            app_commands.Choice(name="Entertainment: Music", value="12"),
            app_commands.Choice(name="Science & Nature", value="17"),
            app_commands.Choice(name="Computers", value="18"),
            app_commands.Choice(name="Sports", value="21"),
            app_commands.Choice(name="Geography", value="22"),
            app_commands.Choice(name="History", value="23"),
            app_commands.Choice(name="Animals", value="27")
        ],
        difficulty=[
            app_commands.Choice(name="Easy", value="easy"),
            app_commands.Choice(name="Medium", value="medium"),
            app_commands.Choice(name="Hard", value="hard")
        ]
    )
    async def trivia_game(self, interaction: discord.Interaction, 
                         category: str = "9", difficulty: str = "medium", amount: int = 5):
        await interaction.response.defer()
        
        try:
            url = f"https://opentdb.com/api.php?amount={amount}&category={category}&difficulty={difficulty}&type=multiple"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        await interaction.followup.send("❌ Failed to fetch trivia questions.", ephemeral=True)
                        return
                    data = await resp.json()
            
            if not data.get('results'):
                await interaction.followup.send("❌ No trivia questions available.", ephemeral=True)
                return
            
            session_id = f"{interaction.guild.id}_{interaction.channel.id}"
            self.trivia_sessions[session_id] = {
                'questions': data['results'],
                'current': 0,
                'scores': {},
                'active': True,
                'channel': interaction.channel
            }
            
            await self.show_trivia_question(interaction, session_id)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error starting trivia: {str(e)}", ephemeral=True)

    async def show_trivia_question(self, interaction, session_id):
        session = self.trivia_sessions[session_id]
        question_data = session['questions'][session['current']]
        
        # Decode HTML entities
        import html
        question = html.unescape(question_data['question'])
        correct_answer = html.unescape(question_data['correct_answer'])
        incorrect_answers = [html.unescape(ans) for ans in question_data['incorrect_answers']]
        
        # Shuffle answers
        all_answers = [correct_answer] + incorrect_answers
        random.shuffle(all_answers)
        correct_index = all_answers.index(correct_answer)
        
        embed = discord.Embed(
            title=f"🧠 Trivia Question {session['current'] + 1}/{len(session['questions'])}",
            description=question,
            color=discord.Color.blue()
        )
        
        reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        for i, answer in enumerate(all_answers):
            embed.add_field(name=f"{reactions[i]} {answer}", value="", inline=False)
        
        embed.set_footer(text="React with the correct number! You have 30 seconds.")
        
        if session['current'] == 0:
            message = await interaction.followup.send(embed=embed)
        else:
            message = await session['channel'].send(embed=embed)
        
        for i in range(len(all_answers)):
            await message.add_reaction(reactions[i])
        
        # Wait for reactions
        def check(reaction, user):
            return (str(reaction.emoji) in reactions[:len(all_answers)] and 
                   user != self.bot.user and 
                   reaction.message.id == message.id)
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            user_answer = reactions.index(str(reaction.emoji))
            
            if user_answer == correct_index:
                session['scores'][user.id] = session['scores'].get(user.id, 0) + 1
                result_text = f"✅ {user.mention} got it right!"
            else:
                result_text = f"❌ {user.mention} was incorrect."
            
            result_text += f"\n**Correct answer:** {correct_answer}"
            
            await message.edit(embed=discord.Embed(
                title="Answer Result",
                description=result_text,
                color=discord.Color.green() if user_answer == correct_index else discord.Color.red()
            ))
            
        except asyncio.TimeoutError:
            await message.edit(embed=discord.Embed(
                title="⏰ Time's Up!",
                description=f"**Correct answer:** {correct_answer}",
                color=discord.Color.orange()
            ))
        
        session['current'] += 1
        
        if session['current'] < len(session['questions']):
            await asyncio.sleep(3)
            await self.show_trivia_question(interaction, session_id)
        else:
            await self.end_trivia_game(session['channel'], session)

    async def end_trivia_game(self, channel, session):
        if not session['scores']:
            await channel.send("🎯 Trivia ended! No one scored any points.")
            return
        
        sorted_scores = sorted(session['scores'].items(), key=lambda x: x[1], reverse=True)
        
        embed = discord.Embed(
            title="🏆 Trivia Results",
            color=discord.Color.gold()
        )
        
        for i, (user_id, score) in enumerate(sorted_scores[:5]):
            user = self.bot.get_user(user_id)
            medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i]
            embed.add_field(
                name=f"{medal} {user.display_name if user else 'Unknown'}",
                value=f"{score} points",
                inline=True
            )
        
        await channel.send(embed=embed)

    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question")
    @app_commands.describe(question="Your question for the magic 8-ball")
    async def magic_8ball(self, interaction: discord.Interaction, question: str):
        responses = [
            "It is certain", "Reply hazy, try again", "Don't count on it",
            "It is decidedly so", "Ask again later", "My reply is no",
            "Without a doubt", "Better not tell you now", "My sources say no",
            "Yes definitely", "Cannot predict now", "Outlook not so good",
            "You may rely on it", "Concentrate and ask again", "Very doubtful",
            "As I see it, yes", "Most likely", "Outlook good",
            "Yes", "Signs point to yes"
        ]
        
        response = random.choice(responses)
        
        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            color=discord.Color.purple()
        )
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=f"*{response}*", inline=False)
        embed.set_footer(text=f"Asked by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="joke", description="Get a random joke")
    @app_commands.describe(category="Type of joke")
    @app_commands.choices(category=[
        app_commands.Choice(name="Programming", value="programming"),
        app_commands.Choice(name="Dad Jokes", value="dad"),
        app_commands.Choice(name="Puns", value="puns"),
        app_commands.Choice(name="Random", value="random")
    ])
    async def random_joke(self, interaction: discord.Interaction, category: str = "random"):
        joke_collections = {
            "programming": [
                "Why do programmers prefer dark mode? Because light attracts bugs!",
                "How many programmers does it take to change a light bulb? None, that's a hardware problem.",
                "Why did the programmer quit his job? He didn't get arrays.",
                "What's a programmer's favorite hangout place? Foo Bar!",
                "Why do Java developers wear glasses? Because they can't C#!"
            ],
            "dad": [
                "I'm reading a book about anti-gravity. It's impossible to put down!",
                "Why don't scientists trust atoms? Because they make up everything!",
                "Did you hear about the mathematician who's afraid of negative numbers? He'll stop at nothing to avoid them!",
                "Why don't eggs tell jokes? They'd crack each other up!",
                "What do you call a fake noodle? An impasta!"
            ],
            "puns": [
                "I wondered why the baseball kept getting bigger. Then it hit me.",
                "A bicycle can't stand on its own because it's two tired.",
                "I used to be a banker, but I lost interest.",
                "Time flies like an arrow. Fruit flies like a banana.",
                "I'm reading a book on the history of glue. Can't put it down!"
            ]
        }
        
        if category == "random":
            all_jokes = []
            for jokes in joke_collections.values():
                all_jokes.extend(jokes)
            joke = random.choice(all_jokes)
        else:
            joke = random.choice(joke_collections.get(category, joke_collections["dad"]))
        
        embed = discord.Embed(
            title="😂 Random Joke",
            description=joke,
            color=discord.Color.yellow()
        )
        embed.set_footer(text=f"Category: {category.title()}")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rps", description="Play Rock Paper Scissors")
    @app_commands.describe(choice="Your choice")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Rock 🪨", value="rock"),
        app_commands.Choice(name="Paper 📄", value="paper"),
        app_commands.Choice(name="Scissors ✂️", value="scissors")
    ])
    async def rock_paper_scissors(self, interaction: discord.Interaction, choice: str):
        bot_choice = random.choice(["rock", "paper", "scissors"])
        
        emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
        
        # Determine winner
        if choice == bot_choice:
            result = "It's a tie!"
            color = discord.Color.yellow()
        elif (choice == "rock" and bot_choice == "scissors" or
              choice == "paper" and bot_choice == "rock" or
              choice == "scissors" and bot_choice == "paper"):
            result = "You win!"
            color = discord.Color.green()
        else:
            result = "I win!"
            color = discord.Color.red()
        
        embed = discord.Embed(
            title="🎮 Rock Paper Scissors",
            description=f"**You:** {emojis[choice]} {choice.title()}\n**Bot:** {emojis[bot_choice]} {bot_choice.title()}\n\n**{result}**",
            color=color
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="dice", description="Roll dice with custom configuration")
    @app_commands.describe(
        count="Number of dice to roll",
        sides="Number of sides per die",
        modifier="Modifier to add to the total"
    )
    async def roll_dice(self, interaction: discord.Interaction, 
                       count: int = 1, sides: int = 6, modifier: int = 0):
        
        if count > 20 or count < 1:
            await interaction.response.send_message("❌ Please roll between 1 and 20 dice!", ephemeral=True)
            return
        
        if sides > 100 or sides < 2:
            await interaction.response.send_message("❌ Dice must have between 2 and 100 sides!", ephemeral=True)
            return
        
        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls) + modifier
        
        embed = discord.Embed(
            title="🎲 Dice Roll",
            color=discord.Color.blue()
        )
        
        if count <= 10:
            rolls_text = " + ".join(map(str, rolls))
            if modifier != 0:
                rolls_text += f" + {modifier}" if modifier > 0 else f" - {abs(modifier)}"
            embed.add_field(name="Rolls", value=rolls_text, inline=False)
        else:
            embed.add_field(name="Individual Rolls", value=f"{rolls[:5]}..." if count > 5 else str(rolls), inline=False)
        
        embed.add_field(name="Total", value=f"**{total}**", inline=True)
        embed.add_field(name="Configuration", value=f"{count}d{sides}{'+' if modifier >= 0 else ''}{modifier if modifier != 0 else ''}", inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="coinflip", description="Flip a coin")
    @app_commands.describe(count="Number of coins to flip")
    async def coin_flip(self, interaction: discord.Interaction, count: int = 1):
        if count > 10 or count < 1:
            await interaction.response.send_message("❌ Please flip between 1 and 10 coins!", ephemeral=True)
            return
        
        results = [random.choice(["Heads", "Tails"]) for _ in range(count)]
        heads = results.count("Heads")
        tails = results.count("Tails")
        
        embed = discord.Embed(
            title="🪙 Coin Flip",
            color=discord.Color.gold()
        )
        
        if count == 1:
            emoji = "🟡" if results[0] == "Heads" else "⚫"
            embed.description = f"{emoji} **{results[0]}!**"
        else:
            embed.add_field(name="Results", value=" ".join("🟡" if r == "Heads" else "⚫" for r in results), inline=False)
            embed.add_field(name="Heads", value=str(heads), inline=True)
            embed.add_field(name="Tails", value=str(tails), inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="riddle", description="Get a riddle to solve")
    async def riddle_challenge(self, interaction: discord.Interaction):
        riddles = [
            {
                "question": "I speak without a mouth and hear without ears. I have no body, but come alive with wind. What am I?",
                "answer": "echo"
            },
            {
                "question": "The more you take, the more you leave behind. What am I?",
                "answer": "footsteps"
            },
            {
                "question": "What has keys but no locks, space but no room, and you can enter but not go inside?",
                "answer": "keyboard"
            },
            {
                "question": "I'm tall when I'm young and short when I'm old. What am I?",
                "answer": "candle"
            },
            {
                "question": "What gets wet while drying?",
                "answer": "towel"
            }
        ]
        
        riddle = random.choice(riddles)
        
        embed = discord.Embed(
            title="🤔 Riddle Challenge",
            description=riddle["question"],
            color=discord.Color.purple()
        )
        embed.add_field(name="Answer", value=f"||{riddle['answer']}||", inline=False)
        embed.set_footer(text="Click the spoiler to reveal the answer!")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="fact", description="Get an interesting fact")
    @app_commands.describe(category="Category of fact")
    @app_commands.choices(category=[
        app_commands.Choice(name="Science", value="science"),
        app_commands.Choice(name="History", value="history"),
        app_commands.Choice(name="Animals", value="animals"),
        app_commands.Choice(name="Space", value="space"),
        app_commands.Choice(name="Random", value="random")
    ])
    async def interesting_fact(self, interaction: discord.Interaction, category: str = "random"):
        facts = {
            "science": [
                "Honey never spoils. Archaeologists have found edible honey in ancient Egyptian tombs!",
                "A group of flamingos is called a 'flamboyance'.",
                "Bananas are berries, but strawberries aren't!",
                "The human brain uses about 20% of the body's total energy.",
                "Lightning strikes about 100 times per second worldwide."
            ],
            "history": [
                "The shortest war in history lasted only 38-45 minutes between Britain and Zanzibar in 1896.",
                "Cleopatra lived closer in time to the Moon landing than to the construction of the Great Pyramid.",
                "The Great Wall of China isn't visible from space with the naked eye.",
                "Napoleon wasn't actually short - he was average height for his time.",
                "The ancient Romans used urine as mouthwash."
            ],
            "animals": [
                "Octopuses have three hearts and blue blood.",
                "A shrimp's heart is in its head.",
                "Elephants can't jump.",
                "A group of pandas is called an 'embarrassment'.",
                "Dolphins have names for each other."
            ],
            "space": [
                "A day on Venus is longer than its year!",
                "There are more possible chess games than atoms in the observable universe.",
                "Saturn would float in water if there was a bathtub big enough.",
                "One teaspoon of a neutron star would weigh 6 billion tons.",
                "The Milky Way galaxy is on a collision course with Andromeda."
            ]
        }
        
        if category == "random":
            all_facts = []
            for category_facts in facts.values():
                all_facts.extend(category_facts)
            fact = random.choice(all_facts)
        else:
            fact = random.choice(facts.get(category, facts["science"]))
        
        embed = discord.Embed(
            title="🤓 Interesting Fact",
            description=fact,
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Category: {category.title()}")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(EntertainmentSuite(bot))