import discord
from discord.ext import commands
import asyncio
from datetime import datetime
from utils.embeds import create_embed

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.group(name='ticket', invoke_without_command=True)
    async def ticket(self, ctx):
        """Ticket system commands"""
        await ctx.send_help('ticket')

    @ticket.command(name='setup')
    @commands.has_permissions(administrator=True)
    async def setup_tickets(self, ctx, category: discord.CategoryChannel = None):
        """Setup the ticket system"""
        if not category:
            # Create tickets category
            category = await ctx.guild.create_category("🎫 Support Tickets")
        
        # Create ticket creation channel
        ticket_channel = discord.utils.get(ctx.guild.text_channels, name="create-ticket")
        if not ticket_channel:
            ticket_channel = await ctx.guild.create_text_channel(
                "create-ticket", 
                category=category,
                topic="React with 🎫 to create a support ticket"
            )
        
        # Create the ticket creation message
        embed = create_embed(
            title="🎫 Create Support Ticket",
            description="Need help? Create a support ticket by reacting with 🎫 below!",
            color=0x00FF00
        )
        embed.add_field(
            name="What happens when you create a ticket?",
            value="• A private channel will be created just for you\n• Only you and staff can see the channel\n• Staff will help you with your issue\n• The ticket will be closed when resolved",
            inline=False
        )
        embed.add_field(
            name="When should you create a ticket?",
            value="• Report rule violations\n• Get help with bot commands\n• Appeal punishments\n• Suggest server improvements\n• Any other support needs",
            inline=False
        )
        
        message = await ticket_channel.send(embed=embed)
        await message.add_reaction("🎫")
        
        # Store ticket message info in database
        await self.bot.db.set_ticket_message(ctx.guild.id, message.id, category.id)
        
        setup_embed = create_embed(
            title="✅ Ticket System Setup Complete",
            description=f"Ticket system has been set up in {ticket_channel.mention}",
            color=0x00FF00
        )
        setup_embed.add_field(name="Category", value=category.name, inline=True)
        setup_embed.add_field(name="Channel", value=ticket_channel.mention, inline=True)
        
        await ctx.send(embed=setup_embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handle ticket creation reactions"""
        if payload.user_id == self.bot.user.id:
            return
        
        # Check if this is a ticket creation reaction
        ticket_data = await self.bot.db.get_ticket_message(payload.guild_id, payload.message_id)
        if not ticket_data or str(payload.emoji) != "🎫":
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)
        category = guild.get_channel(ticket_data['category_id'])
        
        if not guild or not user or not category:
            return
        
        # Check if user already has a ticket
        existing_ticket = await self.bot.db.get_user_ticket(guild.id, user.id)
        if existing_ticket:
            try:
                channel = guild.get_channel(existing_ticket['channel_id'])
                if channel:
                    await user.send(f"❌ You already have an open ticket: {channel.mention}")
                    return
            except discord.Forbidden:
                pass
        
        # Create ticket channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        
        # Add staff roles to overwrites
        for role in guild.roles:
            if any(perm_name in role.name.lower() for perm_name in ['admin', 'mod', 'staff', 'helper']):
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        ticket_channel = await guild.create_text_channel(
            f"ticket-{user.name.lower()}",
            category=category,
            overwrites=overwrites,
            topic=f"Support ticket for {user} - Created {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
        )
        
        # Store ticket in database
        await self.bot.db.create_ticket(guild.id, user.id, ticket_channel.id)
        
        # Send welcome message
        embed = create_embed(
            title="🎫 Support Ticket Created",
            description=f"Hello {user.mention}! Thank you for creating a support ticket.",
            color=0x00FF00
        )
        embed.add_field(
            name="📝 Please describe your issue",
            value="Staff will be with you shortly. In the meantime, please provide as much detail as possible about your issue or question.",
            inline=False
        )
        embed.add_field(
            name="🔒 Close Ticket", 
            value="When your issue is resolved, you can close this ticket by reacting with 🔒 or using `!ticket close`",
            inline=False
        )
        embed.set_footer(text=f"Ticket ID: {ticket_channel.id}")
        
        welcome_msg = await ticket_channel.send(f"{user.mention}", embed=embed)
        await welcome_msg.add_reaction("🔒")
        
        # Notify staff
        staff_embed = create_embed(
            title="🆕 New Ticket Created",
            description=f"New ticket created by {user.mention}",
            color=0xFFD700
        )
        staff_embed.add_field(name="Channel", value=ticket_channel.mention, inline=True)
        staff_embed.add_field(name="User", value=f"{user} ({user.id})", inline=True)
        
        # Send to staff logs if available
        log_channel = discord.utils.get(guild.text_channels, name="ticket-logs")
        if log_channel:
            await log_channel.send(embed=staff_embed)
        
        # Remove user's reaction
        try:
            message = await guild.get_channel(payload.channel_id).fetch_message(payload.message_id)
            await message.remove_reaction("🎫", user)
        except:
            pass

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handle ticket closing reactions"""
        if payload.user_id == self.bot.user.id:
            return
        
        if str(payload.emoji) != "🔒":
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        user = guild.get_member(payload.user_id)
        
        # Check if this is a ticket channel
        ticket = await self.bot.db.get_ticket_by_channel(guild.id, channel.id)
        if not ticket:
            return
        
        # Check if user can close the ticket
        ticket_owner = guild.get_member(ticket['user_id'])
        can_close = (user == ticket_owner or 
                    user.guild_permissions.manage_channels or
                    any(role.name.lower() in ['admin', 'mod', 'staff', 'helper'] for role in user.roles))
        
        if not can_close:
            return
        
        await self.close_ticket(channel, user, ticket)

    @ticket.command(name='close')
    async def close_ticket_command(self, ctx, *, reason="No reason provided"):
        """Close the current ticket"""
        ticket = await self.bot.db.get_ticket_by_channel(ctx.guild.id, ctx.channel.id)
        if not ticket:
            return await ctx.send("❌ This is not a ticket channel!")
        
        # Check permissions
        ticket_owner = ctx.guild.get_member(ticket['user_id'])
        can_close = (ctx.author == ticket_owner or 
                    ctx.author.guild_permissions.manage_channels or
                    any(role.name.lower() in ['admin', 'mod', 'staff', 'helper'] for role in ctx.author.roles))
        
        if not can_close:
            return await ctx.send("❌ You don't have permission to close this ticket!")
        
        await self.close_ticket(ctx.channel, ctx.author, ticket, reason)

    async def close_ticket(self, channel, closer, ticket, reason="No reason provided"):
        """Close a ticket channel"""
        guild = channel.guild
        ticket_owner = guild.get_member(ticket['user_id'])
        
        # Create transcript
        transcript = await self.create_transcript(channel)
        
        # Send closing message
        embed = create_embed(
            title="🔒 Ticket Closing",
            description="This ticket will be closed in 10 seconds...",
            color=0xFF0000
        )
        embed.add_field(name="Closed by", value=closer.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=True)
        embed.add_field(name="Transcript", value="A transcript will be sent to the ticket owner", inline=False)
        
        await channel.send(embed=embed)
        
        # Log ticket closure
        log_channel = discord.utils.get(guild.text_channels, name="ticket-logs")
        if log_channel:
            log_embed = create_embed(
                title="🔒 Ticket Closed",
                description=f"Ticket closed by {closer.mention}",
                color=0xFF0000
            )
            log_embed.add_field(name="Ticket Owner", value=ticket_owner.mention if ticket_owner else "Unknown", inline=True)
            log_embed.add_field(name="Channel", value=channel.name, inline=True)
            log_embed.add_field(name="Reason", value=reason, inline=False)
            log_embed.set_footer(text=f"Ticket ID: {channel.id}")
            
            await log_channel.send(embed=log_embed)
        
        # Send transcript to ticket owner
        if ticket_owner:
            try:
                transcript_embed = create_embed(
                    title="📋 Ticket Transcript",
                    description=f"Your ticket from **{guild.name}** has been closed.",
                    color=0x7289DA
                )
                transcript_embed.add_field(name="Closed by", value=str(closer), inline=True)
                transcript_embed.add_field(name="Reason", value=reason, inline=True)
                transcript_embed.add_field(name="Closed at", value=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), inline=True)
                
                if len(transcript) < 1900:
                    transcript_embed.add_field(name="Messages", value=f"```{transcript}```", inline=False)
                else:
                    # Send as file if too long
                    import io
                    transcript_file = io.BytesIO(transcript.encode('utf-8'))
                    transcript_file.seek(0)
                    
                    file = discord.File(transcript_file, filename=f"ticket-{channel.name}-transcript.txt")
                    await ticket_owner.send(embed=transcript_embed, file=file)
                    
                if len(transcript) <= 1900:
                    await ticket_owner.send(embed=transcript_embed)
                    
            except discord.Forbidden:
                pass
        
        # Close ticket in database
        await self.bot.db.close_ticket(guild.id, channel.id)
        
        # Wait and delete channel
        await asyncio.sleep(10)
        try:
            await channel.delete(reason=f"Ticket closed by {closer}")
        except discord.NotFound:
            pass

    async def create_transcript(self, channel):
        """Create a transcript of the ticket"""
        messages = []
        async for message in channel.history(limit=500, oldest_first=True):
            timestamp = message.created_at.strftime("%Y-%m-%d %H:%M")
            content = message.content or "[No text content]"
            
            # Handle embeds
            if message.embeds:
                content += f" [Embed: {message.embeds[0].title or 'No title'}]"
            
            # Handle attachments
            if message.attachments:
                content += f" [Attachments: {', '.join(att.filename for att in message.attachments)}]"
            
            messages.append(f"[{timestamp}] {message.author}: {content}")
        
        return "\n".join(messages)

    @ticket.command(name='add')
    @commands.has_permissions(manage_channels=True)
    async def add_user(self, ctx, member: discord.Member):
        """Add a user to the current ticket"""
        ticket = await self.bot.db.get_ticket_by_channel(ctx.guild.id, ctx.channel.id)
        if not ticket:
            return await ctx.send("❌ This is not a ticket channel!")
        
        overwrites = ctx.channel.overwrites_for(member)
        overwrites.read_messages = True
        overwrites.send_messages = True
        
        await ctx.channel.set_permissions(member, overwrite=overwrites)
        
        embed = create_embed(
            title="✅ User Added",
            description=f"{member.mention} has been added to this ticket",
            color=0x00FF00
        )
        await ctx.send(embed=embed)

    @ticket.command(name='remove')
    @commands.has_permissions(manage_channels=True)
    async def remove_user(self, ctx, member: discord.Member):
        """Remove a user from the current ticket"""
        ticket = await self.bot.db.get_ticket_by_channel(ctx.guild.id, ctx.channel.id)
        if not ticket:
            return await ctx.send("❌ This is not a ticket channel!")
        
        # Don't remove ticket owner
        if member.id == ticket['user_id']:
            return await ctx.send("❌ You cannot remove the ticket owner!")
        
        await ctx.channel.set_permissions(member, overwrite=None)
        
        embed = create_embed(
            title="✅ User Removed",
            description=f"{member.mention} has been removed from this ticket",
            color=0xFF4500
        )
        await ctx.send(embed=embed)

    @ticket.command(name='rename')
    @commands.has_permissions(manage_channels=True)
    async def rename_ticket(self, ctx, *, new_name):
        """Rename the current ticket"""
        ticket = await self.bot.db.get_ticket_by_channel(ctx.guild.id, ctx.channel.id)
        if not ticket:
            return await ctx.send("❌ This is not a ticket channel!")
        
        old_name = ctx.channel.name
        await ctx.channel.edit(name=new_name)
        
        embed = create_embed(
            title="✅ Ticket Renamed",
            description=f"Ticket renamed from `{old_name}` to `{new_name}`",
            color=0x00FF00
        )
        await ctx.send(embed=embed)

    @ticket.command(name='list')
    @commands.has_permissions(manage_channels=True)
    async def list_tickets(self, ctx):
        """List all open tickets"""
        tickets = await self.bot.db.get_all_tickets(ctx.guild.id)
        
        if not tickets:
            return await ctx.send("✅ No open tickets!")
        
        embed = create_embed(
            title="🎫 Open Tickets",
            description=f"There are {len(tickets)} open tickets",
            color=0x7289DA
        )
        
        for ticket in tickets[:10]:  # Show first 10
            channel = ctx.guild.get_channel(ticket['channel_id'])
            user = ctx.guild.get_member(ticket['user_id'])
            
            if channel and user:
                created_time = datetime.fromisoformat(ticket['created_at']).strftime("%Y-%m-%d %H:%M")
                embed.add_field(
                    name=f"#{channel.name}",
                    value=f"**Owner:** {user.mention}\n**Created:** {created_time}",
                    inline=True
                )
        
        if len(tickets) > 10:
            embed.add_field(name="And more...", value=f"+{len(tickets) - 10} more tickets", inline=False)
        
        await ctx.send(embed=embed)

    @ticket.command(name='stats')
    @commands.has_permissions(manage_channels=True)
    async def ticket_stats(self, ctx):
        """Show ticket statistics"""
        stats = await self.bot.db.get_ticket_stats(ctx.guild.id)
        
        embed = create_embed(
            title="📊 Ticket Statistics",
            color=0x7289DA
        )
        embed.add_field(name="Open Tickets", value=str(stats.get('open', 0)), inline=True)
        embed.add_field(name="Total Tickets", value=str(stats.get('total', 0)), inline=True)
        embed.add_field(name="Closed Today", value=str(stats.get('closed_today', 0)), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Tickets(bot))
