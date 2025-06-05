import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import json
import qrcode
import io
from datetime import datetime, timezone
from typing import Optional
import base64

class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="qr", description="Generate a QR code")
    @app_commands.describe(text="Text to encode in QR code")
    async def qr_code(self, interaction: discord.Interaction, text: str):
        if len(text) > 500:
            await interaction.response.send_message("Text must be 500 characters or less")
            return
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(text)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        file = discord.File(img_bytes, filename='qrcode.png')
        
        embed = discord.Embed(
            title="📱 QR Code Generated",
            description=f"QR code for: `{text}`",
            color=0x3498db
        )
        embed.set_image(url="attachment://qrcode.png")
        
        await interaction.response.send_message(embed=embed, file=file)

    @app_commands.command(name="quickpoll", description="Create a poll")
    @app_commands.describe(
        question="Poll question",
        option1="First option",
        option2="Second option",
        option3="Third option (optional)",
        option4="Fourth option (optional)",
        option5="Fifth option (optional)"
    )
    async def poll(self, interaction: discord.Interaction, question: str, option1: str, option2: str, 
                   option3: Optional[str] = None, option4: Optional[str] = None, option5: Optional[str] = None):
        
        options = [option1, option2]
        if option3: options.append(option3)
        if option4: options.append(option4)
        if option5: options.append(option5)
        
        if len(options) > 5:
            await interaction.response.send_message("Maximum 5 options allowed")
            return
        
        reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        
        embed = discord.Embed(
            title="📊 Poll",
            description=question,
            color=0x3498db
        )
        
        for i, option in enumerate(options):
            embed.add_field(
                name=f"{reactions[i]} Option {i+1}",
                value=option,
                inline=False
            )
        
        embed.set_footer(text="React to vote!")
        
        message = await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        
        for i in range(len(options)):
            await message.add_reaction(reactions[i])

    @app_commands.command(name="reminder", description="Set a reminder")
    @app_commands.describe(
        time="Time in minutes",
        message="Reminder message"
    )
    async def remind(self, interaction: discord.Interaction, time: int, message: str):
        if time < 1 or time > 1440:  # Max 24 hours
            await interaction.response.send_message("Reminder time must be between 1 and 1440 minutes (24 hours)")
            return
        
        await interaction.response.send_message(f"⏰ Reminder set for {time} minutes: {message}")
        
        await asyncio.sleep(time * 60)
        
        embed = discord.Embed(
            title="⏰ Reminder",
            description=message,
            color=0xf39c12
        )
        embed.set_footer(text=f"Reminder from {time} minutes ago")
        
        try:
            await interaction.user.send(embed=embed)
        except:
            channel = interaction.channel
            await channel.send(f"{interaction.user.mention}", embed=embed)

    @app_commands.command(name="math", description="Calculate mathematical expressions")
    @app_commands.describe(expression="Mathematical expression to calculate")
    async def math(self, interaction: discord.Interaction, expression: str):
        # Safe evaluation of mathematical expressions
        allowed_chars = set("0123456789+-*/().^ ")
        if not all(c in allowed_chars for c in expression):
            await interaction.response.send_message("Invalid characters in expression. Only numbers, +, -, *, /, (, ), and ^ are allowed")
            return
        
        try:
            # Replace ^ with ** for Python exponentiation
            expression = expression.replace("^", "**")
            result = eval(expression)
            
            embed = discord.Embed(
                title="🧮 Calculator",
                color=0x2ecc71
            )
            embed.add_field(name="Expression", value=f"`{expression.replace('**', '^')}`", inline=False)
            embed.add_field(name="Result", value=f"`{result}`", inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"Error calculating expression: {str(e)}")

    @app_commands.command(name="timestamp", description="Generate Discord timestamp")
    @app_commands.describe(
        year="Year",
        month="Month (1-12)",
        day="Day (1-31)",
        hour="Hour (0-23, optional)",
        minute="Minute (0-59, optional)"
    )
    async def timestamp(self, interaction: discord.Interaction, year: int, month: int, day: int, 
                       hour: int = 0, minute: int = 0):
        try:
            dt = datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
            timestamp = int(dt.timestamp())
            
            embed = discord.Embed(
                title="🕐 Discord Timestamp",
                color=0x9b59b6
            )
            embed.add_field(name="Date/Time", value=f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d} UTC", inline=False)
            embed.add_field(name="Timestamp", value=f"`<t:{timestamp}>`", inline=False)
            embed.add_field(name="Relative", value=f"`<t:{timestamp}:R>`", inline=False)
            embed.add_field(name="Preview", value=f"<t:{timestamp}> (<t:{timestamp}:R>)", inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except ValueError as e:
            await interaction.response.send_message(f"Invalid date/time: {str(e)}")

    @app_commands.command(name="color", description="Generate color information")
    @app_commands.describe(color="Hex color code (e.g., #FF5733 or FF5733)")
    async def color(self, interaction: discord.Interaction, color: str):
        # Clean hex color
        if color.startswith('#'):
            color = color[1:]
        
        if len(color) != 6 or not all(c in '0123456789ABCDEFabcdef' for c in color):
            await interaction.response.send_message("Invalid hex color. Use format: #FF5733 or FF5733")
            return
        
        # Convert to RGB
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        
        # Convert to decimal
        decimal = int(color, 16)
        
        embed = discord.Embed(
            title="🎨 Color Information",
            color=decimal
        )
        embed.add_field(name="Hex", value=f"#{color.upper()}", inline=True)
        embed.add_field(name="RGB", value=f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})", inline=True)
        embed.add_field(name="Decimal", value=str(decimal), inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="base64", description="Encode or decode base64")
    @app_commands.describe(
        action="encode or decode",
        text="Text to encode/decode"
    )
    async def base64_convert(self, interaction: discord.Interaction, action: str, text: str):
        action = action.lower()
        
        if action not in ['encode', 'decode']:
            await interaction.response.send_message("Action must be 'encode' or 'decode'")
            return
        
        try:
            if action == 'encode':
                result = base64.b64encode(text.encode()).decode()
                title = "📝 Base64 Encoded"
            else:
                result = base64.b64decode(text.encode()).decode()
                title = "📝 Base64 Decoded"
            
            embed = discord.Embed(
                title=title,
                color=0x3498db
            )
            embed.add_field(name="Input", value=f"```{text}```", inline=False)
            embed.add_field(name="Output", value=f"```{result}```", inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"Error during {action}: {str(e)}")

    @app_commands.command(name="hash", description="Generate hash of text")
    @app_commands.describe(
        text="Text to hash",
        algorithm="Hash algorithm (md5, sha1, sha256)"
    )
    async def hash_text(self, interaction: discord.Interaction, text: str, algorithm: str = "sha256"):
        import hashlib
        
        algorithm = algorithm.lower()
        supported = ['md5', 'sha1', 'sha256', 'sha512']
        
        if algorithm not in supported:
            await interaction.response.send_message(f"Supported algorithms: {', '.join(supported)}")
            return
        
        try:
            hasher = getattr(hashlib, algorithm)()
            hasher.update(text.encode())
            result = hasher.hexdigest()
            
            embed = discord.Embed(
                title=f"🔐 {algorithm.upper()} Hash",
                color=0xe74c3c
            )
            embed.add_field(name="Input", value=f"```{text}```", inline=False)
            embed.add_field(name="Hash", value=f"```{result}```", inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"Error generating hash: {str(e)}")

    @app_commands.command(name="weather", description="Get weather information")
    @app_commands.describe(location="City name or location")
    async def weather(self, interaction: discord.Interaction, location: str):
        await interaction.response.send_message(
            "Weather feature requires an API key. Please provide your OpenWeatherMap API key to enable weather commands."
        )

    @app_commands.command(name="translate", description="Translate text")
    @app_commands.describe(
        text="Text to translate",
        target_language="Target language code (e.g., es, fr, de)"
    )
    async def translate(self, interaction: discord.Interaction, text: str, target_language: str):
        await interaction.response.send_message(
            "Translation feature requires an API key. Please provide your Google Translate API key to enable translation commands."
        )

async def setup(bot):
    await bot.add_cog(Utilities(bot))