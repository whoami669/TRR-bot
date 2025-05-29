import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import json
from typing import Optional

class CustomizationHub(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="custom-command", description="Create or manage custom commands")
    @app_commands.describe(
        action="What to do with custom commands",
        name="Command name",
        response="Command response"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Create", value="create"),
        app_commands.Choice(name="Delete", value="delete"),
        app_commands.Choice(name="List", value="list"),
        app_commands.Choice(name="Edit", value="edit")
    ])
    @app_commands.default_permissions(manage_guild=True)
    async def custom_command(self, interaction: discord.Interaction, 
                           action: str, name: str = None, response: str = None):
        
        async with aiosqlite.connect('ultrabot.db') as db:
            if action == "create":
                if not name or not response:
                    await interaction.response.send_message("❌ Please provide both name and response!", ephemeral=True)
                    return
                
                await db.execute('''
                    INSERT OR REPLACE INTO custom_commands (guild_id, command_name, response, created_by)
                    VALUES (?, ?, ?, ?)
                ''', (interaction.guild.id, name.lower(), response, interaction.user.id))
                await db.commit()
                
                embed = discord.Embed(
                    title="✅ Custom Command Created",
                    description=f"Command `/{name}` has been created",
                    color=discord.Color.green()
                )
                embed.add_field(name="Response", value=response[:200] + ("..." if len(response) > 200 else ""), inline=False)
                
            elif action == "delete":
                if not name:
                    await interaction.response.send_message("❌ Please provide a command name!", ephemeral=True)
                    return
                
                await db.execute('''
                    DELETE FROM custom_commands WHERE guild_id = ? AND command_name = ?
                ''', (interaction.guild.id, name.lower()))
                await db.commit()
                
                embed = discord.Embed(
                    title="🗑️ Custom Command Deleted",
                    description=f"Command `/{name}` has been deleted",
                    color=discord.Color.red()
                )
                
            elif action == "list":
                async with db.execute('''
                    SELECT command_name, usage_count FROM custom_commands 
                    WHERE guild_id = ? ORDER BY usage_count DESC
                ''', (interaction.guild.id,)) as cursor:
                    commands_list = await cursor.fetchall()
                
                if not commands_list:
                    await interaction.response.send_message("No custom commands found!", ephemeral=True)
                    return
                
                embed = discord.Embed(
                    title="📋 Custom Commands",
                    color=discord.Color.blue()
                )
                
                for cmd_name, usage in commands_list[:10]:
                    embed.add_field(name=f"/{cmd_name}", value=f"Used {usage} times", inline=True)
                
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="embed-builder", description="Create custom embeds")
    @app_commands.describe(
        title="Embed title",
        description="Embed description",
        color="Embed color (hex code like #FF0000)",
        thumbnail="Thumbnail URL",
        image="Image URL"
    )
    async def embed_builder(self, interaction: discord.Interaction,
                          title: str, description: str = None,
                          color: str = None, thumbnail: str = None, image: str = None):
        
        # Parse color
        embed_color = discord.Color.blue()
        if color:
            try:
                if color.startswith('#'):
                    embed_color = discord.Color(int(color[1:], 16))
                else:
                    embed_color = discord.Color(int(color, 16))
            except:
                pass
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=embed_color
        )
        
        if thumbnail:
            try:
                embed.set_thumbnail(url=thumbnail)
            except:
                pass
        
        if image:
            try:
                embed.set_image(url=image)
            except:
                pass
        
        embed.set_footer(text=f"Created by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="role-menu", description="Create a role selection menu")
    @app_commands.describe(
        title="Menu title",
        roles="Roles to include (mention them separated by spaces)"
    )
    @app_commands.default_permissions(manage_roles=True)
    async def role_menu(self, interaction: discord.Interaction, title: str, roles: str):
        # Parse mentioned roles
        role_mentions = roles.split()
        menu_roles = []
        
        for mention in role_mentions:
            if mention.startswith('<@&') and mention.endswith('>'):
                role_id = int(mention[3:-1])
                role = interaction.guild.get_role(role_id)
                if role:
                    menu_roles.append(role)
        
        if not menu_roles:
            await interaction.response.send_message("❌ No valid roles found!", ephemeral=True)
            return
        
        if len(menu_roles) > 10:
            await interaction.response.send_message("❌ Maximum 10 roles allowed!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=title,
            description="React with the corresponding emoji to get/remove roles:",
            color=discord.Color.blue()
        )
        
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        for i, role in enumerate(menu_roles):
            embed.add_field(name=f"{emojis[i]} {role.name}", value=f"{len(role.members)} members", inline=True)
        
        message = await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        
        for i in range(len(menu_roles)):
            await message.add_reaction(emojis[i])
        
        # Store role menu data
        async with aiosqlite.connect('ultrabot.db') as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS role_menus (
                    message_id INTEGER PRIMARY KEY,
                    guild_id INTEGER,
                    role_data TEXT
                )
            ''')
            
            role_data = json.dumps([{"emoji": emojis[i], "role_id": role.id} for i, role in enumerate(menu_roles)])
            
            await db.execute('''
                INSERT INTO role_menus (message_id, guild_id, role_data)
                VALUES (?, ?, ?)
            ''', (message.id, interaction.guild.id, role_data))
            await db.commit()

    @app_commands.command(name="server-setup", description="Quick server setup with channels and roles")
    @app_commands.describe(template="Server template to use")
    @app_commands.choices(template=[
        app_commands.Choice(name="Gaming Community", value="gaming"),
        app_commands.Choice(name="Study Group", value="study"),
        app_commands.Choice(name="Business/Professional", value="business"),
        app_commands.Choice(name="Art Community", value="art"),
        app_commands.Choice(name="General Community", value="general")
    ])
    @app_commands.default_permissions(administrator=True)
    async def server_setup(self, interaction: discord.Interaction, template: str):
        await interaction.response.defer()
        
        guild = interaction.guild
        
        templates = {
            "gaming": {
                "categories": [
                    {"name": "📢 INFORMATION", "channels": ["📋rules", "📢announcements", "❓faq"]},
                    {"name": "💬 GENERAL", "channels": ["💬general-chat", "🎮game-discussion", "🔥memes"]},
                    {"name": "🎮 GAMING", "channels": ["🎯lfg", "🏆tournaments", "📺streaming"]},
                    {"name": "🔊 VOICE", "channels": ["🎵General Voice", "🎮Gaming Voice", "🎵Music Voice"]}
                ],
                "roles": ["🎮 Gamer", "🏆 Pro Player", "📺 Streamer", "🎵 Music Lover"]
            },
            "study": {
                "categories": [
                    {"name": "📚 INFORMATION", "channels": ["📋rules", "📢announcements", "📝resources"]},
                    {"name": "💬 GENERAL", "channels": ["💬general-chat", "❓help", "💡study-tips"]},
                    {"name": "📖 SUBJECTS", "channels": ["🧮math", "🔬science", "📚literature", "💻programming"]},
                    {"name": "🔊 STUDY ROOMS", "channels": ["📚Study Room 1", "📚Study Room 2", "🎵Music Study"]}
                ],
                "roles": ["📚 Student", "👨‍🏫 Tutor", "🧮 Math Expert", "💻 Programmer"]
            },
            "business": {
                "categories": [
                    {"name": "📢 COMPANY", "channels": ["📋announcements", "📰news", "🎯goals"]},
                    {"name": "💼 WORK", "channels": ["💬general", "💡ideas", "📊reports", "🤝partnerships"]},
                    {"name": "🎯 PROJECTS", "channels": ["📋project-planning", "💻development", "🎨design"]},
                    {"name": "🔊 MEETINGS", "channels": ["📞Meeting Room", "💼Executive Room", "🎥Presentation Room"]}
                ],
                "roles": ["💼 Employee", "👔 Manager", "💎 Executive", "🎯 Project Lead"]
            },
            "art": {
                "categories": [
                    {"name": "📢 INFORMATION", "channels": ["📋rules", "📢announcements", "🎨showcase"]},
                    {"name": "💬 COMMUNITY", "channels": ["💬general-chat", "💡inspiration", "🎭critiques"]},
                    {"name": "🎨 CREATION", "channels": ["✏️sketches", "🎨paintings", "📸photography", "🎵music"]},
                    {"name": "🔊 CREATIVE SPACES", "channels": ["🎨Art Studio", "🎵Music Room", "📸Photo Shoot"]}
                ],
                "roles": ["🎨 Artist", "📸 Photographer", "🎵 Musician", "🎭 Critic"]
            },
            "general": {
                "categories": [
                    {"name": "📢 INFORMATION", "channels": ["📋rules", "📢announcements", "👋introductions"]},
                    {"name": "💬 GENERAL", "channels": ["💬general-chat", "🎈fun", "🤖bot-commands"]},
                    {"name": "🎯 TOPICS", "channels": ["💻technology", "🎵music", "🎬movies", "📚books"]},
                    {"name": "🔊 VOICE", "channels": ["💬General Voice", "🎵Music Voice", "🎮Gaming Voice"]}
                ],
                "roles": ["👋 New Member", "💬 Active", "🌟 Veteran", "🎯 Enthusiast"]
            }
        }
        
        template_data = templates.get(template, templates["general"])
        created_items = {"categories": 0, "channels": 0, "roles": 0}
        
        try:
            # Create roles
            for role_name in template_data["roles"]:
                if not discord.utils.get(guild.roles, name=role_name):
                    await guild.create_role(name=role_name)
                    created_items["roles"] += 1
            
            # Create categories and channels
            for category_data in template_data["categories"]:
                category = discord.utils.get(guild.categories, name=category_data["name"])
                if not category:
                    category = await guild.create_category(category_data["name"])
                    created_items["categories"] += 1
                
                for channel_name in category_data["channels"]:
                    if not discord.utils.get(guild.channels, name=channel_name):
                        if category_data["name"].contains("VOICE") or "Voice" in channel_name:
                            await guild.create_voice_channel(channel_name, category=category)
                        else:
                            await guild.create_text_channel(channel_name, category=category)
                        created_items["channels"] += 1
            
            embed = discord.Embed(
                title="✅ Server Setup Complete",
                description=f"Successfully set up server with **{template.title()}** template",
                color=discord.Color.green()
            )
            embed.add_field(name="Categories Created", value=created_items["categories"], inline=True)
            embed.add_field(name="Channels Created", value=created_items["channels"], inline=True)
            embed.add_field(name="Roles Created", value=created_items["roles"], inline=True)
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Setup failed: {str(e)}")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Handle role menu reactions"""
        if user.bot:
            return
        
        async with aiosqlite.connect('ultrabot.db') as db:
            async with db.execute('''
                SELECT role_data FROM role_menus WHERE message_id = ?
            ''', (reaction.message.id,)) as cursor:
                result = await cursor.fetchone()
        
        if not result:
            return
        
        role_data = json.loads(result[0])
        
        for item in role_data:
            if str(reaction.emoji) == item["emoji"]:
                role = reaction.message.guild.get_role(item["role_id"])
                if role and role not in user.roles:
                    try:
                        await user.add_roles(role)
                    except:
                        pass
                break

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        """Handle role menu reaction removals"""
        if user.bot:
            return
        
        async with aiosqlite.connect('ultrabot.db') as db:
            async with db.execute('''
                SELECT role_data FROM role_menus WHERE message_id = ?
            ''', (reaction.message.id,)) as cursor:
                result = await cursor.fetchone()
        
        if not result:
            return
        
        role_data = json.loads(result[0])
        
        for item in role_data:
            if str(reaction.emoji) == item["emoji"]:
                role = reaction.message.guild.get_role(item["role_id"])
                if role and role in user.roles:
                    try:
                        await user.remove_roles(role)
                    except:
                        pass
                break

async def setup(bot):
    await bot.add_cog(CustomizationHub(bot))