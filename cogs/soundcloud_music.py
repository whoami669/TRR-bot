import discord
from discord.ext import commands
import asyncio
import yt_dlp
import os
from urllib.parse import urlparse
from collections import deque
import aiosqlite


class MusicQueue:
    def __init__(self):
        self.queue = deque()
        self.current = None
        self.loop = False
        self.shuffle = False
    
    def add(self, song):
        self.queue.append(song)
    
    def get_next(self):
        if self.queue:
            return self.queue.popleft()
        return None
    
    def clear(self):
        self.queue.clear()
    
    def size(self):
        return len(self.queue)


class Song:
    def __init__(self, url, title, duration, thumbnail=None, requested_by=None):
        self.url = url
        self.title = title
        self.duration = duration
        self.thumbnail = thumbnail
        self.requested_by = requested_by


class SoundCloudMusic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_clients = {}
        self.queues = {}
        self.ytdl_format_options = {
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
        }
        
        self.ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        
        self.ytdl = yt_dlp.YoutubeDL(self.ytdl_format_options)

    def get_guild_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = MusicQueue()
        return self.queues[guild_id]

    async def search_soundcloud(self, query):
        """Search for music on SoundCloud"""
        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                None, 
                lambda: self.ytdl.extract_info(f"ytsearch:{query} site:soundcloud.com", download=False)
            )
            
            if 'entries' in data and data['entries']:
                entry = data['entries'][0]
                return {
                    'url': entry['url'],
                    'title': entry.get('title', 'Unknown'),
                    'duration': entry.get('duration', 0),
                    'thumbnail': entry.get('thumbnail'),
                    'webpage_url': entry.get('webpage_url')
                }
        except Exception as e:
            print(f"Search error: {e}")
        return None

    async def get_audio_source(self, url):
        """Get audio source for playing"""
        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                None, 
                lambda: self.ytdl.extract_info(url, download=False)
            )
            
            if 'url' in data:
                return discord.FFmpegPCMAudio(data['url'], **self.ffmpeg_options)
            elif 'entries' in data and data['entries']:
                return discord.FFmpegPCMAudio(data['entries'][0]['url'], **self.ffmpeg_options)
        except Exception as e:
            print(f"Audio source error: {e}")
        return None

    @discord.app_commands.command(name="join", description="Join your voice channel")
    async def join(self, interaction: discord.Interaction):
        """Join the user's voice channel"""
        if not interaction.user.voice:
            await interaction.response.send_message("You need to be in a voice channel!", ephemeral=True)
            return
        
        channel = interaction.user.voice.channel
        
        if interaction.guild.voice_client:
            if interaction.guild.voice_client.channel == channel:
                await interaction.response.send_message("I'm already in your voice channel!")
                return
            else:
                await interaction.guild.voice_client.move_to(channel)
                await interaction.response.send_message(f"Moved to {channel.mention}")
                return
        
        try:
            voice_client = await channel.connect()
            self.voice_clients[interaction.guild.id] = voice_client
            await interaction.response.send_message(f"Joined {channel.mention}")
        except Exception as e:
            await interaction.response.send_message(f"Failed to join voice channel: {str(e)}")

    @discord.app_commands.command(name="leave", description="Leave the voice channel")
    async def leave(self, interaction: discord.Interaction):
        """Leave the voice channel"""
        voice_client = interaction.guild.voice_client
        
        if not voice_client:
            await interaction.response.send_message("I'm not in a voice channel!")
            return
        
        # Clear the queue
        queue = self.get_guild_queue(interaction.guild.id)
        queue.clear()
        
        await voice_client.disconnect()
        if interaction.guild.id in self.voice_clients:
            del self.voice_clients[interaction.guild.id]
        
        await interaction.response.send_message("Left the voice channel and cleared the queue.")

    @discord.app_commands.command(name="search", description="Search for songs and get suggestions")
    async def search_songs(self, interaction: discord.Interaction, query: str):
        """Search for songs and show multiple results"""
        await interaction.response.defer()
        
        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                None, 
                lambda: self.ytdl.extract_info(f"ytsearch5:{query} site:soundcloud.com", download=False)
            )
            
            if not data or 'entries' not in data or not data['entries']:
                await interaction.followup.send(f"No results found for '{query}'")
                return
            
            embed = discord.Embed(
                title=f"🔍 Search Results for '{query}'",
                description="Choose a song to play by using `/play` with the exact title",
                color=0xFF5500
            )
            
            for i, entry in enumerate(data['entries'][:5], 1):
                title = entry.get('title', 'Unknown')
                duration = entry.get('duration', 0)
                uploader = entry.get('uploader', 'Unknown')
                
                duration_str = "Unknown"
                if duration:
                    minutes = duration // 60
                    seconds = duration % 60
                    duration_str = f"{minutes}:{seconds:02d}"
                
                embed.add_field(
                    name=f"{i}. {title}",
                    value=f"**Artist:** {uploader}\n**Duration:** {duration_str}",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"Search error: {str(e)}")

    @discord.app_commands.command(name="play", description="Play a song from SoundCloud")
    async def play(self, interaction: discord.Interaction, query: str):
        """Play music from SoundCloud"""
        await interaction.response.defer()
        
        # Check if user is in voice channel
        if not interaction.user.voice:
            await interaction.followup.send("You need to be in a voice channel!")
            return
        
        # Join voice channel if not connected
        if not interaction.guild.voice_client:
            try:
                voice_client = await interaction.user.voice.channel.connect()
                self.voice_clients[interaction.guild.id] = voice_client
            except Exception as e:
                await interaction.followup.send(f"Failed to join voice channel: {str(e)}")
                return
        
        voice_client = interaction.guild.voice_client
        
        # Search for the song
        song_info = await self.search_soundcloud(query)
        if not song_info:
            await interaction.followup.send(f"No results found for '{query}'. Try using `/search` first to see available options.")
            return
        
        # Create song object
        song = Song(
            url=song_info['url'],
            title=song_info['title'],
            duration=song_info['duration'],
            thumbnail=song_info.get('thumbnail'),
            requested_by=interaction.user
        )
        
        # Get queue
        queue = self.get_guild_queue(interaction.guild.id)
        
        # If nothing is playing, play immediately
        if not voice_client.is_playing() and not voice_client.is_paused():
            try:
                source = await self.get_audio_source(song.url)
                if source:
                    voice_client.play(source, after=lambda e: self.play_next(interaction.guild.id) if e else None)
                    queue.current = song
                    
                    embed = discord.Embed(
                        title="🎵 Now Playing",
                        description=f"**{song.title}**",
                        color=0xFF5500
                    )
                    embed.add_field(name="Requested by", value=song.requested_by.mention, inline=True)
                    if song.duration:
                        minutes = song.duration // 60
                        seconds = song.duration % 60
                        embed.add_field(name="Duration", value=f"{minutes}:{seconds:02d}", inline=True)
                    
                    if song.thumbnail:
                        embed.set_thumbnail(url=song.thumbnail)
                    
                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send("Failed to get audio source")
            except Exception as e:
                await interaction.followup.send(f"Error playing song: {str(e)}")
        else:
            # Add to queue
            queue.add(song)
            embed = discord.Embed(
                title="📋 Added to Queue",
                description=f"**{song.title}**",
                color=0x00FF00
            )
            embed.add_field(name="Position in queue", value=f"{queue.size()}", inline=True)
            embed.add_field(name="Requested by", value=song.requested_by.mention, inline=True)
            
            await interaction.followup.send(embed=embed)

    def play_next(self, guild_id):
        """Play the next song in queue"""
        if guild_id not in self.voice_clients:
            return
        
        voice_client = self.voice_clients[guild_id]
        queue = self.get_guild_queue(guild_id)
        
        next_song = queue.get_next()
        if next_song:
            try:
                # This needs to be run in an async context
                asyncio.create_task(self._play_next_song(voice_client, queue, next_song, guild_id))
            except Exception as e:
                print(f"Error playing next song: {e}")

    async def _play_next_song(self, voice_client, queue, song, guild_id):
        """Helper method to play next song"""
        try:
            source = await self.get_audio_source(song.url)
            if source:
                voice_client.play(source, after=lambda e: self.play_next(guild_id) if e else None)
                queue.current = song
        except Exception as e:
            print(f"Error in _play_next_song: {e}")

    @discord.app_commands.command(name="pause", description="Pause the current song")
    async def pause(self, interaction: discord.Interaction):
        """Pause the current song"""
        voice_client = interaction.guild.voice_client
        
        if not voice_client or not voice_client.is_playing():
            await interaction.response.send_message("Nothing is currently playing!")
            return
        
        voice_client.pause()
        await interaction.response.send_message("⏸️ Paused the music")

    @discord.app_commands.command(name="resume", description="Resume the paused song")
    async def resume(self, interaction: discord.Interaction):
        """Resume the paused song"""
        voice_client = interaction.guild.voice_client
        
        if not voice_client or not voice_client.is_paused():
            await interaction.response.send_message("Nothing is paused!")
            return
        
        voice_client.resume()
        await interaction.response.send_message("▶️ Resumed the music")

    @discord.app_commands.command(name="stop", description="Stop the music and clear the queue")
    async def stop(self, interaction: discord.Interaction):
        """Stop the music and clear queue"""
        voice_client = interaction.guild.voice_client
        
        if not voice_client:
            await interaction.response.send_message("I'm not in a voice channel!")
            return
        
        queue = self.get_guild_queue(interaction.guild.id)
        queue.clear()
        queue.current = None
        
        voice_client.stop()
        await interaction.response.send_message("⏹️ Stopped the music and cleared the queue")

    @discord.app_commands.command(name="skip", description="Skip the current song")
    async def skip(self, interaction: discord.Interaction):
        """Skip the current song"""
        voice_client = interaction.guild.voice_client
        
        if not voice_client or not voice_client.is_playing():
            await interaction.response.send_message("Nothing is currently playing!")
            return
        
        voice_client.stop()
        await interaction.response.send_message("⏭️ Skipped the current song")

    @discord.app_commands.command(name="queue", description="Show the current music queue")
    async def show_queue(self, interaction: discord.Interaction):
        """Show the current queue"""
        queue = self.get_guild_queue(interaction.guild.id)
        
        if not queue.current and queue.size() == 0:
            await interaction.response.send_message("The queue is empty!")
            return
        
        embed = discord.Embed(title="🎵 Music Queue", color=0xFF5500)
        
        if queue.current:
            embed.add_field(
                name="🎵 Now Playing",
                value=f"**{queue.current.title}** - {queue.current.requested_by.mention}",
                inline=False
            )
        
        if queue.size() > 0:
            queue_list = []
            for i, song in enumerate(list(queue.queue)[:10], 1):
                queue_list.append(f"{i}. **{song.title}** - {song.requested_by.mention}")
            
            embed.add_field(
                name="📋 Up Next",
                value="\n".join(queue_list) if queue_list else "No songs in queue",
                inline=False
            )
            
            if queue.size() > 10:
                embed.add_field(
                    name="➕ More",
                    value=f"And {queue.size() - 10} more songs...",
                    inline=False
                )
        
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="nowplaying", description="Show information about the current song")
    async def now_playing(self, interaction: discord.Interaction):
        """Show current playing song info"""
        queue = self.get_guild_queue(interaction.guild.id)
        voice_client = interaction.guild.voice_client
        
        if not voice_client or not queue.current:
            await interaction.response.send_message("Nothing is currently playing!")
            return
        
        song = queue.current
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"**{song.title}**",
            color=0xFF5500
        )
        
        embed.add_field(name="Requested by", value=song.requested_by.mention, inline=True)
        
        if song.duration:
            minutes = song.duration // 60
            seconds = song.duration % 60
            embed.add_field(name="Duration", value=f"{minutes}:{seconds:02d}", inline=True)
        
        status = "Playing" if voice_client.is_playing() else "Paused" if voice_client.is_paused() else "Stopped"
        embed.add_field(name="Status", value=status, inline=True)
        
        if song.thumbnail:
            embed.set_thumbnail(url=song.thumbnail)
        
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(SoundCloudMusic(bot))