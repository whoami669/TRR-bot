import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import asyncio
import youtube_dl
import random
from collections import deque
from typing import Optional

# YouTube-DL options
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')
        self.uploader = data.get('uploader')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        
        if 'entries' in data:
            data = data['entries'][0]
        
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class MusicPlayer:
    def __init__(self, bot):
        self.bot = bot
        self.queue = deque()
        self.current = None
        self.volume = 0.5
        self.loop = False
        self.loop_queue = False
        
    def add_to_queue(self, source):
        self.queue.append(source)
    
    def get_queue(self):
        return list(self.queue)
    
    def clear_queue(self):
        self.queue.clear()
    
    def shuffle_queue(self):
        queue_list = list(self.queue)
        random.shuffle(queue_list)
        self.queue = deque(queue_list)

class MusicPremium(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players = {}

    def get_player(self, guild_id):
        if guild_id not in self.players:
            self.players[guild_id] = MusicPlayer(self.bot)
        return self.players[guild_id]

    @app_commands.command(name="join", description="Join your voice channel")
    async def join_voice(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            await interaction.response.send_message("❌ You need to be in a voice channel!", ephemeral=True)
            return
        
        channel = interaction.user.voice.channel
        
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.move_to(channel)
        else:
            await channel.connect()
        
        embed = discord.Embed(
            title="🎵 Joined Voice Channel",
            description=f"Connected to **{channel.name}**",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leave", description="Leave the voice channel")
    async def leave_voice(self, interaction: discord.Interaction):
        if not interaction.guild.voice_client:
            await interaction.response.send_message("❌ Not connected to a voice channel!", ephemeral=True)
            return
        
        player = self.get_player(interaction.guild.id)
        player.clear_queue()
        
        await interaction.guild.voice_client.disconnect()
        
        embed = discord.Embed(
            title="👋 Left Voice Channel",
            description="Disconnected and cleared the queue",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="play", description="Play music from YouTube")
    @app_commands.describe(search="Song name or YouTube URL")
    async def play_music(self, interaction: discord.Interaction, search: str):
        await interaction.response.defer()
        
        if not interaction.user.voice:
            await interaction.followup.send("❌ You need to be in a voice channel!")
            return
        
        if not interaction.guild.voice_client:
            channel = interaction.user.voice.channel
            await channel.connect()
        
        try:
            player = self.get_player(interaction.guild.id)
            source = await YTDLSource.from_url(search, loop=self.bot.loop, stream=True)
            
            if interaction.guild.voice_client.is_playing():
                player.add_to_queue(source)
                embed = discord.Embed(
                    title="📜 Added to Queue",
                    description=f"**{source.title}**",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Duration", value=f"{source.duration}s" if source.duration else "Unknown", inline=True)
                embed.add_field(name="Uploader", value=source.uploader or "Unknown", inline=True)
                embed.add_field(name="Position in Queue", value=str(len(player.queue)), inline=True)
                
                await interaction.followup.send(embed=embed)
            else:
                player.current = source
                interaction.guild.voice_client.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(interaction)))
                
                embed = discord.Embed(
                    title="🎵 Now Playing",
                    description=f"**{source.title}**",
                    color=discord.Color.green()
                )
                embed.add_field(name="Duration", value=f"{source.duration}s" if source.duration else "Unknown", inline=True)
                embed.add_field(name="Uploader", value=source.uploader or "Unknown", inline=True)
                embed.add_field(name="Requested by", value=interaction.user.mention, inline=True)
                
                await interaction.followup.send(embed=embed)
                
        except Exception as e:
            await interaction.followup.send(f"❌ An error occurred: {str(e)}")

    async def play_next(self, interaction):
        player = self.get_player(interaction.guild.id)
        
        if player.loop and player.current:
            # Replay current song
            try:
                source = await YTDLSource.from_url(player.current.url, loop=self.bot.loop, stream=True)
                interaction.guild.voice_client.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(interaction)))
            except:
                pass
        elif player.queue:
            # Play next in queue
            source = player.queue.popleft()
            player.current = source
            
            if player.loop_queue:
                player.add_to_queue(source)
            
            interaction.guild.voice_client.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(interaction)))
            
            embed = discord.Embed(
                title="🎵 Now Playing",
                description=f"**{source.title}**",
                color=discord.Color.green()
            )
            
            try:
                await interaction.followup.send(embed=embed)
            except:
                pass

    @app_commands.command(name="pause", description="Pause the current song")
    async def pause_music(self, interaction: discord.Interaction):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.pause()
            
            embed = discord.Embed(
                title="⏸️ Paused",
                description="Music has been paused",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ Nothing is currently playing!", ephemeral=True)

    @app_commands.command(name="resume", description="Resume the current song")
    async def resume_music(self, interaction: discord.Interaction):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_paused():
            interaction.guild.voice_client.resume()
            
            embed = discord.Embed(
                title="▶️ Resumed",
                description="Music has been resumed",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ Music is not paused!", ephemeral=True)

    @app_commands.command(name="skip", description="Skip the current song")
    async def skip_song(self, interaction: discord.Interaction):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()
            
            embed = discord.Embed(
                title="⏭️ Skipped",
                description="Skipped the current song",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ Nothing is currently playing!", ephemeral=True)

    @app_commands.command(name="stop", description="Stop music and clear queue")
    async def stop_music(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            player = self.get_player(interaction.guild.id)
            player.clear_queue()
            player.current = None
            interaction.guild.voice_client.stop()
            
            embed = discord.Embed(
                title="⏹️ Stopped",
                description="Music stopped and queue cleared",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ Not connected to voice!", ephemeral=True)

    @app_commands.command(name="queue", description="Show the music queue")
    async def show_queue(self, interaction: discord.Interaction):
        player = self.get_player(interaction.guild.id)
        queue = player.get_queue()
        
        if not queue and not player.current:
            await interaction.response.send_message("❌ Queue is empty!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📜 Music Queue",
            color=discord.Color.blue()
        )
        
        if player.current:
            embed.add_field(
                name="🎵 Currently Playing",
                value=f"**{player.current.title}**",
                inline=False
            )
        
        if queue:
            queue_text = ""
            for i, source in enumerate(queue[:10], 1):
                queue_text += f"{i}. **{source.title}**\n"
            
            if len(queue) > 10:
                queue_text += f"\n... and {len(queue) - 10} more songs"
            
            embed.add_field(name="📋 Up Next", value=queue_text, inline=False)
            embed.add_field(name="Total Songs", value=str(len(queue)), inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="volume", description="Set the music volume")
    @app_commands.describe(volume="Volume level (0-100)")
    async def set_volume(self, interaction: discord.Interaction, volume: int):
        if volume < 0 or volume > 100:
            await interaction.response.send_message("❌ Volume must be between 0 and 100!", ephemeral=True)
            return
        
        if interaction.guild.voice_client and interaction.guild.voice_client.source:
            player = self.get_player(interaction.guild.id)
            player.volume = volume / 100
            interaction.guild.voice_client.source.volume = player.volume
            
            embed = discord.Embed(
                title="🔊 Volume Set",
                description=f"Volume set to **{volume}%**",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ Nothing is currently playing!", ephemeral=True)

    @app_commands.command(name="shuffle", description="Shuffle the music queue")
    async def shuffle_queue(self, interaction: discord.Interaction):
        player = self.get_player(interaction.guild.id)
        
        if not player.queue:
            await interaction.response.send_message("❌ Queue is empty!", ephemeral=True)
            return
        
        player.shuffle_queue()
        
        embed = discord.Embed(
            title="🔀 Queue Shuffled",
            description=f"Shuffled {len(player.queue)} songs",
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="loop", description="Toggle loop mode")
    @app_commands.describe(mode="Loop mode")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Off", value="off"),
        app_commands.Choice(name="Current Song", value="song"),
        app_commands.Choice(name="Entire Queue", value="queue")
    ])
    async def toggle_loop(self, interaction: discord.Interaction, mode: str = "song"):
        player = self.get_player(interaction.guild.id)
        
        if mode == "off":
            player.loop = False
            player.loop_queue = False
            status = "Loop disabled"
            color = discord.Color.red()
        elif mode == "song":
            player.loop = True
            player.loop_queue = False
            status = "Looping current song"
            color = discord.Color.green()
        elif mode == "queue":
            player.loop = False
            player.loop_queue = True
            status = "Looping entire queue"
            color = discord.Color.blue()
        
        embed = discord.Embed(
            title="🔁 Loop Mode",
            description=status,
            color=color
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="nowplaying", description="Show currently playing song")
    async def now_playing(self, interaction: discord.Interaction):
        player = self.get_player(interaction.guild.id)
        
        if not player.current:
            await interaction.response.send_message("❌ Nothing is currently playing!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"**{player.current.title}**",
            color=discord.Color.green()
        )
        
        if player.current.duration:
            embed.add_field(name="Duration", value=f"{player.current.duration}s", inline=True)
        if player.current.uploader:
            embed.add_field(name="Uploader", value=player.current.uploader, inline=True)
        
        embed.add_field(name="Volume", value=f"{int(player.volume * 100)}%", inline=True)
        
        if player.loop:
            embed.add_field(name="Loop", value="🔁 Song", inline=True)
        elif player.loop_queue:
            embed.add_field(name="Loop", value="🔁 Queue", inline=True)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(MusicPremium(bot))