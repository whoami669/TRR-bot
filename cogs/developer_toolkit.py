import discord
from discord.ext import commands
import aiosqlite
import asyncio
import random
import json
from datetime import datetime, timezone, timedelta

class DeveloperToolkit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="code_review", description="Request code reviews from the community")
    async def code_review(self, interaction: discord.Interaction, 
                         language: str, code_snippet: str, 
                         review_type: str = "general", github_link: str = ""):
        """Request code reviews"""
        embed = discord.Embed(
            title="🔍 Code Review Request",
            description=f"{interaction.user.display_name} is looking for feedback!",
            color=0x24292e
        )
        embed.add_field(name="Language", value=language, inline=True)
        embed.add_field(name="Review Type", value=review_type, inline=True)
        embed.add_field(name="Code", value=f"```{language}\n{code_snippet[:500]}{'...' if len(code_snippet) > 500 else ''}\n```", inline=False)
        
        if github_link:
            embed.add_field(name="Full Code", value=f"[View on GitHub]({github_link})", inline=False)
        
        embed.set_footer(text="React with 👀 to review!")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction("👀")

    @discord.app_commands.command(name="bug_report", description="Report and track software bugs")
    async def bug_report(self, interaction: discord.Interaction, 
                        project: str, severity: str, description: str,
                        steps_to_reproduce: str = "", expected_behavior: str = ""):
        """Track bug reports"""
        severity_colors = {
            "critical": 0xff0000,
            "high": 0xff6600,
            "medium": 0xffcc00,
            "low": 0x00ff00
        }
        
        embed = discord.Embed(
            title="🐛 Bug Report",
            description=description,
            color=severity_colors.get(severity.lower(), 0xffcc00)
        )
        embed.add_field(name="Project", value=project, inline=True)
        embed.add_field(name="Severity", value=severity, inline=True)
        embed.add_field(name="Reported by", value=interaction.user.mention, inline=True)
        
        if steps_to_reproduce:
            embed.add_field(name="Steps to Reproduce", value=steps_to_reproduce, inline=False)
        
        if expected_behavior:
            embed.add_field(name="Expected Behavior", value=expected_behavior, inline=False)
        
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="feature_request", description="Submit feature requests for projects")
    async def feature_request(self, interaction: discord.Interaction, 
                             project: str, feature_title: str, description: str,
                             priority: str = "medium", use_case: str = ""):
        """Submit feature requests"""
        embed = discord.Embed(
            title="💡 Feature Request",
            description=description,
            color=0x0066cc
        )
        embed.add_field(name="Project", value=project, inline=True)
        embed.add_field(name="Feature", value=feature_title, inline=True)
        embed.add_field(name="Priority", value=priority, inline=True)
        embed.add_field(name="Requested by", value=interaction.user.mention, inline=True)
        
        if use_case:
            embed.add_field(name="Use Case", value=use_case, inline=False)
        
        embed.set_footer(text="React with 💡 if you want this feature!")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction("💡")

    @discord.app_commands.command(name="project_showcase", description="Showcase your development projects")
    async def project_showcase(self, interaction: discord.Interaction, 
                              project_name: str, description: str, 
                              tech_stack: str, status: str = "in progress",
                              github_link: str = "", demo_link: str = ""):
        """Showcase development projects"""
        embed = discord.Embed(
            title="🚀 Project Showcase",
            description=description,
            color=0x6f42c1
        )
        embed.add_field(name="Project", value=project_name, inline=True)
        embed.add_field(name="Tech Stack", value=tech_stack, inline=True)
        embed.add_field(name="Status", value=status, inline=True)
        embed.add_field(name="Developer", value=interaction.user.mention, inline=True)
        
        if github_link:
            embed.add_field(name="Source Code", value=f"[GitHub]({github_link})", inline=True)
        
        if demo_link:
            embed.add_field(name="Live Demo", value=f"[Try it out]({demo_link})", inline=True)
        
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="learning_resource", description="Share programming learning resources")
    async def learning_resource(self, interaction: discord.Interaction, 
                               resource_type: str, title: str, 
                               topic: str, difficulty: str = "beginner",
                               link: str = "", description: str = ""):
        """Share learning materials"""
        embed = discord.Embed(
            title="📚 Learning Resource",
            description=description if description else f"Resource shared by {interaction.user.display_name}",
            color=0x28a745
        )
        embed.add_field(name="Resource", value=title, inline=True)
        embed.add_field(name="Type", value=resource_type, inline=True)
        embed.add_field(name="Topic", value=topic, inline=True)
        embed.add_field(name="Difficulty", value=difficulty, inline=True)
        
        if link:
            embed.add_field(name="Link", value=f"[Access Resource]({link})", inline=False)
        
        embed.set_footer(text="React with 📚 if this helped you!")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction("📚")

    @discord.app_commands.command(name="tech_discussion", description="Start technical discussions")
    async def tech_discussion(self, interaction: discord.Interaction, 
                             topic: str, question: str, 
                             context: str = "", tags: str = ""):
        """Start technical discussions"""
        embed = discord.Embed(
            title="💬 Tech Discussion",
            description=question,
            color=0xfd7e14
        )
        embed.add_field(name="Topic", value=topic, inline=True)
        embed.add_field(name="Started by", value=interaction.user.mention, inline=True)
        
        if context:
            embed.add_field(name="Context", value=context, inline=False)
        
        if tags:
            embed.add_field(name="Tags", value=tags, inline=False)
        
        embed.set_footer(text="Join the discussion below!")
        
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="algorithm_challenge", description="Create or solve algorithm challenges")
    async def algorithm_challenge(self, interaction: discord.Interaction, 
                                 challenge_type: str, title: str, 
                                 description: str, difficulty: str = "medium",
                                 time_limit: str = "1 hour"):
        """Create algorithm challenges"""
        difficulty_colors = {
            "easy": 0x28a745,
            "medium": 0xffc107,
            "hard": 0xdc3545,
            "expert": 0x6f42c1
        }
        
        embed = discord.Embed(
            title="🧠 Algorithm Challenge",
            description=description,
            color=difficulty_colors.get(difficulty.lower(), 0xffc107)
        )
        embed.add_field(name="Challenge", value=title, inline=True)
        embed.add_field(name="Type", value=challenge_type, inline=True)
        embed.add_field(name="Difficulty", value=difficulty, inline=True)
        embed.add_field(name="Time Limit", value=time_limit, inline=True)
        embed.add_field(name="Created by", value=interaction.user.mention, inline=True)
        
        embed.set_footer(text="React with 🧠 to participate!")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction("🧠")

    @discord.app_commands.command(name="career_advice", description="Share or request programming career advice")
    async def career_advice(self, interaction: discord.Interaction, 
                           advice_type: str, topic: str, 
                           content: str, experience_level: str = "any"):
        """Share career guidance"""
        embed = discord.Embed(
            title="💼 Career Advice",
            description=content,
            color=0x17a2b8
        )
        embed.add_field(name="Type", value=advice_type, inline=True)
        embed.add_field(name="Topic", value=topic, inline=True)
        embed.add_field(name="Experience Level", value=experience_level, inline=True)
        embed.add_field(name="Shared by", value=interaction.user.mention, inline=True)
        
        embed.set_footer(text="React with 💼 if this advice resonates!")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction("💼")

    @discord.app_commands.command(name="open_source", description="Promote open source contributions")
    async def open_source(self, interaction: discord.Interaction, 
                         action: str, project_name: str, 
                         description: str, skill_level: str = "any",
                         repository: str = ""):
        """Promote open source participation"""
        if action.lower() == "contribute":
            title = "🤝 Looking for Contributors"
            desc = f"**{project_name}** needs your help!"
            color = 0x28a745
        else:
            title = "🔍 Seeking Projects"
            desc = f"{interaction.user.display_name} wants to contribute to open source!"
            color = 0x0366d6
        
        embed = discord.Embed(title=title, description=desc, color=color)
        embed.add_field(name="Project", value=project_name, inline=True)
        embed.add_field(name="Skill Level", value=skill_level, inline=True)
        embed.add_field(name="Details", value=description, inline=False)
        
        if repository:
            embed.add_field(name="Repository", value=f"[View on GitHub]({repository})", inline=False)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(DeveloperToolkit(bot))