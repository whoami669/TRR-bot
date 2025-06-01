import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import asyncio
import json
import base64
import qrcode
import io
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import time
import random
import string
from datetime import datetime, timedelta
import hashlib
import re

class AdvancedUtilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reminders = {}
        
    @app_commands.command(name="qr-code", description="Generate QR codes with custom options")
    @app_commands.describe(
        text="Text to encode in QR code",
        size="QR code size",
        color="QR code color (hex)",
        background="Background color (hex)"
    )
    async def generate_qr(self, interaction: discord.Interaction, text: str, 
                         size: int = 200, color: str = "000000", background: str = "FFFFFF"):
        await interaction.response.defer()
        
        try:
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(text)
            qr.make(fit=True)
            
            # Create image with custom colors
            img = qr.make_image(fill_color=f"#{color}", back_color=f"#{background}")
            img = img.resize((size, size))
            
            # Save to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            file = discord.File(img_bytes, filename='qrcode.png')
            
            embed = discord.Embed(
                title="📱 QR Code Generated",
                description=f"**Content:** {text[:100]}{'...' if len(text) > 100 else ''}",
                color=discord.Color.blue()
            )
            embed.set_image(url="attachment://qrcode.png")
            embed.add_field(name="Size", value=f"{size}x{size}", inline=True)
            embed.add_field(name="Colors", value=f"FG: #{color}\nBG: #{background}", inline=True)
            
            await interaction.followup.send(embed=embed, file=file)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to generate QR code: {str(e)}")

    @app_commands.command(name="url-shortener", description="Create short URLs and track clicks")
    @app_commands.describe(url="URL to shorten", custom_alias="Custom alias (optional)")
    async def shorten_url(self, interaction: discord.Interaction, url: str, custom_alias: str = None):
        await interaction.response.defer()
        
        try:
            # Generate short code
            if custom_alias:
                short_code = custom_alias
            else:
                short_code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            
            # Store in database
            async with aiosqlite.connect('ultrabot.db') as db:
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS short_urls (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        short_code TEXT UNIQUE,
                        original_url TEXT,
                        creator_id INTEGER,
                        guild_id INTEGER,
                        clicks INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                await db.execute('''
                    INSERT INTO short_urls (short_code, original_url, creator_id, guild_id)
                    VALUES (?, ?, ?, ?)
                ''', (short_code, url, interaction.user.id, interaction.guild.id))
                await db.commit()
            
            short_url = f"https://bot.link/{short_code}"
            
            embed = discord.Embed(
                title="🔗 URL Shortened",
                color=discord.Color.green()
            )
            embed.add_field(name="Original URL", value=url[:100] + "..." if len(url) > 100 else url, inline=False)
            embed.add_field(name="Short URL", value=f"`{short_url}`", inline=False)
            embed.add_field(name="Short Code", value=short_code, inline=True)
            embed.add_field(name="Clicks", value="0", inline=True)
            embed.set_footer(text="Use /url-stats to track clicks")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to shorten URL: {str(e)}")

    @app_commands.command(name="reminder", description="Set smart reminders with multiple options")
    @app_commands.describe(
        time="Time (e.g., 5m, 2h, 1d)",
        message="Reminder message",
        repeat="Repeat interval (optional)",
        private="Send as DM instead of channel"
    )
    async def set_reminder(self, interaction: discord.Interaction, time: str, message: str, 
                          repeat: str = None, private: bool = False):
        await interaction.response.defer()
        
        try:
            # Parse time
            time_seconds = self.parse_time(time)
            if time_seconds is None:
                await interaction.followup.send("❌ Invalid time format. Use: 5m, 2h, 1d, etc.")
                return
            
            reminder_time = datetime.now() + timedelta(seconds=time_seconds)
            reminder_id = f"{interaction.user.id}_{int(time.time())}"
            
            # Store reminder
            async with aiosqlite.connect('ultrabot.db') as db:
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS reminders (
                        id TEXT PRIMARY KEY,
                        user_id INTEGER,
                        channel_id INTEGER,
                        guild_id INTEGER,
                        message TEXT,
                        reminder_time TIMESTAMP,
                        repeat_interval TEXT,
                        is_private BOOLEAN,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                await db.execute('''
                    INSERT INTO reminders VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ''', (reminder_id, interaction.user.id, interaction.channel.id, 
                      interaction.guild.id, message, reminder_time, repeat, private))
                await db.commit()
            
            # Schedule reminder
            asyncio.create_task(self.schedule_reminder(reminder_id, time_seconds, message, 
                                                     interaction.user.id, interaction.channel.id, private))
            
            embed = discord.Embed(
                title="⏰ Reminder Set",
                description=f"**Message:** {message}",
                color=discord.Color.orange()
            )
            embed.add_field(name="Time", value=f"<t:{int(reminder_time.timestamp())}:R>", inline=True)
            embed.add_field(name="Repeat", value=repeat or "None", inline=True)
            embed.add_field(name="Private", value="Yes" if private else "No", inline=True)
            embed.set_footer(text=f"Reminder ID: {reminder_id}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to set reminder: {str(e)}")

    @app_commands.command(name="password-generator", description="Generate secure passwords")
    @app_commands.describe(
        length="Password length (8-128)",
        include_symbols="Include special characters",
        include_numbers="Include numbers",
        exclude_ambiguous="Exclude ambiguous characters (0, O, l, I)"
    )
    async def generate_password(self, interaction: discord.Interaction, length: int = 16,
                               include_symbols: bool = True, include_numbers: bool = True,
                               exclude_ambiguous: bool = True):
        await interaction.response.defer(ephemeral=True)
        
        try:
            if length < 8 or length > 128:
                await interaction.followup.send("❌ Password length must be between 8 and 128 characters.")
                return
            
            # Character sets
            lowercase = "abcdefghijklmnopqrstuvwxyz"
            uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            numbers = "0123456789"
            symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            
            if exclude_ambiguous:
                lowercase = lowercase.replace('l', '')
                uppercase = uppercase.replace('O', '').replace('I', '')
                numbers = numbers.replace('0', '')
            
            # Build character set
            chars = lowercase + uppercase
            if include_numbers:
                chars += numbers
            if include_symbols:
                chars += symbols
            
            # Generate password
            password = ''.join(random.choices(chars, k=length))
            
            # Calculate strength
            strength_score = self.calculate_password_strength(password)
            strength_text = ["Very Weak", "Weak", "Fair", "Good", "Strong"][min(4, strength_score // 20)]
            
            embed = discord.Embed(
                title="🔐 Password Generated",
                color=discord.Color.green()
            )
            embed.add_field(name="Password", value=f"```{password}```", inline=False)
            embed.add_field(name="Length", value=str(length), inline=True)
            embed.add_field(name="Strength", value=strength_text, inline=True)
            embed.add_field(name="Score", value=f"{strength_score}/100", inline=True)
            embed.set_footer(text="This password is sent privately to you only")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to generate password: {str(e)}")

    @app_commands.command(name="text-analysis", description="Analyze text for various metrics")
    @app_commands.describe(text="Text to analyze")
    async def analyze_text(self, interaction: discord.Interaction, text: str):
        await interaction.response.defer()
        
        try:
            # Basic metrics
            char_count = len(text)
            word_count = len(text.split())
            sentence_count = len([s for s in text.split('.') if s.strip()])
            paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
            
            # Advanced metrics
            avg_word_length = sum(len(word.strip('.,!?;:')) for word in text.split()) / word_count if word_count > 0 else 0
            reading_time = word_count / 200  # Average reading speed
            
            # Word frequency
            words = [word.lower().strip('.,!?;:()[]{}') for word in text.split()]
            word_freq = {}
            for word in words:
                if len(word) > 3:  # Only count words longer than 3 characters
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Language detection patterns
            language_hints = []
            if any(word in text.lower() for word in ['the', 'and', 'is', 'are', 'was']):
                language_hints.append("English")
            if any(word in text.lower() for word in ['el', 'la', 'es', 'son', 'fue']):
                language_hints.append("Spanish")
            if any(word in text.lower() for word in ['le', 'la', 'est', 'sont', 'était']):
                language_hints.append("French")
            
            embed = discord.Embed(
                title="📊 Text Analysis Results",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="📝 Basic Metrics", 
                           value=f"Characters: {char_count:,}\nWords: {word_count:,}\nSentences: {sentence_count}\nParagraphs: {paragraph_count}", 
                           inline=True)
            
            embed.add_field(name="📈 Advanced Metrics", 
                           value=f"Avg Word Length: {avg_word_length:.1f}\nReading Time: {reading_time:.1f} min\nReadability: {'Easy' if avg_word_length < 5 else 'Medium' if avg_word_length < 7 else 'Hard'}", 
                           inline=True)
            
            if top_words:
                top_words_text = "\n".join([f"{word}: {count}" for word, count in top_words])
                embed.add_field(name="🔤 Top Words", value=top_words_text, inline=True)
            
            if language_hints:
                embed.add_field(name="🌐 Detected Language", value=", ".join(language_hints), inline=True)
            
            embed.set_footer(text=f"Analysis completed • Text preview: {text[:50]}...")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to analyze text: {str(e)}")

    @app_commands.command(name="color-palette", description="Generate color palettes and convert formats")
    @app_commands.describe(
        base_color="Base color (hex, rgb, or color name)",
        palette_type="Type of palette to generate",
        count="Number of colors to generate"
    )
    @app_commands.choices(palette_type=[
        app_commands.Choice(name="Complementary", value="complementary"),
        app_commands.Choice(name="Analogous", value="analogous"),
        app_commands.Choice(name="Triadic", value="triadic"),
        app_commands.Choice(name="Monochromatic", value="monochromatic"),
        app_commands.Choice(name="Random", value="random")
    ])
    async def color_palette(self, interaction: discord.Interaction, base_color: str, 
                           palette_type: str = "complementary", count: int = 5):
        await interaction.response.defer()
        
        try:
            # Parse base color
            base_rgb = self.parse_color(base_color)
            if not base_rgb:
                await interaction.followup.send("❌ Invalid color format. Use hex (#FF0000), rgb (255,0,0), or color names.")
                return
            
            # Generate palette
            colors = self.generate_color_palette(base_rgb, palette_type, count)
            
            # Create color swatch image
            img = Image.new('RGB', (count * 100, 100), 'white')
            draw = ImageDraw.Draw(img)
            
            for i, color in enumerate(colors):
                x = i * 100
                draw.rectangle([x, 0, x + 100, 100], fill=color)
            
            # Save image
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            file = discord.File(img_bytes, filename='palette.png')
            
            # Create embed
            embed = discord.Embed(
                title="🎨 Color Palette",
                description=f"**Type:** {palette_type.title()}\n**Base Color:** {base_color}",
                color=int(f"{base_rgb[0]:02x}{base_rgb[1]:02x}{base_rgb[2]:02x}", 16)
            )
            
            color_info = ""
            for i, color in enumerate(colors):
                hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                rgb_color = f"rgb({color[0]}, {color[1]}, {color[2]})"
                color_info += f"**Color {i+1}:** {hex_color}\n{rgb_color}\n\n"
            
            embed.add_field(name="Color Codes", value=color_info[:1024], inline=False)
            embed.set_image(url="attachment://palette.png")
            
            await interaction.followup.send(embed=embed, file=file)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to generate palette: {str(e)}")

    def parse_time(self, time_str: str) -> int:
        """Parse time string to seconds"""
        time_str = time_str.lower().strip()
        
        patterns = {
            r'(\d+)s': 1,
            r'(\d+)m': 60,
            r'(\d+)h': 3600,
            r'(\d+)d': 86400,
            r'(\d+)w': 604800
        }
        
        for pattern, multiplier in patterns.items():
            match = re.match(pattern, time_str)
            if match:
                return int(match.group(1)) * multiplier
        
        return None

    def calculate_password_strength(self, password: str) -> int:
        """Calculate password strength score (0-100)"""
        score = 0
        
        # Length bonus
        score += min(25, len(password) * 2)
        
        # Character variety
        if any(c.islower() for c in password):
            score += 15
        if any(c.isupper() for c in password):
            score += 15
        if any(c.isdigit() for c in password):
            score += 15
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 20
        
        # Deduct for common patterns
        if password.lower() in ['password', '123456', 'qwerty']:
            score -= 50
        
        return max(0, min(100, score))

    def parse_color(self, color_str: str):
        """Parse color string to RGB tuple"""
        color_str = color_str.strip().lower()
        
        # Hex color
        if color_str.startswith('#'):
            try:
                return tuple(int(color_str[i:i+2], 16) for i in (1, 3, 5))
            except ValueError:
                return None
        
        # RGB format
        if color_str.startswith('rgb'):
            try:
                numbers = re.findall(r'\d+', color_str)
                return tuple(int(n) for n in numbers[:3])
            except ValueError:
                return None
        
        # Color names
        color_names = {
            'red': (255, 0, 0), 'green': (0, 255, 0), 'blue': (0, 0, 255),
            'yellow': (255, 255, 0), 'purple': (128, 0, 128), 'orange': (255, 165, 0),
            'pink': (255, 192, 203), 'brown': (165, 42, 42), 'gray': (128, 128, 128),
            'black': (0, 0, 0), 'white': (255, 255, 255)
        }
        
        return color_names.get(color_str)

    def generate_color_palette(self, base_rgb, palette_type, count):
        """Generate color palette based on type"""
        colors = [base_rgb]
        
        if palette_type == "complementary":
            # Add complementary color
            comp = (255 - base_rgb[0], 255 - base_rgb[1], 255 - base_rgb[2])
            colors.append(comp)
            
        elif palette_type == "analogous":
            # Add colors with slight hue shifts
            for i in range(1, count):
                shift = i * 30
                new_color = self.shift_hue(base_rgb, shift)
                colors.append(new_color)
                
        elif palette_type == "monochromatic":
            # Add lighter/darker versions
            for i in range(1, count):
                factor = 0.2 + (i * 0.15)
                new_color = tuple(int(c * factor) for c in base_rgb)
                colors.append(new_color)
        
        # Fill remaining with random colors if needed
        while len(colors) < count:
            colors.append((random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        
        return colors[:count]

    def shift_hue(self, rgb, degrees):
        """Shift RGB color hue by degrees"""
        # Simplified hue shift - in a real implementation you'd convert to HSV
        r, g, b = rgb
        shift = degrees / 360.0
        
        # Basic color rotation
        new_r = int((r + shift * 255) % 255)
        new_g = int((g + shift * 128) % 255)
        new_b = int((b + shift * 64) % 255)
        
        return (new_r, new_g, new_b)

    async def schedule_reminder(self, reminder_id, delay, message, user_id, channel_id, is_private):
        """Schedule and send reminder"""
        await asyncio.sleep(delay)
        
        try:
            if is_private:
                user = self.bot.get_user(user_id)
                if user:
                    embed = discord.Embed(
                        title="⏰ Reminder",
                        description=message,
                        color=discord.Color.orange()
                    )
                    await user.send(embed=embed)
            else:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    embed = discord.Embed(
                        title="⏰ Reminder",
                        description=f"<@{user_id}> {message}",
                        color=discord.Color.orange()
                    )
                    await channel.send(embed=embed)
        except Exception as e:
            print(f"Failed to send reminder {reminder_id}: {e}")

async def setup(bot):
    await bot.add_cog(AdvancedUtilities(bot))