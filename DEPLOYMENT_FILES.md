# New AI Features Deployment

## Files to Copy to Your Local Bot

Copy these three files to your `C:\Users\darea\Downloads\discord-bot-clean\cogs\` folder:

### 1. sassy_ai.py
```python
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
        self.cooldown_seconds = 30
        
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
            "Your point being what exactly?",
            "That's fascinating. Said no one ever.",
            "I'm sure that sounded better in your head."
        ]

    @commands.Cog.listener()
    async def on_message(self, message):
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
            
        user_id = message.author.id
        now = datetime.now(timezone.utc)
        
        # Check cooldown
        if user_id in self.last_response_time:
            time_diff = (now - self.last_response_time[user_id]).total_seconds()
            if time_diff < self.cooldown_seconds:
                return
                
        self.last_response_time[user_id] = now
        
        # Add typing indicator for dramatic effect
        async with message.channel.typing():
            await asyncio.sleep(random.uniform(1, 3))
            
            # 70% chance for AI response, 30% for quick response
            if random.random() < 0.7 and os.getenv('OPENAI_API_KEY'):
                response = await self._generate_sassy_response(message.content, message.author.display_name)
            else:
                response = random.choice(self.quick_responses)
            
            await message.reply(response, mention_author=False)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Respond to edited messages that newly mention the bot"""
        if after.author.bot:
            return
            
        # Check if the edit added a mention of the bot
        bot_mentioned_before = self.bot.user in before.mentions
        bot_mentioned_after = self.bot.user in after.mentions
        
        if not bot_mentioned_before and bot_mentioned_after:
            # Treat as new mention
            await self.on_message(after)

    async def _generate_sassy_response(self, user_message: str, username: str) -> str:
        """Generate AI-powered sassy response"""
        try:
            prompt = f"You are a sarcastic, dismissive AI assistant. A user named {username} said: '{user_message}'. Respond with a rude, sassy comment but keep it under 150 characters. Be witty and dismissive but not offensive."
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a sarcastic, dismissive AI. Respond rudely but briefly. Be witty and sassy."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.9
            )
            
            result = response.choices[0].message.content
            return result.strip() if result else random.choice(self.quick_responses)
            
        except Exception as e:
            # Fallback to quick responses if AI fails
            return random.choice(self.quick_responses)

async def setup(bot):
    await bot.add_cog(SassyAI(bot))
```

## Deployment Commands

After copying all three files, run these PowerShell commands:

```powershell
cd "C:\Users\darea\Downloads\discord-bot-clean"
git add .
git commit -m "Add sassy AI responses and 13 new AI entertainment commands"
git push heroku main
heroku logs --tail --app my-discord-bot-2025
```

## New Features Added

### Sassy AI
- Responds rudely when bot is mentioned or replied to
- 30-second cooldown per user
- 70% AI-generated responses, 30% quick comebacks
- Typing indicator for dramatic effect

### AI Entertainment (8 commands)
- /ai-persona - Chat with wizard, detective, comedian, therapist, coach
- /ai-story - Interactive stories in multiple genres
- /ai-roast - Friendly AI roasts
- /ai-advice - Therapist advice
- /ai-motivate - Motivational coaching
- /ai-create - Collaborative creativity (poems, lyrics, stories, business ideas)
- /ai-debate - Balanced debates on any topic

### AI Games (5 commands)
- /twenty-questions - Interactive 20 Questions game
- /ai-riddle - AI-generated riddles with difficulty levels
- /ai-trivia - Multiple choice trivia with interactive buttons
- /ai-wordgame - Story building, rhyming, word association
- /ai-mystery - Interactive mystery scenarios

Total: 13 new AI-powered commands + sassy mention responses