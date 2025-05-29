import discord
from discord.ext import commands
import random
from utils.embeds import create_embed
from PIL import Image, ImageDraw, ImageFont
import io
import aiohttp

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """Award XP for messages"""
        if message.author.bot or not message.guild:
            return
        
        # Don't give XP for commands
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return
        
        # Award XP
        xp_gained = random.randint(15, 25)
        old_level = await self.bot.db.get_level(message.guild.id, message.author.id)
        
        await self.bot.db.add_xp(message.guild.id, message.author.id, xp_gained)
        
        new_level = await self.bot.db.get_level(message.guild.id, message.author.id)
        
        # Check for level up
        if new_level > old_level:
            await self.handle_level_up(message, old_level, new_level)

    async def handle_level_up(self, message, old_level, new_level):
        """Handle level up rewards and announcements"""
        # Send level up message
        embed = create_embed(
            title="🎉 Level Up!",
            description=f"{message.author.mention} reached level **{new_level}**!",
            color=0x00FF00
        )
        embed.add_field(name="Previous Level", value=str(old_level), inline=True)
        embed.add_field(name="New Level", value=str(new_level), inline=True)
        
        # Calculate coins reward
        coins_reward = new_level * 100
        await self.bot.db.add_balance(message.guild.id, message.author.id, coins_reward)
        embed.add_field(name="Coins Earned", value=f"{coins_reward:,}", inline=True)
        
        await message.channel.send(embed=embed)
        
        # Check for role rewards
        await self.check_level_roles(message.guild, message.author, new_level)

    async def check_level_roles(self, guild, member, level):
        """Give roles based on level milestones"""
        level_roles = {
            5: "Level 5",
            10: "Level 10", 
            25: "Level 25",
            50: "Level 50",
            75: "Level 75",
            100: "Level 100"
        }
        
        for required_level, role_name in level_roles.items():
            if level >= required_level:
                role = discord.utils.get(guild.roles, name=role_name)
                if role and role not in member.roles:
                    try:
                        await member.add_roles(role)
                    except discord.Forbidden:
                        pass

    @commands.command(name='rank', aliases=['level'])
    async def show_rank(self, ctx, member: discord.Member = None):
        """Show rank information for a user"""
        target = member or ctx.author
        
        user_data = await self.bot.db.get_user_stats(ctx.guild.id, target.id)
        
        if not user_data:
            return await ctx.send("❌ No data found for this user!")
        
        level = user_data['level']
        xp = user_data['xp']
        xp_for_next = self.calculate_xp_for_level(level + 1)
        xp_for_current = self.calculate_xp_for_level(level)
        xp_progress = xp - xp_for_current
        xp_needed = xp_for_next - xp_for_current
        
        # Get user's rank
        rank = await self.bot.db.get_user_rank(ctx.guild.id, target.id)
        
        embed = create_embed(
            title=f"📊 {target.display_name}'s Rank",
            color=0x7289DA
        )
        embed.add_field(name="Level", value=str(level), inline=True)
        embed.add_field(name="XP", value=f"{xp:,}", inline=True)
        embed.add_field(name="Rank", value=f"#{rank}", inline=True)
        embed.add_field(
            name="Progress to Next Level",
            value=f"{xp_progress:,}/{xp_needed:,} XP",
            inline=False
        )
        
        # Progress bar
        progress_percentage = (xp_progress / xp_needed) * 100
        progress_bar = self.create_progress_bar(progress_percentage)
        embed.add_field(name="Progress", value=f"`{progress_bar}` {progress_percentage:.1f}%", inline=False)
        
        embed.set_thumbnail(url=target.avatar.url if target.avatar else target.default_avatar.url)
        
        await ctx.send(embed=embed)

    @commands.command(name='leaderboard', aliases=['lb'])
    async def show_leaderboard(self, ctx):
        """Show the server's top ranked members"""
        top_users = await self.bot.db.get_top_users(ctx.guild.id, 10)
        
        if not top_users:
            return await ctx.send("❌ No ranking data found!")
        
        embed = create_embed(
            title="🏆 Server Leaderboard",
            description="Top ranked members",
            color=0xFFD700
        )
        
        for i, user_data in enumerate(top_users, 1):
            member = ctx.guild.get_member(user_data['user_id'])
            name = member.display_name if member else "Unknown User"
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            
            embed.add_field(
                name=f"{medal} {name}",
                value=f"Level {user_data['level']} • {user_data['xp']:,} XP",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command(name='setlevel')
    @commands.has_permissions(administrator=True)
    async def set_level(self, ctx, member: discord.Member, level: int):
        """Set a user's level (Admin only)"""
        if level < 0:
            return await ctx.send("❌ Level cannot be negative!")
        
        required_xp = self.calculate_xp_for_level(level)
        await self.bot.db.set_user_xp(ctx.guild.id, member.id, required_xp)
        
        embed = create_embed(
            title="✅ Level Set",
            description=f"{member.mention}'s level has been set to {level}",
            color=0x00FF00
        )
        embed.add_field(name="Required XP", value=f"{required_xp:,}", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name='addxp')
    @commands.has_permissions(administrator=True) 
    async def add_xp(self, ctx, member: discord.Member, amount: int):
        """Add XP to a user (Admin only)"""
        if amount <= 0:
            return await ctx.send("❌ Amount must be positive!")
        
        old_level = await self.bot.db.get_level(ctx.guild.id, member.id)
        await self.bot.db.add_xp(ctx.guild.id, member.id, amount)
        new_level = await self.bot.db.get_level(ctx.guild.id, member.id)
        
        embed = create_embed(
            title="✅ XP Added",
            description=f"Added {amount:,} XP to {member.mention}",
            color=0x00FF00
        )
        embed.add_field(name="Old Level", value=str(old_level), inline=True)
        embed.add_field(name="New Level", value=str(new_level), inline=True)
        
        await ctx.send(embed=embed)
        
        # Check for level up
        if new_level > old_level:
            fake_message = type('obj', (object,), {
                'author': member,
                'guild': ctx.guild,
                'channel': ctx.channel
            })
            await self.handle_level_up(fake_message, old_level, new_level)

    @commands.command(name='removexp')
    @commands.has_permissions(administrator=True)
    async def remove_xp(self, ctx, member: discord.Member, amount: int):
        """Remove XP from a user (Admin only)"""
        if amount <= 0:
            return await ctx.send("❌ Amount must be positive!")
        
        old_level = await self.bot.db.get_level(ctx.guild.id, member.id)
        current_xp = await self.bot.db.get_user_xp(ctx.guild.id, member.id)
        
        new_xp = max(0, current_xp - amount)
        await self.bot.db.set_user_xp(ctx.guild.id, member.id, new_xp)
        
        new_level = await self.bot.db.get_level(ctx.guild.id, member.id)
        
        embed = create_embed(
            title="✅ XP Removed",
            description=f"Removed {amount:,} XP from {member.mention}",
            color=0xFF4500
        )
        embed.add_field(name="Old Level", value=str(old_level), inline=True)
        embed.add_field(name="New Level", value=str(new_level), inline=True)
        embed.add_field(name="Current XP", value=f"{new_xp:,}", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name='resetlevels')
    @commands.has_permissions(administrator=True)
    async def reset_levels(self, ctx):
        """Reset all levels in the server (Admin only)"""
        confirm_embed = create_embed(
            title="⚠️ Confirm Reset",
            description="Are you sure you want to reset ALL user levels and XP in this server? This action cannot be undone!",
            color=0xFF0000
        )
        confirm_embed.add_field(name="Confirmation", value="React with ✅ to confirm or ❌ to cancel", inline=False)
        
        message = await ctx.send(embed=confirm_embed)
        await message.add_reaction("✅")
        await message.add_reaction("❌")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == message.id
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == "✅":
                await self.bot.db.reset_all_levels(ctx.guild.id)
                
                embed = create_embed(
                    title="✅ Levels Reset",
                    description="All user levels and XP have been reset to 0",
                    color=0x00FF00
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Reset cancelled.")
                
        except asyncio.TimeoutError:
            await ctx.send("❌ Reset cancelled - no response received.")

    @staticmethod
    def calculate_xp_for_level(level):
        """Calculate total XP required for a given level"""
        if level <= 0:
            return 0
        return int(50 * (level ** 2) + 50 * level)

    @staticmethod
    def create_progress_bar(percentage, length=20):
        """Create a text-based progress bar"""
        filled = int(length * percentage / 100)
        empty = length - filled
        return "█" * filled + "░" * empty

    @commands.command(name='xpmultiplier')
    @commands.has_permissions(administrator=True)
    async def set_xp_multiplier(self, ctx, multiplier: float):
        """Set XP multiplier for the server (Admin only)"""
        if multiplier < 0.1 or multiplier > 10:
            return await ctx.send("❌ Multiplier must be between 0.1 and 10!")
        
        await self.bot.db.set_xp_multiplier(ctx.guild.id, multiplier)
        
        embed = create_embed(
            title="✅ XP Multiplier Set",
            description=f"XP multiplier set to {multiplier}x",
            color=0x00FF00
        )
        await ctx.send(embed=embed)

    @commands.command(name='xpblacklist')
    @commands.has_permissions(administrator=True)
    async def xp_blacklist_channel(self, ctx, channel: discord.TextChannel = None):
        """Blacklist a channel from gaining XP"""
        channel = channel or ctx.channel
        
        is_blacklisted = await self.bot.db.is_channel_blacklisted(ctx.guild.id, channel.id)
        
        if is_blacklisted:
            await self.bot.db.remove_channel_blacklist(ctx.guild.id, channel.id)
            embed = create_embed(
                title="✅ Channel Unblacklisted",
                description=f"{channel.mention} can now gain XP",
                color=0x00FF00
            )
        else:
            await self.bot.db.add_channel_blacklist(ctx.guild.id, channel.id)
            embed = create_embed(
                title="🚫 Channel Blacklisted",
                description=f"{channel.mention} will no longer gain XP",
                color=0xFF0000
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Leveling(bot))
