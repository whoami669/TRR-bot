import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
import logging

class ServerEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.welcome_channel = None
        
    async def setup_channel(self, guild):
        """Setup server info category and welcome channel"""
        try:
            # Look for existing category
            category = discord.utils.get(guild.categories, name="server info")
            
            if not category:
                # Create category
                category = await guild.create_category("server info")
                print(f"Created 'server info' category in {guild.name}")
            
            # Look for existing channel
            channel = discord.utils.get(category.channels, name="welcome-leave-boost")
            
            if not channel:
                # Create channel in the category
                channel = await guild.create_text_channel(
                    "welcome-leave-boost", 
                    category=category
                )
                print(f"Created 'welcome-leave-boost' channel in {guild.name}")
            
            return channel
            
        except discord.Forbidden:
            logging.warning(f"Missing permissions to create channels in {guild.name}")
            return None
        except Exception as e:
            logging.error(f"Error setting up channel in {guild.name}: {e}")
            return None

    @commands.Cog.listener()
    async def on_ready(self):
        """Setup channels when bot is ready"""
        for guild in self.bot.guilds:
            await self.setup_channel(guild)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Setup channels when joining new guild"""
        await self.setup_channel(guild)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Send welcome message when member joins"""
        try:
            channel = await self.setup_channel(member.guild)
            if not channel:
                return
                
            # Get user avatar with fallback
            avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
            
            embed = discord.Embed(
                title="New Arrival 🚀",
                description=f"Yoooo welcome in **{member.mention}**",
                color=0x57F287,  # Discord green
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_thumbnail(url=avatar_url)
            embed.set_footer(text=f"Joined on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
            
            await channel.send(embed=embed)
            print(f"User joined: {member.name} in {member.guild.name}")
            
        except Exception as e:
            logging.error(f"Error sending welcome message: {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Send leave message when member leaves"""
        try:
            channel = await self.setup_channel(member.guild)
            if not channel:
                return
                
            # Get user avatar with fallback
            avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
            
            embed = discord.Embed(
                title="Departure 🌿",
                description=f"**{member.name}** went to go touch some grass",
                color=0xED4245,  # Discord red
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_thumbnail(url=avatar_url)
            embed.set_footer(text=f"Left on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
            
            await channel.send(embed=embed)
            print(f"User left: {member.name} from {member.guild.name}")
            
        except Exception as e:
            logging.error(f"Error sending leave message: {e}")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Detect server boosts"""
        try:
            # Check if user started boosting
            if before.premium_since is None and after.premium_since is not None:
                channel = await self.setup_channel(after.guild)
                if not channel:
                    return
                    
                # Get user avatar with fallback
                avatar_url = after.avatar.url if after.avatar else after.default_avatar.url
                
                embed = discord.Embed(
                    title="Server Boosted 💎",
                    description=f"Bro a legend called **{after.mention}** has boosted the server!",
                    color=0x9B59B6,  # Purple
                    timestamp=datetime.now(timezone.utc)
                )
                embed.set_thumbnail(url=avatar_url)
                embed.set_footer(text=f"Total Boosts: {after.guild.premium_subscription_count}")
                
                await channel.send(embed=embed)
                print(f"User boosted: {after.name} in {after.guild.name}")
                
        except Exception as e:
            logging.error(f"Error sending boost message: {e}")

    @app_commands.command(name="boosts", description="Check total server boosts")
    async def boosts(self, interaction: discord.Interaction):
        """Show current server boost count"""
        try:
            guild = interaction.guild
            boost_count = guild.premium_subscription_count
            boost_tier = guild.premium_tier
            
            embed = discord.Embed(
                title="💎 Server Boost Status",
                color=0x9B59B6
            )
            embed.add_field(name="Current Boosts", value=f"{boost_count}", inline=True)
            embed.add_field(name="Boost Tier", value=f"Level {boost_tier}", inline=True)
            embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                "Error getting boost information.", 
                ephemeral=True
            )
            logging.error(f"Error in boosts command: {e}")

async def setup(bot):
    await bot.add_cog(ServerEvents(bot))