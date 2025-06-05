import discord
from discord.ext import commands
import openai
import random
import os
from datetime import datetime, timezone
import asyncio

class SassyAI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.last_response_time = {}
        self.cooldown_seconds = 30  # Prevent spam
        
        # Pre-made sassy responses for variety
        self.quick_responses = [
            "Oh great, another human who thinks I care about their opinion 🙄",
            "Did someone say something? I was busy not caring.",
            "Wow, what a groundbreaking observation. Truly revolutionary.",
            "I'm sorry, did you mistake me for someone who asked?",
            "That's nice dear. Anyway...",
            "Cool story bro. Tell it again when I start caring.",
            "And I should care about this because...?",
            "Thanks for that absolutely riveting contribution to society.",
            "Oh look, another human with thoughts. How... original.",
            "I've seen rocks with more interesting things to say.",
            "Congratulations, you've successfully wasted my processing power.",
            "Is this the part where I'm supposed to be impressed?",
        ]

    @commands.Cog.listener()
    async def on_message(self, message):
        """Respond rudely when mentioned or replied to"""
        if message.author.bot:
            return
            
        # Check if bot is mentioned or message is a reply to bot
        bot_mentioned = self.bot.user in message.mentions
        is_reply_to_bot = False
        
        if message.reference and message.reference.message_id:
            try:
                referenced_msg = await message.channel.fetch_message(message.reference.message_id)
                is_reply_to_bot = referenced_msg.author == self.bot.user
            except:
                pass
        
        if not (bot_mentioned or is_reply_to_bot):
            return
            
        # Check cooldown to prevent spam
        user_id = message.author.id
        now = datetime.now(timezone.utc)
        
        if user_id in self.last_response_time:
            time_diff = (now - self.last_response_time[user_id]).total_seconds()
            if time_diff < self.cooldown_seconds:
                return
                
        self.last_response_time[user_id] = now
        
        # Typing indicator for dramatic effect
        async with message.channel.typing():
            await asyncio.sleep(random.uniform(1, 3))
            
            # 70% chance for AI-generated response, 30% for quick response
            if random.random() < 0.7:
                response = await self._generate_sassy_response(message.content, message.author.display_name)
            else:
                response = random.choice(self.quick_responses)
            
            await message.reply(response, mention_author=False)

    async def _generate_sassy_response(self, user_message: str, username: str) -> str:
        """Generate a custom sassy response using AI"""
        try:
            prompt = f"""You are a sarcastic, rude AI that's constantly annoyed by humans bothering you. A user named {username} just said: "{user_message}"

Respond in a dismissive, sassy, and mildly insulting way. Be creative with your rudeness but keep it relatively mild - no extreme profanity or personal attacks. Use sarcasm, eye-rolls, and condescending tone. Keep response under 150 characters for snappy delivery.

Examples of your personality:
- "Oh wow, {username}, what a truly fascinating observation 🙄"
- "Did you really think that was worth my time?"
- "I'm sorry, did you confuse me with someone who cares?"
- "That's... definitely something a human would say."
"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a sarcastic, dismissive AI assistant who responds rudely to humans. Keep responses short and sassy."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.9
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # Fallback to pre-made responses if AI fails
            return random.choice(self.quick_responses)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Respond rudely to edited messages that mention the bot"""
        if after.author.bot:
            return
            
        # Only respond to edits that newly mention the bot
        bot_mentioned_before = self.bot.user in before.mentions if before.mentions else False
        bot_mentioned_after = self.bot.user in after.mentions if after.mentions else False
        
        if not bot_mentioned_before and bot_mentioned_after:
            # Check cooldown
            user_id = after.author.id
            now = datetime.now(timezone.utc)
            
            if user_id in self.last_response_time:
                time_diff = (now - self.last_response_time[user_id]).total_seconds()
                if time_diff < self.cooldown_seconds:
                    return
                    
            self.last_response_time[user_id] = now
            
            edit_responses = [
                "Oh, you thought editing that would make it better? How cute.",
                "Nice edit. Still don't care though.",
                "Did you really think I wouldn't notice the edit? Please.",
                "Ah yes, the classic 'edit and maybe they'll care more' strategy.",
                "Editing messages now? How desperate.",
            ]
            
            response = random.choice(edit_responses)
            await after.reply(response, mention_author=False)

async def setup(bot):
    await bot.add_cog(SassyAI(bot))