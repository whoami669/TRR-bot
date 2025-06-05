import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
import base64
import io
import qrcode
from datetime import datetime, timezone
import asyncio
import random
import hashlib

class EnhancedUtilities(commands.Cog):
    """Enhanced utility commands replacing music functionality"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="qr", description="Generate QR code from text")
    @app_commands.describe(text="Text to encode in QR code")
    async def qr_code(self, interaction: discord.Interaction, text: str):
        """Generate QR code from text"""
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(text)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            file = discord.File(img_bytes, filename="qrcode.png")
            
            embed = discord.Embed(
                title="QR Code Generated",
                description=f"QR code for: `{text[:100]}{'...' if len(text) > 100 else ''}`",
                color=0x3498db
            )
            embed.set_image(url="attachment://qrcode.png")
            
            await interaction.response.send_message(embed=embed, file=file)
            
        except Exception as e:
            await interaction.response.send_message(f"Error generating QR code: {str(e)}")
    
    @app_commands.command(name="base64", description="Encode or decode base64")
    @app_commands.describe(
        action="Encode or decode",
        text="Text to encode/decode"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="encode", value="encode"),
        app_commands.Choice(name="decode", value="decode")
    ])
    async def base64_convert(self, interaction: discord.Interaction, action: str, text: str):
        """Encode or decode base64 text"""
        try:
            if action == "encode":
                encoded = base64.b64encode(text.encode()).decode()
                embed = discord.Embed(
                    title="Base64 Encoded",
                    description=f"**Original:** `{text[:100]}{'...' if len(text) > 100 else ''}`\n**Encoded:** `{encoded}`",
                    color=0x2ecc71
                )
            else:
                decoded = base64.b64decode(text.encode()).decode()
                embed = discord.Embed(
                    title="Base64 Decoded",
                    description=f"**Encoded:** `{text[:100]}{'...' if len(text) > 100 else ''}`\n**Decoded:** `{decoded}`",
                    color=0x2ecc71
                )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"Error with base64 conversion: {str(e)}")
    
    @app_commands.command(name="hash", description="Generate hash of text")
    @app_commands.describe(
        text="Text to hash",
        algorithm="Hash algorithm"
    )
    @app_commands.choices(algorithm=[
        app_commands.Choice(name="MD5", value="md5"),
        app_commands.Choice(name="SHA1", value="sha1"),
        app_commands.Choice(name="SHA256", value="sha256"),
        app_commands.Choice(name="SHA512", value="sha512")
    ])
    async def hash_text(self, interaction: discord.Interaction, text: str, algorithm: str = "sha256"):
        """Generate hash of text"""
        try:
            if algorithm == "md5":
                hash_obj = hashlib.md5(text.encode())
            elif algorithm == "sha1":
                hash_obj = hashlib.sha1(text.encode())
            elif algorithm == "sha256":
                hash_obj = hashlib.sha256(text.encode())
            elif algorithm == "sha512":
                hash_obj = hashlib.sha512(text.encode())
            
            hash_value = hash_obj.hexdigest()
            
            embed = discord.Embed(
                title=f"{algorithm.upper()} Hash",
                description=f"**Text:** `{text[:50]}{'...' if len(text) > 50 else ''}`\n**Hash:** `{hash_value}`",
                color=0x9b59b6
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"Error generating hash: {str(e)}")
    
    @app_commands.command(name="random", description="Generate random values")
    @app_commands.describe(
        type="Type of random value",
        min_val="Minimum value (for numbers)",
        max_val="Maximum value (for numbers)"
    )
    @app_commands.choices(type=[
        app_commands.Choice(name="Number", value="number"),
        app_commands.Choice(name="Password", value="password"),
        app_commands.Choice(name="UUID", value="uuid"),
        app_commands.Choice(name="Color", value="color")
    ])
    async def random_generator(self, interaction: discord.Interaction, type: str, min_val: int = 1, max_val: int = 100):
        """Generate random values"""
        try:
            if type == "number":
                result = random.randint(min_val, max_val)
                embed = discord.Embed(
                    title="Random Number",
                    description=f"**Range:** {min_val} - {max_val}\n**Result:** `{result}`",
                    color=0xe67e22
                )
            
            elif type == "password":
                import string
                chars = string.ascii_letters + string.digits + "!@#$%^&*"
                password = ''.join(random.choice(chars) for _ in range(16))
                embed = discord.Embed(
                    title="Random Password",
                    description=f"**Password:** `{password}`\n**Length:** 16 characters",
                    color=0xe67e22
                )
            
            elif type == "uuid":
                import uuid
                uuid_val = str(uuid.uuid4())
                embed = discord.Embed(
                    title="Random UUID",
                    description=f"**UUID:** `{uuid_val}`",
                    color=0xe67e22
                )
            
            elif type == "color":
                color_hex = f"#{random.randint(0, 0xFFFFFF):06x}"
                embed = discord.Embed(
                    title="Random Color",
                    description=f"**Hex:** `{color_hex}`",
                    color=int(color_hex[1:], 16)
                )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"Error generating random value: {str(e)}")
    
    @app_commands.command(name="timestamp", description="Generate Discord timestamps")
    @app_commands.describe(
        format="Timestamp format",
        offset_hours="Hours from now (optional)"
    )
    @app_commands.choices(format=[
        app_commands.Choice(name="Short Time", value="t"),
        app_commands.Choice(name="Long Time", value="T"),
        app_commands.Choice(name="Short Date", value="d"),
        app_commands.Choice(name="Long Date", value="D"),
        app_commands.Choice(name="Short Date/Time", value="f"),
        app_commands.Choice(name="Long Date/Time", value="F"),
        app_commands.Choice(name="Relative", value="R")
    ])
    async def timestamp_generator(self, interaction: discord.Interaction, format: str = "f", offset_hours: int = 0):
        """Generate Discord timestamps"""
        try:
            from datetime import timedelta
            
            target_time = datetime.now(timezone.utc) + timedelta(hours=offset_hours)
            timestamp = int(target_time.timestamp())
            
            discord_timestamp = f"<t:{timestamp}:{format}>"
            
            embed = discord.Embed(
                title="Discord Timestamp",
                description=f"**Timestamp:** `{discord_timestamp}`\n**Preview:** {discord_timestamp}",
                color=0x5865f2
            )
            embed.add_field(name="Unix Timestamp", value=f"`{timestamp}`", inline=True)
            embed.add_field(name="Offset", value=f"{offset_hours} hours", inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"Error generating timestamp: {str(e)}")
    
    @app_commands.command(name="weather", description="Get weather information")
    @app_commands.describe(city="City name")
    async def weather(self, interaction: discord.Interaction, city: str):
        """Get weather information for a city"""
        await interaction.response.defer()
        
        try:
            # Using a free weather API
            async with aiohttp.ClientSession() as session:
                url = f"http://wttr.in/{city}?format=j1"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        current = data['current_condition'][0]
                        
                        embed = discord.Embed(
                            title=f"Weather in {city}",
                            color=0x87ceeb
                        )
                        embed.add_field(name="Temperature", value=f"{current['temp_C']}°C / {current['temp_F']}°F", inline=True)
                        embed.add_field(name="Feels Like", value=f"{current['FeelsLikeC']}°C / {current['FeelsLikeF']}°F", inline=True)
                        embed.add_field(name="Humidity", value=f"{current['humidity']}%", inline=True)
                        embed.add_field(name="Condition", value=current['weatherDesc'][0]['value'], inline=True)
                        embed.add_field(name="Wind", value=f"{current['windspeedKmph']} km/h", inline=True)
                        embed.add_field(name="Visibility", value=f"{current['visibility']} km", inline=True)
                        
                        await interaction.followup.send(embed=embed)
                    else:
                        await interaction.followup.send("Could not fetch weather data. Please check the city name.")
        
        except Exception as e:
            await interaction.followup.send(f"Error fetching weather: {str(e)}")
    
    @app_commands.command(name="url", description="URL utilities")
    @app_commands.describe(
        action="URL action",
        url="URL to process"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Shorten", value="shorten"),
        app_commands.Choice(name="Expand", value="expand"),
        app_commands.Choice(name="Validate", value="validate")
    ])
    async def url_utils(self, interaction: discord.Interaction, action: str, url: str):
        """URL utilities"""
        try:
            if action == "validate":
                import re
                url_pattern = re.compile(
                    r'^https?://'  # http:// or https://
                    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                    r'localhost|'  # localhost...
                    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                    r'(?::\d+)?'  # optional port
                    r'(?:/?|[/?]\S+)$', re.IGNORECASE)
                
                is_valid = url_pattern.match(url) is not None
                
                embed = discord.Embed(
                    title="URL Validation",
                    description=f"**URL:** `{url}`\n**Valid:** {'✅ Yes' if is_valid else '❌ No'}",
                    color=0x2ecc71 if is_valid else 0xe74c3c
                )
                
                await interaction.response.send_message(embed=embed)
            
            elif action == "expand":
                async with aiohttp.ClientSession() as session:
                    async with session.head(url, allow_redirects=True) as response:
                        final_url = str(response.url)
                        
                        embed = discord.Embed(
                            title="URL Expanded",
                            description=f"**Original:** `{url}`\n**Expanded:** `{final_url}`",
                            color=0x3498db
                        )
                        
                        await interaction.response.send_message(embed=embed)
            
            else:  # shorten
                await interaction.response.send_message("URL shortening requires external API. Please provide an API key if needed.")
                
        except Exception as e:
            await interaction.response.send_message(f"Error processing URL: {str(e)}")

async def setup(bot):
    await bot.add_cog(EnhancedUtilities(bot))