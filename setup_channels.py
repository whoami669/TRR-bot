import discord
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def setup_channels():
    """Setup the three channels in the specified category"""
    
    # Bot setup
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        print(f'Logged in as {client.user}')
        
        # Your specific category ID
        category_id = 1377685666972041296
        
        # Find the guild (assuming bot is in one guild)
        guild = client.guilds[0]
        print(f"Working in guild: {guild.name}")
        
        # Get the category
        category = guild.get_channel(category_id)
        if not category:
            print(f"Category with ID {category_id} not found!")
            await client.close()
            return
        
        print(f"Found category: {category.name}")
        
        # Channels to create
        channels_to_create = [
            ("welcome", "👋 New members join here"),
            ("boosts", "🚀 Server boosts celebrated here"), 
            ("leaves", "👋 Member departures logged here")
        ]
        
        # Check existing channels
        existing_channels = {channel.name: channel for channel in category.channels}
        
        for channel_name, topic in channels_to_create:
            if channel_name not in existing_channels:
                try:
                    new_channel = await guild.create_text_channel(
                        name=channel_name,
                        category=category,
                        topic=topic
                    )
                    print(f"✅ Created #{channel_name} channel")
                except discord.Forbidden:
                    print(f"❌ Missing permissions to create #{channel_name}")
                except Exception as e:
                    print(f"❌ Error creating #{channel_name}: {e}")
            else:
                print(f"📋 #{channel_name} already exists")
        
        print("Channel setup complete!")
        await client.close()
    
    # Start the bot
    await client.start(os.getenv('DISCORD_TOKEN'))

if __name__ == "__main__":
    asyncio.run(setup_channels())