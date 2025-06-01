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
from collections import defaultdict

logger = logging.getLogger(__name__)

class AIConversationManager:
    """Enhanced conversation memory system"""
    def __init__(self, max_context_length: int = 8):
        self.conversations = {}
        self.max_context_length = max_context_length
    
    def get_conversation(self, user_id: int, channel_id: int) -> List[Dict]:
        key = f"{user_id}_{channel_id}"
        return self.conversations.get(key, [])
    
    def add_message(self, user_id: int, channel_id: int, role: str, content: str):
        key = f"{user_id}_{channel_id}"
        if key not in self.conversations:
            self.conversations[key] = []
        
        self.conversations[key].append({"role": role, "content": content})
        
        if len(self.conversations[key]) > self.max_context_length:
            self.conversations[key] = self.conversations[key][-self.max_context_length:]
    
    def clear_conversation(self, user_id: int, channel_id: int):
        key = f"{user_id}_{channel_id}"
        if key in self.conversations:
            del self.conversations[key]

class AIFeatures(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.conversation_manager = AIConversationManager()
        self.usage_tracker = defaultdict(int)
    
    # AI Chat Commands
    async def log_usage(self, user_id: int, command: str, tokens: int = 0):
        """Track AI usage for analytics"""
        try:
            async with aiosqlite.connect('ultrabot.db') as db:
                await db.execute('''
                    INSERT OR IGNORE INTO ai_usage 
                    (user_id, command_name, tokens_used, timestamp)
                    VALUES (?, ?, ?, datetime('now'))
                ''', (user_id, command, tokens))
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to log usage: {e}")

    @app_commands.command(name="ai", description="Enhanced AI chat with conversation memory")
    @app_commands.describe(
        prompt="Your message to the AI",
        model="AI model to use",
        system="Custom instructions for the AI",
        remember="Remember this conversation for context"
    )
    @app_commands.choices(model=[
        app_commands.Choice(name="GPT-4o (Latest & Best)", value="gpt-4o"),
        app_commands.Choice(name="GPT-4 Turbo", value="gpt-4-turbo"),
        app_commands.Choice(name="GPT-3.5 Turbo (Faster)", value="gpt-3.5-turbo")
    ])
    async def ai(self, interaction: discord.Interaction, prompt: str, 
                 model: str = "gpt-4o", system: str = None, remember: bool = True):
        await interaction.response.defer()
        
        try:
            # Build conversation with memory
            messages = []
            if remember:
                conversation = self.conversation_manager.get_conversation(
                    interaction.user.id, interaction.channel.id
                )
                messages.extend(conversation)
            
            # Add system message if not present
            system_msg = system or f"""You are ChatGPT, an AI assistant integrated into Discord. 
            You're helping {interaction.user.display_name} in the {interaction.guild.name} server.
            Be helpful, concise, and engaging. Format responses nicely for Discord."""
            
            if not messages or messages[0]["role"] != "system":
                messages.insert(0, {"role": "system", "content": system_msg})
            
            messages.append({"role": "user", "content": prompt})
            
            # Generate response with timing
            start_time = time.time()
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=2000,
                temperature=0.7
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
            
            # Enhanced embed with metrics
            embed = discord.Embed(
                title="🤖 AI Assistant",
                description=ai_response,
                color=0x00D084
            )
            embed.set_footer(text=f"Model: {model} | Requested by {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ AI service error: {str(e)}", ephemeral=True)

    @app_commands.command(name="analyze-image", description="Analyze an image with AI vision")
    @app_commands.describe(
        image="Image to analyze",
        prompt="What would you like to know about the image?"
    )
    async def analyze_image(self, interaction: discord.Interaction, 
                           image: discord.Attachment, prompt: str = "Describe this image"):
        await interaction.response.defer()
        
        try:
            if not image.content_type.startswith('image/'):
                await interaction.followup.send("❌ Please provide a valid image file.", ephemeral=True)
                return
            
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
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            embed = discord.Embed(
                title="👁️ AI Image Analysis",
                description=response.choices[0].message.content,
                color=discord.Color.purple()
            )
            embed.set_image(url=image.url)
            embed.set_footer(text=f"Analysis by {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Image analysis error: {str(e)}", ephemeral=True)

    @app_commands.command(name="generate-image", description="Generate an image with AI")
    @app_commands.describe(
        prompt="Description of the image you want",
        style="Art style for the image",
        size="Image size"
    )
    @app_commands.choices(
        style=[
            app_commands.Choice(name="Realistic", value="photorealistic"),
            app_commands.Choice(name="Anime", value="anime style"),
            app_commands.Choice(name="Digital Art", value="digital art"),
            app_commands.Choice(name="Oil Painting", value="oil painting"),
            app_commands.Choice(name="Cartoon", value="cartoon style")
        ],
        size=[
            app_commands.Choice(name="Square (1024x1024)", value="1024x1024"),
            app_commands.Choice(name="Portrait (1024x1792)", value="1024x1792"),
            app_commands.Choice(name="Landscape (1792x1024)", value="1792x1024")
        ]
    )
    async def generate_image(self, interaction: discord.Interaction, prompt: str, 
                           style: str = "", size: str = "1024x1024"):
        await interaction.response.defer()
        
        try:
            full_prompt = f"{prompt}, {style}" if style else prompt
            
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=full_prompt,
                size=size,
                quality="standard",
                n=1
            )
            
            embed = discord.Embed(
                title="🎨 AI Generated Image",
                description=f"**Prompt:** {prompt}",
                color=discord.Color.green()
            )
            embed.set_image(url=response.data[0].url)
            embed.set_footer(text=f"Generated for {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Image generation error: {str(e)}", ephemeral=True)

    @app_commands.command(name="summarize", description="Summarize text or web content")
    @app_commands.describe(
        content="Text to summarize or URL to web page",
        length="Summary length preference"
    )
    @app_commands.choices(length=[
        app_commands.Choice(name="Brief", value="brief"),
        app_commands.Choice(name="Detailed", value="detailed"),
        app_commands.Choice(name="Key Points", value="bullets")
    ])
    async def summarize_content(self, interaction: discord.Interaction, 
                              content: str, length: str = "brief"):
        await interaction.response.defer()
        
        try:
            # Check if content is a URL
            if content.startswith(('http://', 'https://')):
                async with aiohttp.ClientSession() as session:
                    async with session.get(content) as resp:
                        if resp.status == 200:
                            html_content = await resp.text()
                            # Simple text extraction (in production, use proper HTML parser)
                            content = html_content[:4000]  # Limit content length
            
            system_prompts = {
                "brief": "Provide a brief, concise summary in 2-3 sentences.",
                "detailed": "Provide a detailed summary with main points and context.",
                "bullets": "Summarize as bullet points highlighting key information."
            }
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompts[length]},
                    {"role": "user", "content": f"Summarize this content: {content}"}
                ],
                max_tokens=500
            )
            
            embed = discord.Embed(
                title="📝 Content Summary",
                description=response.choices[0].message.content,
                color=discord.Color.orange()
            )
            embed.set_footer(text=f"Summary type: {length} | Requested by {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Summary error: {str(e)}", ephemeral=True)



    @app_commands.command(name="code-explain", description="Explain code or programming concepts")
    @app_commands.describe(
        code="Code to explain or programming question",
        language="Programming language (if applicable)"
    )
    async def explain_code(self, interaction: discord.Interaction, code: str, 
                          language: str = "auto-detect"):
        await interaction.response.defer()
        
        try:
            prompt = f"Explain this code in detail, including what it does and how it works"
            if language != "auto-detect":
                prompt += f" (Language: {language})"
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a programming expert. Explain code clearly and educationally."},
                    {"role": "user", "content": f"{prompt}:\n\n```{code}```"}
                ],
                max_tokens=1500
            )
            
            embed = discord.Embed(
                title="💻 Code Explanation",
                description=response.choices[0].message.content,
                color=discord.Color.dark_blue()
            )
            embed.add_field(name="Code", value=f"```{language}\n{code[:500]}```", inline=False)
            embed.set_footer(text=f"Explained for {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Code explanation error: {str(e)}", ephemeral=True)

    @app_commands.command(name="sentiment", description="Analyze sentiment of text")
    @app_commands.describe(text="Text to analyze for sentiment")
    async def analyze_sentiment(self, interaction: discord.Interaction, text: str):
        await interaction.response.defer()
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system", 
                        "content": "Analyze sentiment and provide a score from -1 (very negative) to 1 (very positive), with explanation. Format as JSON: {\"score\": 0.5, \"sentiment\": \"positive\", \"explanation\": \"...\", \"confidence\": 0.9}"
                    },
                    {"role": "user", "content": text}
                ],
                response_format={"type": "json_object"},
                max_tokens=300
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Determine color based on sentiment
            if result["score"] > 0.3:
                color = discord.Color.green()
                emoji = "😊"
            elif result["score"] < -0.3:
                color = discord.Color.red()
                emoji = "😞"
            else:
                color = discord.Color.yellow()
                emoji = "😐"
            
            embed = discord.Embed(
                title=f"{emoji} Sentiment Analysis",
                color=color
            )
            embed.add_field(name="Text", value=text[:500], inline=False)
            embed.add_field(name="Sentiment", value=result["sentiment"].title(), inline=True)
            embed.add_field(name="Score", value=f"{result['score']:.2f}", inline=True)
            embed.add_field(name="Confidence", value=f"{result['confidence']:.1%}", inline=True)
            embed.add_field(name="Analysis", value=result["explanation"], inline=False)
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Sentiment analysis error: {str(e)}", ephemeral=True)

    @app_commands.command(name="ai-conversation", description="Start an AI conversation thread")
    @app_commands.describe(
        topic="Topic or initial message for the conversation",
        personality="AI personality to use"
    )
    @app_commands.choices(personality=[
        app_commands.Choice(name="Friendly Assistant", value="friendly"),
        app_commands.Choice(name="Professional", value="professional"),
        app_commands.Choice(name="Creative Writer", value="creative"),
        app_commands.Choice(name="Technical Expert", value="technical"),
        app_commands.Choice(name="Casual Friend", value="casual")
    ])
    async def start_ai_conversation(self, interaction: discord.Interaction, 
                                  topic: str, personality: str = "friendly"):
        await interaction.response.defer()
        
        try:
            personalities = {
                "friendly": "You are a warm, friendly AI assistant who loves helping people.",
                "professional": "You are a professional, knowledgeable AI assistant.",
                "creative": "You are a creative, imaginative AI assistant who thinks outside the box.",
                "technical": "You are a technical expert AI assistant with deep knowledge.",
                "casual": "You are a casual, laid-back AI assistant who speaks informally."
            }
            
            thread = await interaction.followup.send(
                f"🧠 Starting AI conversation about: **{topic}**\nPersonality: {personality.title()}"
            )
            
            # Store conversation context in memory (in production, use database)
            conversation_data = {
                "personality": personalities[personality],
                "messages": [{"role": "user", "content": topic}]
            }
            
            # Generate initial response
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": personalities[personality]},
                    {"role": "user", "content": topic}
                ],
                max_tokens=1000
            )
            
            embed = discord.Embed(
                title="🤖 AI Response",
                description=response.choices[0].message.content,
                color=discord.Color.blue()
            )
            embed.set_footer(text="Reply to continue the conversation!")
            
            await thread.edit(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Conversation error: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AIFeatures(bot))