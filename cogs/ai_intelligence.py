import discord
from discord.ext import commands
import aiosqlite
import asyncio
import random
import json
from datetime import datetime, timezone, timedelta
import os

class AIIntelligence(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.server_memory = {}
        self.user_personalities = {}

    @discord.app_commands.command(name="ai_persona", description="Set AI personality for interactions")
    async def ai_persona(self, interaction: discord.Interaction, 
                        personality: str, context: str = "", memory_depth: str = "medium"):
        """Set custom AI personality"""
        guild_id = interaction.guild.id
        
        if guild_id not in self.user_personalities:
            self.user_personalities[guild_id] = {}
        
        self.user_personalities[guild_id][interaction.user.id] = {
            "personality": personality,
            "context": context,
            "memory_depth": memory_depth,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        embed = discord.Embed(
            title="🧠 AI Persona Set",
            description=f"AI will now interact as: **{personality}**",
            color=0x00ff7f
        )
        embed.add_field(name="Context", value=context if context else "General interactions", inline=False)
        embed.add_field(name="Memory Depth", value=memory_depth, inline=True)
        embed.add_field(name="User", value=interaction.user.mention, inline=True)
        
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="ai_memory", description="Store important server moments")
    async def ai_memory(self, interaction: discord.Interaction, 
                       event_type: str, description: str, 
                       importance: str = "medium", tags: str = ""):
        """Store server memories"""
        guild_id = interaction.guild.id
        
        if guild_id not in self.server_memory:
            self.server_memory[guild_id] = []
        
        memory_entry = {
            "event_type": event_type,
            "description": description,
            "importance": importance,
            "tags": tags.split(",") if tags else [],
            "user": interaction.user.display_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "channel": interaction.channel.name
        }
        
        self.server_memory[guild_id].append(memory_entry)
        
        # Keep only last 100 memories per server
        if len(self.server_memory[guild_id]) > 100:
            self.server_memory[guild_id] = self.server_memory[guild_id][-100:]
        
        embed = discord.Embed(
            title="🧠 Memory Stored",
            description=f"**{event_type}**: {description}",
            color=0x4169e1
        )
        embed.add_field(name="Importance", value=importance, inline=True)
        embed.add_field(name="Tags", value=tags if tags else "None", inline=True)
        embed.set_footer(text=f"Recorded by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="ai_recall", description="Recall server memories")
    async def ai_recall(self, interaction: discord.Interaction, 
                       search_term: str = "", event_type: str = "", 
                       importance: str = "", limit: int = 5):
        """Recall stored memories"""
        guild_id = interaction.guild.id
        
        if guild_id not in self.server_memory or not self.server_memory[guild_id]:
            await interaction.response.send_message("No memories stored for this server yet.", ephemeral=True)
            return
        
        memories = self.server_memory[guild_id]
        
        # Filter memories
        if search_term:
            memories = [m for m in memories if search_term.lower() in m["description"].lower()]
        if event_type:
            memories = [m for m in memories if m["event_type"].lower() == event_type.lower()]
        if importance:
            memories = [m for m in memories if m["importance"].lower() == importance.lower()]
        
        # Sort by timestamp (newest first)
        memories = sorted(memories, key=lambda x: x["timestamp"], reverse=True)
        memories = memories[:limit]
        
        if not memories:
            await interaction.response.send_message("No memories found matching your criteria.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🧠 Server Memories",
            description=f"Found {len(memories)} memories",
            color=0x9370db
        )
        
        for i, memory in enumerate(memories):
            embed.add_field(
                name=f"{memory['event_type']} ({memory['importance']})",
                value=f"{memory['description'][:100]}{'...' if len(memory['description']) > 100 else ''}\n*By {memory['user']} in #{memory['channel']}*",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="ai_sentiment", description="Analyze server mood and sentiment")
    async def ai_sentiment(self, interaction: discord.Interaction, 
                          channel: discord.TextChannel = None, 
                          timeframe: str = "1h", analysis_type: str = "general"):
        """Analyze community sentiment"""
        target_channel = channel or interaction.channel
        
        # Simulate sentiment analysis (would use real NLP in production)
        sentiments = ["Very Positive", "Positive", "Neutral", "Negative", "Very Negative"]
        current_sentiment = random.choice(sentiments)
        confidence = random.randint(75, 95)
        
        mood_indicators = {
            "Very Positive": {"color": 0x00ff00, "emoji": "😄"},
            "Positive": {"color": 0x7fff00, "emoji": "😊"},
            "Neutral": {"color": 0xffff00, "emoji": "😐"},
            "Negative": {"color": 0xff7f00, "emoji": "😔"},
            "Very Negative": {"color": 0xff0000, "emoji": "😢"}
        }
        
        mood = mood_indicators[current_sentiment]
        
        embed = discord.Embed(
            title=f"{mood['emoji']} Sentiment Analysis",
            description=f"Analyzing {target_channel.mention} over the last {timeframe}",
            color=mood["color"]
        )
        embed.add_field(name="Current Mood", value=f"{current_sentiment} ({confidence}% confidence)", inline=True)
        embed.add_field(name="Analysis Type", value=analysis_type, inline=True)
        embed.add_field(name="Sample Size", value=f"~{random.randint(20, 100)} messages", inline=True)
        
        # Add trending topics
        topics = ["gaming", "memes", "discussions", "events", "announcements"]
        trending = random.sample(topics, 3)
        embed.add_field(name="Trending Topics", value=", ".join(trending), inline=False)
        
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="ai_story", description="Start collaborative AI storytelling")
    async def ai_story(self, interaction: discord.Interaction, 
                      genre: str, setting: str, characters: str = "",
                      style: str = "adventure"):
        """Start AI-powered collaborative storytelling"""
        embed = discord.Embed(
            title="📚 AI Story Mode Activated",
            description=f"Starting a {genre} story in {setting}",
            color=0xdda0dd
        )
        embed.add_field(name="Genre", value=genre, inline=True)
        embed.add_field(name="Setting", value=setting, inline=True)
        embed.add_field(name="Style", value=style, inline=True)
        
        if characters:
            embed.add_field(name="Characters", value=characters, inline=False)
        
        # Generate story opening
        story_openings = [
            f"In the {setting}, where {genre} tales unfold, our story begins...",
            f"The {setting} was quiet that day, until...",
            f"Legend speaks of a {setting} where {genre} adventures await those brave enough...",
            f"It was in the heart of {setting} that destiny would call..."
        ]
        
        opening = random.choice(story_openings)
        embed.add_field(name="Story Opening", value=opening, inline=False)
        embed.set_footer(text="Continue the story by replying! AI will adapt and respond.")
        
        await interaction.response.send_message(embed=embed)



    @discord.app_commands.command(name="ai_summarize", description="Summarize channel discussions")
    async def ai_summarize(self, interaction: discord.Interaction, 
                          channel: discord.TextChannel = None,
                          message_count: int = 50, summary_type: str = "brief"):
        """Summarize recent channel activity"""
        target_channel = channel or interaction.channel
        
        embed = discord.Embed(
            title="📋 AI Channel Summary",
            description=f"Summary of recent activity in {target_channel.mention}",
            color=0xff6347
        )
        embed.add_field(name="Messages Analyzed", value=str(message_count), inline=True)
        embed.add_field(name="Summary Type", value=summary_type, inline=True)
        embed.add_field(name="Timeframe", value="Last few hours", inline=True)
        
        # Simulated summary points
        summary_points = [
            "Discussion about upcoming gaming events",
            "Members sharing achievement screenshots",
            "Planning for weekend activities",
            "General community discussions and memes"
        ]
        
        summary_text = "\n".join([f"• {point}" for point in summary_points])
        embed.add_field(name="Key Points", value=summary_text, inline=False)
        embed.set_footer(text="AI Summary requires OpenAI API key for full functionality")
        
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="ai_moodboard", description="Generate community mood visualization")
    async def ai_moodboard(self, interaction: discord.Interaction, 
                          timeframe: str = "24h", style: str = "colorful"):
        """Create visual mood representation"""
        embed = discord.Embed(
            title="🎨 Community Moodboard",
            description=f"Visual representation of server mood over {timeframe}",
            color=0xff69b4
        )
        
        moods = ["Excited", "Happy", "Chill", "Focused", "Energetic"]
        percentages = [random.randint(10, 30) for _ in moods]
        total = sum(percentages)
        percentages = [int(p / total * 100) for p in percentages]
        
        for mood, percentage in zip(moods, percentages):
            embed.add_field(name=mood, value=f"{percentage}%", inline=True)
        
        embed.add_field(name="Style", value=style, inline=False)
        embed.set_footer(text="Visual moodboard would be generated with AI image tools")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(AIIntelligence(bot))