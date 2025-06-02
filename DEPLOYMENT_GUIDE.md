# Discord Bot Deployment Guide

## Complete Steps to Deploy to GitHub and Heroku

### Prerequisites
- Git installed on your local machine
- Heroku CLI installed
- GitHub account
- Heroku account

### Step 1: Download Files from Replit
Download these files to your local project folder:
- `main.py`
- `cogs/` folder (containing all 7 cog files)
- `requirements.txt`
- `Procfile`
- `runtime.txt`
- `app.json`
- `.env.example`

### Step 2: Set up Local Git Repository
```bash
# Navigate to your project folder
cd your-bot-project

# Initialize git if not already done
git init

# Add all files
git add .

# Commit changes
git commit -m "Clean bot version - removed automated messaging"
```

### Step 3: Connect to GitHub
```bash
# Add your GitHub repository as remote
git remote add origin https://github.com/yourusername/your-repo-name.git

# Push to GitHub
git push -u origin main
```

### Step 4: Deploy to Heroku
```bash
# Login to Heroku
heroku login

# Add Heroku remote for your existing app
heroku git:remote -a trrr-bot

# Push to Heroku
git push heroku main --force
```

### Step 5: Set Environment Variables on Heroku
```bash
# Set Discord bot token
heroku config:set DISCORD_TOKEN=your_discord_bot_token -a trrr-bot

# Set OpenAI API key (for AI commands)
heroku config:set OPENAI_API_KEY=your_openai_api_key -a trrr-bot
```

### Step 6: Verify Deployment
```bash
# Check app status
heroku ps -a trrr-bot

# View logs
heroku logs --tail -a trrr-bot
```

## Bot Features (40+ Commands)
- **AI Features**: /ai, /clear-conversation
- **Basic Commands**: /ping, /info, /uptime, /serverinfo, /userinfo, /avatar
- **Moderation**: /kick, /ban, /unban, /timeout, /untimeout, /clear
- **Economy**: /balance, /daily, /work, /crime, /leaderboard
- **Utility**: /remind, /poll, /choose, /8ball, /dice, /flip, /say, /embed, /membercount
- **Entertainment**: /joke, /fact, /quote, /riddle, /trivia, /meme, /roast, /compliment
- **Leveling**: /rank, /leaderboard-xp, /give-xp, /reset-levels

## Important Notes
- All automated messaging has been completely removed
- No conversation sparks, gratitude moments, or activity boosters
- Bot only responds to slash commands
- No automatic responses when mentioned
- Database tables will be created automatically when commands are used

## Troubleshooting
If deployment fails:
1. Check your environment variables are set correctly
2. Verify your Discord token is valid
3. Ensure all files are properly uploaded
4. Check Heroku logs for specific errors

Your bot is now ready for deployment with clean functionality and no unwanted automated messages.