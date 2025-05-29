import discord
from discord.ext import commands
import aiosqlite
import asyncio
import random
from datetime import datetime, timezone, timedelta

class EsportsManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="tournament_create", description="Create and manage esports tournaments")
    async def tournament_create(self, interaction: discord.Interaction, 
                              tournament_name: str, game: str, max_teams: int,
                              entry_fee: str = "Free", prize_pool: str = "",
                              start_date: str = "TBD"):
        """Create esports tournaments"""
        embed = discord.Embed(
            title="🏆 Tournament Created",
            description=f"**{tournament_name}** is now open for registration!",
            color=0xffd700
        )
        embed.add_field(name="Game", value=game, inline=True)
        embed.add_field(name="Max Teams", value=str(max_teams), inline=True)
        embed.add_field(name="Entry Fee", value=entry_fee, inline=True)
        embed.add_field(name="Start Date", value=start_date, inline=True)
        embed.add_field(name="Organizer", value=interaction.user.mention, inline=True)
        
        if prize_pool:
            embed.add_field(name="Prize Pool", value=prize_pool, inline=True)
        
        embed.set_footer(text="React with 🏆 to register your team!")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction("🏆")

    @discord.app_commands.command(name="team_registration", description="Register teams for tournaments")
    async def team_registration(self, interaction: discord.Interaction, 
                               team_name: str, captain: discord.Member,
                               members: str, tournament: str = "Latest"):
        """Register teams for competitions"""
        embed = discord.Embed(
            title="⚔️ Team Registration",
            description=f"**{team_name}** has registered for competition!",
            color=0x00ff00
        )
        embed.add_field(name="Team Name", value=team_name, inline=True)
        embed.add_field(name="Captain", value=captain.mention, inline=True)
        embed.add_field(name="Tournament", value=tournament, inline=True)
        embed.add_field(name="Members", value=members, inline=False)
        embed.add_field(name="Registered by", value=interaction.user.mention, inline=True)
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="match_schedule", description="Schedule tournament matches")
    async def match_schedule(self, interaction: discord.Interaction, 
                           team1: str, team2: str, match_time: str,
                           tournament_round: str, stream_link: str = ""):
        """Schedule competitive matches"""
        embed = discord.Embed(
            title="📅 Match Scheduled",
            description=f"**{team1}** vs **{team2}**",
            color=0xff4500
        )
        embed.add_field(name="Round", value=tournament_round, inline=True)
        embed.add_field(name="Time", value=match_time, inline=True)
        embed.add_field(name="Scheduled by", value=interaction.user.mention, inline=True)
        
        if stream_link:
            embed.add_field(name="Stream", value=f"[Watch Live]({stream_link})", inline=False)
        
        embed.set_footer(text="Good luck to both teams!")
        
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="match_result", description="Report tournament match results")
    async def match_result(self, interaction: discord.Interaction, 
                          winner: str, loser: str, score: str,
                          tournament_round: str, notes: str = ""):
        """Report match outcomes"""
        embed = discord.Embed(
            title="🎯 Match Result",
            description=f"**{winner}** defeats **{loser}**",
            color=0x32cd32
        )
        embed.add_field(name="Score", value=score, inline=True)
        embed.add_field(name="Round", value=tournament_round, inline=True)
        embed.add_field(name="Reported by", value=interaction.user.mention, inline=True)
        
        if notes:
            embed.add_field(name="Notes", value=notes, inline=False)
        
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scrim_request", description="Request practice scrimmages")
    async def scrim_request(self, interaction: discord.Interaction, 
                           team_name: str, game: str, skill_level: str,
                           preferred_time: str, contact: str = ""):
        """Request practice matches"""
        embed = discord.Embed(
            title="⚔️ Scrim Request",
            description=f"**{team_name}** is looking for practice opponents!",
            color=0x9370db
        )
        embed.add_field(name="Game", value=game, inline=True)
        embed.add_field(name="Skill Level", value=skill_level, inline=True)
        embed.add_field(name="Preferred Time", value=preferred_time, inline=True)
        embed.add_field(name="Requested by", value=interaction.user.mention, inline=True)
        
        if contact:
            embed.add_field(name="Contact", value=contact, inline=True)
        
        embed.set_footer(text="React with ⚔️ to accept the scrim!")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction("⚔️")

    @discord.app_commands.command(name="player_stats", description="Track competitive player statistics")
    async def player_stats(self, interaction: discord.Interaction, 
                          player: discord.Member, game: str,
                          wins: int, losses: int, kda: str = "",
                          rank: str = "", notes: str = ""):
        """Track player performance stats"""
        total_games = wins + losses
        win_rate = (wins / total_games * 100) if total_games > 0 else 0
        
        embed = discord.Embed(
            title="📊 Player Statistics",
            description=f"Competitive stats for **{player.display_name}**",
            color=0x4169e1
        )
        embed.add_field(name="Game", value=game, inline=True)
        embed.add_field(name="Wins", value=str(wins), inline=True)
        embed.add_field(name="Losses", value=str(losses), inline=True)
        embed.add_field(name="Win Rate", value=f"{win_rate:.1f}%", inline=True)
        
        if kda:
            embed.add_field(name="KDA", value=kda, inline=True)
        if rank:
            embed.add_field(name="Rank", value=rank, inline=True)
        if notes:
            embed.add_field(name="Notes", value=notes, inline=False)
        
        embed.set_thumbnail(url=player.avatar.url if player.avatar else None)
        
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="coach_application", description="Apply to coach teams or offer coaching")
    async def coach_application(self, interaction: discord.Interaction, 
                               action: str, games: str, experience: str,
                               availability: str, rate: str = "Negotiable"):
        """Manage coaching applications"""
        if action.lower() == "offer":
            title = "🎓 Coaching Services Available"
            desc = f"{interaction.user.display_name} is offering coaching services!"
            color = 0x20b2aa
        else:
            title = "📚 Coach Wanted"
            desc = f"{interaction.user.display_name} is looking for a coach!"
            color = 0xdda0dd
        
        embed = discord.Embed(title=title, description=desc, color=color)
        embed.add_field(name="Games", value=games, inline=True)
        embed.add_field(name="Experience", value=experience, inline=True)
        embed.add_field(name="Availability", value=availability, inline=True)
        embed.add_field(name="Rate", value=rate, inline=True)
        
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="sponsor_team", description="Connect teams with potential sponsors")
    async def sponsor_team(self, interaction: discord.Interaction, 
                          team_name: str, achievements: str, 
                          looking_for: str, contact: str):
        """Help teams find sponsorship"""
        embed = discord.Embed(
            title="💼 Sponsorship Opportunity",
            description=f"**{team_name}** is seeking sponsorship!",
            color=0x4682b4
        )
        embed.add_field(name="Achievements", value=achievements, inline=False)
        embed.add_field(name="Looking For", value=looking_for, inline=True)
        embed.add_field(name="Contact", value=contact, inline=True)
        embed.add_field(name="Posted by", value=interaction.user.mention, inline=True)
        embed.set_footer(text="Serious inquiries only!")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(EsportsManagement(bot))