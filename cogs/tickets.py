import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import asyncio
from datetime import datetime, timezone
from typing import Optional

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.green, emoji="🎫")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        # Check if user already has a ticket
        existing_channel = discord.utils.get(interaction.guild.channels, name=f"ticket-{interaction.user.id}")
        if existing_channel:
            await interaction.followup.send("You already have an open ticket!", ephemeral=True)
            return
        
        # Create ticket channel
        category = discord.utils.get(interaction.guild.categories, name="Tickets")
        if not category:
            category = await interaction.guild.create_category("Tickets")
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        channel = await interaction.guild.create_text_channel(
            f"ticket-{interaction.user.id}",
            category=category,
            overwrites=overwrites
        )
        
        embed = discord.Embed(
            title="🎫 Support Ticket",
            description=f"Hello {interaction.user.mention}! Please describe your issue and a staff member will assist you.",
            color=0x3498db
        )
        
        close_view = TicketCloseView()
        await channel.send(embed=embed, view=close_view)
        
        await interaction.followup.send(f"Ticket created: {channel.mention}", ephemeral=True)

class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        if not interaction.user.guild_permissions.manage_channels:
            if not interaction.channel.name.endswith(str(interaction.user.id)):
                await interaction.followup.send("You can only close your own ticket!", ephemeral=True)
                return
        
        embed = discord.Embed(
            title="🔒 Ticket Closed",
            description="This ticket will be deleted in 5 seconds...",
            color=0xe74c3c
        )
        await interaction.followup.send(embed=embed)
        
        await asyncio.sleep(5)
        await interaction.channel.delete()

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'tickets.db'

    async def init_database(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS ticket_panels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.commit()

    async def cog_load(self):
        await self.init_database()
        self.bot.add_view(TicketView())
        self.bot.add_view(TicketCloseView())

    @app_commands.command(name="ticket-panel", description="Create a ticket panel")
    @app_commands.describe(
        title="Title for the ticket panel",
        description="Description for the ticket panel"
    )
    @commands.has_permissions(manage_guild=True)
    async def ticket_panel(self, interaction: discord.Interaction, title: str, description: str = "Click the button below to create a support ticket."):
        await interaction.response.defer()
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=0x3498db
        )
        embed.set_footer(text="Support Team")
        
        view = TicketView()
        message = await interaction.followup.send(embed=embed, view=view)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO ticket_panels (guild_id, channel_id, message_id, title, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (interaction.guild_id, interaction.channel_id, message.id, title, description))
            await db.commit()

    @app_commands.command(name="ticket-add", description="Add user to current ticket")
    @app_commands.describe(user="User to add to the ticket")
    @commands.has_permissions(manage_channels=True)
    async def ticket_add(self, interaction: discord.Interaction, user: discord.Member):
        if not interaction.channel.name.startswith("ticket-"):
            await interaction.response.send_message("This command can only be used in ticket channels!", ephemeral=True)
            return
        
        await interaction.channel.set_permissions(user, read_messages=True, send_messages=True)
        
        embed = discord.Embed(
            title="✅ User Added",
            description=f"{user.mention} has been added to this ticket.",
            color=0x2ecc71
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ticket-remove", description="Remove user from current ticket")
    @app_commands.describe(user="User to remove from the ticket")
    @commands.has_permissions(manage_channels=True)
    async def ticket_remove(self, interaction: discord.Interaction, user: discord.Member):
        if not interaction.channel.name.startswith("ticket-"):
            await interaction.response.send_message("This command can only be used in ticket channels!", ephemeral=True)
            return
        
        await interaction.channel.set_permissions(user, overwrite=None)
        
        embed = discord.Embed(
            title="❌ User Removed",
            description=f"{user.mention} has been removed from this ticket.",
            color=0xe74c3c
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Tickets(bot))