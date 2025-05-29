import discord
from discord.ext import commands
import asyncio
import youtube_dl
import os
from utils.embeds import create_embed

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

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
        self.thumbnail = data.get('thumbnail')

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
        self.queue = []
        self.current = None
        self.volume = 0.5
        self.loop_song = False
        self.loop_queue = False

    def add_to_queue(self, source):
        self.queue.append(source)

    def get_queue(self):
        return self.queue

    def clear_queue(self):
        self.queue = []

    def shuffle_queue(self):
        import random
        random.shuffle(self.queue)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players = {}

    def get_player(self, guild_id):
        if guild_id not in self.players:
            self.players[guild_id] = MusicPlayer(self.bot)
        return self.players[guild_id]

    @commands.command(name='join')
    async def join_voice(self, ctx):
        """Join the voice channel"""
        if not ctx.author.voice:
            return await ctx.send("❌ You need to be in a voice channel!")

        channel = ctx.author.voice.channel
        
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()

        embed = create_embed(
            title="🎵 Joined Voice Channel",
            description=f"Connected to {channel.name}",
            color=0x00FF00
        )
        await ctx.send(embed=embed)

    @commands.command(name='leave')
    async def leave_voice(self, ctx):
        """Leave the voice channel"""
        if not ctx.voice_client:
            return await ctx.send("❌ I'm not connected to a voice channel!")

        await ctx.voice_client.disconnect()
        
        # Clear the player
        if ctx.guild.id in self.players:
            self.players[ctx.guild.id].clear_queue()

        embed = create_embed(
            title="👋 Left Voice Channel",
            description="Disconnected from voice channel",
            color=0xFF0000
        )
        await ctx.send(embed=embed)

    @commands.command(name='play')
    async def play_music(self, ctx, *, search):
        """Play music from YouTube"""
        if not ctx.author.voice:
            return await ctx.send("❌ You need to be in a voice channel!")

        if not ctx.voice_client:
            await ctx.invoke(self.join_voice)

        player = self.get_player(ctx.guild.id)

        async with ctx.typing():
            try:
                source = await YTDLSource.from_url(search, loop=self.bot.loop, stream=True)
                player.add_to_queue(source)

                if not ctx.voice_client.is_playing():
                    await self.play_next(ctx)
                else:
                    embed = create_embed(
                        title="📝 Added to Queue",
                        description=f"**{source.title}** has been added to the queue",
                        color=0x7289DA
                    )
                    embed.add_field(name="Position", value=str(len(player.queue)), inline=True)
                    embed.add_field(name="Requested by", value=ctx.author.mention, inline=True)
                    if source.thumbnail:
                        embed.set_thumbnail(url=source.thumbnail)
                    await ctx.send(embed=embed)

            except Exception as e:
                await ctx.send(f"❌ An error occurred: {str(e)}")

    async def play_next(self, ctx):
        """Play the next song in queue"""
        player = self.get_player(ctx.guild.id)
        
        if not player.queue:
            return

        source = player.queue.pop(0)
        player.current = source

        def after_playing(error):
            if error:
                print(f'Player error: {error}')
            
            # Schedule the next song
            coro = self.handle_next_song(ctx, player)
            fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
            try:
                fut.result()
            except:
                pass

        ctx.voice_client.play(source, after=after_playing)

        embed = create_embed(
            title="🎵 Now Playing",
            description=f"**{source.title}**",
            color=0x00FF00
        )
        embed.add_field(name="Volume", value=f"{int(source.volume * 100)}%", inline=True)
        embed.add_field(name="Queue Length", value=str(len(player.queue)), inline=True)
        if source.thumbnail:
            embed.set_thumbnail(url=source.thumbnail)
        
        await ctx.send(embed=embed)

    async def handle_next_song(self, ctx, player):
        """Handle what happens after a song finishes"""
        if player.loop_song and player.current:
            # Re-add current song to front of queue
            player.queue.insert(0, player.current)
        elif player.loop_queue and player.current:
            # Add current song to end of queue
            player.queue.append(player.current)

        if player.queue:
            await self.play_next(ctx)

    @commands.command(name='pause')
    async def pause_music(self, ctx):
        """Pause the current song"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            embed = create_embed(
                title="⏸️ Music Paused",
                description="The music has been paused",
                color=0xFFA500
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Nothing is currently playing!")

    @commands.command(name='resume')
    async def resume_music(self, ctx):
        """Resume the current song"""
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            embed = create_embed(
                title="▶️ Music Resumed",
                description="The music has been resumed",
                color=0x00FF00
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Nothing is currently paused!")

    @commands.command(name='stop')
    async def stop_music(self, ctx):
        """Stop the music and clear the queue"""
        if ctx.voice_client:
            player = self.get_player(ctx.guild.id)
            player.clear_queue()
            ctx.voice_client.stop()
            
            embed = create_embed(
                title="⏹️ Music Stopped",
                description="Music stopped and queue cleared",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Nothing is currently playing!")

    @commands.command(name='skip')
    async def skip_song(self, ctx):
        """Skip the current song"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            embed = create_embed(
                title="⏭️ Song Skipped",
                description="Skipped to the next song",
                color=0x7289DA
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Nothing is currently playing!")

    @commands.command(name='queue')
    async def show_queue(self, ctx):
        """Show the current music queue"""
        player = self.get_player(ctx.guild.id)
        
        if not player.queue and not player.current:
            return await ctx.send("❌ The queue is empty!")

        embed = create_embed(
            title="🎵 Music Queue",
            color=0x7289DA
        )

        if player.current:
            embed.add_field(
                name="🎵 Now Playing",
                value=f"**{player.current.title}**",
                inline=False
            )

        if player.queue:
            queue_list = []
            for i, song in enumerate(player.queue[:10], 1):  # Show first 10 songs
                queue_list.append(f"{i}. **{song.title}**")
            
            embed.add_field(
                name="📝 Up Next",
                value="\n".join(queue_list),
                inline=False
            )

            if len(player.queue) > 10:
                embed.add_field(
                    name="And More...",
                    value=f"+{len(player.queue) - 10} more songs",
                    inline=False
                )

        await ctx.send(embed=embed)

    @commands.command(name='volume')
    async def set_volume(self, ctx, volume: int):
        """Set the music volume (0-100)"""
        if not ctx.voice_client:
            return await ctx.send("❌ I'm not connected to a voice channel!")

        if not 0 <= volume <= 100:
            return await ctx.send("❌ Volume must be between 0 and 100!")

        player = self.get_player(ctx.guild.id)
        
        if ctx.voice_client.source:
            ctx.voice_client.source.volume = volume / 100
            player.volume = volume / 100

        embed = create_embed(
            title="🔊 Volume Changed",
            description=f"Volume set to {volume}%",
            color=0x7289DA
        )
        await ctx.send(embed=embed)

    @commands.command(name='shuffle')
    async def shuffle_queue(self, ctx):
        """Shuffle the music queue"""
        player = self.get_player(ctx.guild.id)
        
        if not player.queue:
            return await ctx.send("❌ The queue is empty!")

        player.shuffle_queue()
        
        embed = create_embed(
            title="🔀 Queue Shuffled",
            description="The music queue has been shuffled",
            color=0x7289DA
        )
        await ctx.send(embed=embed)

    @commands.command(name='loop')
    async def toggle_loop(self, ctx, mode="song"):
        """Toggle loop mode (song/queue/off)"""
        player = self.get_player(ctx.guild.id)
        
        if mode.lower() == "song":
            player.loop_song = not player.loop_song
            player.loop_queue = False
            status = "enabled" if player.loop_song else "disabled"
            embed = create_embed(
                title="🔂 Song Loop",
                description=f"Song loop {status}",
                color=0x7289DA
            )
        elif mode.lower() == "queue":
            player.loop_queue = not player.loop_queue
            player.loop_song = False
            status = "enabled" if player.loop_queue else "disabled"
            embed = create_embed(
                title="🔁 Queue Loop",
                description=f"Queue loop {status}",
                color=0x7289DA
            )
        else:
            player.loop_song = False
            player.loop_queue = False
            embed = create_embed(
                title="⏹️ Loop Disabled",
                description="All loop modes disabled",
                color=0x7289DA
            )

        await ctx.send(embed=embed)

    @commands.command(name='nowplaying', aliases=['np'])
    async def now_playing(self, ctx):
        """Show the currently playing song"""
        player = self.get_player(ctx.guild.id)
        
        if not player.current:
            return await ctx.send("❌ Nothing is currently playing!")

        embed = create_embed(
            title="🎵 Now Playing",
            description=f"**{player.current.title}**",
            color=0x00FF00
        )
        embed.add_field(name="Volume", value=f"{int(player.current.volume * 100)}%", inline=True)
        embed.add_field(name="Queue Length", value=str(len(player.queue)), inline=True)
        
        loop_status = "🔂 Song" if player.loop_song else "🔁 Queue" if player.loop_queue else "❌ Off"
        embed.add_field(name="Loop", value=loop_status, inline=True)
        
        if player.current.thumbnail:
            embed.set_thumbnail(url=player.current.thumbnail)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Music(bot))
