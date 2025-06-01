import discord
from discord.ext import commands
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
import aiosqlite
import asyncio
from datetime import datetime
import json


class SpotifyIntegration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spotify = None
        self.init_spotify()
    
    def init_spotify(self):
        """Initialize Spotify client with credentials"""
        try:
            client_id = "e23060a32a444332a4d7eee418966156"
            client_secret = "00a6524cb1d34d18bca772563d3f33f0"
            
            if client_id and client_secret:
                client_credentials_manager = SpotifyClientCredentials(
                    client_id=client_id,
                    client_secret=client_secret
                )
                self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        except Exception as e:
            print(f"Spotify initialization error: {e}")

    @discord.app_commands.command(name="search_song", description="Search for a song on Spotify")
    async def search_song(self, interaction: discord.Interaction, query: str, limit: int = 5):
        """Search for songs on Spotify"""
        if not self.spotify:
            await interaction.response.send_message("Spotify integration is not available.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            results = self.spotify.search(q=query, type='track', limit=limit)
            tracks = results['tracks']['items']
            
            if not tracks:
                await interaction.followup.send(f"No songs found for '{query}'")
                return
            
            embed = discord.Embed(
                title=f"🎵 Search Results for '{query}'",
                color=0x1DB954
            )
            
            for i, track in enumerate(tracks, 1):
                artists = ", ".join([artist['name'] for artist in track['artists']])
                duration_ms = track['duration_ms']
                duration = f"{duration_ms // 60000}:{(duration_ms % 60000) // 1000:02d}"
                
                embed.add_field(
                    name=f"{i}. {track['name']}",
                    value=f"**Artist:** {artists}\n**Album:** {track['album']['name']}\n**Duration:** {duration}\n[Open in Spotify]({track['external_urls']['spotify']})",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"Error searching for songs: {str(e)}")

    @discord.app_commands.command(name="search_artist", description="Search for an artist on Spotify")
    async def search_artist(self, interaction: discord.Interaction, artist_name: str):
        """Search for artists on Spotify"""
        if not self.spotify:
            await interaction.response.send_message("Spotify integration is not available.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            results = self.spotify.search(q=artist_name, type='artist', limit=5)
            artists = results['artists']['items']
            
            if not artists:
                await interaction.followup.send(f"No artists found for '{artist_name}'")
                return
            
            embed = discord.Embed(
                title=f"🎤 Artist Search Results for '{artist_name}'",
                color=0x1DB954
            )
            
            for i, artist in enumerate(artists, 1):
                followers = artist['followers']['total']
                genres = ", ".join(artist['genres'][:3]) if artist['genres'] else "No genres listed"
                
                embed.add_field(
                    name=f"{i}. {artist['name']}",
                    value=f"**Followers:** {followers:,}\n**Genres:** {genres}\n**Popularity:** {artist['popularity']}/100\n[Open in Spotify]({artist['external_urls']['spotify']})",
                    inline=False
                )
                
                if artist['images']:
                    embed.set_thumbnail(url=artist['images'][0]['url'])
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"Error searching for artists: {str(e)}")

    @discord.app_commands.command(name="artist_top_tracks", description="Get top tracks for an artist")
    async def artist_top_tracks(self, interaction: discord.Interaction, artist_name: str, country: str = "US"):
        """Get top tracks for an artist"""
        if not self.spotify:
            await interaction.response.send_message("Spotify integration is not available.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            # First search for the artist
            artist_results = self.spotify.search(q=artist_name, type='artist', limit=1)
            if not artist_results['artists']['items']:
                await interaction.followup.send(f"Artist '{artist_name}' not found")
                return
            
            artist = artist_results['artists']['items'][0]
            artist_id = artist['id']
            
            # Get top tracks
            top_tracks = self.spotify.artist_top_tracks(artist_id, country=country)
            tracks = top_tracks['tracks']
            
            if not tracks:
                await interaction.followup.send(f"No top tracks found for {artist['name']}")
                return
            
            embed = discord.Embed(
                title=f"🔥 Top Tracks for {artist['name']}",
                color=0x1DB954
            )
            
            if artist['images']:
                embed.set_thumbnail(url=artist['images'][0]['url'])
            
            for i, track in enumerate(tracks[:10], 1):
                duration_ms = track['duration_ms']
                duration = f"{duration_ms // 60000}:{(duration_ms % 60000) // 1000:02d}"
                
                embed.add_field(
                    name=f"{i}. {track['name']}",
                    value=f"**Album:** {track['album']['name']}\n**Duration:** {duration}\n**Popularity:** {track['popularity']}/100\n[Listen on Spotify]({track['external_urls']['spotify']})",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"Error getting top tracks: {str(e)}")

    @discord.app_commands.command(name="album_info", description="Get information about an album")
    async def album_info(self, interaction: discord.Interaction, album_name: str, artist_name: str = ""):
        """Get album information"""
        if not self.spotify:
            await interaction.response.send_message("Spotify integration is not available.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            search_query = f"{album_name}"
            if artist_name:
                search_query += f" artist:{artist_name}"
            
            results = self.spotify.search(q=search_query, type='album', limit=1)
            
            if not results['albums']['items']:
                await interaction.followup.send(f"Album '{album_name}' not found")
                return
            
            album = results['albums']['items'][0]
            artists = ", ".join([artist['name'] for artist in album['artists']])
            
            embed = discord.Embed(
                title=f"💿 {album['name']}",
                description=f"**Artists:** {artists}",
                color=0x1DB954
            )
            
            if album['images']:
                embed.set_thumbnail(url=album['images'][0]['url'])
            
            embed.add_field(name="Release Date", value=album['release_date'], inline=True)
            embed.add_field(name="Total Tracks", value=album['total_tracks'], inline=True)
            embed.add_field(name="Album Type", value=album['album_type'].title(), inline=True)
            
            if album['genres']:
                embed.add_field(name="Genres", value=", ".join(album['genres']), inline=False)
            
            embed.add_field(
                name="Spotify Link", 
                value=f"[Open in Spotify]({album['external_urls']['spotify']})", 
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"Error getting album info: {str(e)}")

    @discord.app_commands.command(name="music_recommendations", description="Get music recommendations based on genres")
    async def music_recommendations(self, interaction: discord.Interaction, 
                                  genres: str, limit: int = 10, popularity: int = 50):
        """Get music recommendations"""
        if not self.spotify:
            await interaction.response.send_message("Spotify integration is not available.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            genre_list = [genre.strip().lower() for genre in genres.split(',')]
            
            recommendations = self.spotify.recommendations(
                seed_genres=genre_list[:5],  # Spotify allows max 5 seed genres
                limit=limit,
                target_popularity=popularity
            )
            
            tracks = recommendations['tracks']
            
            if not tracks:
                await interaction.followup.send(f"No recommendations found for genres: {genres}")
                return
            
            embed = discord.Embed(
                title=f"🎯 Music Recommendations",
                description=f"Based on genres: {', '.join(genre_list)}",
                color=0x1DB954
            )
            
            for i, track in enumerate(tracks, 1):
                artists = ", ".join([artist['name'] for artist in track['artists']])
                duration_ms = track['duration_ms']
                duration = f"{duration_ms // 60000}:{(duration_ms % 60000) // 1000:02d}"
                
                embed.add_field(
                    name=f"{i}. {track['name']}",
                    value=f"**Artist:** {artists}\n**Duration:** {duration}\n[Listen]({track['external_urls']['spotify']})",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"Error getting recommendations: {str(e)}")

    @discord.app_commands.command(name="spotify_genres", description="List available Spotify genres for recommendations")
    async def spotify_genres(self, interaction: discord.Interaction):
        """List available genres"""
        if not self.spotify:
            await interaction.response.send_message("Spotify integration is not available.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            genres = self.spotify.recommendation_genre_seeds()
            genre_list = genres['genres']
            
            # Split genres into chunks for better display
            chunks = [genre_list[i:i+15] for i in range(0, len(genre_list), 15)]
            
            embed = discord.Embed(
                title="🎵 Available Spotify Genres",
                description="Use these genres with the `/music_recommendations` command",
                color=0x1DB954
            )
            
            for i, chunk in enumerate(chunks, 1):
                embed.add_field(
                    name=f"Genres {i}",
                    value=", ".join(chunk),
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"Error getting genres: {str(e)}")

    @discord.app_commands.command(name="track_features", description="Get audio features for a track")
    async def track_features(self, interaction: discord.Interaction, song_name: str, artist_name: str = ""):
        """Get track audio features"""
        if not self.spotify:
            await interaction.response.send_message("Spotify integration is not available.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            search_query = song_name
            if artist_name:
                search_query += f" artist:{artist_name}"
            
            results = self.spotify.search(q=search_query, type='track', limit=1)
            
            if not results['tracks']['items']:
                await interaction.followup.send(f"Track '{song_name}' not found")
                return
            
            track = results['tracks']['items'][0]
            track_id = track['id']
            
            # Get audio features
            features = self.spotify.audio_features([track_id])[0]
            
            if not features:
                await interaction.followup.send("Audio features not available for this track")
                return
            
            artists = ", ".join([artist['name'] for artist in track['artists']])
            
            embed = discord.Embed(
                title=f"🎼 Audio Features",
                description=f"**{track['name']}** by {artists}",
                color=0x1DB954
            )
            
            if track['album']['images']:
                embed.set_thumbnail(url=track['album']['images'][0]['url'])
            
            # Create feature bars
            def create_bar(value, max_val=1.0):
                filled = int((value / max_val) * 10)
                return "█" * filled + "░" * (10 - filled)
            
            embed.add_field(
                name="Energy", 
                value=f"{create_bar(features['energy'])} {features['energy']:.2f}",
                inline=True
            )
            embed.add_field(
                name="Danceability", 
                value=f"{create_bar(features['danceability'])} {features['danceability']:.2f}",
                inline=True
            )
            embed.add_field(
                name="Valence (Mood)", 
                value=f"{create_bar(features['valence'])} {features['valence']:.2f}",
                inline=True
            )
            embed.add_field(
                name="Acousticness", 
                value=f"{create_bar(features['acousticness'])} {features['acousticness']:.2f}",
                inline=True
            )
            embed.add_field(
                name="Instrumentalness", 
                value=f"{create_bar(features['instrumentalness'])} {features['instrumentalness']:.2f}",
                inline=True
            )
            embed.add_field(
                name="Speechiness", 
                value=f"{create_bar(features['speechiness'])} {features['speechiness']:.2f}",
                inline=True
            )
            
            # Additional info
            embed.add_field(
                name="Key", 
                value=f"{features['key']}", 
                inline=True
            )
            embed.add_field(
                name="Tempo", 
                value=f"{features['tempo']:.0f} BPM", 
                inline=True
            )
            embed.add_field(
                name="Loudness", 
                value=f"{features['loudness']:.1f} dB", 
                inline=True
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"Error getting track features: {str(e)}")


async def setup(bot):
    await bot.add_cog(SpotifyIntegration(bot))