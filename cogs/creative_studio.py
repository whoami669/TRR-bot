import discord
from discord.ext import commands
import aiosqlite
import asyncio
import random
import json
from datetime import datetime, timezone, timedelta

class CreativeStudio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="art_commission", description="Commission custom artwork from community artists")
    async def art_commission(self, interaction: discord.Interaction, 
                            art_type: str, style: str, description: str,
                            budget: str = "negotiable", deadline: str = "flexible"):
        """Commission artwork from community members"""
        embed = discord.Embed(
            title="🎨 Art Commission Request",
            description=description,
            color=0xff69b4
        )
        embed.add_field(name="Art Type", value=art_type, inline=True)
        embed.add_field(name="Style", value=style, inline=True)
        embed.add_field(name="Budget", value=budget, inline=True)
        embed.add_field(name="Deadline", value=deadline, inline=True)
        embed.add_field(name="Commissioned by", value=interaction.user.mention, inline=True)
        embed.set_footer(text="React with 🎨 to express interest in this commission!")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction("🎨")

    @discord.app_commands.command(name="portfolio_showcase", description="Showcase your creative portfolio")
    async def portfolio_showcase(self, interaction: discord.Interaction, 
                                medium: str, title: str, description: str,
                                gallery_link: str = "", price: str = ""):
        """Display creative work portfolio"""
        embed = discord.Embed(
            title="🖼️ Portfolio Showcase",
            description=description,
            color=0x9932cc
        )
        embed.add_field(name="Title", value=title, inline=True)
        embed.add_field(name="Medium", value=medium, inline=True)
        embed.add_field(name="Artist", value=interaction.user.mention, inline=True)
        
        if price:
            embed.add_field(name="Price", value=price, inline=True)
        
        if gallery_link:
            embed.add_field(name="Full Gallery", value=f"[View Collection]({gallery_link})", inline=False)
        
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="creative_challenge", description="Start community creative challenges")
    async def creative_challenge(self, interaction: discord.Interaction, 
                               challenge_type: str, theme: str, duration: str,
                               prize: str = "Recognition", rules: str = ""):
        """Launch creative competitions"""
        embed = discord.Embed(
            title="🏆 Creative Challenge",
            description=f"**Theme:** {theme}",
            color=0xffd700
        )
        embed.add_field(name="Challenge Type", value=challenge_type, inline=True)
        embed.add_field(name="Duration", value=duration, inline=True)
        embed.add_field(name="Prize", value=prize, inline=True)
        embed.add_field(name="Host", value=interaction.user.mention, inline=True)
        
        if rules:
            embed.add_field(name="Rules", value=rules, inline=False)
        
        embed.set_footer(text="Submit your entries in this channel!")
        
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="inspiration_board", description="Create collaborative inspiration boards")
    async def inspiration_board(self, interaction: discord.Interaction, 
                              board_theme: str, description: str, 
                              collaborative: str = "yes"):
        """Create inspiration mood boards"""
        embed = discord.Embed(
            title="💡 Inspiration Board",
            description=description,
            color=0x20b2aa
        )
        embed.add_field(name="Theme", value=board_theme, inline=True)
        embed.add_field(name="Collaborative", value=collaborative, inline=True)
        embed.add_field(name="Created by", value=interaction.user.mention, inline=True)
        embed.add_field(name="How to Contribute", 
                       value="Share images, colors, quotes, or ideas that match the theme!", 
                       inline=False)
        embed.set_footer(text="Add your inspiration below!")
        
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="tutorial_share", description="Share creative tutorials and techniques")
    async def tutorial_share(self, interaction: discord.Interaction, 
                           skill: str, difficulty: str, tutorial_type: str,
                           content: str, resources: str = ""):
        """Share creative learning resources"""
        difficulty_colors = {
            "beginner": 0x00ff00,
            "intermediate": 0xffff00,
            "advanced": 0xff0000,
            "expert": 0x800080
        }
        
        embed = discord.Embed(
            title="📚 Creative Tutorial",
            description=content,
            color=difficulty_colors.get(difficulty.lower(), 0x00ff00)
        )
        embed.add_field(name="Skill", value=skill, inline=True)
        embed.add_field(name="Difficulty", value=difficulty, inline=True)
        embed.add_field(name="Type", value=tutorial_type, inline=True)
        embed.add_field(name="Shared by", value=interaction.user.mention, inline=True)
        
        if resources:
            embed.add_field(name="Resources", value=resources, inline=False)
        
        embed.set_footer(text="React with 📚 if this tutorial helped you!")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction("📚")

    @discord.app_commands.command(name="feedback_request", description="Request constructive feedback on creative work")
    async def feedback_request(self, interaction: discord.Interaction, 
                             work_type: str, stage: str, specific_areas: str,
                             work_link: str = ""):
        """Request creative feedback"""
        embed = discord.Embed(
            title="🔍 Feedback Request",
            description=f"{interaction.user.display_name} is seeking creative feedback!",
            color=0xff6347
        )
        embed.add_field(name="Work Type", value=work_type, inline=True)
        embed.add_field(name="Stage", value=stage, inline=True)
        embed.add_field(name="Focus Areas", value=specific_areas, inline=False)
        
        if work_link:
            embed.add_field(name="View Work", value=f"[Click here]({work_link})", inline=False)
        
        embed.set_footer(text="Provide constructive feedback below!")
        
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="collaboration_call", description="Find creative collaboration partners")
    async def collaboration_call(self, interaction: discord.Interaction, 
                                project_type: str, looking_for: str, 
                                project_description: str, timeline: str = "open"):
        """Find creative collaborators"""
        embed = discord.Embed(
            title="🤝 Collaboration Opportunity",
            description=project_description,
            color=0x32cd32
        )
        embed.add_field(name="Project Type", value=project_type, inline=True)
        embed.add_field(name="Looking For", value=looking_for, inline=True)
        embed.add_field(name="Timeline", value=timeline, inline=True)
        embed.add_field(name="Project Lead", value=interaction.user.mention, inline=True)
        embed.set_footer(text="React with 🤝 to join this collaboration!")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction("🤝")

    @discord.app_commands.command(name="creative_resources", description="Share tools and resources for creators")
    async def creative_resources(self, interaction: discord.Interaction, 
                               resource_type: str, name: str, description: str,
                               link: str = "", cost: str = "Free"):
        """Share creative tools and resources"""
        embed = discord.Embed(
            title="🛠️ Creative Resource",
            description=description,
            color=0x4169e1
        )
        embed.add_field(name="Resource", value=name, inline=True)
        embed.add_field(name="Type", value=resource_type, inline=True)
        embed.add_field(name="Cost", value=cost, inline=True)
        embed.add_field(name="Shared by", value=interaction.user.mention, inline=True)
        
        if link:
            embed.add_field(name="Access", value=f"[Get Resource]({link})", inline=False)
        
        embed.set_footer(text="React with 🛠️ if you found this useful!")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction("🛠️")

    @discord.app_commands.command(name="work_in_progress", description="Share and track creative work progress")
    async def work_in_progress(self, interaction: discord.Interaction, 
                             project_name: str, progress_percentage: int, 
                             update_description: str, next_steps: str = ""):
        """Track creative project progress"""
        if progress_percentage < 0:
            progress_percentage = 0
        elif progress_percentage > 100:
            progress_percentage = 100
        
        progress_bar = "█" * (progress_percentage // 10) + "░" * (10 - progress_percentage // 10)
        
        embed = discord.Embed(
            title="🚧 Work in Progress",
            description=update_description,
            color=0xffa500
        )
        embed.add_field(name="Project", value=project_name, inline=True)
        embed.add_field(name="Creator", value=interaction.user.mention, inline=True)
        embed.add_field(name="Progress", 
                       value=f"{progress_percentage}%\n{progress_bar}", 
                       inline=False)
        
        if next_steps:
            embed.add_field(name="Next Steps", value=next_steps, inline=False)
        
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="technique_exchange", description="Exchange creative techniques and tips")
    async def technique_exchange(self, interaction: discord.Interaction, 
                               technique_name: str, medium: str, 
                               description: str, difficulty: str = "medium"):
        """Share creative techniques"""
        embed = discord.Embed(
            title="⚡ Technique Exchange",
            description=description,
            color=0x8a2be2
        )
        embed.add_field(name="Technique", value=technique_name, inline=True)
        embed.add_field(name="Medium", value=medium, inline=True)
        embed.add_field(name="Difficulty", value=difficulty, inline=True)
        embed.add_field(name="Shared by", value=interaction.user.mention, inline=True)
        embed.set_footer(text="Try this technique and share your results!")
        
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="mood_palette", description="Create and share color mood palettes")
    async def mood_palette(self, interaction: discord.Interaction, 
                          palette_name: str, mood: str, colors: str,
                          inspiration: str = ""):
        """Share color palettes and moods"""
        embed = discord.Embed(
            title="🎨 Mood Palette",
            description=f"**{palette_name}** - Capturing the essence of {mood}",
            color=0xff1493
        )
        embed.add_field(name="Colors", value=colors, inline=False)
        embed.add_field(name="Mood", value=mood, inline=True)
        embed.add_field(name="Created by", value=interaction.user.mention, inline=True)
        
        if inspiration:
            embed.add_field(name="Inspiration", value=inspiration, inline=False)
        
        embed.set_footer(text="Use this palette in your next creative project!")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(CreativeStudio(bot))