import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiosqlite
import asyncio
import random
import json
from datetime import datetime, timezone, timedelta
from typing import Optional

class ServerTakeover(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_events.start()
        self.engagement_boost.start()
        self.member_recognition.start()

    @app_commands.command(name="revive-server", description="Complete server transformation for gaming community")
    @app_commands.default_permissions(administrator=True)
    async def revive_server(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        guild = interaction.guild
        results = {"deleted": 0, "created": 0, "configured": 0}
        
        # Phase 1: Clean existing structure
        await interaction.followup.send("🔄 **Phase 1**: Cleaning server structure...")
        
        # Delete unnecessary channels (keep important ones)
        keep_channels = {'rules', 'announcements', 'general', 'bot-commands'}
        for channel in guild.text_channels:
            if channel.name.lower() not in keep_channels and not channel.permissions_for(guild.me).manage_channels:
                continue
            if channel.name.lower() not in keep_channels:
                try:
                    await channel.delete(reason="Server revival - cleaning structure")
                    results["deleted"] += 1
                    await asyncio.sleep(1)  # Rate limit protection
                except:
                    pass
        
        # Delete empty categories
        for category in guild.categories:
            if not category.channels:
                try:
                    await category.delete(reason="Server revival - removing empty categories")
                    results["deleted"] += 1
                except:
                    pass
        
        # Phase 2: Create optimal gaming community structure
        await interaction.followup.send("🏗️ **Phase 2**: Building gaming community structure...")
        
        # Create main categories and channels
        structure = {
            "📢 SERVER INFO": {
                "channels": ["📋│rules", "📢│announcements", "🎉│events", "💡│suggestions"],
                "permissions": {"send_messages": False, "add_reactions": True}
            },
            "💬 COMMUNITY": {
                "channels": ["💬│general-chat", "🎮│gaming-talk", "🔥│memes-and-fun", "📸│screenshots"],
                "permissions": {}
            },
            "🎮 GAMING HUB": {
                "channels": ["🎯│looking-for-group", "🏆│achievements", "🎲│game-suggestions", "💻│tech-talk"],
                "permissions": {}
            },
            "🎵 ENTERTAINMENT": {
                "channels": ["🎵│music-commands", "🎬│movie-night", "📚│book-club", "🎨│creative-corner"],
                "permissions": {}
            },
            "🔊 VOICE CHANNELS": {
                "channels": ["🎮 Gaming Lounge", "💬 Chill Zone", "🎵 Music Room", "📞 Private Chat"],
                "voice": True
            }
        }
        
        for category_name, data in structure.items():
            try:
                category = await guild.create_category(category_name, reason="Server revival")
                results["created"] += 1
                
                for channel_name in data["channels"]:
                    if data.get("voice"):
                        channel = await guild.create_voice_channel(
                            channel_name, 
                            category=category,
                            reason="Server revival - gaming community structure"
                        )
                    else:
                        overwrites = {}
                        if data.get("permissions"):
                            overwrites[guild.default_role] = discord.PermissionOverwrite(**data["permissions"])
                        
                        channel = await guild.create_text_channel(
                            channel_name,
                            category=category,
                            overwrites=overwrites,
                            reason="Server revival - gaming community structure"
                        )
                    results["created"] += 1
                    await asyncio.sleep(0.5)
            except:
                pass
        
        # Phase 3: Create engaging roles
        await interaction.followup.send("🎭 **Phase 3**: Setting up community roles...")
        
        gaming_roles = [
            {"name": "🎮 Gamer", "color": 0x00ff00, "mentionable": True},
            {"name": "🏆 Pro Player", "color": 0xffd700, "mentionable": True},
            {"name": "🎯 Casual Player", "color": 0x87ceeb, "mentionable": True},
            {"name": "🎵 Music Lover", "color": 0xff69b4, "mentionable": True},
            {"name": "🎨 Creative", "color": 0x9370db, "mentionable": True},
            {"name": "📚 Bookworm", "color": 0x8b4513, "mentionable": True},
            {"name": "🌙 Night Owl", "color": 0x191970, "mentionable": True},
            {"name": "☀️ Early Bird", "color": 0xffa500, "mentionable": True}
        ]
        
        for role_data in gaming_roles:
            if not discord.utils.get(guild.roles, name=role_data["name"]):
                try:
                    await guild.create_role(**role_data, reason="Server revival - community roles")
                    results["created"] += 1
                except:
                    pass
        
        # Phase 4: Configure automation systems
        await interaction.followup.send("⚙️ **Phase 4**: Configuring automation systems...")
        
        # Set up welcome system
        welcome_channel = discord.utils.get(guild.text_channels, name="general-chat")
        if welcome_channel:
            async with aiosqlite.connect('ultrabot.db') as db:
                await db.execute('''
                    INSERT OR REPLACE INTO welcome_config (guild_id, channel_id, message, auto_role_id)
                    VALUES (?, ?, ?, ?)
                ''', (guild.id, welcome_channel.id, 
                      "Welcome {user} to our gaming community! 🎮 You're member #{count}! Check out <#{}> for the rules and jump into the fun! Ready to game? 🔥".format(
                          discord.utils.get(guild.text_channels, name="rules").id if discord.utils.get(guild.text_channels, name="rules") else welcome_channel.id
                      ), 
                      discord.utils.get(guild.roles, name="🎮 Gamer").id if discord.utils.get(guild.roles, name="🎮 Gamer") else None))
                await db.commit()
        
        # Set up auto-reactions for engagement
        channels_reactions = {
            "memes-and-fun": ["😂", "🔥", "💯"],
            "screenshots": ["📸", "🔥", "❤️"],
            "achievements": ["🏆", "👏", "🎉"]
        }
        
        async with aiosqlite.connect('ultrabot.db') as db:
            for channel_name, emojis in channels_reactions.items():
                channel = discord.utils.get(guild.text_channels, name=channel_name)
                if channel:
                    await db.execute('''
                        INSERT OR REPLACE INTO auto_reactions (guild_id, trigger_type, trigger_value, emojis)
                        VALUES (?, ?, ?, ?)
                    ''', (guild.id, "channel", str(channel.id), " ".join(emojis)))
            await db.commit()
        
        results["configured"] += 5
        
        # Phase 5: Setup engagement systems
        await interaction.followup.send("🚀 **Phase 5**: Activating engagement systems...")
        
        # Create daily events
        events_channel = discord.utils.get(guild.text_channels, name="events")
        if events_channel:
            daily_events = [
                "🎮 **Gaming Session** - Join voice channels for multiplayer madness!",
                "🎵 **Music Party** - Share your favorite tracks in the music room!",
                "🎨 **Creative Challenge** - Show off your artistic skills!",
                "🎯 **Trivia Night** - Test your knowledge with /trivia!",
                "🏆 **Achievement Hunt** - Share your latest gaming accomplishments!",
                "📸 **Screenshot Saturday** - Post your best gaming moments!",
                "🔥 **Meme Monday** - Share the funniest memes you've got!"
            ]
            
            # Schedule first event
            embed = discord.Embed(
                title="🎉 Daily Community Event",
                description=random.choice(daily_events),
                color=0x00ff00
            )
            embed.add_field(name="How to Participate", value="Just join in and have fun! React with 🎉 if you're interested!", inline=False)
            await events_channel.send(embed=embed)
        
        # Final summary
        final_embed = discord.Embed(
            title="🎊 Server Revival Complete!",
            description="Your server has been transformed into a thriving gaming community!",
            color=0x00ff00
        )
        final_embed.add_field(name="📊 Changes Made", 
                             value=f"• Deleted: {results['deleted']} old items\n• Created: {results['created']} new items\n• Configured: {results['configured']} systems", 
                             inline=False)
        final_embed.add_field(name="🎮 What's New", 
                             value="• Organized gaming-focused channels\n• Auto-welcome system\n• Daily events\n• Engagement boosters\n• Gaming roles\n• Auto-reactions", 
                             inline=False)
        final_embed.add_field(name="🚀 Next Steps", 
                             value="• Invite friends to join\n• Use /role-menu to let members pick roles\n• Set up game-specific channels with /custom-command\n• Host events with /schedule-message", 
                             inline=False)
        
        await interaction.followup.send(embed=final_embed)

    @tasks.loop(hours=24)
    async def daily_events(self):
        """Post daily community events"""
        for guild in self.bot.guilds:
            events_channel = discord.utils.get(guild.text_channels, name="events")
            if events_channel:
                daily_events = [
                    "🎮 **Gaming Session** - Join voice channels for multiplayer madness! What's everyone playing today?",
                    "🎵 **Music Sharing** - Drop your current favorite song in the music channel!",
                    "🎨 **Creative Challenge** - Show off something you've created - art, music, code, anything!",
                    "🎯 **Community Trivia** - Use /trivia to start a knowledge battle!",
                    "🏆 **Achievement Showcase** - Share your latest gaming accomplishments and milestones!",
                    "📸 **Screenshot Spotlight** - Post your coolest gaming screenshots or moments!",
                    "🔥 **Meme War** - Share the funniest memes and let's see who wins!",
                    "💬 **Story Time** - Share an interesting or funny story from your day!",
                    "🎲 **Game Recommendation** - Suggest a game everyone should try!",
                    "🌟 **Compliment Circle** - Use /compliment to spread positivity!"
                ]
                
                embed = discord.Embed(
                    title="🎉 Daily Community Event",
                    description=random.choice(daily_events),
                    color=random.choice([0x00ff00, 0xff6b6b, 0x4ecdc4, 0x45b7d1, 0xf39c12, 0xe74c3c])
                )
                embed.add_field(name="Participate Now!", value="React with 🎉 and join the fun! Let's keep this community active!", inline=False)
                embed.set_footer(text="Daily events keep our community thriving!")
                
                try:
                    message = await events_channel.send(embed=embed)
                    await message.add_reaction("🎉")
                    await message.add_reaction("🔥")
                except:
                    pass

    @tasks.loop(hours=6)
    async def engagement_boost(self):
        """Send engagement boosters to keep community active"""
        engagement_messages = [
            "💬 **Chat Challenge**: What's the weirdest dream you've ever had?",
            "🎮 **Gaming Question**: What's your all-time favorite video game and why?",
            "🔥 **Hot Take**: Pineapple on pizza - yes or no? Defend your answer!",
            "🎵 **Music Mood**: What song always gets you hyped up?",
            "🌟 **Daily Positivity**: Share something good that happened today!",
            "🎯 **Would You Rather**: Be able to fly or be invisible?",
            "🎨 **Creative Spark**: If you could create anything, what would it be?",
            "📱 **Tech Talk**: What's the coolest app you've discovered recently?",
            "🍕 **Food Fight**: What's your go-to comfort food?",
            "🎪 **Random Fun**: If you had a superpower for one day, what would you do?"
        ]
        
        for guild in self.bot.guilds:
            general_channel = discord.utils.get(guild.text_channels, name="general-chat")
            if general_channel and random.random() < 0.3:  # 30% chance every 6 hours
                try:
                    await general_channel.send(random.choice(engagement_messages))
                except:
                    pass

    @tasks.loop(hours=12)
    async def member_recognition(self):
        """Recognize active members"""
        for guild in self.bot.guilds:
            general_channel = discord.utils.get(guild.text_channels, name="general-chat")
            if general_channel:
                # Get recent active members
                async with aiosqlite.connect('ultrabot.db') as db:
                    async with db.execute('''
                        SELECT user_id, messages_sent FROM users 
                        WHERE guild_id = ? AND messages_sent > 10
                        ORDER BY messages_sent DESC LIMIT 3
                    ''', (guild.id,)) as cursor:
                        active_members = await cursor.fetchall()
                
                if active_members and random.random() < 0.4:  # 40% chance
                    member = guild.get_member(active_members[0][0])
                    if member:
                        recognition_messages = [
                            f"🌟 Shoutout to {member.mention} for keeping our community alive with great conversations!",
                            f"👏 Big thanks to {member.mention} for being such an active and awesome community member!",
                            f"🔥 {member.mention} has been absolutely crushing it with their activity - thanks for the energy!",
                            f"💫 Special recognition goes to {member.mention} for making our server such a fun place!",
                            f"🎉 Let's give some love to {member.mention} for their amazing contributions to our community!"
                        ]
                        
                        try:
                            message = await general_channel.send(random.choice(recognition_messages))
                            await message.add_reaction("👏")
                            await message.add_reaction("🔥")
                            await message.add_reaction("❤️")
                        except:
                            pass

    @daily_events.before_loop
    @engagement_boost.before_loop
    @member_recognition.before_loop
    async def before_loops(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(ServerTakeover(bot))