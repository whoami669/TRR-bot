import discord
from discord.ext import commands
import aiosqlite
import asyncio
import random
import json
from datetime import datetime, timezone, timedelta

class GamerSuite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="setup_gaming_session", description="Set up a gaming session with friends")
    async def setup_gaming_session(self, interaction: discord.Interaction, 
                                  game: str, max_players: int = 4, 
                                  start_time: str = "now", voice_channel: discord.VoiceChannel = None):
        """Create a gaming session"""
        embed = discord.Embed(
            title="🎮 Gaming Session Created",
            description=f"**Game:** {game}\n**Max Players:** {max_players}\n**Start Time:** {start_time}",
            color=0x00ff00
        )
        
        if voice_channel:
            embed.add_field(name="Voice Channel", value=voice_channel.mention, inline=False)
        
        embed.add_field(name="Host", value=interaction.user.mention, inline=True)
        embed.add_field(name="Players", value="1/{}".format(max_players), inline=True)
        embed.set_footer(text="React with 🎮 to join!")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction("🎮")

    @discord.app_commands.command(name="lfg", description="Looking for group - find players for your game")
    async def lfg(self, interaction: discord.Interaction, game: str, 
                 players_needed: int, skill_level: str = "any", region: str = "any"):
        """Looking for group system"""
        embed = discord.Embed(
            title="🔍 Looking for Group",
            description=f"**{interaction.user.display_name}** is looking for players!",
            color=0xff6600
        )
        embed.add_field(name="Game", value=game, inline=True)
        embed.add_field(name="Players Needed", value=str(players_needed), inline=True)
        embed.add_field(name="Skill Level", value=skill_level, inline=True)
        embed.add_field(name="Region", value=region, inline=True)
        embed.set_footer(text="React with ✋ to join!")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction("✋")

    @discord.app_commands.command(name="game_stats", description="Track and display your game statistics")
    async def game_stats(self, interaction: discord.Interaction, game: str, 
                        stat_type: str, value: str):
        """Track gaming statistics"""
        async with aiosqlite.connect('ultrabot.db') as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS game_stats (
                    user_id INTEGER, guild_id INTEGER, game TEXT, 
                    stat_type TEXT, value TEXT, updated_at TEXT
                )
            ''')
            
            # Update or insert stat
            await db.execute('''
                INSERT OR REPLACE INTO game_stats 
                (user_id, guild_id, game, stat_type, value, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (interaction.user.id, interaction.guild.id, game, stat_type, 
                  value, datetime.now(timezone.utc).isoformat()))
            await db.commit()
        
        embed = discord.Embed(
            title="📊 Game Stats Updated",
            description=f"**{game}** - {stat_type}: {value}",
            color=0x0099ff
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="achievement", description="Share a gaming achievement")
    async def achievement(self, interaction: discord.Interaction, game: str, 
                         achievement: str, description: str = ""):
        """Share gaming achievements"""
        embed = discord.Embed(
            title="🏆 Achievement Unlocked!",
            description=f"**{achievement}**",
            color=0xffd700
        )
        embed.add_field(name="Game", value=game, inline=True)
        embed.add_field(name="Player", value=interaction.user.mention, inline=True)
        
        if description:
            embed.add_field(name="Details", value=description, inline=False)
        
        embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction("🏆")
        await message.add_reaction("🎉")

    @discord.app_commands.command(name="game_tier_list", description="Create or vote on game tier lists")
    async def game_tier_list(self, interaction: discord.Interaction, category: str, 
                            s_tier: str = "", a_tier: str = "", b_tier: str = "", 
                            c_tier: str = "", d_tier: str = ""):
        """Create game tier lists"""
        embed = discord.Embed(
            title=f"🎮 {category} Tier List",
            description=f"Created by {interaction.user.display_name}",
            color=0xff0000
        )
        
        if s_tier:
            embed.add_field(name="🔥 S Tier", value=s_tier, inline=False)
        if a_tier:
            embed.add_field(name="⭐ A Tier", value=a_tier, inline=False)
        if b_tier:
            embed.add_field(name="👍 B Tier", value=b_tier, inline=False)
        if c_tier:
            embed.add_field(name="👌 C Tier", value=c_tier, inline=False)
        if d_tier:
            embed.add_field(name="👎 D Tier", value=d_tier, inline=False)
        
        embed.set_footer(text="React to show agreement!")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        reactions = ["🔥", "⭐", "👍", "👌", "👎"]
        for reaction in reactions:
            await message.add_reaction(reaction)

    @discord.app_commands.command(name="game_review", description="Write and share game reviews")
    async def game_review(self, interaction: discord.Interaction, game: str, 
                         rating: int, review: str, platform: str = "PC"):
        """Share detailed game reviews"""
        if rating < 1 or rating > 10:
            await interaction.response.send_message("Rating must be between 1 and 10!", ephemeral=True)
            return
        
        stars = "⭐" * rating + "☆" * (10 - rating)
        
        embed = discord.Embed(
            title=f"📝 Game Review: {game}",
            description=review,
            color=0x9932cc
        )
        embed.add_field(name="Rating", value=f"{rating}/10 {stars}", inline=True)
        embed.add_field(name="Platform", value=platform, inline=True)
        embed.add_field(name="Reviewer", value=interaction.user.mention, inline=True)
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="speedrun_pb", description="Track your speedrun personal bests")
    async def speedrun_pb(self, interaction: discord.Interaction, game: str, 
                         category: str, time: str, video_link: str = ""):
        """Track speedrun personal bests"""
        embed = discord.Embed(
            title="⚡ Speedrun Personal Best",
            description=f"**{game}** - {category}",
            color=0xff4500
        )
        embed.add_field(name="Time", value=time, inline=True)
        embed.add_field(name="Runner", value=interaction.user.mention, inline=True)
        
        if video_link:
            embed.add_field(name="Video", value=f"[Watch Run]({video_link})", inline=False)
        
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="gaming_schedule", description="Set your gaming schedule")
    async def gaming_schedule(self, interaction: discord.Interaction, 
                             day: str, start_time: str, end_time: str, 
                             game: str = "Various", status: str = "Available"):
        """Set gaming availability schedule"""
        embed = discord.Embed(
            title="📅 Gaming Schedule",
            description=f"{interaction.user.display_name}'s availability",
            color=0x00ffff
        )
        embed.add_field(name="Day", value=day, inline=True)
        embed.add_field(name="Time", value=f"{start_time} - {end_time}", inline=True)
        embed.add_field(name="Game", value=game, inline=True)
        embed.add_field(name="Status", value=status, inline=True)
        
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="game_recommendation", description="Get personalized game recommendations")
    async def game_recommendation(self, interaction: discord.Interaction, 
                                 genre: str, platform: str = "any", 
                                 playtime: str = "any", mood: str = "any"):
        """Get game recommendations based on preferences"""
        recommendations = {
            "action": ["Doom Eternal", "Hades", "Devil May Cry 5", "Sekiro"],
            "rpg": ["The Witcher 3", "Persona 5", "Divinity: Original Sin 2", "Elden Ring"],
            "strategy": ["Civilization VI", "Total War: Warhammer III", "Crusader Kings III", "Age of Empires IV"],
            "indie": ["Hollow Knight", "Celeste", "Stardew Valley", "Among Us"],
            "multiplayer": ["Valorant", "Rocket League", "Fall Guys", "Overwatch 2"]
        }
        
        genre_games = recommendations.get(genre.lower(), ["Check Steam recommendations!"])
        recommended_game = random.choice(genre_games)
        
        embed = discord.Embed(
            title="🎯 Game Recommendation",
            description=f"Based on your preferences, you might enjoy:",
            color=0x32cd32
        )
        embed.add_field(name="Recommended Game", value=recommended_game, inline=False)
        embed.add_field(name="Genre", value=genre, inline=True)
        embed.add_field(name="Platform", value=platform, inline=True)
        embed.add_field(name="Playtime", value=playtime, inline=True)
        embed.add_field(name="Mood", value=mood, inline=True)
        
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="gaming_clan", description="Manage gaming clan/team information")
    async def gaming_clan(self, interaction: discord.Interaction, 
                         action: str, clan_name: str = "", 
                         member: discord.Member = None, role: str = ""):
        """Manage gaming clans and teams"""
        if action.lower() == "create":
            embed = discord.Embed(
                title="🛡️ Gaming Clan Created",
                description=f"**{clan_name}** has been established!",
                color=0x8b0000
            )
            embed.add_field(name="Leader", value=interaction.user.mention, inline=True)
            embed.add_field(name="Founded", value=datetime.now(timezone.utc).strftime("%Y-%m-%d"), inline=True)
            
        elif action.lower() == "invite" and member:
            embed = discord.Embed(
                title="📨 Clan Invitation",
                description=f"{member.mention} has been invited to join **{clan_name}**!",
                color=0x4169e1
            )
            embed.add_field(name="Invited by", value=interaction.user.mention, inline=True)
            embed.add_field(name="Role", value=role if role else "Member", inline=True)
        
        else:
            embed = discord.Embed(
                title="❌ Invalid Action",
                description="Available actions: create, invite",
                color=0xff0000
            )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(GamerSuite(bot))