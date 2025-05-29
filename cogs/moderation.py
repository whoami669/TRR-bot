import discord
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio
from utils.embeds import create_embed
from utils.helpers import format_time

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.group(name='mod', invoke_without_command=True)
    @commands.has_permissions(manage_messages=True)
    async def moderation(self, ctx):
        """Moderation command group"""
        await ctx.send_help('mod')

    @commands.command(name='kick')
    @commands.has_permissions(kick_members=True)
    async def kick_member(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Kick a member from the server"""
        if member.top_role >= ctx.author.top_role:
            return await ctx.send("❌ You cannot kick someone with equal or higher role!")
        
        try:
            await member.kick(reason=f"{ctx.author}: {reason}")
            
            embed = create_embed(
                title="👢 Member Kicked",
                description=f"{member.mention} has been kicked from the server",
                color=0xFF4500
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=embed)
            
            # Log the action
            await self.log_moderation(ctx.guild, "Kick", member, ctx.author, reason)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to kick this member!")

    @commands.command(name='ban')
    @commands.has_permissions(ban_members=True)
    async def ban_member(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Ban a member from the server"""
        if member.top_role >= ctx.author.top_role:
            return await ctx.send("❌ You cannot ban someone with equal or higher role!")
        
        try:
            await member.ban(reason=f"{ctx.author}: {reason}")
            
            embed = create_embed(
                title="🔨 Member Banned",
                description=f"{member.mention} has been banned from the server",
                color=0xFF0000
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=embed)
            
            # Log the action
            await self.log_moderation(ctx.guild, "Ban", member, ctx.author, reason)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to ban this member!")

    @commands.command(name='unban')
    @commands.has_permissions(ban_members=True)
    async def unban_member(self, ctx, *, member):
        """Unban a member from the server"""
        banned_users = [entry async for entry in ctx.guild.bans(limit=2000)]
        
        member_name, member_discriminator = member.split('#')
        
        for ban_entry in banned_users:
            user = ban_entry.user
            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                
                embed = create_embed(
                    title="✅ Member Unbanned",
                    description=f"{user.mention} has been unbanned",
                    color=0x00FF00
                )
                embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
                
                await ctx.send(embed=embed)
                return
        
        await ctx.send("❌ Member not found in ban list!")

    @commands.command(name='mute')
    @commands.has_permissions(manage_roles=True)
    async def mute_member(self, ctx, member: discord.Member, duration: int = None, *, reason="No reason provided"):
        """Mute a member (duration in minutes)"""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        
        if not muted_role:
            return await ctx.send("❌ Muted role not found! Please create a 'Muted' role.")
        
        if muted_role in member.roles:
            return await ctx.send("❌ Member is already muted!")
        
        try:
            await member.add_roles(muted_role, reason=f"{ctx.author}: {reason}")
            
            embed = create_embed(
                title="🔇 Member Muted",
                description=f"{member.mention} has been muted",
                color=0xFFA500
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            
            if duration:
                embed.add_field(name="Duration", value=f"{duration} minutes", inline=True)
                # Schedule unmute
                await asyncio.sleep(duration * 60)
                if muted_role in member.roles:
                    await member.remove_roles(muted_role)
                    await ctx.send(f"🔊 {member.mention} has been automatically unmuted.")
            
            await ctx.send(embed=embed)
            
            # Log the action
            await self.log_moderation(ctx.guild, "Mute", member, ctx.author, reason, duration)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to mute this member!")

    @commands.command(name='unmute')
    @commands.has_permissions(manage_roles=True)
    async def unmute_member(self, ctx, member: discord.Member):
        """Unmute a member"""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        
        if not muted_role or muted_role not in member.roles:
            return await ctx.send("❌ Member is not muted!")
        
        try:
            await member.remove_roles(muted_role)
            
            embed = create_embed(
                title="🔊 Member Unmuted",
                description=f"{member.mention} has been unmuted",
                color=0x00FF00
            )
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to unmute this member!")

    @commands.command(name='warn')
    @commands.has_permissions(manage_messages=True)
    async def warn_member(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Warn a member"""
        # Store warning in database
        await self.bot.db.add_warning(ctx.guild.id, member.id, ctx.author.id, reason)
        warnings = await self.bot.db.get_warnings(ctx.guild.id, member.id)
        
        embed = create_embed(
            title="⚠️ Member Warned",
            description=f"{member.mention} has been warned",
            color=0xFFFF00
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        embed.add_field(name="Total Warnings", value=str(len(warnings)), inline=True)
        
        await ctx.send(embed=embed)
        
        # Log the action
        await self.log_moderation(ctx.guild, "Warning", member, ctx.author, reason)

    @commands.command(name='warnings')
    @commands.has_permissions(manage_messages=True)
    async def view_warnings(self, ctx, member: discord.Member):
        """View warnings for a member"""
        warnings = await self.bot.db.get_warnings(ctx.guild.id, member.id)
        
        if not warnings:
            return await ctx.send(f"✅ {member.mention} has no warnings!")
        
        embed = create_embed(
            title=f"⚠️ Warnings for {member.display_name}",
            description=f"Total warnings: {len(warnings)}",
            color=0xFFFF00
        )
        
        for i, warning in enumerate(warnings[:10], 1):  # Show last 10 warnings
            moderator = ctx.guild.get_member(warning['moderator_id'])
            mod_name = moderator.display_name if moderator else "Unknown"
            
            embed.add_field(
                name=f"Warning #{i}",
                value=f"**Reason:** {warning['reason']}\n**Moderator:** {mod_name}\n**Date:** {format_time(warning['timestamp'])}",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command(name='clear')
    @commands.has_permissions(manage_messages=True)
    async def clear_messages(self, ctx, amount: int, member: discord.Member = None):
        """Clear messages from a channel"""
        if amount > 100:
            return await ctx.send("❌ Cannot delete more than 100 messages at once!")
        
        def check(message):
            if member:
                return message.author == member
            return True
        
        try:
            deleted = await ctx.channel.purge(limit=amount + 1, check=check)
            
            embed = create_embed(
                title="🧹 Messages Cleared",
                description=f"Deleted {len(deleted) - 1} messages",
                color=0x00FF00
            )
            if member:
                embed.add_field(name="Target", value=member.mention, inline=True)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            
            msg = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await msg.delete()
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to delete messages!")

    @commands.command(name='slowmode')
    @commands.has_permissions(manage_channels=True)
    async def set_slowmode(self, ctx, seconds: int = 0):
        """Set slowmode for the current channel"""
        if seconds > 21600:  # Discord limit
            return await ctx.send("❌ Slowmode cannot exceed 6 hours!")
        
        try:
            await ctx.channel.edit(slowmode_delay=seconds)
            
            if seconds == 0:
                embed = create_embed(
                    title="🚀 Slowmode Disabled",
                    description="Slowmode has been disabled for this channel",
                    color=0x00FF00
                )
            else:
                embed = create_embed(
                    title="🐌 Slowmode Enabled",
                    description=f"Slowmode set to {seconds} seconds for this channel",
                    color=0xFFA500
                )
            
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to manage this channel!")

    async def log_moderation(self, guild, action, target, moderator, reason, duration=None):
        """Log moderation actions"""
        log_channel = discord.utils.get(guild.text_channels, name="mod-logs")
        if not log_channel:
            return
        
        embed = create_embed(
            title=f"📋 Moderation Log - {action}",
            color=0xFF4500
        )
        embed.add_field(name="Target", value=f"{target.mention} ({target})", inline=True)
        embed.add_field(name="Moderator", value=f"{moderator.mention} ({moderator})", inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        
        if duration:
            embed.add_field(name="Duration", value=f"{duration} minutes", inline=True)
        
        embed.set_footer(text=f"User ID: {target.id}")
        embed.timestamp = datetime.utcnow()
        
        await log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
