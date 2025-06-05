import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import json
from typing import Optional, Dict, List

class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'reaction_roles.db'
        
    async def init_database(self):
        """Initialize the reaction roles database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS reaction_roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    emoji TEXT NOT NULL,
                    role_id INTEGER NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(message_id, emoji)
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS reaction_role_messages (
                    message_id INTEGER PRIMARY KEY,
                    guild_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    color INTEGER DEFAULT 3447003,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.commit()

    async def cog_load(self):
        """Initialize database when cog loads"""
        await self.init_database()

    @app_commands.command(name="create-reaction-role", description="Create a reaction role message")
    @app_commands.describe(
        title="Title for the reaction role embed",
        description="Description text for the embed",
        channel="Channel to send the message (optional, defaults to current channel)"
    )
    @commands.has_permissions(manage_roles=True)
    async def create_reaction_role(self, interaction: discord.Interaction, title: str, 
                                 description: str = "React to get your roles!", 
                                 channel: Optional[discord.TextChannel] = None):
        """Create a new reaction role message"""
        await interaction.response.defer()
        
        target_channel = channel or interaction.channel
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=0x3498db
        )
        embed.set_footer(text="React with emojis to get roles!")
        
        message = await target_channel.send(embed=embed)
        
        # Store message info in database
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO reaction_role_messages 
                (message_id, guild_id, channel_id, title, description, color)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (message.id, interaction.guild_id, target_channel.id, title, description, 0x3498db))
            await db.commit()
        
        embed_response = discord.Embed(
            title="✅ Reaction Role Message Created",
            description=f"Created reaction role message in {target_channel.mention}\nMessage ID: `{message.id}`",
            color=0x2ecc71
        )
        await interaction.followup.send(embed=embed_response)

    @app_commands.command(name="add-reaction-role", description="Add a reaction role to a message")
    @app_commands.describe(
        message_id="ID of the reaction role message",
        emoji="Emoji to react with",
        role="Role to assign when reacting",
        description="Description for this reaction role"
    )
    @commands.has_permissions(manage_roles=True)
    async def add_reaction_role(self, interaction: discord.Interaction, message_id: str, 
                              emoji: str, role: discord.Role, description: str = ""):
        """Add a reaction role to an existing message"""
        await interaction.response.defer()
        
        try:
            msg_id = int(message_id)
        except ValueError:
            await interaction.followup.send("❌ Invalid message ID format", ephemeral=True)
            return
        
        # Check if message exists in database
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT * FROM reaction_role_messages WHERE message_id = ? AND guild_id = ?
            ''', (msg_id, interaction.guild_id))
            message_data = await cursor.fetchone()
            
            if not message_data:
                await interaction.followup.send("❌ Reaction role message not found", ephemeral=True)
                return
        
        # Find the message and add reaction
        try:
            channel = self.bot.get_channel(message_data[2])
            message = await channel.fetch_message(msg_id)
            await message.add_reaction(emoji)
        except Exception as e:
            await interaction.followup.send(f"❌ Error adding reaction: {str(e)}", ephemeral=True)
            return
        
        # Store reaction role in database
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute('''
                    INSERT INTO reaction_roles 
                    (guild_id, channel_id, message_id, emoji, role_id, description)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (interaction.guild_id, message_data[2], msg_id, emoji, role.id, description))
                await db.commit()
            except aiosqlite.IntegrityError:
                await interaction.followup.send("❌ This emoji is already used on this message", ephemeral=True)
                return
        
        # Update the embed to show current reaction roles
        await self.update_reaction_role_embed(msg_id)
        
        embed = discord.Embed(
            title="✅ Reaction Role Added",
            description=f"Added {emoji} → {role.mention}\nDescription: {description or 'None'}",
            color=0x2ecc71
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="remove-reaction-role", description="Remove a reaction role from a message")
    @app_commands.describe(
        message_id="ID of the reaction role message",
        emoji="Emoji to remove"
    )
    @commands.has_permissions(manage_roles=True)
    async def remove_reaction_role(self, interaction: discord.Interaction, message_id: str, emoji: str):
        """Remove a reaction role from a message"""
        await interaction.response.defer()
        
        try:
            msg_id = int(message_id)
        except ValueError:
            await interaction.followup.send("❌ Invalid message ID format", ephemeral=True)
            return
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT * FROM reaction_roles WHERE message_id = ? AND emoji = ? AND guild_id = ?
            ''', (msg_id, emoji, interaction.guild_id))
            reaction_data = await cursor.fetchone()
            
            if not reaction_data:
                await interaction.followup.send("❌ Reaction role not found", ephemeral=True)
                return
            
            await db.execute('''
                DELETE FROM reaction_roles WHERE message_id = ? AND emoji = ? AND guild_id = ?
            ''', (msg_id, emoji, interaction.guild_id))
            await db.commit()
        
        # Remove reaction from message
        try:
            channel = self.bot.get_channel(reaction_data[2])
            message = await channel.fetch_message(msg_id)
            await message.clear_reaction(emoji)
        except Exception:
            pass  # Message might be deleted
        
        # Update the embed
        await self.update_reaction_role_embed(msg_id)
        
        embed = discord.Embed(
            title="✅ Reaction Role Removed",
            description=f"Removed {emoji} reaction role",
            color=0x2ecc71
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="list-reaction-roles", description="List all reaction role messages in this server")
    @commands.has_permissions(manage_roles=True)
    async def list_reaction_roles(self, interaction: discord.Interaction):
        """List all reaction role messages"""
        await interaction.response.defer()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT m.message_id, m.channel_id, m.title, COUNT(r.id) as role_count
                FROM reaction_role_messages m
                LEFT JOIN reaction_roles r ON m.message_id = r.message_id
                WHERE m.guild_id = ?
                GROUP BY m.message_id
                ORDER BY m.created_at DESC
            ''', (interaction.guild_id,))
            messages = await cursor.fetchall()
        
        if not messages:
            await interaction.followup.send("❌ No reaction role messages found in this server")
            return
        
        embed = discord.Embed(
            title="🎭 Reaction Role Messages",
            description="All reaction role messages in this server",
            color=0x3498db
        )
        
        for msg_id, channel_id, title, role_count in messages:
            channel = self.bot.get_channel(channel_id)
            channel_name = channel.mention if channel else "Unknown Channel"
            embed.add_field(
                name=f"📋 {title}",
                value=f"ID: `{msg_id}`\nChannel: {channel_name}\nRoles: {role_count}",
                inline=True
            )
        
        await interaction.followup.send(embed=embed)

    async def update_reaction_role_embed(self, message_id: int):
        """Update the reaction role embed with current roles"""
        async with aiosqlite.connect(self.db_path) as db:
            # Get message info
            cursor = await db.execute('''
                SELECT * FROM reaction_role_messages WHERE message_id = ?
            ''', (message_id,))
            message_data = await cursor.fetchone()
            
            if not message_data:
                return
            
            # Get all reaction roles for this message
            cursor = await db.execute('''
                SELECT emoji, role_id, description FROM reaction_roles 
                WHERE message_id = ? ORDER BY id
            ''', (message_id,))
            roles = await cursor.fetchall()
        
        try:
            channel = self.bot.get_channel(message_data[2])
            message = await channel.fetch_message(message_id)
            
            embed = discord.Embed(
                title=message_data[3],  # title
                description=message_data[4],  # description
                color=message_data[5] or 0x3498db  # color
            )
            
            if roles:
                role_list = []
                for emoji, role_id, desc in roles:
                    role = channel.guild.get_role(role_id)
                    if role:
                        role_text = f"{emoji} → {role.mention}"
                        if desc:
                            role_text += f" - {desc}"
                        role_list.append(role_text)
                
                if role_list:
                    embed.add_field(
                        name="Available Roles",
                        value="\n".join(role_list),
                        inline=False
                    )
            
            embed.set_footer(text="React with emojis to get roles!")
            await message.edit(embed=embed)
        
        except Exception:
            pass  # Message might be deleted

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handle reaction additions"""
        if payload.user_id == self.bot.user.id:
            return
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT role_id FROM reaction_roles 
                WHERE message_id = ? AND emoji = ? AND guild_id = ?
            ''', (payload.message_id, str(payload.emoji), payload.guild_id))
            result = await cursor.fetchone()
        
        if result:
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = guild.get_role(result[0])
            
            if member and role and role not in member.roles:
                try:
                    await member.add_roles(role, reason="Reaction role")
                except discord.Forbidden:
                    pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Handle reaction removals"""
        if payload.user_id == self.bot.user.id:
            return
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT role_id FROM reaction_roles 
                WHERE message_id = ? AND emoji = ? AND guild_id = ?
            ''', (payload.message_id, str(payload.emoji), payload.guild_id))
            result = await cursor.fetchone()
        
        if result:
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = guild.get_role(result[0])
            
            if member and role and role in member.roles:
                try:
                    await member.remove_roles(role, reason="Reaction role removed")
                except discord.Forbidden:
                    pass

    @create_reaction_role.error
    @add_reaction_role.error
    @remove_reaction_role.error
    @list_reaction_roles.error
    async def reaction_role_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle command errors"""
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ You need the 'Manage Roles' permission to use this command", ephemeral=True)
        else:
            await interaction.response.send_message("❌ An error occurred while processing your request", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))