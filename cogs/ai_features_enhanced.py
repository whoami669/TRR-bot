import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import openai
import base64
import io
import aiohttp
import json
import asyncio
from PIL import Image
import os
import logging
import time
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

class AIConversationManager:
    """Manages AI conversation contexts and memory"""
    def __init__(self, max_context_length: int = 10):
        self.conversations = {}
        self.max_context_length = max_context_length
    
    def get_conversation(self, user_id: int, channel_id: int) -> List[Dict]:
        """Get conversation history for a user in a channel"""
        key = f"{user_id}_{channel_id}"
        return self.conversations.get(key, [])
    
    def add_message(self, user_id: int, channel_id: int, role: str, content: str):
        """Add a message to conversation history"""
        key = f"{user_id}_{channel_id}"
        if key not in self.conversations:
            self.conversations[key] = []
        
        self.conversations[key].append({"role": role, "content": content})
        
        # Keep only the last N messages to prevent token overflow
        if len(self.conversations[key]) > self.max_context_length:
            self.conversations[key] = self.conversations[key][-self.max_context_length:]
    
    def clear_conversation(self, user_id: int, channel_id: int):
        """Clear conversation history"""
        key = f"{user_id}_{channel_id}"
        if key in self.conversations:
            del self.conversations[key]

class AIFeaturesEnhanced(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.conversation_manager = AIConversationManager()
        self.usage_stats = {}
        
    async def log_ai_usage(self, user_id: int, command: str, tokens_used: int = 0):
        """Log AI command usage for analytics"""
        async with aiosqlite.connect('ultrabot.db') as db:
            await db.execute('''
                INSERT OR IGNORE INTO ai_usage 
                (user_id, command_name, tokens_used, timestamp)
                VALUES (?, ?, ?, datetime('now'))
            ''', (user_id, command, tokens_used))
            await db.commit()
    
    @app_commands.command(name="ai", description="Enhanced AI chat with conversation memory")
    @app_commands.describe(
        prompt="Your message to the AI",
        model="AI model to use",
        system="Custom instructions for the AI",
        remember="Whether to remember this conversation",
        temperature="Creativity level (0.0-2.0)"
    )
    @app_commands.choices(model=[
        app_commands.Choice(name="GPT-4o (Latest & Best)", value="gpt-4o"),
        app_commands.Choice(name="GPT-4 Turbo", value="gpt-4-turbo"),
        app_commands.Choice(name="GPT-3.5 Turbo (Faster)", value="gpt-3.5-turbo")
    ])
    async def ai_chat(self, interaction: discord.Interaction, prompt: str, 
                     model: str = "gpt-4o", system: str = None, 
                     remember: bool = True, temperature: float = 0.7):
        await interaction.response.defer()
        
        try:
            # Get conversation history if remembering
            messages = []
            if remember:
                conversation = self.conversation_manager.get_conversation(
                    interaction.user.id, interaction.channel.id
                )
                messages.extend(conversation)
            
            # Add system message
            system_msg = system or f"""You are ChatGPT, an AI assistant integrated into Discord. 
            You're helping {interaction.user.display_name} in the {interaction.guild.name} server.
            Be helpful, concise, and engaging. Format your responses nicely for Discord."""
            
            if not messages or messages[0]["role"] != "system":
                messages.insert(0, {"role": "system", "content": system_msg})
            
            # Add user message
            messages.append({"role": "user", "content": prompt})
            
            # Generate response
            start_time = time.time()
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=2000,
                temperature=max(0.0, min(2.0, temperature))
            )
            response_time = time.time() - start_time
            
            ai_response = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            # Update conversation memory
            if remember:
                self.conversation_manager.add_message(
                    interaction.user.id, interaction.channel.id, "user", prompt
                )
                self.conversation_manager.add_message(
                    interaction.user.id, interaction.channel.id, "assistant", ai_response
                )
            
            # Create enhanced embed
            embed = discord.Embed(
                title="🤖 AI Assistant",
                description=ai_response,
                color=discord.Color.blue(),
                timestamp=interaction.created_at
            )
            embed.set_author(
                name=interaction.user.display_name, 
                icon_url=interaction.user.display_avatar.url
            )
            embed.add_field(
                name="Model", value=model, inline=True
            )
            embed.add_field(
                name="Response Time", value=f"{response_time:.2f}s", inline=True
            )
            embed.add_field(
                name="Tokens Used", value=str(tokens_used), inline=True
            )
            embed.set_footer(text="Powered by OpenAI GPT")
            
            await interaction.followup.send(embed=embed)
            await self.log_ai_usage(interaction.user.id, "ai_chat", tokens_used)
            
        except openai.AuthenticationError:
            await interaction.followup.send("❌ OpenAI authentication failed. Please check the API key.")
        except openai.RateLimitError:
            await interaction.followup.send("⏰ Rate limit exceeded. Please try again later.")
        except Exception as e:
            logger.error(f"AI chat error: {e}")
            await interaction.followup.send("❌ An error occurred while processing your request.")
    
    @app_commands.command(name="ai-clear", description="Clear conversation memory")
    async def clear_conversation(self, interaction: discord.Interaction):
        self.conversation_manager.clear_conversation(
            interaction.user.id, interaction.channel.id
        )
        await interaction.response.send_message(
            "✅ Conversation memory cleared!", ephemeral=True
        )
    
    @app_commands.command(name="analyze-image", description="Analyze images with AI vision")
    @app_commands.describe(
        image="Image to analyze",
        prompt="What you want to know about the image",
        detail="Level of detail in analysis"
    )
    @app_commands.choices(detail=[
        app_commands.Choice(name="High Detail", value="high"),
        app_commands.Choice(name="Low Detail (Faster)", value="low")
    ])
    async def analyze_image(self, interaction: discord.Interaction, 
                           image: discord.Attachment, 
                           prompt: str = "Describe this image in detail",
                           detail: str = "high"):
        await interaction.response.defer()
        
        try:
            if not image.content_type.startswith('image/'):
                await interaction.followup.send("❌ Please provide a valid image file.")
                return
            
            # Download and encode image
            image_data = await image.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": detail
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            analysis = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            embed = discord.Embed(
                title="🔍 Image Analysis",
                description=analysis,
                color=discord.Color.green()
            )
            embed.set_image(url=image.url)
            embed.add_field(name="Detail Level", value=detail.title(), inline=True)
            embed.add_field(name="Tokens Used", value=str(tokens_used), inline=True)
            embed.set_footer(text="Powered by GPT-4 Vision")
            
            await interaction.followup.send(embed=embed)
            await self.log_ai_usage(interaction.user.id, "image_analysis", tokens_used)
            
        except Exception as e:
            logger.error(f"Image analysis error: {e}")
            await interaction.followup.send("❌ Failed to analyze image. Please try again.")
    
    @app_commands.command(name="generate-image", description="Generate images with DALL-E")
    @app_commands.describe(
        prompt="Description of the image to generate",
        size="Image size",
        style="Art style",
        quality="Image quality"
    )
    @app_commands.choices(
        size=[
            app_commands.Choice(name="Square (1024x1024)", value="1024x1024"),
            app_commands.Choice(name="Portrait (1024x1792)", value="1024x1792"),
            app_commands.Choice(name="Landscape (1792x1024)", value="1792x1024")
        ],
        style=[
            app_commands.Choice(name="Vivid", value="vivid"),
            app_commands.Choice(name="Natural", value="natural")
        ],
        quality=[
            app_commands.Choice(name="Standard", value="standard"),
            app_commands.Choice(name="HD", value="hd")
        ]
    )
    async def generate_image(self, interaction: discord.Interaction, 
                           prompt: str, size: str = "1024x1024",
                           style: str = "vivid", quality: str = "standard"):
        await interaction.response.defer()
        
        try:
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality=quality,
                style=style,
                n=1
            )
            
            image_url = response.data[0].url
            revised_prompt = getattr(response.data[0], 'revised_prompt', prompt)
            
            embed = discord.Embed(
                title="🎨 Generated Image",
                description=f"**Original Prompt:** {prompt}",
                color=discord.Color.purple()
            )
            embed.set_image(url=image_url)
            embed.add_field(name="Size", value=size, inline=True)
            embed.add_field(name="Style", value=style.title(), inline=True)
            embed.add_field(name="Quality", value=quality.upper(), inline=True)
            
            if revised_prompt != prompt:
                embed.add_field(
                    name="Revised Prompt", 
                    value=revised_prompt[:1000] + "..." if len(revised_prompt) > 1000 else revised_prompt,
                    inline=False
                )
            
            embed.set_footer(text="Generated by DALL-E 3")
            
            await interaction.followup.send(embed=embed)
            await self.log_ai_usage(interaction.user.id, "image_generation")
            
        except Exception as e:
            logger.error(f"Image generation error: {e}")
            await interaction.followup.send("❌ Failed to generate image. Please try again.")
    
    @app_commands.command(name="code-review", description="Get AI code review and suggestions")
    @app_commands.describe(
        code="Code to review",
        language="Programming language",
        focus="What to focus on in the review"
    )
    async def code_review(self, interaction: discord.Interaction, 
                         code: str, language: str = "auto-detect",
                         focus: str = "general quality and best practices"):
        await interaction.response.defer()
        
        try:
            prompt = f"""Please review this {language} code focusing on {focus}:

```{language}
{code}
```

Provide:
1. Overall assessment
2. Specific issues found
3. Suggestions for improvement
4. Best practices recommendations

Format your response clearly for Discord."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert code reviewer. Provide constructive, detailed feedback."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500
            )
            
            review = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            embed = discord.Embed(
                title="🔍 Code Review",
                description=review,
                color=discord.Color.orange()
            )
            embed.add_field(name="Language", value=language, inline=True)
            embed.add_field(name="Focus", value=focus, inline=True)
            embed.add_field(name="Tokens Used", value=str(tokens_used), inline=True)
            embed.set_footer(text="AI Code Review • Use responsibly")
            
            await interaction.followup.send(embed=embed)
            await self.log_ai_usage(interaction.user.id, "code_review", tokens_used)
            
        except Exception as e:
            logger.error(f"Code review error: {e}")
            await interaction.followup.send("❌ Failed to review code. Please try again.")
    
    @app_commands.command(name="ai-stats", description="View your AI usage statistics")
    async def ai_stats(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            async with aiosqlite.connect('ultrabot.db') as db:
                # Get user stats
                async with db.execute('''
                    SELECT command_name, COUNT(*) as count, SUM(tokens_used) as total_tokens
                    FROM ai_usage 
                    WHERE user_id = ?
                    GROUP BY command_name
                ''', (interaction.user.id,)) as cursor:
                    stats = await cursor.fetchall()
                
                if not stats:
                    await interaction.followup.send("📊 No AI usage found for your account.")
                    return
                
                embed = discord.Embed(
                    title="📊 Your AI Usage Statistics",
                    color=discord.Color.blue()
                )
                
                total_commands = sum(stat[1] for stat in stats)
                total_tokens = sum(stat[2] for stat in stats)
                
                embed.add_field(
                    name="Total Commands", value=f"{total_commands:,}", inline=True
                )
                embed.add_field(
                    name="Total Tokens", value=f"{total_tokens:,}", inline=True
                )
                
                for command, count, tokens in stats:
                    embed.add_field(
                        name=command.replace('_', ' ').title(),
                        value=f"{count} uses • {tokens:,} tokens",
                        inline=True
                    )
                
                await interaction.followup.send(embed=embed)
                
        except Exception as e:
            logger.error(f"AI stats error: {e}")
            await interaction.followup.send("❌ Failed to retrieve statistics.")

async def setup(bot):
    # Create AI usage table
    async with aiosqlite.connect('ultrabot.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS ai_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                command_name TEXT NOT NULL,
                tokens_used INTEGER DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()
    
    await bot.add_cog(AIFeaturesEnhanced(bot))