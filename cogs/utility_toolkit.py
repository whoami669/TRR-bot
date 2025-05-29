import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import asyncio
import re
import json
import qrcode
import io
import base64
from datetime import datetime, timezone, timedelta
from typing import Optional

class UtilityToolkit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="serverinfo", description="Detailed server information")
    async def server_info(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        # Get detailed statistics
        text_channels = len([c for c in guild.channels if isinstance(c, discord.TextChannel)])
        voice_channels = len([c for c in guild.channels if isinstance(c, discord.VoiceChannel)])
        categories = len([c for c in guild.channels if isinstance(c, discord.CategoryChannel)])
        
        embed = discord.Embed(
            title=f"📊 {guild.name}",
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Basic info
        embed.add_field(name="👑 Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="🆔 Server ID", value=guild.id, inline=True)
        embed.add_field(name="📅 Created", value=f"<t:{int(guild.created_at.timestamp())}:R>", inline=True)
        
        # Member info
        embed.add_field(name="👥 Members", value=f"{guild.member_count:,}", inline=True)
        embed.add_field(name="🤖 Bots", value=len([m for m in guild.members if m.bot]), inline=True)
        embed.add_field(name="👤 Humans", value=len([m for m in guild.members if not m.bot]), inline=True)
        
        # Channel info
        embed.add_field(name="💬 Text Channels", value=text_channels, inline=True)
        embed.add_field(name="🔊 Voice Channels", value=voice_channels, inline=True)
        embed.add_field(name="📁 Categories", value=categories, inline=True)
        
        # Additional info
        embed.add_field(name="🎭 Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="😀 Emojis", value=len(guild.emojis), inline=True)
        embed.add_field(name="🚀 Boost Level", value=f"Level {guild.premium_tier}", inline=True)
        
        if guild.premium_subscription_count:
            embed.add_field(name="💎 Boosts", value=guild.premium_subscription_count, inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="Detailed user information")
    @app_commands.describe(user="User to get information about")
    async def user_info(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        
        embed = discord.Embed(
            title=f"👤 {target.display_name}",
            color=target.color or discord.Color.default(),
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.set_thumbnail(url=target.display_avatar.url)
        
        # Basic info
        embed.add_field(name="📛 Username", value=str(target), inline=True)
        embed.add_field(name="🆔 User ID", value=target.id, inline=True)
        embed.add_field(name="🤖 Bot", value="Yes" if target.bot else "No", inline=True)
        
        # Dates
        embed.add_field(name="📅 Account Created", value=f"<t:{int(target.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="📥 Joined Server", value=f"<t:{int(target.joined_at.timestamp())}:R>", inline=True)
        
        # Join position
        sorted_members = sorted(interaction.guild.members, key=lambda m: m.joined_at)
        join_position = sorted_members.index(target) + 1
        embed.add_field(name="📍 Join Position", value=f"#{join_position:,}", inline=True)
        
        # Roles
        roles = [role.mention for role in target.roles[1:]]  # Exclude @everyone
        if roles:
            embed.add_field(name=f"🎭 Roles ({len(roles)})", value=" ".join(roles[:10]) + (f" +{len(roles)-10} more" if len(roles) > 10 else ""), inline=False)
        
        # Activity
        if target.activity:
            activity_type = {
                discord.ActivityType.playing: "🎮 Playing",
                discord.ActivityType.streaming: "📺 Streaming",
                discord.ActivityType.listening: "🎵 Listening to",
                discord.ActivityType.watching: "👀 Watching",
                discord.ActivityType.competing: "🏆 Competing in"
            }
            embed.add_field(name="🎯 Activity", value=f"{activity_type.get(target.activity.type, '❓')} {target.activity.name}", inline=False)
        
        # Get user stats from database
        async with aiosqlite.connect('ultrabot.db') as db:
            async with db.execute('''
                SELECT messages_sent, warnings FROM users 
                WHERE user_id = ? AND guild_id = ?
            ''', (target.id, interaction.guild.id)) as cursor:
                stats = await cursor.fetchone()
        
        if stats:
            embed.add_field(name="📊 Messages Sent", value=f"{stats[0]:,}", inline=True)
            embed.add_field(name="⚠️ Warnings", value=stats[1], inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="avatar", description="Display user's avatar")
    @app_commands.describe(user="User to show avatar for")
    async def show_avatar(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        
        embed = discord.Embed(
            title=f"🖼️ {target.display_name}'s Avatar",
            color=target.color or discord.Color.blue()
        )
        embed.set_image(url=target.display_avatar.url)
        embed.add_field(name="Direct Link", value=f"[Click here]({target.display_avatar.url})", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="qr", description="Generate QR code")
    @app_commands.describe(
        text="Text or URL to encode",
        size="QR code size"
    )
    @app_commands.choices(size=[
        app_commands.Choice(name="Small", value="small"),
        app_commands.Choice(name="Medium", value="medium"),
        app_commands.Choice(name="Large", value="large")
    ])
    async def generate_qr(self, interaction: discord.Interaction, text: str, size: str = "medium"):
        await interaction.response.defer()
        
        try:
            size_map = {"small": 5, "medium": 10, "large": 15}
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=size_map[size],
                border=4,
            )
            qr.add_data(text)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            file = discord.File(img_bytes, filename="qrcode.png")
            
            embed = discord.Embed(
                title="📱 QR Code Generated",
                description=f"**Content:** {text[:100]}{'...' if len(text) > 100 else ''}",
                color=discord.Color.blue()
            )
            embed.set_image(url="attachment://qrcode.png")
            
            await interaction.followup.send(embed=embed, file=file)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to generate QR code: {str(e)}", ephemeral=True)

    @app_commands.command(name="poll", description="Create an advanced poll")
    @app_commands.describe(
        question="Poll question",
        options="Poll options separated by semicolons (;)",
        duration="Poll duration (e.g., 1h, 30m)"
    )
    async def create_poll(self, interaction: discord.Interaction, 
                         question: str, options: str, duration: str = "1h"):
        
        option_list = [opt.strip() for opt in options.split(';')]
        
        if len(option_list) < 2:
            await interaction.response.send_message("❌ Poll needs at least 2 options!", ephemeral=True)
            return
        
        if len(option_list) > 10:
            await interaction.response.send_message("❌ Maximum 10 options allowed!", ephemeral=True)
            return
        
        # Parse duration
        try:
            time_units = {'m': 60, 'h': 3600, 'd': 86400}
            match = re.match(r'(\d+)([mhd])', duration.lower())
            if not match:
                await interaction.response.send_message("❌ Invalid duration format! Use: 30m, 1h, 2d", ephemeral=True)
                return
            
            amount, unit = match.groups()
            seconds = int(amount) * time_units[unit]
            end_time = datetime.now(timezone.utc) + timedelta(seconds=seconds)
        except:
            await interaction.response.send_message("❌ Invalid duration format!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📊 Poll",
            description=question,
            color=discord.Color.blue(),
            timestamp=end_time
        )
        
        reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        for i, option in enumerate(option_list):
            embed.add_field(name=f"{reactions[i]} {option}", value="0 votes", inline=False)
        
        embed.set_footer(text=f"Poll ends at")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        
        for i in range(len(option_list)):
            await message.add_reaction(reactions[i])

    @app_commands.command(name="reminder", description="Set a reminder")
    @app_commands.describe(
        time="When to remind (e.g., 1h, 30m, 2d)",
        message="Reminder message"
    )
    async def set_reminder(self, interaction: discord.Interaction, time: str, message: str):
        # Parse time
        try:
            time_units = {'m': 60, 'h': 3600, 'd': 86400, 'w': 604800}
            match = re.match(r'(\d+)([mhdw])', time.lower())
            if not match:
                await interaction.response.send_message("❌ Invalid time format! Use: 30m, 1h, 2d, 1w", ephemeral=True)
                return
            
            amount, unit = match.groups()
            seconds = int(amount) * time_units[unit]
            remind_at = datetime.now(timezone.utc) + timedelta(seconds=seconds)
        except:
            await interaction.response.send_message("❌ Invalid time format!", ephemeral=True)
            return
        
        # Store reminder in database
        async with aiosqlite.connect('ultrabot.db') as db:
            await db.execute('''
                INSERT INTO reminders (user_id, guild_id, channel_id, reminder_text, remind_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (interaction.user.id, interaction.guild.id, interaction.channel.id, message, remind_at))
            await db.commit()
        
        embed = discord.Embed(
            title="⏰ Reminder Set",
            description=f"I'll remind you about: **{message}**",
            color=discord.Color.green()
        )
        embed.add_field(name="Remind at", value=f"<t:{int(remind_at.timestamp())}:F>", inline=False)
        embed.add_field(name="That's in", value=f"<t:{int(remind_at.timestamp())}:R>", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="weather", description="Get weather information")
    @app_commands.describe(location="City name or location")
    async def get_weather(self, interaction: discord.Interaction, location: str):
        await interaction.response.send_message(
            "Weather functionality requires an API key. Please provide your OpenWeatherMap API key to enable weather commands.",
            ephemeral=True
        )

    @app_commands.command(name="translate", description="Translate text between languages")
    @app_commands.describe(
        text="Text to translate",
        to_language="Target language code (e.g., es, fr, de)",
        from_language="Source language (auto-detect if not specified)"
    )
    async def translate_text(self, interaction: discord.Interaction, 
                           text: str, to_language: str, from_language: str = "auto"):
        await interaction.response.send_message(
            "Translation functionality requires an API key. Please provide your Google Translate API key to enable translation.",
            ephemeral=True
        )

    @app_commands.command(name="calculate", description="Perform mathematical calculations")
    @app_commands.describe(expression="Mathematical expression to calculate")
    async def calculate(self, interaction: discord.Interaction, expression: str):
        try:
            # Basic safety check - only allow certain characters
            allowed_chars = set('0123456789+-*/().,^ ')
            if not all(c in allowed_chars for c in expression):
                await interaction.response.send_message("❌ Invalid characters in expression!", ephemeral=True)
                return
            
            # Replace ^ with ** for power operations
            expression = expression.replace('^', '**')
            
            # Evaluate safely
            result = eval(expression)
            
            embed = discord.Embed(
                title="🧮 Calculator",
                color=discord.Color.blue()
            )
            embed.add_field(name="Expression", value=f"`{expression}`", inline=False)
            embed.add_field(name="Result", value=f"**{result}**", inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error calculating expression: Invalid syntax", ephemeral=True)

    @app_commands.command(name="timestamp", description="Convert time to Discord timestamp")
    @app_commands.describe(
        datetime_input="Date and time (YYYY-MM-DD HH:MM or relative like '+2h')",
        format_type="Timestamp format"
    )
    @app_commands.choices(format_type=[
        app_commands.Choice(name="Short Date Time", value="f"),
        app_commands.Choice(name="Long Date Time", value="F"),
        app_commands.Choice(name="Short Date", value="d"),
        app_commands.Choice(name="Long Date", value="D"),
        app_commands.Choice(name="Short Time", value="t"),
        app_commands.Choice(name="Long Time", value="T"),
        app_commands.Choice(name="Relative", value="R")
    ])
    async def create_timestamp(self, interaction: discord.Interaction, 
                             datetime_input: str, format_type: str = "f"):
        try:
            # Handle relative time
            if datetime_input.startswith('+') or datetime_input.startswith('-'):
                time_units = {'m': 60, 'h': 3600, 'd': 86400, 'w': 604800}
                match = re.match(r'([+-])(\d+)([mhdw])', datetime_input.lower())
                if match:
                    sign, amount, unit = match.groups()
                    seconds = int(amount) * time_units[unit]
                    if sign == '-':
                        seconds = -seconds
                    target_time = datetime.now(timezone.utc) + timedelta(seconds=seconds)
                else:
                    raise ValueError("Invalid relative time format")
            else:
                # Parse absolute datetime
                try:
                    target_time = datetime.strptime(datetime_input, "%Y-%m-%d %H:%M")
                    target_time = target_time.replace(tzinfo=timezone.utc)
                except ValueError:
                    target_time = datetime.strptime(datetime_input, "%Y-%m-%d")
                    target_time = target_time.replace(tzinfo=timezone.utc)
            
            timestamp = int(target_time.timestamp())
            formatted = f"<t:{timestamp}:{format_type}>"
            
            embed = discord.Embed(
                title="🕐 Discord Timestamp",
                color=discord.Color.blue()
            )
            embed.add_field(name="Input", value=datetime_input, inline=False)
            embed.add_field(name="Timestamp Code", value=f"`{formatted}`", inline=False)
            embed.add_field(name="Preview", value=formatted, inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                "❌ Invalid date format! Use YYYY-MM-DD HH:MM or relative time like +2h, -30m",
                ephemeral=True
            )

    @app_commands.command(name="base64", description="Encode or decode base64")
    @app_commands.describe(
        text="Text to encode/decode",
        operation="Encode or decode"
    )
    @app_commands.choices(operation=[
        app_commands.Choice(name="Encode", value="encode"),
        app_commands.Choice(name="Decode", value="decode")
    ])
    async def base64_convert(self, interaction: discord.Interaction, 
                           text: str, operation: str):
        try:
            if operation == "encode":
                result = base64.b64encode(text.encode()).decode()
                title = "🔒 Base64 Encoded"
            else:
                result = base64.b64decode(text).decode()
                title = "🔓 Base64 Decoded"
            
            embed = discord.Embed(
                title=title,
                color=discord.Color.blue()
            )
            embed.add_field(name="Input", value=f"```{text[:500]}```", inline=False)
            embed.add_field(name="Output", value=f"```{result[:500]}```", inline=False)
            
            if len(result) > 500:
                embed.set_footer(text="Output truncated - result is longer than 500 characters")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error processing base64: Invalid input", ephemeral=True)

async def setup(bot):
    await bot.add_cog(UtilityToolkit(bot))