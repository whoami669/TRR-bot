import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import yt_dlp
import aiosqlite
from typing import Optional

# Configure yt-dlp
ytdl_format_options = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'prefer_ffmpeg': True
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
            
            if data is None:
                raise Exception("Could not extract video information")
            
            if 'entries' in data and data['entries']:
                data = data['entries'][0]
            
            if stream:
                filename = data.get('url')
                if not filename:
                    raise Exception("Could not get stream URL")
            else:
                filename = ytdl.prepare_filename(data)
            
            ffmpeg_options = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn'
            }
            return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
        except Exception as e:
            raise Exception(f"Error processing audio: {str(e)}")

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'music.db'
        self.queues = {}
        self.voice_clients = {}

    async def init_database(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS playlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    songs TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.commit()

    async def cog_load(self):
        await self.init_database()

    @app_commands.command(name="join", description="Join voice channel")
    async def join(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            await interaction.response.send_message("You need to be in a voice channel")
            return
        
        channel = interaction.user.voice.channel
        voice_client = await channel.connect()
        self.voice_clients[interaction.guild_id] = voice_client
        
        embed = discord.Embed(
            title="🎵 Joined Voice Channel",
            description=f"Connected to {channel.name}",
            color=0x3498db
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leave", description="Leave voice channel")
    async def leave(self, interaction: discord.Interaction):
        if interaction.guild_id in self.voice_clients:
            await self.voice_clients[interaction.guild_id].disconnect()
            del self.voice_clients[interaction.guild_id]
            if interaction.guild_id in self.queues:
                del self.queues[interaction.guild_id]
        
        embed = discord.Embed(
            title="👋 Left Voice Channel",
            description="Disconnected from voice channel",
            color=0xe74c3c
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="play", description="Play music from URL or search")
    @app_commands.describe(query="YouTube URL or search term")
    async def play(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        
        if not interaction.user.voice:
            await interaction.followup.send("You need to be in a voice channel")
            return
        
        if interaction.guild_id not in self.voice_clients:
            channel = interaction.user.voice.channel
            voice_client = await channel.connect()
            self.voice_clients[interaction.guild_id] = voice_client
        
        try:
            player = await YTDLSource.from_url(query, stream=True)
            
            if interaction.guild_id not in self.queues:
                self.queues[interaction.guild_id] = []
            
            self.queues[interaction.guild_id].append(player)
            
            if not self.voice_clients[interaction.guild_id].is_playing():
                await self.play_next(interaction.guild_id)
            
            embed = discord.Embed(
                title="🎵 Added to Queue",
                description=f"**{player.title}**",
                color=0x2ecc71
            )
            embed.add_field(name="Position", value=len(self.queues[interaction.guild_id]), inline=True)
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"Error playing music: {str(e)}")

    async def play_next(self, guild_id):
        if guild_id in self.queues and self.queues[guild_id]:
            player = self.queues[guild_id].pop(0)
            self.voice_clients[guild_id].play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(guild_id), self.bot.loop))

    @app_commands.command(name="pause", description="Pause current song")
    async def pause(self, interaction: discord.Interaction):
        if interaction.guild_id in self.voice_clients and self.voice_clients[interaction.guild_id].is_playing():
            self.voice_clients[interaction.guild_id].pause()
            embed = discord.Embed(title="⏸️ Paused", color=0xf39c12)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nothing is playing")

    @app_commands.command(name="resume", description="Resume current song")
    async def resume(self, interaction: discord.Interaction):
        if interaction.guild_id in self.voice_clients and self.voice_clients[interaction.guild_id].is_paused():
            self.voice_clients[interaction.guild_id].resume()
            embed = discord.Embed(title="▶️ Resumed", color=0x2ecc71)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nothing is paused")

    @app_commands.command(name="stop", description="Stop music and clear queue")
    async def stop(self, interaction: discord.Interaction):
        if interaction.guild_id in self.voice_clients:
            self.voice_clients[interaction.guild_id].stop()
            if interaction.guild_id in self.queues:
                self.queues[interaction.guild_id].clear()
            
            embed = discord.Embed(title="⏹️ Stopped", description="Music stopped and queue cleared", color=0xe74c3c)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nothing is playing")

    @app_commands.command(name="skip", description="Skip current song")
    async def skip(self, interaction: discord.Interaction):
        if interaction.guild_id in self.voice_clients and self.voice_clients[interaction.guild_id].is_playing():
            self.voice_clients[interaction.guild_id].stop()
            embed = discord.Embed(title="⏭️ Skipped", color=0x3498db)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Nothing is playing")

    @app_commands.command(name="queue", description="Show music queue")
    async def queue(self, interaction: discord.Interaction):
        if interaction.guild_id not in self.queues or not self.queues[interaction.guild_id]:
            await interaction.response.send_message("Queue is empty")
            return
        
        embed = discord.Embed(title="🎵 Music Queue", color=0x3498db)
        queue_list = []
        
        for i, player in enumerate(self.queues[interaction.guild_id][:10], 1):
            queue_list.append(f"{i}. {player.title}")
        
        embed.description = "\n".join(queue_list)
        
        if len(self.queues[interaction.guild_id]) > 10:
            embed.set_footer(text=f"... and {len(self.queues[interaction.guild_id]) - 10} more")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="volume", description="Set music volume")
    @app_commands.describe(volume="Volume level (0-100)")
    async def volume(self, interaction: discord.Interaction, volume: int):
        if volume < 0 or volume > 100:
            await interaction.response.send_message("Volume must be between 0 and 100")
            return
        
        if interaction.guild_id in self.voice_clients:
            source = self.voice_clients[interaction.guild_id].source
            if isinstance(source, discord.PCMVolumeTransformer):
                source.volume = volume / 100
                embed = discord.Embed(
                    title="🔊 Volume Changed",
                    description=f"Volume set to {volume}%",
                    color=0x3498db
                )
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("Cannot change volume for this audio source")
        else:
            await interaction.response.send_message("Not connected to voice channel")

async def setup(bot):
    await bot.add_cog(Music(bot))