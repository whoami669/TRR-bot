import discord
from discord.ext import commands
from discord import app_commands
import random
import aiohttp
import json
from typing import Optional

class FunCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question")
    @app_commands.describe(question="Your question for the 8-ball")
    async def eight_ball(self, interaction: discord.Interaction, question: str):
        responses = [
            "It is certain", "It is decidedly so", "Without a doubt", "Yes definitely",
            "You may rely on it", "As I see it, yes", "Most likely", "Outlook good",
            "Yes", "Signs point to yes", "Reply hazy, try again", "Ask again later",
            "Better not tell you now", "Cannot predict now", "Concentrate and ask again",
            "Don't count on it", "My reply is no", "My sources say no",
            "Outlook not so good", "Very doubtful"
        ]
        
        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            color=0x8b00ff
        )
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=random.choice(responses), inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="coinflip", description="Flip a coin")
    async def coinflip(self, interaction: discord.Interaction):
        result = random.choice(["Heads", "Tails"])
        emoji = "🪙" if result == "Heads" else "🔴"
        
        embed = discord.Embed(
            title=f"{emoji} Coin Flip",
            description=f"The coin landed on **{result}**!",
            color=0xffd700
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="dice", description="Roll dice")
    @app_commands.describe(sides="Number of sides on the dice (default: 6)", count="Number of dice to roll (default: 1)")
    async def dice(self, interaction: discord.Interaction, sides: int = 6, count: int = 1):
        if sides < 2 or sides > 100:
            await interaction.response.send_message("Dice must have between 2 and 100 sides")
            return
        
        if count < 1 or count > 10:
            await interaction.response.send_message("You can roll between 1 and 10 dice")
            return
        
        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls)
        
        embed = discord.Embed(
            title="🎲 Dice Roll",
            color=0xff6b6b
        )
        embed.add_field(name="Rolls", value=", ".join(map(str, rolls)), inline=False)
        embed.add_field(name="Total", value=str(total), inline=True)
        embed.add_field(name="Dice", value=f"{count}d{sides}", inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rps", description="Play Rock Paper Scissors")
    @app_commands.describe(choice="Your choice: rock, paper, or scissors")
    async def rock_paper_scissors(self, interaction: discord.Interaction, choice: str):
        choices = ["rock", "paper", "scissors"]
        choice = choice.lower()
        
        if choice not in choices:
            await interaction.response.send_message("Please choose rock, paper, or scissors")
            return
        
        bot_choice = random.choice(choices)
        
        # Determine winner
        if choice == bot_choice:
            result = "It's a tie!"
            color = 0xffff00
        elif (choice == "rock" and bot_choice == "scissors") or \
             (choice == "paper" and bot_choice == "rock") or \
             (choice == "scissors" and bot_choice == "paper"):
            result = "You win!"
            color = 0x00ff00
        else:
            result = "I win!"
            color = 0xff0000
        
        emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
        
        embed = discord.Embed(
            title="🎮 Rock Paper Scissors",
            description=f"You: {emojis[choice]} {choice.title()}\nMe: {emojis[bot_choice]} {bot_choice.title()}\n\n**{result}**",
            color=color
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="quote", description="Get a random inspirational quote")
    async def quote(self, interaction: discord.Interaction):
        quotes = [
            ("The only way to do great work is to love what you do.", "Steve Jobs"),
            ("Innovation distinguishes between a leader and a follower.", "Steve Jobs"),
            ("Life is what happens to you while you're busy making other plans.", "John Lennon"),
            ("The future belongs to those who believe in the beauty of their dreams.", "Eleanor Roosevelt"),
            ("It is during our darkest moments that we must focus to see the light.", "Aristotle"),
            ("The way to get started is to quit talking and begin doing.", "Walt Disney"),
            ("Don't let yesterday take up too much of today.", "Will Rogers"),
            ("You learn more from failure than from success.", "Unknown"),
            ("If you are working on something exciting that you really care about, you don't have to be pushed.", "Steve Jobs"),
            ("Experience is the teacher of all things.", "Julius Caesar")
        ]
        
        quote_text, author = random.choice(quotes)
        
        embed = discord.Embed(
            title="💭 Inspirational Quote",
            description=f'"{quote_text}"',
            color=0x9b59b6
        )
        embed.set_footer(text=f"— {author}")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="joke", description="Get a random joke")
    async def joke(self, interaction: discord.Interaction):
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the scarecrow win an award? He was outstanding in his field!",
            "Why don't eggs tell jokes? They'd crack each other up!",
            "What do you call a fake noodle? An impasta!",
            "Why did the math book look so sad? Because it was full of problems!",
            "What do you call a bear with no teeth? A gummy bear!",
            "Why can't a bicycle stand up by itself? It's two tired!",
            "What do you call a sleeping bull? A bulldozer!",
            "Why don't skeletons fight each other? They don't have the guts!",
            "What's the best thing about Switzerland? I don't know, but the flag is a big plus!"
        ]
        
        embed = discord.Embed(
            title="😂 Random Joke",
            description=random.choice(jokes),
            color=0xf39c12
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="choose", description="Let the bot choose from a list of options")
    @app_commands.describe(options="Comma-separated list of options")
    async def choose(self, interaction: discord.Interaction, options: str):
        choices = [choice.strip() for choice in options.split(",")]
        
        if len(choices) < 2:
            await interaction.response.send_message("Please provide at least 2 options separated by commas")
            return
        
        chosen = random.choice(choices)
        
        embed = discord.Embed(
            title="🤔 Decision Maker",
            description=f"I choose: **{chosen}**",
            color=0x3498db
        )
        embed.add_field(name="Options", value=", ".join(choices), inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="password", description="Generate a secure password")
    @app_commands.describe(length="Length of the password (8-50)")
    async def password(self, interaction: discord.Interaction, length: int = 12):
        if length < 8 or length > 50:
            await interaction.response.send_message("Password length must be between 8 and 50 characters")
            return
        
        import string
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(random.choice(characters) for _ in range(length))
        
        embed = discord.Embed(
            title="🔐 Password Generator",
            description=f"Your secure password: `{password}`",
            color=0x2ecc71
        )
        embed.set_footer(text="Keep this password safe!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="reverse", description="Reverse text")
    @app_commands.describe(text="Text to reverse")
    async def reverse(self, interaction: discord.Interaction, text: str):
        reversed_text = text[::-1]
        
        embed = discord.Embed(
            title="🔄 Text Reverser",
            color=0xe67e22
        )
        embed.add_field(name="Original", value=text, inline=False)
        embed.add_field(name="Reversed", value=reversed_text, inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ascii", description="Convert text to ASCII art")
    @app_commands.describe(text="Text to convert (max 10 characters)")
    async def ascii_art(self, interaction: discord.Interaction, text: str):
        if len(text) > 10:
            await interaction.response.send_message("Text must be 10 characters or less")
            return
        
        # Simple ASCII art conversion
        ascii_chars = {
            'A': ['  █  ', ' █ █ ', '█████', '█   █', '█   █'],
            'B': ['████ ', '█   █', '████ ', '█   █', '████ '],
            'C': [' ████', '█    ', '█    ', '█    ', ' ████'],
            'H': ['█   █', '█   █', '█████', '█   █', '█   █'],
            'I': ['█████', '  █  ', '  █  ', '  █  ', '█████'],
            'O': [' ███ ', '█   █', '█   █', '█   █', ' ███ '],
            ' ': ['     ', '     ', '     ', '     ', '     ']
        }
        
        text = text.upper()
        ascii_lines = ['', '', '', '', '']
        
        for char in text:
            if char in ascii_chars:
                for i in range(5):
                    ascii_lines[i] += ascii_chars[char][i] + ' '
            else:
                for i in range(5):
                    ascii_lines[i] += '█████ '
        
        ascii_art = '\n'.join(ascii_lines)
        
        embed = discord.Embed(
            title="🎨 ASCII Art",
            description=f"```\n{ascii_art}\n```",
            color=0x9b59b6
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(FunCommands(bot))