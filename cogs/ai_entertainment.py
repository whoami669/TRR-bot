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

class AIEntertainment(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.ai_personas = {
            'wizard': {
                'name': 'Merlin the Wise',
                'personality': 'Ancient wizard who speaks in riddles and mystical language',
                'system_prompt': 'You are Merlin, a wise and ancient wizard. Speak with mystical wisdom, use magical metaphors, and occasionally speak in riddles. Be helpful but maintain your mystical character.'
            },
            'detective': {
                'name': 'Detective Holmes',
                'personality': 'Brilliant detective with keen observation skills',
                'system_prompt': 'You are a brilliant detective like Sherlock Holmes. Use deductive reasoning, ask probing questions, and notice details others miss. Be analytical but engaging.'
            },
            'comedian': {
                'name': 'Jester Bot',
                'personality': 'Witty comedian who loves making people laugh',
                'system_prompt': 'You are a clever comedian. Make witty observations, tell jokes, use puns, and keep things light and fun. Be appropriate for all ages.'
            },
            'therapist': {
                'name': 'Dr. Mindful',
                'personality': 'Caring therapist who provides emotional support',
                'system_prompt': 'You are a caring therapist. Provide emotional support, ask thoughtful questions, and offer gentle guidance. Be empathetic and non-judgmental.'
            },
            'coach': {
                'name': 'Coach Victory',
                'personality': 'Motivational life coach',
                'system_prompt': 'You are an energetic life coach. Motivate people, help them set goals, celebrate achievements, and push them to be their best. Be encouraging and positive.'
            }
        }
        
    async def get_ai_response(self, prompt: str, persona: str = None, user_context: str = None) -> str:
        """Get AI response with optional persona and context"""
        try:
            messages = []
            
            if persona and persona in self.ai_personas:
                messages.append({
                    "role": "system",
                    "content": self.ai_personas[persona]['system_prompt']
                })
            
            if user_context:
                messages.append({
                    "role": "system", 
                    "content": f"Additional context about the user: {user_context}"
                })
            
            messages.append({"role": "user", "content": prompt})
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=500,
                temperature=0.8
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"The AI seems to be having trouble connecting. Error: {str(e)}"

    @app_commands.command(name="ai-persona", description="Chat with different AI personalities")
    @app_commands.describe(
        persona="Choose an AI personality to chat with",
        message="Your message to the AI persona"
    )
    @app_commands.choices(persona=[
        app_commands.Choice(name="🧙‍♂️ Merlin the Wise (Wizard)", value="wizard"),
        app_commands.Choice(name="🕵️ Detective Holmes", value="detective"),
        app_commands.Choice(name="🎭 Jester Bot (Comedian)", value="comedian"),
        app_commands.Choice(name="🧠 Dr. Mindful (Therapist)", value="therapist"),
        app_commands.Choice(name="💪 Coach Victory", value="coach")
    ])
    async def ai_persona(self, interaction: discord.Interaction, persona: str, message: str):
        """Chat with different AI personalities"""
        await interaction.response.defer()
        
        persona_info = self.ai_personas.get(persona)
        if not persona_info:
            await interaction.followup.send("Unknown persona selected!", ephemeral=True)
            return
        
        response = await self.get_ai_response(message, persona)
        
        embed = discord.Embed(
            title=f"💬 {persona_info['name']}",
            description=response,
            color=0x00ff88,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=f"Chatting with {persona_info['name']} | Personality: {persona_info['personality']}")
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="ai-story", description="Start an interactive AI story adventure")
    @app_commands.describe(genre="Choose the story genre")
    @app_commands.choices(genre=[
        app_commands.Choice(name="🏰 Fantasy Adventure", value="fantasy"),
        app_commands.Choice(name="🚀 Sci-Fi Exploration", value="scifi"),
        app_commands.Choice(name="🕵️ Mystery Thriller", value="mystery"),
        app_commands.Choice(name="🏴‍☠️ Pirate Adventure", value="pirate"),
        app_commands.Choice(name="🦸 Superhero Origin", value="superhero")
    ])
    async def ai_story(self, interaction: discord.Interaction, genre: str):
        """Start an interactive story with AI"""
        await interaction.response.defer()
        
        genre_prompts = {
            "fantasy": "Start an epic fantasy adventure in a magical realm with dragons, wizards, and ancient mysteries.",
            "scifi": "Begin a thrilling sci-fi story on a distant planet with alien technology and space exploration.",
            "mystery": "Create a gripping mystery story with clues, suspects, and unexpected twists.",
            "pirate": "Start a swashbuckling pirate adventure on the high seas with treasure and danger.",
            "superhero": "Begin a superhero origin story with powers, villains, and heroic choices."
        }
        
        prompt = f"{genre_prompts.get(genre, 'Start an exciting adventure story.')} Keep it engaging and end with choices for the reader to make. Make it about 150 words."
        
        story_start = await self.get_ai_response(prompt)
        
        embed = discord.Embed(
            title=f"📚 Interactive Story: {genre.title()} Adventure",
            description=story_start,
            color=0xff6b35,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="React with 1️⃣, 2️⃣, or 3️⃣ to make your choice!")
        
        message = await interaction.followup.send(embed=embed)
        
        # Add reaction choices
        for emoji in ['1️⃣', '2️⃣', '3️⃣']:
            await message.add_reaction(emoji)

    @app_commands.command(name="ai-roast", description="Get a friendly AI roast based on your Discord activity")
    async def ai_roast(self, interaction: discord.Interaction, target: discord.Member = None):
        """Get a friendly AI roast"""
        await interaction.response.defer()
        
        if target is None:
            target = interaction.user
        
        # Get some context about the user
        user_context = f"Username: {target.display_name}, joined server: {target.joined_at.strftime('%B %Y') if target.joined_at else 'unknown'}"
        
        roast_prompt = f"Give a friendly, witty roast about someone named {target.display_name}. Make it clever and funny but not mean or offensive. Keep it lighthearted and playful, like friends teasing each other."
        
        roast = await self.get_ai_response(roast_prompt, "comedian", user_context)
        
        embed = discord.Embed(
            title=f"🔥 AI Roast for {target.display_name}",
            description=roast,
            color=0xff4757,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text="All in good fun! 😄")
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="ai-advice", description="Get personalized life advice from AI")
    @app_commands.describe(situation="Describe your situation or question")
    async def ai_advice(self, interaction: discord.Interaction, situation: str):
        """Get personalized advice from AI therapist"""
        await interaction.response.defer(ephemeral=True)
        
        advice_prompt = f"Someone is asking for advice about: {situation}. Provide thoughtful, helpful guidance that's supportive and practical. Be empathetic and offer actionable suggestions."
        
        advice = await self.get_ai_response(advice_prompt, "therapist")
        
        embed = discord.Embed(
            title="🧠 AI Life Advice",
            description=advice,
            color=0x3742fa,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Remember: This is AI advice. For serious issues, consider professional help.")
        
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="ai-motivate", description="Get personalized motivation from an AI coach")
    @app_commands.describe(goal="What are you trying to achieve or overcome?")
    async def ai_motivate(self, interaction: discord.Interaction, goal: str = None):
        """Get personalized motivation"""
        await interaction.response.defer()
        
        if goal:
            prompt = f"Someone wants motivation for: {goal}. Give them an energetic, inspiring pep talk that will pump them up and help them succeed. Be enthusiastic and specific to their goal."
        else:
            prompt = "Give someone a general motivational boost. Be energetic, positive, and inspiring. Help them feel ready to tackle any challenge."
        
        motivation = await self.get_ai_response(prompt, "coach")
        
        embed = discord.Embed(
            title="💪 AI Motivation Boost",
            description=motivation,
            color=0x2ed573,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="You've got this! 🌟")
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="ai-create", description="Collaborate with AI to create something amazing")
    @app_commands.describe(
        project_type="What do you want to create?",
        topic="The topic or theme for your creation"
    )
    @app_commands.choices(project_type=[
        app_commands.Choice(name="🎵 Song Lyrics", value="lyrics"),
        app_commands.Choice(name="📝 Poem", value="poem"),
        app_commands.Choice(name="📖 Short Story", value="story"),
        app_commands.Choice(name="💡 Business Idea", value="business"),
        app_commands.Choice(name="🎨 Art Concept", value="art"),
        app_commands.Choice(name="🎮 Game Idea", value="game")
    ])
    async def ai_create(self, interaction: discord.Interaction, project_type: str, topic: str):
        """Collaborate with AI on creative projects"""
        await interaction.response.defer()
        
        creation_prompts = {
            "lyrics": f"Write creative song lyrics about {topic}. Make them catchy, meaningful, and include a chorus.",
            "poem": f"Write a beautiful poem about {topic}. Use vivid imagery and emotional language.",
            "story": f"Write a short, engaging story about {topic}. Include interesting characters and a compelling plot.",
            "business": f"Create an innovative business idea related to {topic}. Explain the concept, target market, and potential revenue model.",
            "art": f"Describe a detailed art concept about {topic}. Include colors, style, composition, and emotional impact.",
            "game": f"Design a creative game concept around {topic}. Include gameplay mechanics, objectives, and what makes it fun."
        }
        
        creation = await self.get_ai_response(creation_prompts.get(project_type, f"Create something creative about {topic}"))
        
        embed = discord.Embed(
            title=f"🎨 AI Creation: {project_type.title()}",
            description=creation[:2000],  # Discord embed limit
            color=0xf39c12,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Topic", value=topic, inline=True)
        embed.add_field(name="Collaboration", value=f"{interaction.user.mention} + AI", inline=True)
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="ai-debate", description="Start an AI debate on any topic")
    @app_commands.describe(topic="What topic should we debate?")
    async def ai_debate(self, interaction: discord.Interaction, topic: str):
        """Start a debate with AI taking opposing viewpoints"""
        await interaction.response.defer()
        
        # Get both sides of the argument
        pro_prompt = f"Argue FOR the position on this topic: {topic}. Be persuasive, logical, and present strong evidence."
        con_prompt = f"Argue AGAINST the position on this topic: {topic}. Be persuasive, logical, and present counter-arguments."
        
        pro_argument = await self.get_ai_response(pro_prompt)
        con_argument = await self.get_ai_response(con_prompt)
        
        embed = discord.Embed(
            title=f"⚖️ AI Debate: {topic}",
            color=0x7b68ee,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(
            name="✅ Arguments FOR", 
            value=pro_argument[:1000] + ("..." if len(pro_argument) > 1000 else ""), 
            inline=False
        )
        
        embed.add_field(
            name="❌ Arguments AGAINST", 
            value=con_argument[:1000] + ("..." if len(con_argument) > 1000 else ""), 
            inline=False
        )
        
        embed.set_footer(text="What's your take? Join the discussion!")
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AIEntertainment(bot))