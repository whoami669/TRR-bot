import discord
from discord.ext import commands
import random
import aiohttp
import json
from utils.embeds import create_embed

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='meme')
    async def get_meme(self, ctx):
        """Get a random meme from Reddit"""
        subreddits = ['memes', 'dankmemes', 'wholesomememes', 'ProgrammerHumor']
        subreddit = random.choice(subreddits)
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f'https://www.reddit.com/r/{subreddit}/random/.json') as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        post = data[0]['data']['children'][0]['data']
                        
                        if not post.get('over_18'):  # SFW only
                            embed = create_embed(
                                title=post['title'][:100] + ('...' if len(post['title']) > 100 else ''),
                                color=0xFF4500
                            )
                            embed.set_image(url=post['url'])
                            embed.add_field(name="👍 Upvotes", value=str(post['ups']), inline=True)
                            embed.add_field(name="💬 Comments", value=str(post['num_comments']), inline=True)
                            embed.add_field(name="📱 Subreddit", value=f"r/{post['subreddit']}", inline=True)
                            
                            await ctx.send(embed=embed)
                            return
            except:
                pass
        
        await ctx.send("❌ Couldn't fetch a meme right now. Try again later!")

    @commands.command(name='joke')
    async def random_joke(self, ctx):
        """Get a random joke"""
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the scarecrow win an award? He was outstanding in his field!",
            "Why don't eggs tell jokes? They'd crack each other up!",
            "What do you call a fake noodle? An impasta!",
            "Why did the math book look so sad? Because it had too many problems!",
            "What do you call a bear with no teeth? A gummy bear!",
            "Why can't a bicycle stand up by itself? It's two tired!",
            "What do you call a fish wearing a bowtie? Sofishticated!",
            "Why don't skeletons fight each other? They don't have the guts!",
            "What do you call a sleeping bull? A bulldozer!"
        ]
        
        joke = random.choice(jokes)
        
        embed = create_embed(
            title="😂 Random Joke",
            description=joke,
            color=0xFFD700
        )
        
        await ctx.send(embed=embed)

    @commands.command(name='fact')
    async def random_fact(self, ctx):
        """Get a random fun fact"""
        facts = [
            "Honey never spoils. Archaeologists have found edible honey in ancient Egyptian tombs!",
            "A group of flamingos is called a 'flamboyance'.",
            "Bananas are berries, but strawberries aren't!",
            "The shortest war in history lasted only 38-45 minutes.",
            "A single cloud can weigh more than a million pounds.",
            "Octopuses have three hearts and blue blood.",
            "The Great Wall of China isn't visible from space with the naked eye.",
            "Wombat poop is cube-shaped.",
            "There are more possible games of chess than atoms in the observable universe.",
            "Sharks are older than trees!"
        ]
        
        fact = random.choice(facts)
        
        embed = create_embed(
            title="🧠 Fun Fact",
            description=fact,
            color=0x00CED1
        )
        
        await ctx.send(embed=embed)

    @commands.command(name='coinflip', aliases=['flip'])
    async def coin_flip(self, ctx):
        """Flip a coin"""
        result = random.choice(['Heads', 'Tails'])
        emoji = "🪙" if result == "Heads" else "🥈"
        
        embed = create_embed(
            title=f"{emoji} Coin Flip",
            description=f"**{result}**",
            color=0xFFD700
        )
        
        await ctx.send(embed=embed)

    @commands.command(name='dice', aliases=['roll'])
    async def roll_dice(self, ctx, sides: int = 6):
        """Roll a dice"""
        if sides < 2 or sides > 100:
            return await ctx.send("❌ Dice must have between 2 and 100 sides!")
        
        result = random.randint(1, sides)
        
        embed = create_embed(
            title="🎲 Dice Roll",
            description=f"You rolled a **{result}** on a {sides}-sided dice!",
            color=0x7289DA
        )
        
        await ctx.send(embed=embed)

    @commands.command(name='rps')
    async def rock_paper_scissors(self, ctx, choice):
        """Play rock paper scissors"""
        choices = ['rock', 'paper', 'scissors']
        emojis = {'rock': '🪨', 'paper': '📄', 'scissors': '✂️'}
        
        if choice.lower() not in choices:
            return await ctx.send("❌ Choose rock, paper, or scissors!")
        
        user_choice = choice.lower()
        bot_choice = random.choice(choices)
        
        # Determine winner
        if user_choice == bot_choice:
            result = "It's a tie!"
            color = 0xFFFF00
        elif (user_choice == 'rock' and bot_choice == 'scissors') or \
             (user_choice == 'paper' and bot_choice == 'rock') or \
             (user_choice == 'scissors' and bot_choice == 'paper'):
            result = "You win!"
            color = 0x00FF00
        else:
            result = "I win!"
            color = 0xFF0000
        
        embed = create_embed(
            title="🎮 Rock Paper Scissors",
            description=result,
            color=color
        )
        embed.add_field(name="Your choice", value=f"{emojis[user_choice]} {user_choice.title()}", inline=True)
        embed.add_field(name="My choice", value=f"{emojis[bot_choice]} {bot_choice.title()}", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name='slots')
    async def slot_machine(self, ctx):
        """Play the slot machine"""
        emojis = ['🍎', '🍌', '🍒', '🍇', '🍊', '🍓', '💎', '7️⃣']
        
        # Weighted random for different rarities
        weights = [15, 15, 15, 15, 15, 15, 8, 2]
        
        results = []
        for _ in range(3):
            results.append(random.choices(emojis, weights=weights)[0])
        
        # Check for wins
        if results[0] == results[1] == results[2]:
            if results[0] == '7️⃣':
                result_text = "🎉 JACKPOT! Triple 7s!"
                color = 0xFFD700
            elif results[0] == '💎':
                result_text = "💎 DIAMONDS! Big win!"
                color = 0x00FFFF
            else:
                result_text = "🎉 Three of a kind!"
                color = 0x00FF00
        elif results[0] == results[1] or results[1] == results[2] or results[0] == results[2]:
            result_text = "🎊 Two of a kind!"
            color = 0xFFA500
        else:
            result_text = "😢 No match, try again!"
            color = 0xFF0000
        
        embed = create_embed(
            title="🎰 Slot Machine",
            description=f"{results[0]} {results[1]} {results[2]}",
            color=color
        )
        embed.add_field(name="Result", value=result_text, inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name='magic')
    async def magic_trick(self, ctx):
        """Perform a magic trick"""
        tricks = [
            "🎩 *waves wand* Abracadabra! I've made your problems disappear! ...just kidding, they're still there.",
            "✨ *snaps fingers* Is this your card? No? Well, I tried.",
            "🔮 I can see into the future... you're going to use another bot command!",
            "🎭 Watch closely... *dramatic pause* ...Ta-da! Nothing happened!",
            "🌟 For my next trick, I'll make myself disappear! *goes offline*",
            "🎪 Behold! I shall read your mind... you're thinking this trick is silly!"
        ]
        
        trick = random.choice(tricks)
        
        embed = create_embed(
            title="🎩 Magic Show",
            description=trick,
            color=0x800080
        )
        
        await ctx.send(embed=embed)

    @commands.command(name='compliment')
    async def give_compliment(self, ctx, member: discord.Member = None):
        """Give someone a compliment"""
        target = member or ctx.author
        
        compliments = [
            "You're an awesome person!",
            "You have a great sense of humor!",
            "You're really smart!",
            "You're very kind and caring!",
            "You have excellent taste!",
            "You're incredibly creative!",
            "You brighten everyone's day!",
            "You're a wonderful friend!",
            "You have amazing energy!",
            "You're absolutely fantastic!"
        ]
        
        compliment = random.choice(compliments)
        
        embed = create_embed(
            title="💝 Compliment",
            description=f"{target.mention}, {compliment}",
            color=0xFF69B4
        )
        
        await ctx.send(embed=embed)

    @commands.command(name='insult')
    async def playful_insult(self, ctx, member: discord.Member = None):
        """Give someone a playful insult"""
        target = member or ctx.author
        
        # Keep insults very light and playful
        insults = [
            "You're about as useful as a chocolate teapot!",
            "You have the attention span of a goldfish!",
            "You're slower than Internet Explorer!",
            "You're the reason shampoo has instructions!",
            "You're like a dictionary - you add meaning to my life but I never use you!",
            "You're proof that evolution can go in reverse!",
            "You're the human equivalent of a participation trophy!",
            "You're like Monday mornings - nobody likes you!",
            "You have the personality of a wet sock!",
            "You're about as sharp as a bowling ball!"
        ]
        
        insult = random.choice(insults)
        
        embed = create_embed(
            title="😈 Playful Roast",
            description=f"{target.mention}, {insult}",
            color=0xFF4500
        )
        embed.set_footer(text="Just kidding! You're awesome! ❤️")
        
        await ctx.send(embed=embed)

    @commands.command(name='ship')
    async def ship_users(self, ctx, user1: discord.Member, user2: discord.Member):
        """Ship two users together"""
        if user1 == user2:
            return await ctx.send("❌ You can't ship someone with themselves!")
        
        # Calculate compatibility percentage
        compatibility = random.randint(1, 100)
        
        # Ship name (combine parts of usernames)
        name1 = user1.display_name[:len(user1.display_name)//2]
        name2 = user2.display_name[len(user2.display_name)//2:]
        ship_name = name1 + name2
        
        # Compatibility levels
        if compatibility >= 90:
            level = "💕 Perfect Match!"
            color = 0xFF1493
        elif compatibility >= 70:
            level = "💖 Great Match!"
            color = 0xFF69B4
        elif compatibility >= 50:
            level = "💗 Good Match!"
            color = 0xFFA0C9
        elif compatibility >= 30:
            level = "💝 Okay Match"
            color = 0xFFB6C1
        else:
            level = "💔 Not Compatible"
            color = 0x800080
        
        embed = create_embed(
            title="💘 Matchmaker",
            description=f"**{user1.display_name}** + **{user2.display_name}** = **{ship_name}**",
            color=color
        )
        embed.add_field(name="Compatibility", value=f"{compatibility}%", inline=True)
        embed.add_field(name="Status", value=level, inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name='quote')
    async def inspirational_quote(self, ctx):
        """Get an inspirational quote"""
        quotes = [
            "The only way to do great work is to love what you do. - Steve Jobs",
            "Innovation distinguishes between a leader and a follower. - Steve Jobs",
            "Life is what happens to you while you're busy making other plans. - John Lennon",
            "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
            "It is during our darkest moments that we must focus to see the light. - Aristotle",
            "The only impossible journey is the one you never begin. - Tony Robbins",
            "Success is not final, failure is not fatal: it is the courage to continue that counts. - Winston Churchill",
            "The way to get started is to quit talking and begin doing. - Walt Disney"
        ]
        
        quote = random.choice(quotes)
        
        embed = create_embed(
            title="💭 Inspirational Quote",
            description=quote,
            color=0x4682B4
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Fun(bot))
