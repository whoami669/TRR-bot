import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import asyncio
import random
from datetime import datetime, timezone, timedelta
from typing import Optional

class Giveaways(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'giveaways.db'
        
    async def init_database(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS giveaways (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    host_id INTEGER NOT NULL,
                    prize TEXT NOT NULL,
                    winners INTEGER NOT NULL,
                    ends_at TIMESTAMP NOT NULL,
                    ended BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS giveaway_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    giveaway_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    entered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(giveaway_id, user_id),
                    FOREIGN KEY (giveaway_id) REFERENCES giveaways (id)
                )
            ''')
            await db.commit()

    async def cog_load(self):
        await self.init_database()
        self.bot.loop.create_task(self.check_giveaways())

    async def check_giveaways(self):
        while not self.bot.is_closed():
            await asyncio.sleep(30)  # Check every 30 seconds
            
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    SELECT * FROM giveaways 
                    WHERE ended = FALSE AND ends_at <= ?
                ''', (datetime.now(timezone.utc).isoformat(),))
                expired_giveaways = await cursor.fetchall()
                
                for giveaway in expired_giveaways:
                    await self.end_giveaway(giveaway)

    @app_commands.command(name="gstart", description="Start a giveaway")
    @app_commands.describe(
        duration="Duration (e.g., 1h, 2d, 1w)",
        winners="Number of winners",
        prize="Prize description"
    )
    @commands.has_permissions(manage_guild=True)
    async def gstart(self, interaction: discord.Interaction, duration: str, winners: int, prize: str):
        await interaction.response.defer()
        
        # Parse duration
        duration_map = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400, 'w': 604800}
        time_unit = duration[-1].lower()
        
        if time_unit not in duration_map:
            await interaction.followup.send("Invalid duration format. Use: 1h, 2d, 1w, etc.")
            return
        
        try:
            time_amount = int(duration[:-1])
            total_seconds = time_amount * duration_map[time_unit]
            ends_at = datetime.now(timezone.utc) + timedelta(seconds=total_seconds)
        except ValueError:
            await interaction.followup.send("Invalid duration format")
            return
        
        if winners < 1:
            await interaction.followup.send("Number of winners must be at least 1")
            return
        
        embed = discord.Embed(
            title="🎉 GIVEAWAY 🎉",
            description=f"**Prize:** {prize}\n**Winners:** {winners}\n**Ends:** <t:{int(ends_at.timestamp())}:R>",
            color=0xf39c12
        )
        embed.add_field(name="How to Enter", value="React with 🎉 to enter!", inline=False)
        embed.set_footer(text=f"Hosted by {interaction.user.display_name}")
        
        message = await interaction.followup.send(embed=embed)
        await message.add_reaction("🎉")
        
        # Store giveaway in database
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO giveaways 
                (guild_id, channel_id, message_id, host_id, prize, winners, ends_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (interaction.guild_id, interaction.channel_id, message.id, 
                  interaction.user.id, prize, winners, ends_at.isoformat()))
            await db.commit()

    @app_commands.command(name="gend", description="End a giveaway early")
    @app_commands.describe(message_id="Message ID of the giveaway")
    @commands.has_permissions(manage_guild=True)
    async def gend(self, interaction: discord.Interaction, message_id: str):
        await interaction.response.defer()
        
        try:
            msg_id = int(message_id)
        except ValueError:
            await interaction.followup.send("Invalid message ID")
            return
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT * FROM giveaways 
                WHERE message_id = ? AND guild_id = ? AND ended = FALSE
            ''', (msg_id, interaction.guild_id))
            giveaway = await cursor.fetchone()
            
            if not giveaway:
                await interaction.followup.send("Giveaway not found or already ended")
                return
            
            await self.end_giveaway(giveaway)
            await interaction.followup.send("Giveaway ended!")

    async def end_giveaway(self, giveaway_data):
        guild_id, channel_id, message_id = giveaway_data[1], giveaway_data[2], giveaway_data[3]
        host_id, prize, winners_count = giveaway_data[4], giveaway_data[5], giveaway_data[6]
        
        try:
            guild = self.bot.get_guild(guild_id)
            channel = guild.get_channel(channel_id)
            message = await channel.fetch_message(message_id)
            
            # Get all entries
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    SELECT user_id FROM giveaway_entries WHERE giveaway_id = ?
                ''', (giveaway_data[0],))
                entries = await cursor.fetchall()
                
                # Mark as ended
                await db.execute('''
                    UPDATE giveaways SET ended = TRUE WHERE id = ?
                ''', (giveaway_data[0],))
                await db.commit()
            
            if not entries:
                embed = discord.Embed(
                    title="🎉 Giveaway Ended",
                    description=f"**Prize:** {prize}\n**Winners:** No valid entries",
                    color=0xe74c3c
                )
            else:
                # Select winners
                entry_ids = [entry[0] for entry in entries]
                winners = random.sample(entry_ids, min(winners_count, len(entry_ids)))
                
                winner_mentions = []
                for winner_id in winners:
                    user = guild.get_member(winner_id)
                    if user:
                        winner_mentions.append(user.mention)
                
                embed = discord.Embed(
                    title="🎉 Giveaway Ended",
                    description=f"**Prize:** {prize}\n**Winners:** {', '.join(winner_mentions) if winner_mentions else 'No valid winners'}",
                    color=0x2ecc71
                )
            
            embed.set_footer(text=f"Hosted by {guild.get_member(host_id)}")
            await message.edit(embed=embed)
            
            if winner_mentions:
                await channel.send(f"Congratulations {', '.join(winner_mentions)}! You won **{prize}**!")
        
        except Exception:
            pass  # Handle silently if message/channel is deleted

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id or str(payload.emoji) != "🎉":
            return
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT id FROM giveaways 
                WHERE message_id = ? AND guild_id = ? AND ended = FALSE
            ''', (payload.message_id, payload.guild_id))
            giveaway = await cursor.fetchone()
            
            if giveaway:
                try:
                    await db.execute('''
                        INSERT INTO giveaway_entries (giveaway_id, user_id)
                        VALUES (?, ?)
                    ''', (giveaway[0], payload.user_id))
                    await db.commit()
                except aiosqlite.IntegrityError:
                    pass  # User already entered

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.user_id == self.bot.user.id or str(payload.emoji) != "🎉":
            return
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT id FROM giveaways 
                WHERE message_id = ? AND guild_id = ? AND ended = FALSE
            ''', (payload.message_id, payload.guild_id))
            giveaway = await cursor.fetchone()
            
            if giveaway:
                await db.execute('''
                    DELETE FROM giveaway_entries 
                    WHERE giveaway_id = ? AND user_id = ?
                ''', (giveaway[0], payload.user_id))
                await db.commit()

    @app_commands.command(name="glist", description="List active giveaways")
    async def glist(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT prize, winners, ends_at, channel_id, message_id 
                FROM giveaways 
                WHERE guild_id = ? AND ended = FALSE
                ORDER BY ends_at ASC
            ''', (interaction.guild_id,))
            giveaways = await cursor.fetchall()
        
        if not giveaways:
            await interaction.followup.send("No active giveaways")
            return
        
        embed = discord.Embed(
            title="🎉 Active Giveaways",
            color=0xf39c12
        )
        
        for prize, winners, ends_at, channel_id, message_id in giveaways:
            end_time = datetime.fromisoformat(ends_at.replace('Z', '+00:00'))
            channel = interaction.guild.get_channel(channel_id)
            channel_name = channel.mention if channel else "Unknown Channel"
            
            embed.add_field(
                name=prize,
                value=f"Winners: {winners}\nEnds: <t:{int(end_time.timestamp())}:R>\nChannel: {channel_name}",
                inline=True
            )
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Giveaways(bot))