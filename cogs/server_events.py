import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
import logging

class ServerEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.welcome_channel = None
        
    async def setup_channels(self, guild):
        """Setup welcome, leave, and boost channels in existing server info category"""
        try:
            # Look for existing category
            category = discord.utils.get(guild.categories, name="server info")
            
            if not category:
                logging.warning(f"'server info' category not found in {guild.name}")
                return None, None, None
            
            # Create/find welcome channel
            welcome_channel = discord.utils.get(category.channels, name="welcome")
            if not welcome_channel:
                welcome_channel = await guild.create_text_channel("welcome", category=category)
                print(f"Created 'welcome' channel in {guild.name}")
            
            # Create/find leave channel  
            leave_channel = discord.utils.get(category.channels, name="leave")
            if not leave_channel:
                leave_channel = await guild.create_text_channel("leave", category=category)
                print(f"Created 'leave' channel in {guild.name}")
                
            # Create/find boost channel
            boost_channel = discord.utils.get(category.channels, name="boost")
            if not boost_channel:
                boost_channel = await guild.create_text_channel("boost", category=category)
                print(f"Created 'boost' channel in {guild.name}")
            
            return welcome_channel, leave_channel, boost_channel
            
        except discord.Forbidden:
            logging.warning(f"Missing permissions to create channels in {guild.name}")
            return None, None, None
        except Exception as e:
            logging.error(f"Error setting up channels in {guild.name}: {e}")
            return None, None, None

    @commands.Cog.listener()
    async def on_ready(self):
        """Setup channels when bot is ready"""
        for guild in self.bot.guilds:
            await self.setup_channels(guild)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Setup channels when joining new guild"""
        await self.setup_channels(guild)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Send welcome message when member joins"""
        try:
            welcome_channel, _, _ = await self.setup_channels(member.guild)
            if not welcome_channel:
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
            
            await welcome_channel.send(embed=embed)
            print(f"User joined: {member.name} in {member.guild.name}")
            
        except Exception as e:
            logging.error(f"Error sending welcome message: {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Send leave message when member leaves"""
        try:
            _, leave_channel, _ = await self.setup_channels(member.guild)
            if not leave_channel:
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
            
            await leave_channel.send(embed=embed)
            print(f"User left: {member.name} from {member.guild.name}")
            
        except Exception as e:
            logging.error(f"Error sending leave message: {e}")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Detect server boosts"""
        try:
            # Check if user started boosting
            if before.premium_since is None and after.premium_since is not None:
                _, _, boost_channel = await self.setup_channels(after.guild)
                if not boost_channel:
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
                
                await boost_channel.send(embed=embed)
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

    @app_commands.command(name="setup-welcome", description="Setup welcome/leave/boost channels in server info category")
    @app_commands.default_permissions(administrator=True)
    async def setup_welcome(self, interaction: discord.Interaction):
        """Manually setup the welcome system"""
        await interaction.response.defer()
        
        try:
            welcome_channel, leave_channel, boost_channel = await self.setup_channels(interaction.guild)
            
            if welcome_channel and leave_channel and boost_channel:
                embed = discord.Embed(
                    title="✅ Welcome System Setup Complete",
                    description=f"Created/found in **server info** category:",
                    color=0x57F287
                )
                embed.add_field(
                    name="Channels Created", 
                    value=f"👋 {welcome_channel.mention}\n🚪 {leave_channel.mention}\n💎 {boost_channel.mention}", 
                    inline=False
                )
                embed.add_field(
                    name="Features Active", 
                    value="• Welcome messages → #welcome\n• Leave messages → #leave\n• Boost notifications → #boost", 
                    inline=False
                )
                await interaction.followup.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="❌ Setup Failed",
                    description="'server info' category not found or missing permissions.",
                    color=0xED4245
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            await interaction.followup.send(
                "Error setting up welcome system.", 
                ephemeral=True
            )
            logging.error(f"Error in setup-welcome command: {e}")

async def setup(bot):
    await bot.add_cog(ServerEvents(bot))